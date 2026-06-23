function run_oversampling_offgrid_ablation()
%RUN_OVERSAMPLING_OFFGRID_ABLATION
% Lightweight reproducible experiment for TechnicalDesign v2.2 Section 6.5.13.
%
% This is not the final learned T-OMP-Net training run. It isolates the
% physical question behind the new ablation: how much grid densification is
% needed before a bounded off-grid refinement step closes most of the
% angle-delay-Doppler mismatch.

rootDir = fileparts(fileparts(mfilename('fullpath')));
outDir = fullfile(rootDir, 'Results', 'oversampling_offgrid_ablation');
if ~exist(outDir, 'dir')
    mkdir(outDir);
end

rng(20260623, 'twister');

cfg = struct();
cfg.Nv = 32;              % Nt * Nr virtual aperture in the current MATLAB prototype
cfg.K = 16;               % FDMA effective subcarriers per transmitter
cfg.M = 16;               % OFDM symbols in the lightweight smoke experiment
cfg.thetaRangeDeg = [-60, 60];
cfg.tauSpanNs = 100;
cfg.dopplerSpanHz = 1000;
cfg.snrDb = 20;
cfg.trials = 24;
cfg.baseGtheta = cfg.Nv;
cfg.baseGtau = cfg.K;
cfg.baseGnu = cfg.M;
cfg.fixedRho = 2;
cfg.rhoValues = [1, 2, 4, 8];

scanNames = {'theta', 'tau', 'nu'};
allRows = {};

for s = 1:numel(scanNames)
    scanDim = scanNames{s};
    for r = 1:numel(cfg.rhoValues)
        rho = cfg.rhoValues(r);
        localCfg = grid_config(cfg, scanDim, rho);
        fprintf('Running scan=%s rho=%g grid=%dx%dx%d\n', ...
            scanDim, rho, localCfg.Gtheta, localCfg.Gtau, localCfg.Gnu);
        summary = run_condition(localCfg);
        allRows(end+1, :) = { ...
            scanDim, rho, localCfg.Gtheta, localCfg.Gtau, localCfg.Gnu, ...
            localCfg.Gtheta * localCfg.Gtau * localCfg.Gnu, ...
            summary.thetaGridDeg, summary.thetaOffgridDeg, ...
            summary.tauGridNs, summary.tauOffgridNs, ...
            summary.nuGridHz, summary.nuOffgridHz, ...
            summary.nmseGridDb, summary.nmseOffgridDb, ...
            summary.avgRuntimeSec}; %#ok<AGROW>
    end
end

results = cell2table(allRows, 'VariableNames', { ...
    'scan_dim', 'rho', 'G_theta', 'G_tau', 'G_nu', 'dictionary_atoms', ...
    'theta_rmse_grid_deg', 'theta_rmse_offgrid_deg', ...
    'tau_rmse_grid_ns', 'tau_rmse_offgrid_ns', ...
    'doppler_rmse_grid_hz', 'doppler_rmse_offgrid_hz', ...
    'nmse_grid_db', 'nmse_offgrid_db', 'avg_runtime_s'});

csvPath = fullfile(outDir, 'oversampling_offgrid_ablation.csv');
writetable(results, csvPath);

save(fullfile(outDir, 'oversampling_offgrid_ablation.mat'), 'results', 'cfg');
plot_results(results, outDir);
write_summary(results, cfg, outDir);

fprintf('Saved results to %s\n', outDir);
end

function localCfg = grid_config(cfg, scanDim, rho)
localCfg = cfg;
rhoTheta = cfg.fixedRho;
rhoTau = cfg.fixedRho;
rhoNu = cfg.fixedRho;

switch scanDim
    case 'theta'
        rhoTheta = rho;
    case 'tau'
        rhoTau = rho;
    case 'nu'
        rhoNu = rho;
    otherwise
        error('Unknown scan dimension: %s', scanDim);
end

localCfg.Gtheta = cfg.baseGtheta * rhoTheta;
localCfg.Gtau = cfg.baseGtau * rhoTau;
localCfg.Gnu = cfg.baseGnu * rhoNu;
localCfg.scanDim = scanDim;
localCfg.rho = rho;
localCfg.thetaGrid = linspace(deg2rad(cfg.thetaRangeDeg(1)), ...
    deg2rad(cfg.thetaRangeDeg(2)), localCfg.Gtheta);
localCfg.tauGrid = linspace(0, 1, localCfg.Gtau);
localCfg.nuGrid = linspace(-0.5, 0.5, localCfg.Gnu);
localCfg.A = dictionary_theta(localCfg.thetaGrid, cfg.Nv);
localCfg.P = dictionary_tau(localCfg.tauGrid, cfg.K);
localCfg.D = dictionary_nu(localCfg.nuGrid, cfg.M);
end

function summary = run_condition(cfg)
thetaGridErr = zeros(cfg.trials, 1);
thetaRefErr = zeros(cfg.trials, 1);
tauGridErr = zeros(cfg.trials, 1);
tauRefErr = zeros(cfg.trials, 1);
nuGridErr = zeros(cfg.trials, 1);
nuRefErr = zeros(cfg.trials, 1);
nmseGrid = zeros(cfg.trials, 1);
nmseRef = zeros(cfg.trials, 1);
runtime = zeros(cfg.trials, 1);

for trial = 1:cfg.trials
    thetaTrue = deg2rad(cfg.thetaRangeDeg(1) + diff(cfg.thetaRangeDeg) * rand());
    tauTrue = rand();
    nuTrue = -0.45 + 0.90 * rand();
    alphaTrue = exp(1j * 2 * pi * rand());

    cleanAtom = atom_tensor(thetaTrue, tauTrue, nuTrue, cfg);
    cleanY = alphaTrue * cleanAtom;
    noisePower = mean(abs(cleanY(:)).^2) / (10^(cfg.snrDb / 10));
    noise = sqrt(noisePower / 2) * (randn(size(cleanY)) + 1j * randn(size(cleanY)));
    noisyY = cleanY + noise;

    tic;
    [theta0, tau0, nu0] = grid_estimate(noisyY, cfg);
    [theta1, tau1, nu1] = refine_offgrid(noisyY, cfg, theta0, tau0, nu0);
    runtime(trial) = toc;

    alphaGrid = project_alpha(noisyY, theta0, tau0, nu0, cfg);
    alphaRef = project_alpha(noisyY, theta1, tau1, nu1, cfg);
    gridY = alphaGrid * atom_tensor(theta0, tau0, nu0, cfg);
    refY = alphaRef * atom_tensor(theta1, tau1, nu1, cfg);

    thetaGridErr(trial) = abs(rad2deg(theta0 - thetaTrue));
    thetaRefErr(trial) = abs(rad2deg(theta1 - thetaTrue));
    tauGridErr(trial) = abs(tau0 - tauTrue) * cfg.tauSpanNs;
    tauRefErr(trial) = abs(tau1 - tauTrue) * cfg.tauSpanNs;
    nuGridErr(trial) = abs(nu0 - nuTrue) * cfg.dopplerSpanHz;
    nuRefErr(trial) = abs(nu1 - nuTrue) * cfg.dopplerSpanHz;
    nmseGrid(trial) = nmse_db(cleanY, gridY);
    nmseRef(trial) = nmse_db(cleanY, refY);
end

summary = struct();
summary.thetaGridDeg = rms(thetaGridErr);
summary.thetaOffgridDeg = rms(thetaRefErr);
summary.tauGridNs = rms(tauGridErr);
summary.tauOffgridNs = rms(tauRefErr);
summary.nuGridHz = rms(nuGridErr);
summary.nuOffgridHz = rms(nuRefErr);
summary.nmseGridDb = mean(nmseGrid);
summary.nmseOffgridDb = mean(nmseRef);
summary.avgRuntimeSec = mean(runtime);
end

function [thetaHat, tauHat, nuHat] = grid_estimate(Y, cfg)
Ctheta = cfg.A' * reshape(Y, cfg.Nv, cfg.K * cfg.M);
Ctheta = reshape(Ctheta, cfg.Gtheta, cfg.K, cfg.M);

tmpTau = permute(Ctheta, [2, 1, 3]);
Ctau = cfg.P' * reshape(tmpTau, cfg.K, cfg.Gtheta * cfg.M);
Ctau = reshape(Ctau, cfg.Gtau, cfg.Gtheta, cfg.M);
Ctau = permute(Ctau, [2, 1, 3]);

tmpNu = permute(Ctau, [3, 1, 2]);
Cnu = cfg.D' * reshape(tmpNu, cfg.M, cfg.Gtheta * cfg.Gtau);
Cnu = reshape(Cnu, cfg.Gnu, cfg.Gtheta, cfg.Gtau);
C = permute(Cnu, [2, 3, 1]);

[~, linearIdx] = max(abs(C(:)));
[thetaIdx, tauIdx, nuIdx] = ind2sub(size(C), linearIdx);
thetaHat = cfg.thetaGrid(thetaIdx);
tauHat = cfg.tauGrid(tauIdx);
nuHat = cfg.nuGrid(nuIdx);
end

function [thetaHat, tauHat, nuHat] = refine_offgrid(Y, cfg, theta0, tau0, nu0)
thetaStep = grid_half_step(cfg.thetaGrid, deg2rad(diff(cfg.thetaRangeDeg)));
tauStep = grid_half_step(cfg.tauGrid, 1);
nuStep = grid_half_step(cfg.nuGrid, 1);

thetaBounds = [max(deg2rad(cfg.thetaRangeDeg(1)), theta0 - thetaStep), ...
    min(deg2rad(cfg.thetaRangeDeg(2)), theta0 + thetaStep)];
tauBounds = [max(0, tau0 - tauStep), min(1, tau0 + tauStep)];
nuBounds = [max(-0.5, nu0 - nuStep), min(0.5, nu0 + nuStep)];

thetaHat = theta0;
tauHat = tau0;
nuHat = nu0;

for pass = 1:3
    thetaHat = golden_max(@(x) corr_objective(Y, x, tauHat, nuHat, cfg), thetaBounds(1), thetaBounds(2), 12);
    tauHat = golden_max(@(x) corr_objective(Y, thetaHat, x, nuHat, cfg), tauBounds(1), tauBounds(2), 12);
    nuHat = golden_max(@(x) corr_objective(Y, thetaHat, tauHat, x, cfg), nuBounds(1), nuBounds(2), 12);
end
end

function step = grid_half_step(grid, fullRange)
if numel(grid) > 1
    step = abs(grid(2) - grid(1)) / 2;
else
    step = fullRange / 2;
end
end

function score = corr_objective(Y, theta, tauNorm, nuNorm, cfg)
a = atom_tensor(theta, tauNorm, nuNorm, cfg);
score = abs(sum(conj(a(:)) .* Y(:))).^2;
end

function xBest = golden_max(fun, lo, hi, iterations)
if hi <= lo
    xBest = lo;
    return;
end

gr = (sqrt(5) - 1) / 2;
c = hi - gr * (hi - lo);
d = lo + gr * (hi - lo);
fc = fun(c);
fd = fun(d);

for i = 1:iterations
    if fc < fd
        lo = c;
        c = d;
        fc = fd;
        d = lo + gr * (hi - lo);
        fd = fun(d);
    else
        hi = d;
        d = c;
        fd = fc;
        c = hi - gr * (hi - lo);
        fc = fun(c);
    end
end

xBest = (lo + hi) / 2;
end

function alpha = project_alpha(Y, theta, tauNorm, nuNorm, cfg)
a = atom_tensor(theta, tauNorm, nuNorm, cfg);
alpha = sum(conj(a(:)) .* Y(:)) / sum(abs(a(:)).^2);
end

function A = dictionary_theta(thetaGrid, Nv)
v = (0:Nv-1).';
A = exp(1j * pi * v * sin(thetaGrid)) / sqrt(Nv);
end

function P = dictionary_tau(tauGrid, K)
k = (0:K-1).';
P = exp(-1j * 2 * pi * k * tauGrid) / sqrt(K);
end

function D = dictionary_nu(nuGrid, M)
m = (0:M-1).';
D = exp(1j * 2 * pi * m * nuGrid) / sqrt(M);
end

function A = atom_tensor(theta, tauNorm, nuNorm, cfg)
a = dictionary_theta(theta, cfg.Nv);
p = dictionary_tau(tauNorm, cfg.K);
d = dictionary_nu(nuNorm, cfg.M);
A = reshape(a, cfg.Nv, 1, 1) .* reshape(p, 1, cfg.K, 1) .* reshape(d, 1, 1, cfg.M);
end

function val = nmse_db(reference, estimate)
val = 10 * log10(norm(reference(:) - estimate(:))^2 / max(norm(reference(:))^2, eps));
end

function plot_results(results, outDir)
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 1200 360]);
scanNames = {'theta', 'tau', 'nu'};
metricGrid = {'theta_rmse_grid_deg', 'tau_rmse_grid_ns', 'doppler_rmse_grid_hz'};
metricRef = {'theta_rmse_offgrid_deg', 'tau_rmse_offgrid_ns', 'doppler_rmse_offgrid_hz'};
yLabels = {'Angle RMSE (deg)', 'Delay RMSE (ns)', 'Doppler RMSE (Hz)'};

for i = 1:numel(scanNames)
    subplot(1, 3, i);
    rows = strcmp(results.scan_dim, scanNames{i});
    rho = results.rho(rows);
    [rho, order] = sort(rho);
    gridVals = results.(metricGrid{i})(rows);
    refVals = results.(metricRef{i})(rows);
    semilogy(rho, gridVals(order), '-o', 'LineWidth', 1.4);
    hold on;
    semilogy(rho, refVals(order), '-s', 'LineWidth', 1.4);
    grid on;
    xlabel('Oversampling ratio \rho');
    ylabel(yLabels{i});
    title(sprintf('%s scan', scanNames{i}));
    legend('Grid only', 'Bounded off-grid', 'Location', 'southwest');
end

pngPath = fullfile(outDir, 'oversampling_offgrid_ablation.png');
pdfPath = fullfile(outDir, 'oversampling_offgrid_ablation.pdf');
try
    exportgraphics(fig, pngPath, 'Resolution', 200);
    exportgraphics(fig, pdfPath, 'ContentType', 'vector');
catch
    saveas(fig, pngPath);
    saveas(fig, pdfPath);
end
close(fig);
end

function write_summary(results, cfg, outDir)
summaryPath = fullfile(outDir, 'summary.md');
fid = fopen(summaryPath, 'w');
cleanup = onCleanup(@() fclose(fid));

fprintf(fid, '# Oversampling and Off-Grid Ablation\n\n');
fprintf(fid, 'This lightweight experiment supports TechnicalDesign v2.2 Section 6.5.13. ');
fprintf(fid, 'It isolates one rank-1 angle-delay-Doppler component and compares coarse grid matching with bounded local off-grid refinement.\n\n');
fprintf(fid, '- Seed: `20260623`\n');
fprintf(fid, '- Trials per condition: `%d`\n', cfg.trials);
fprintf(fid, '- SNR: `%g dB`\n', cfg.snrDb);
fprintf(fid, '- Tensor size: `%d x %d x %d`\n\n', cfg.Nv, cfg.K, cfg.M);
fprintf(fid, 'The run is a smoke/ablation experiment, not the final learned T-OMP-Net result.\n\n');
fprintf(fid, '## Result Table\n\n');
fprintf(fid, '| scan | rho | atoms | theta grid | theta offgrid | tau grid | tau offgrid | doppler grid | doppler offgrid | NMSE grid | NMSE offgrid |\n');
fprintf(fid, '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n');
for i = 1:height(results)
    fprintf(fid, '| %s | %.0f | %.0f | %.4g | %.4g | %.4g | %.4g | %.4g | %.4g | %.4g | %.4g |\n', ...
        results.scan_dim{i}, results.rho(i), results.dictionary_atoms(i), ...
        results.theta_rmse_grid_deg(i), results.theta_rmse_offgrid_deg(i), ...
        results.tau_rmse_grid_ns(i), results.tau_rmse_offgrid_ns(i), ...
        results.doppler_rmse_grid_hz(i), results.doppler_rmse_offgrid_hz(i), ...
        results.nmse_grid_db(i), results.nmse_offgrid_db(i));
end
end

