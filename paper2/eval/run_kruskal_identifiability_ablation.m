function run_kruskal_identifiability_ablation()
%RUN_KRUSKAL_IDENTIFIABILITY_ABLATION
% Lightweight reproducible experiment for TechnicalDesign v2.2 Section 6.5.13.
%
% This smoke experiment studies how a Tensor-OMP style greedy recovery
% degrades as the number of sparse angle-delay-Doppler components approaches
% the Kruskal identifiability bound of the simulated tensor dimensions.

rootDir = fileparts(fileparts(mfilename('fullpath')));
outDir = fullfile(rootDir, 'Results', 'kruskal_identifiability_ablation');
if ~exist(outDir, 'dir')
    mkdir(outDir);
end

rng(20260623, 'twister');

cfg = struct();
cfg.Nv = 32;
cfg.K = 16;
cfg.M = 16;
cfg.rho = 2;
cfg.Gtheta = cfg.Nv * cfg.rho;
cfg.Gtau = cfg.K * cfg.rho;
cfg.Gnu = cfg.M * cfg.rho;
cfg.thetaRangeDeg = [-60, 60];
cfg.snrDb = 20;
cfg.trials = 6;
cfg.LValues = [2, 4, 8, 16, 24, 32];
cfg.localKruskalBound = floor((cfg.Nv + cfg.K + cfg.M - 2) / 2);
cfg.paperNv = 128;
cfg.paperK = 16;
cfg.paperM = 32;
cfg.paperKruskalBound = floor((cfg.paperNv + cfg.paperK + cfg.paperM - 2) / 2);

cfg.thetaGrid = linspace(deg2rad(cfg.thetaRangeDeg(1)), ...
    deg2rad(cfg.thetaRangeDeg(2)), cfg.Gtheta);
cfg.tauGrid = linspace(0, 1, cfg.Gtau);
cfg.nuGrid = linspace(-0.5, 0.5, cfg.Gnu);
cfg.A = dictionary_theta(cfg.thetaGrid, cfg.Nv);
cfg.P = dictionary_tau(cfg.tauGrid, cfg.K);
cfg.D = dictionary_nu(cfg.nuGrid, cfg.M);

rows = {};
for idx = 1:numel(cfg.LValues)
    L = cfg.LValues(idx);
    fprintf('Running L=%d, local Kruskal bound=%d\n', L, cfg.localKruskalBound);
    summary = run_condition(cfg, L);
    rows(end+1, :) = { ...
        L, cfg.localKruskalBound, L / cfg.localKruskalBound, ...
        summary.pd, summary.supportExactRate, summary.nmseDb, ...
        summary.avgRuntimeSec, summary.avgResidualEnergyDb}; %#ok<AGROW>
end

results = cell2table(rows, 'VariableNames', { ...
    'num_targets', 'local_kruskal_bound', 'bound_ratio', ...
    'detection_probability', 'exact_support_rate', ...
    'nmse_db', 'avg_runtime_s', 'residual_energy_db'});

csvPath = fullfile(outDir, 'kruskal_identifiability_ablation.csv');
writetable(results, csvPath);
save(fullfile(outDir, 'kruskal_identifiability_ablation.mat'), 'results', 'cfg');
plot_results(results, cfg, outDir);
write_summary(results, cfg, outDir);

fprintf('Saved results to %s\n', outDir);
end

function summary = run_condition(cfg, L)
pd = zeros(cfg.trials, 1);
exactRate = zeros(cfg.trials, 1);
nmseVals = zeros(cfg.trials, 1);
runtime = zeros(cfg.trials, 1);
residualVals = zeros(cfg.trials, 1);

for trial = 1:cfg.trials
    support = sample_support(cfg, L);
    [Y, coeffs] = synthesize_tensor(cfg, support);
    noisePower = mean(abs(Y(:)).^2) / (10^(cfg.snrDb / 10));
    noise = sqrt(noisePower / 2) * (randn(size(Y)) + 1j * randn(size(Y)));
    noisyY = Y + noise;

    tic;
    [estSupport, estCoeff, residual] = tensor_omp(noisyY, cfg, L);
    runtime(trial) = toc;

    Yhat = reconstruct_tensor(cfg, estSupport, estCoeff);
    pd(trial) = support_detection_probability(support, estSupport);
    exactRate(trial) = exact_support_rate(support, estSupport);
    nmseVals(trial) = nmse_db(Y, Yhat);
    residualVals(trial) = energy_ratio_db(residual, noisyY);

    %#ok<NASGU> keeps coeffs explicit as part of the generated sample state.
    coeffs = coeffs;
end

summary = struct();
summary.pd = mean(pd);
summary.supportExactRate = mean(exactRate);
summary.nmseDb = mean(nmseVals);
summary.avgRuntimeSec = mean(runtime);
summary.avgResidualEnergyDb = mean(residualVals);
end

function support = sample_support(cfg, L)
totalAtoms = cfg.Gtheta * cfg.Gtau * cfg.Gnu;
linearIdx = randperm(totalAtoms, L);
[ti, ai, di] = ind2sub([cfg.Gtheta, cfg.Gtau, cfg.Gnu], linearIdx);
support = [ti(:), ai(:), di(:)];
end

function [Y, coeffs] = synthesize_tensor(cfg, support)
L = size(support, 1);
coeffs = (randn(L, 1) + 1j * randn(L, 1)) / sqrt(2 * L);
Y = zeros(cfg.Nv, cfg.K, cfg.M);

for l = 1:L
    atom = atom_from_indices(cfg, support(l, :));
    Y = Y + coeffs(l) * atom;
end
end

function [support, coeffs, residualTensor] = tensor_omp(Y, cfg, L)
y = Y(:);
residual = y;
support = zeros(L, 3);
selected = false(cfg.Gtheta, cfg.Gtau, cfg.Gnu);
Aselected = zeros(numel(y), L);
coeffs = zeros(L, 1);

for iter = 1:L
    C = separable_correlations(reshape(residual, cfg.Nv, cfg.K, cfg.M), cfg);
    C(selected) = 0;
    [~, linearIdx] = max(abs(C(:)));
    [thetaIdx, tauIdx, nuIdx] = ind2sub(size(C), linearIdx);
    support(iter, :) = [thetaIdx, tauIdx, nuIdx];
    selected(thetaIdx, tauIdx, nuIdx) = true;

    Aselected(:, iter) = reshape(atom_from_indices(cfg, support(iter, :)), [], 1);
    activeA = Aselected(:, 1:iter);
    activeCoeff = activeA \ y;
    residual = y - activeA * activeCoeff;
    coeffs(1:iter) = activeCoeff;
end

residualTensor = reshape(residual, cfg.Nv, cfg.K, cfg.M);
end

function C = separable_correlations(Y, cfg)
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
end

function pd = support_detection_probability(trueSupport, estSupport)
matched = false(size(trueSupport, 1), 1);
for i = 1:size(estSupport, 1)
    same = all(trueSupport == estSupport(i, :), 2);
    firstMatch = find(same & ~matched, 1);
    if ~isempty(firstMatch)
        matched(firstMatch) = true;
    end
end
pd = sum(matched) / size(trueSupport, 1);
end

function rate = exact_support_rate(trueSupport, estSupport)
rate = double(size(trueSupport, 1) == size(estSupport, 1) && ...
    support_detection_probability(trueSupport, estSupport) == 1);
end

function Y = reconstruct_tensor(cfg, support, coeffs)
Y = zeros(cfg.Nv, cfg.K, cfg.M);
for i = 1:size(support, 1)
    Y = Y + coeffs(i) * atom_from_indices(cfg, support(i, :));
end
end

function atom = atom_from_indices(cfg, indexTriplet)
a = cfg.A(:, indexTriplet(1));
p = cfg.P(:, indexTriplet(2));
d = cfg.D(:, indexTriplet(3));
atom = reshape(a, cfg.Nv, 1, 1) .* reshape(p, 1, cfg.K, 1) .* reshape(d, 1, 1, cfg.M);
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

function val = nmse_db(reference, estimate)
val = 10 * log10(norm(reference(:) - estimate(:))^2 / max(norm(reference(:))^2, eps));
end

function val = energy_ratio_db(numerator, denominator)
val = 10 * log10(norm(numerator(:))^2 / max(norm(denominator(:))^2, eps));
end

function plot_results(results, cfg, outDir)
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 1200 360]);

subplot(1, 3, 1);
plot(results.num_targets, results.detection_probability, '-o', 'LineWidth', 1.4);
hold on;
xline(cfg.localKruskalBound, '--');
ylim([0 1.05]);
grid on;
xlabel('Number of targets L');
ylabel('Detection probability P_d');
title('Support recovery');

subplot(1, 3, 2);
plot(results.num_targets, results.nmse_db, '-s', 'LineWidth', 1.4);
hold on;
xline(cfg.localKruskalBound, '--');
grid on;
xlabel('Number of targets L');
ylabel('NMSE (dB)');
title('Reconstruction error');

subplot(1, 3, 3);
plot(results.num_targets, results.avg_runtime_s, '-d', 'LineWidth', 1.4);
hold on;
xline(cfg.localKruskalBound, '--');
grid on;
xlabel('Number of targets L');
ylabel('Runtime (s)');
title('Tensor-OMP runtime');

pngPath = fullfile(outDir, 'kruskal_identifiability_ablation.png');
pdfPath = fullfile(outDir, 'kruskal_identifiability_ablation.pdf');
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

fprintf(fid, '# Kruskal Identifiability Ablation\n\n');
fprintf(fid, 'This lightweight experiment supports TechnicalDesign v2.2 Section 6.5.13(b,c). ');
fprintf(fid, 'It uses on-grid multi-target tensors and a Tensor-OMP style greedy solver to measure degradation as target count L grows.\n');
fprintf(fid, 'Because this smoke run is on-grid and high-SNR, P_d is expected to remain strong; the more useful early indicators are NMSE, exact-support rate, and runtime growth.\n\n');
fprintf(fid, '- Seed: `20260623`\n');
fprintf(fid, '- Trials per condition: `%d`\n', cfg.trials);
fprintf(fid, '- SNR: `%g dB`\n', cfg.snrDb);
fprintf(fid, '- Tensor size: `%d x %d x %d`\n', cfg.Nv, cfg.K, cfg.M);
fprintf(fid, '- Oversampling ratio: `%g`\n', cfg.rho);
fprintf(fid, '- Local Kruskal bound: `floor((%d + %d + %d - 2) / 2) = %d`\n', ...
    cfg.Nv, cfg.K, cfg.M, cfg.localKruskalBound);
fprintf(fid, '- Paper-scale Kruskal bound from v2.2: `floor((%d + %d + %d - 2) / 2) = %d`\n\n', ...
    cfg.paperNv, cfg.paperK, cfg.paperM, cfg.paperKruskalBound);
fprintf(fid, 'The local bound is lower than the paper-scale bound because this smoke run uses a compact tensor for fast desktop reproducibility.\n\n');
fprintf(fid, '## Result Table\n\n');
fprintf(fid, '| L | L/Lmax | P_d | exact support rate | NMSE (dB) | residual energy (dB) | runtime (s) |\n');
fprintf(fid, '|---:|---:|---:|---:|---:|---:|---:|\n');
for i = 1:height(results)
    fprintf(fid, '| %d | %.3f | %.3f | %.3f | %.3f | %.3f | %.4f |\n', ...
        results.num_targets(i), results.bound_ratio(i), ...
        results.detection_probability(i), results.exact_support_rate(i), ...
        results.nmse_db(i), results.residual_energy_db(i), results.avg_runtime_s(i));
end
end
