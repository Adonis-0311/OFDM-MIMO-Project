function run_cdl_profile_generalization_smoke()
%RUN_CDL_PROFILE_GENERALIZATION_SMOKE
% Lightweight CDL-A/C/D communication-side generalization smoke experiment.
%
% This compact CDL-like generator supports TechnicalDesign v2.2 Section 6.2.
% It is not a full 3GPP TR 38.901 implementation; it is a reproducible
% scaffold before the final standards-aligned CDL/DeepMIMO pipeline.

rootDir = fileparts(fileparts(mfilename('fullpath')));
outDir = fullfile(rootDir, 'Results', 'cdl_profile_generalization_smoke');
if ~exist(outDir, 'dir')
    mkdir(outDir);
end

rng(20260623, 'twister');

cfg = struct();
cfg.seed = 20260623;
cfg.Nr = 8;
cfg.Nt = 4;
cfg.K = 128;
cfg.bandwidthHz = 300e6;
cfg.snrDb = [0, 5, 10, 15, 20];
cfg.trials = 32;
cfg.keepDelayTaps = 20;
cfg.profiles = profile_configs();

rows = {};
for pi = 1:numel(cfg.profiles)
    profile = cfg.profiles(pi);
    for si = 1:numel(cfg.snrDb)
        snrDb = cfg.snrDb(si);
        fprintf('Running %s at SNR=%g dB\n', profile.name, snrDb);
        summary = run_condition(cfg, profile, snrDb);
        rows(end+1, :) = {profile.name, snrDb, profile.numPaths, ...
            profile.delaySpreadNs, profile.kFactorDb, cfg.keepDelayTaps, ...
            summary.lsNmseDb, summary.delaySparseNmseDb, ...
            summary.improvementDb, summary.avgRuntimeSec}; %#ok<AGROW>
    end
end

results = cell2table(rows, 'VariableNames', { ...
    'profile', 'snr_db', 'num_paths', 'delay_spread_ns', 'k_factor_db', ...
    'kept_delay_taps', 'ls_nmse_db', 'delay_sparse_nmse_db', ...
    'improvement_db', 'avg_runtime_s'});

writetable(results, fullfile(outDir, 'cdl_profile_generalization_smoke.csv'));
save(fullfile(outDir, 'cdl_profile_generalization_smoke.mat'), 'cfg', 'results');
plot_results(results, outDir);
write_summary(results, cfg, outDir);

fprintf('Saved results to %s\n', outDir);
end

function profiles = profile_configs()
profiles = struct( ...
    'name', {'CDL-A', 'CDL-C', 'CDL-D'}, ...
    'numPaths', {12, 18, 13}, ...
    'delaySpreadNs', {45, 100, 30}, ...
    'angularSpreadDeg', {35, 22, 12}, ...
    'kFactorDb', {-Inf, -Inf, 13.3});
end

function summary = run_condition(cfg, profile, snrDb)
lsNmse = zeros(cfg.trials, 1);
delaySparseNmse = zeros(cfg.trials, 1);
runtime = zeros(cfg.trials, 1);

for trial = 1:cfg.trials
    H = generate_cdl_like_channel(cfg, profile);
    Hnoisy = add_awgn(H, snrDb);

    tic;
    Hls = Hnoisy;
    HdelaySparse = delay_sparse_denoise(Hnoisy, cfg.keepDelayTaps);
    runtime(trial) = toc;

    lsNmse(trial) = nmse_db(H, Hls);
    delaySparseNmse(trial) = nmse_db(H, HdelaySparse);
end

summary = struct();
summary.lsNmseDb = mean(lsNmse);
summary.delaySparseNmseDb = mean(delaySparseNmse);
summary.improvementDb = summary.lsNmseDb - summary.delaySparseNmseDb;
summary.avgRuntimeSec = mean(runtime);
end

function H = generate_cdl_like_channel(cfg, profile)
K = cfg.K;
Nr = cfg.Nr;
Nt = cfg.Nt;
subcarrierFreq = ((0:K-1) - (K-1) / 2) * (cfg.bandwidthHz / K);

delays = sort(rand(profile.numPaths, 1).^1.5) * profile.delaySpreadNs * 1e-9;
aoa = deg2rad(profile.angularSpreadDeg) * randn(profile.numPaths, 1);
aod = deg2rad(profile.angularSpreadDeg) * randn(profile.numPaths, 1);

if isfinite(profile.kFactorDb)
    kLin = 10^(profile.kFactorDb / 10);
    losPower = kLin / (kLin + 1);
    nlosPower = 1 / (kLin + 1);
    gains = sqrt(nlosPower / max(profile.numPaths - 1, 1)) * ...
        (randn(profile.numPaths, 1) + 1j * randn(profile.numPaths, 1)) / sqrt(2);
    gains(1) = sqrt(losPower) * exp(1j * 2 * pi * rand());
    delays(1) = 0;
    aoa(1) = 0;
    aod(1) = 0;
else
    gains = (randn(profile.numPaths, 1) + 1j * randn(profile.numPaths, 1)) / sqrt(2 * profile.numPaths);
end

H = zeros(Nr, Nt, K);
for p = 1:profile.numPaths
    arx = steering_vector(Nr, aoa(p));
    atx = steering_vector(Nt, aod(p));
    spatial = arx * atx';
    phase = exp(-1j * 2 * pi * subcarrierFreq * delays(p));
    H = H + reshape(gains(p) * spatial, Nr, Nt, 1) .* reshape(phase, 1, 1, K);
end

targetNorm = sqrt(Nr * Nt * K);
H = H * targetNorm / max(norm(H(:)), eps);
end

function a = steering_vector(N, angleRad)
n = (0:N-1).';
a = exp(1j * pi * n * sin(angleRad)) / sqrt(N);
end

function Hnoisy = add_awgn(H, snrDb)
signalPower = mean(abs(H(:)).^2);
noisePower = signalPower / (10^(snrDb / 10));
noise = sqrt(noisePower / 2) * (randn(size(H)) + 1j * randn(size(H)));
Hnoisy = H + noise;
end

function Hhat = delay_sparse_denoise(Hnoisy, keepDelayTaps)
[Nr, Nt, K] = size(Hnoisy);
Hdelay = ifft(Hnoisy, [], 3);
delayMatrix = reshape(permute(Hdelay, [3, 1, 2]), K, Nr * Nt);
delayPower = sum(abs(delayMatrix).^2, 2);
[~, order] = sort(delayPower, 'descend');
keep = false(K, 1);
keep(order(1:min(keepDelayTaps, K))) = true;
delayMatrix(~keep, :) = 0;
HdelayKept = ipermute(reshape(delayMatrix, K, Nr, Nt), [3, 1, 2]);
Hhat = fft(HdelayKept, [], 3);
end

function val = nmse_db(reference, estimate)
val = 10 * log10(norm(reference(:) - estimate(:))^2 / max(norm(reference(:))^2, eps));
end

function plot_results(results, outDir)
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 980 390]);
profiles = unique(results.profile, 'stable');

subplot(1, 2, 1);
for i = 1:numel(profiles)
    rows = strcmp(results.profile, profiles{i});
    plot(results.snr_db(rows), results.ls_nmse_db(rows), '--o', 'LineWidth', 1.2);
    hold on;
    plot(results.snr_db(rows), results.delay_sparse_nmse_db(rows), '-s', 'LineWidth', 1.2);
end
grid on;
xlabel('SNR (dB)');
ylabel('NMSE (dB)');
title('CDL-like profile NMSE');
legend(compose_legend(profiles), 'Location', 'southwest');

subplot(1, 2, 2);
profileLabels = {};
improvements = [];
for i = 1:numel(profiles)
    rows = strcmp(results.profile, profiles{i}) & results.snr_db == 10;
    profileLabels{end+1} = profiles{i}; %#ok<AGROW>
    improvements(end+1) = results.improvement_db(rows); %#ok<AGROW>
end
bar(categorical(profileLabels), improvements);
grid on;
ylabel('NMSE gain at 10 dB (dB)');
title('Delay-sparse gain');

pngPath = fullfile(outDir, 'cdl_profile_generalization_smoke.png');
pdfPath = fullfile(outDir, 'cdl_profile_generalization_smoke.pdf');
try
    exportgraphics(fig, pngPath, 'Resolution', 200);
    exportgraphics(fig, pdfPath, 'ContentType', 'vector');
catch
    saveas(fig, pngPath);
    saveas(fig, pdfPath);
end
close(fig);
end

function labels = compose_legend(profiles)
labels = cell(1, numel(profiles) * 2);
for i = 1:numel(profiles)
    labels{2*i-1} = [profiles{i} ' LS'];
    labels{2*i} = [profiles{i} ' delay-sparse'];
end
end

function write_summary(results, cfg, outDir)
summaryPath = fullfile(outDir, 'summary.md');
fid = fopen(summaryPath, 'w');
cleanup = onCleanup(@() fclose(fid));

fprintf(fid, '# CDL Profile Generalization Smoke Experiment\n\n');
fprintf(fid, 'This lightweight experiment supports TechnicalDesign v2.2 Section 6.2 Set B-D.\n');
fprintf(fid, 'It uses a compact CDL-like generator for CDL-A/CDL-C/CDL-D communication-side channel NMSE checks. ');
fprintf(fid, 'It is not a full 3GPP TR 38.901 implementation.\n\n');
fprintf(fid, '- Seed: `%d`\n', cfg.seed);
fprintf(fid, '- Channel size: `Nr=%d, Nt=%d, K=%d`\n', cfg.Nr, cfg.Nt, cfg.K);
fprintf(fid, '- Trials per profile/SNR: `%d`\n', cfg.trials);
fprintf(fid, '- SNR grid: `%s dB`\n', mat2str(cfg.snrDb));
fprintf(fid, '- Delay-sparse kept taps: `%d`\n\n', cfg.keepDelayTaps);

fprintf(fid, '## Result Table\n\n');
fprintf(fid, '| Profile | SNR | LS NMSE | Delay-sparse NMSE | Gain | Runtime (s) |\n');
fprintf(fid, '|---|---:|---:|---:|---:|---:|\n');
for i = 1:height(results)
    fprintf(fid, '| %s | %.0f | %.3f | %.3f | %.3f | %.5f |\n', ...
        results.profile{i}, results.snr_db(i), results.ls_nmse_db(i), ...
        results.delay_sparse_nmse_db(i), results.improvement_db(i), ...
        results.avg_runtime_s(i));
end

fprintf(fid, '\n## Interpretation Boundary\n\n');
fprintf(fid, 'This smoke run validates the evaluation scaffold and profile-specific reporting. ');
fprintf(fid, 'Delay-sparse denoising is expected to help in low-to-mid SNR, while a truncation bias floor can appear for wider NLOS profiles at high SNR. ');
fprintf(fid, 'The final paper experiment should replace this generator with a standards-aligned 3GPP CDL or MATLAB 5G Toolbox pipeline and add trained T-OMP-Net inference.\n');
end
