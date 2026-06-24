function run_crlb_delay_asymptotic_smoke()
%RUN_CRLB_DELAY_ASYMPTOTIC_SMOKE
% Lightweight CRLB asymptotic validation for TechnicalDesign v2.2 Section 5.2.
%
% This smoke run studies a single-path delay estimation problem with unknown
% complex gain. It compares ML/NLS delay RMSE against the corresponding
% nuisance-aware CRLB. It is a scaffold for the final 5L ISAC CRLB.

rootDir = fileparts(fileparts(mfilename('fullpath')));
outDir = fullfile(rootDir, 'Results', 'crlb_delay_asymptotic_smoke');
if ~exist(outDir, 'dir')
    mkdir(outDir);
end

rng(20260623, 'twister');

cfg = struct();
cfg.seed = 20260623;
cfg.K = 128;
cfg.bandwidthHz = 300e6;
cfg.tauTrueNs = 37;
cfg.tauSearchNs = [0, 100];
cfg.alphaTrue = 1.0 * exp(1j * 0.7);
cfg.snrDb = [0, 5, 10, 15, 20, 25, 30];
cfg.trials = 96;
cfg.coarseGridSize = 2048;
cfg.goldenIterations = 36;

freq = ((0:cfg.K-1).' - (cfg.K-1) / 2) * (cfg.bandwidthHz / cfg.K);
tauTrue = cfg.tauTrueNs * 1e-9;
sTrue = steering_delay(freq, tauTrue);
clean = cfg.alphaTrue * sTrue;

rows = {};
for si = 1:numel(cfg.snrDb)
    snrDb = cfg.snrDb(si);
    fprintf('Running delay CRLB smoke at SNR=%g dB\n', snrDb);
    signalPower = mean(abs(clean).^2);
    noiseVar = signalPower / (10^(snrDb / 10));
    crlbTau = delay_crlb_with_unknown_gain(freq, tauTrue, cfg.alphaTrue, noiseVar);
    estimates = zeros(cfg.trials, 1);
    tic;
    for trial = 1:cfg.trials
        noise = sqrt(noiseVar / 2) * (randn(size(clean)) + 1j * randn(size(clean)));
        y = clean + noise;
        estimates(trial) = estimate_delay_ml(y, freq, cfg);
    end
    elapsed = toc;
    errNs = (estimates - tauTrue) * 1e9;
    rmseNs = sqrt(mean(errNs.^2));
    crlbNs = sqrt(crlbTau) * 1e9;
    rows(end+1, :) = {snrDb, rmseNs, crlbNs, rmseNs / crlbNs, ...
        mean(errNs), std(errNs), elapsed / cfg.trials}; %#ok<AGROW>
end

results = cell2table(rows, 'VariableNames', { ...
    'snr_db', 'rmse_ns', 'sqrt_crlb_ns', 'rmse_to_crlb_ratio', ...
    'bias_ns', 'std_error_ns', 'avg_runtime_s'});

writetable(results, fullfile(outDir, 'crlb_delay_asymptotic_smoke.csv'));
save(fullfile(outDir, 'crlb_delay_asymptotic_smoke.mat'), 'cfg', 'results');
plot_results(results, outDir);
write_summary(results, cfg, outDir);

fprintf('Saved results to %s\n', outDir);
end

function s = steering_delay(freq, tau)
s = exp(-1j * 2 * pi * freq * tau);
end

function crlbTau = delay_crlb_with_unknown_gain(freq, tau, alpha, noiseVar)
s = steering_delay(freq, tau);
ds = -1j * 2 * pi * freq .* s;

J = [s, 1j * s, alpha * ds];
fim = (2 / noiseVar) * real(J' * J);
fimInv = pinv(fim);
crlbTau = fimInv(3, 3);
end

function tauHat = estimate_delay_ml(y, freq, cfg)
lo = cfg.tauSearchNs(1) * 1e-9;
hi = cfg.tauSearchNs(2) * 1e-9;
grid = linspace(lo, hi, cfg.coarseGridSize);
scores = zeros(size(grid));
for i = 1:numel(grid)
    scores(i) = delay_score(y, freq, grid(i));
end
[~, idx] = max(scores);

leftIdx = max(1, idx - 1);
rightIdx = min(numel(grid), idx + 1);
tauHat = golden_max(@(x) delay_score(y, freq, x), grid(leftIdx), grid(rightIdx), cfg.goldenIterations);
end

function score = delay_score(y, freq, tau)
s = steering_delay(freq, tau);
score = abs(s' * y)^2 / max(real(s' * s), eps);
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

function plot_results(results, outDir)
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 980 390]);

subplot(1, 2, 1);
semilogy(results.snr_db, results.rmse_ns, '-o', 'LineWidth', 1.4);
hold on;
semilogy(results.snr_db, results.sqrt_crlb_ns, '--s', 'LineWidth', 1.4);
grid on;
xlabel('SNR (dB)');
ylabel('Delay error (ns)');
title('Delay RMSE versus CRLB');
legend('ML/NLS RMSE', 'sqrt(CRLB)', 'Location', 'southwest');

subplot(1, 2, 2);
plot(results.snr_db, results.rmse_to_crlb_ratio, '-d', 'LineWidth', 1.4);
grid on;
xlabel('SNR (dB)');
ylabel('RMSE / sqrt(CRLB)');
title('Asymptotic tightness ratio');
yline(1, '--');

pngPath = fullfile(outDir, 'crlb_delay_asymptotic_smoke.png');
pdfPath = fullfile(outDir, 'crlb_delay_asymptotic_smoke.pdf');
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

highRows = results.snr_db >= 20;
highRatio = mean(results.rmse_to_crlb_ratio(highRows));

fprintf(fid, '# CRLB Delay Asymptotic Smoke Experiment\n\n');
fprintf(fid, 'This lightweight experiment supports TechnicalDesign v2.2 Section 5.2 and Section 6.5.5.\n');
fprintf(fid, 'It estimates one path delay with unknown complex gain and compares ML/NLS RMSE against the nuisance-aware CRLB.\n\n');
fprintf(fid, '- Seed: `%d`\n', cfg.seed);
fprintf(fid, '- Subcarriers: `%d`\n', cfg.K);
fprintf(fid, '- Bandwidth: `%g MHz`\n', cfg.bandwidthHz / 1e6);
fprintf(fid, '- True delay: `%g ns`\n', cfg.tauTrueNs);
fprintf(fid, '- Trials per SNR: `%d`\n', cfg.trials);
fprintf(fid, '- SNR grid: `%s dB`\n\n', mat2str(cfg.snrDb));
fprintf(fid, 'Mean RMSE/sqrt(CRLB) ratio for SNR >= 20 dB: `%.3f`.\n\n', highRatio);

fprintf(fid, '## Result Table\n\n');
fprintf(fid, '| SNR | RMSE (ns) | sqrt(CRLB) (ns) | Ratio | Bias (ns) | Runtime (s) |\n');
fprintf(fid, '|---:|---:|---:|---:|---:|---:|\n');
for i = 1:height(results)
    fprintf(fid, '| %.0f | %.5f | %.5f | %.3f | %.5f | %.5f |\n', ...
        results.snr_db(i), results.rmse_ns(i), results.sqrt_crlb_ns(i), ...
        results.rmse_to_crlb_ratio(i), results.bias_ns(i), results.avg_runtime_s(i));
end

fprintf(fid, '\n## Interpretation Boundary\n\n');
fprintf(fid, 'This is a single-delay smoke validation, not the final 5L joint range-velocity-angle CRLB. ');
fprintf(fid, 'It validates the expected high-SNR tightening behavior and the plotting/reporting scaffold for the final CRLB experiment.\n');
end

