function run_offgrid_mismatch_lemma_validation()
%RUN_OFFGRID_MISMATCH_LEMMA_VALIDATION
% Lightweight validation for TechnicalDesign v2.2 Section 5.1.1.
%
% The experiment checks the small-offset behavior of ULA steering-vector
% mismatch. It fits epsilon_grid ~= beta * delta_theta^2 and compares the
% fitted beta with the Lemma 1 reference scale (pi^2/12) * Nv^2 * cos^2(theta).

rootDir = fileparts(fileparts(fileparts(mfilename('fullpath'))));
outDir = fullfile(rootDir, '05_results', 'offgrid_mismatch_lemma');
if ~exist(outDir, 'dir')
    mkdir(outDir);
end

cfg = struct();
cfg.seed = 20260623;
cfg.NvValues = [16, 32, 64, 128];
cfg.thetaCentersDeg = [-45, -20, 0, 20, 45];
cfg.offsetFractions = linspace(-0.5, 0.5, 41);
cfg.gridStepDeg = 0.5;
cfg.learnedResidualScale = 0.1;

rng(cfg.seed, 'twister');

rows = {};
samples = {};
for ni = 1:numel(cfg.NvValues)
    Nv = cfg.NvValues(ni);
    for ti = 1:numel(cfg.thetaCentersDeg)
        thetaGrid = deg2rad(cfg.thetaCentersDeg(ti));
        offsets = deg2rad(cfg.gridStepDeg * cfg.offsetFractions(:));
        epsilonGrid = zeros(size(offsets));
        epsilonCorrected = zeros(size(offsets));

        for oi = 1:numel(offsets)
            delta = offsets(oi);
            thetaTrue = thetaGrid + delta;
            epsilonGrid(oi) = mismatch_epsilon(Nv, thetaGrid, thetaTrue);

            residual = cfg.learnedResidualScale * delta;
            thetaCorrected = thetaTrue - residual;
            epsilonCorrected(oi) = mismatch_epsilon(Nv, thetaCorrected, thetaTrue);

            samples(end+1, :) = {Nv, cfg.thetaCentersDeg(ti), rad2deg(delta), ...
                epsilonGrid(oi), epsilonCorrected(oi)}; %#ok<AGROW>
        end

        fitMask = abs(offsets) > 0;
        betaGrid = fit_quadratic_coeff(offsets(fitMask), epsilonGrid(fitMask));
        betaCorrected = fit_quadratic_coeff(offsets(fitMask), epsilonCorrected(fitMask));
        betaLemma = (pi^2 / 12) * Nv^2 * cos(thetaGrid)^2;

        rows(end+1, :) = {Nv, cfg.thetaCentersDeg(ti), cfg.gridStepDeg, ...
            betaGrid, betaCorrected, betaLemma, betaGrid / betaLemma, ...
            betaCorrected / max(betaGrid, eps), ...
            max(epsilonGrid), max(epsilonCorrected)}; %#ok<AGROW>
    end
end

summary = cell2table(rows, 'VariableNames', { ...
    'Nv', 'theta_center_deg', 'grid_step_deg', ...
    'beta_grid_fit', 'beta_corrected_fit', 'beta_lemma_reference', ...
    'grid_to_lemma_ratio', 'corrected_to_grid_ratio', ...
    'max_epsilon_grid', 'max_epsilon_corrected'});

sampleTable = cell2table(samples, 'VariableNames', { ...
    'Nv', 'theta_center_deg', 'delta_theta_deg', ...
    'epsilon_grid', 'epsilon_corrected'});

writetable(summary, fullfile(outDir, 'offgrid_mismatch_lemma_summary.csv'));
writetable(sampleTable, fullfile(outDir, 'offgrid_mismatch_lemma_samples.csv'));
save(fullfile(outDir, 'offgrid_mismatch_lemma_validation.mat'), 'cfg', 'summary', 'sampleTable');
plot_results(summary, sampleTable, cfg, outDir);
write_summary(summary, cfg, outDir);

fprintf('Saved results to %s\n', outDir);
end

function epsVal = mismatch_epsilon(Nv, thetaA, thetaB)
a = steering_vector(Nv, thetaA);
b = steering_vector(Nv, thetaB);
epsVal = 1 - abs(a' * b);
end

function a = steering_vector(Nv, theta)
v = (0:Nv-1).';
a = exp(1j * pi * v * sin(theta)) / sqrt(Nv);
end

function beta = fit_quadratic_coeff(delta, epsilon)
x = delta(:).^2;
y = epsilon(:);
beta = (x' * y) / max(x' * x, eps);
end

function plot_results(summary, sampleTable, cfg, outDir)
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 1200 380]);

subplot(1, 3, 1);
rows = sampleTable.Nv == 64 & sampleTable.theta_center_deg == 0;
plot(sampleTable.delta_theta_deg(rows).^2, sampleTable.epsilon_grid(rows), '-o', 'LineWidth', 1.2);
hold on;
plot(sampleTable.delta_theta_deg(rows).^2, sampleTable.epsilon_corrected(rows), '-s', 'LineWidth', 1.2);
grid on;
xlabel('\delta_\theta^2 (deg^2)');
ylabel('Mismatch \epsilon');
title('Quadratic mismatch');
legend('Grid atom', 'After residual correction', 'Location', 'northwest');

subplot(1, 3, 2);
centerRows = summary.theta_center_deg == 0;
plot(summary.Nv(centerRows), summary.beta_grid_fit(centerRows), '-o', 'LineWidth', 1.2);
hold on;
plot(summary.Nv(centerRows), summary.beta_lemma_reference(centerRows), '--', 'LineWidth', 1.2);
grid on;
xlabel('Virtual aperture N_v');
ylabel('Quadratic coefficient');
title('N_v^2 scaling');
legend('Fitted beta', 'Lemma scale', 'Location', 'northwest');

subplot(1, 3, 3);
scatter(summary.beta_lemma_reference, summary.beta_grid_fit, 42, summary.theta_center_deg, 'filled');
grid on;
xlabel('Lemma reference scale');
ylabel('Fitted beta');
title('Fit versus reference');
cb = colorbar;
cb.Label.String = 'theta center (deg)';

pngPath = fullfile(outDir, 'offgrid_mismatch_lemma_validation.png');
pdfPath = fullfile(outDir, 'offgrid_mismatch_lemma_validation.pdf');
try
    exportgraphics(fig, pngPath, 'Resolution', 200);
    exportgraphics(fig, pdfPath, 'ContentType', 'vector');
catch
    saveas(fig, pngPath);
    saveas(fig, pdfPath);
end
close(fig);
end

function write_summary(summary, cfg, outDir)
summaryPath = fullfile(outDir, 'summary.md');
fid = fopen(summaryPath, 'w');
cleanup = onCleanup(@() fclose(fid));

medianRatio = median(summary.grid_to_lemma_ratio);
medianCorrection = median(summary.corrected_to_grid_ratio);

fprintf(fid, '# Off-Grid Mismatch Lemma Validation\n\n');
fprintf(fid, 'This lightweight experiment supports TechnicalDesign v2.2 Section 5.1.1 and Phase 3.\n');
fprintf(fid, 'It measures ULA steering-vector mismatch for small angular offsets and fits `epsilon_grid ~= beta * delta_theta^2`.\n\n');
fprintf(fid, '- Seed: `%d`\n', cfg.seed);
fprintf(fid, '- Virtual apertures: `%s`\n', mat2str(cfg.NvValues));
fprintf(fid, '- Angle centers (deg): `%s`\n', mat2str(cfg.thetaCentersDeg));
fprintf(fid, '- Grid step: `%g deg`\n', cfg.gridStepDeg);
fprintf(fid, '- Simulated learned residual scale after correction: `%g x delta_theta`\n\n', cfg.learnedResidualScale);
fprintf(fid, 'Median fitted/reference beta ratio: `%.4g`.\n', medianRatio);
fprintf(fid, 'Median corrected/grid beta ratio: `%.4g`, close to the expected squared residual scale `%.4g`.\n\n', ...
    medianCorrection, cfg.learnedResidualScale^2);
fprintf(fid, 'The reference beta uses the Lemma 1 scale `(pi^2/12) * Nv^2 * cos(theta)^2`. ');
fprintf(fid, 'Because the measured mismatch is `1 - |a(theta_g)^H a(theta*)|`, the coefficient is used as a scaling reference rather than an exact equality.\n\n');
fprintf(fid, '## Summary Table\n\n');
fprintf(fid, '| Nv | theta | beta grid | beta corrected | beta ref | grid/ref | corrected/grid |\n');
fprintf(fid, '|---:|---:|---:|---:|---:|---:|---:|\n');
for i = 1:height(summary)
    fprintf(fid, '| %d | %.0f | %.4g | %.4g | %.4g | %.4g | %.4g |\n', ...
        summary.Nv(i), summary.theta_center_deg(i), summary.beta_grid_fit(i), ...
        summary.beta_corrected_fit(i), summary.beta_lemma_reference(i), ...
        summary.grid_to_lemma_ratio(i), summary.corrected_to_grid_ratio(i));
end
end
