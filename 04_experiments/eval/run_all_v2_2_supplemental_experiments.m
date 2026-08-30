function run_all_v2_2_supplemental_experiments()
%RUN_ALL_V2_2_SUPPLEMENTAL_EXPERIMENTS
% Reproduce the lightweight v2.2 supplemental experiment package.

rootDir = fileparts(fileparts(fileparts(mfilename('fullpath'))));
resultsDir = fullfile(rootDir, '05_results');
if ~exist(resultsDir, 'dir')
    mkdir(resultsDir);
end

experiments = {
    'Oversampling/off-grid ablation', ...
    'Section 6.5.13(a)', ...
    @run_oversampling_offgrid_ablation, ...
    fullfile(resultsDir, 'oversampling_offgrid_ablation', 'summary.md');

    'Kruskal identifiability ablation', ...
    'Section 6.5.13(b,c)', ...
    @run_kruskal_identifiability_ablation, ...
    fullfile(resultsDir, 'kruskal_identifiability_ablation', 'summary.md');

    'Off-grid mismatch lemma validation', ...
    'Section 5.1.1 / Phase 3', ...
    @run_offgrid_mismatch_lemma_validation, ...
    fullfile(resultsDir, 'offgrid_mismatch_lemma', 'summary.md');

    'CDL profile generalization smoke', ...
    'Section 6.2 Set B-D', ...
    @run_cdl_profile_generalization_smoke, ...
    fullfile(resultsDir, 'cdl_profile_generalization_smoke', 'summary.md');

    'CRLB delay asymptotic smoke', ...
    'Section 5.2 / Section 6.5.5', ...
    @run_crlb_delay_asymptotic_smoke, ...
    fullfile(resultsDir, 'crlb_delay_asymptotic_smoke', 'summary.md');

    'DeepMIMO Set E access audit', ...
    'Section 6.2 Set E', ...
    @run_deepmimo_set_e_access_audit, ...
    fullfile(resultsDir, 'deepmimo_set_e_access_audit', 'summary.md')
};

runRows = cell(size(experiments, 1), 5);
for i = 1:size(experiments, 1)
    name = experiments{i, 1};
    section = experiments{i, 2};
    fn = experiments{i, 3};
    summaryPath = experiments{i, 4};

    fprintf('=== Running %s ===\n', name);
    tStart = tic;
    fn();
    elapsed = toc(tStart);
    status = "ok";
    if ~exist(summaryPath, 'file')
        status = "missing-summary";
    end
    runRows(i, :) = {name, section, char(status), elapsed, relative_path(rootDir, summaryPath)};
end

runTable = cell2table(runRows, 'VariableNames', { ...
    'experiment', 'outline_section', 'status', 'runtime_s', 'summary_path'});
writetable(runTable, fullfile(resultsDir, 'v2_2_supplemental_manifest.csv'));
write_manifest(rootDir, resultsDir, runTable);

fprintf('Saved manifest to %s\n', fullfile(resultsDir, 'v2_2_supplemental_manifest.md'));
end

function write_manifest(rootDir, resultsDir, runTable)
manifestPath = fullfile(resultsDir, 'v2_2_supplemental_manifest.md');
fid = fopen(manifestPath, 'w');
cleanup = onCleanup(@() fclose(fid));

fprintf(fid, '# v2.2 Supplemental Experiment Manifest\n\n');
fprintf(fid, 'This manifest summarizes the lightweight experiments added against `ISAC_DeepUnfolding_TechnicalDesign_v2.2.md`.\n');
fprintf(fid, 'The runs are desktop reproducibility checks and early paper-upgrade evidence, not the final full-scale T-OMP-Net training campaign.\n\n');
fprintf(fid, '## Reproduction Command\n\n');
fprintf(fid, '```matlab\n');
fprintf(fid, 'run(''04_experiments/eval/run_all_v2_2_supplemental_experiments.m'')\n');
fprintf(fid, '```\n\n');

fprintf(fid, '## Run Table\n\n');
fprintf(fid, '| Experiment | Outline target | Status | Runtime (s) | Summary |\n');
fprintf(fid, '|---|---|---:|---:|---|\n');
for i = 1:height(runTable)
    fprintf(fid, '| %s | %s | %s | %.2f | `%s` |\n', ...
        runTable.experiment{i}, runTable.outline_section{i}, ...
        runTable.status{i}, runTable.runtime_s(i), runTable.summary_path{i});
end

fprintf(fid, '\n## Key Evidence\n\n');
write_oversampling_evidence(fid, resultsDir);
write_kruskal_evidence(fid, resultsDir);
write_mismatch_evidence(fid, resultsDir);
write_cdl_evidence(fid, resultsDir);
write_crlb_evidence(fid, resultsDir);
write_deepmimo_evidence(fid, resultsDir);

fprintf(fid, '\n## Remaining Gaps\n\n');
fprintf(fid, '- Full-size Tensor-OMP/T-OMP-Net training and inference pipeline is still pending.\n');
fprintf(fid, '- Standards-aligned CDL-A/C/D and DeepMIMO Set E cross-scene performance validation are still pending.\n');
fprintf(fid, '- Full 5L joint ISAC CRLB is still pending; the current CRLB result is a single-delay smoke validation.\n');
fprintf(fid, '- FLOPs/latency should be measured on the final implementation, not only the lightweight smoke scripts.\n');
fprintf(fid, '- GitHub remote upload still requires an authenticated GitHub CLI session or a provided remote URL.\n');
end

function write_oversampling_evidence(fid, resultsDir)
csvPath = fullfile(resultsDir, 'oversampling_offgrid_ablation', 'oversampling_offgrid_ablation.csv');
if ~exist(csvPath, 'file')
    fprintf(fid, '- Oversampling/off-grid: CSV missing.\n');
    return;
end

T = readtable(csvPath);
rho2 = T(T.rho == 2, :);
gridNmse = mean(rho2.nmse_grid_db);
offgridNmse = mean(rho2.nmse_offgrid_db);
fprintf(fid, '- Oversampling/off-grid: at `rho=2`, bounded off-grid improves mean NMSE from `%.2f dB` to `%.2f dB` across the three scans.\n', ...
    gridNmse, offgridNmse);
end

function write_kruskal_evidence(fid, resultsDir)
csvPath = fullfile(resultsDir, 'kruskal_identifiability_ablation', 'kruskal_identifiability_ablation.csv');
if ~exist(csvPath, 'file')
    fprintf(fid, '- Kruskal identifiability: CSV missing.\n');
    return;
end

T = readtable(csvPath);
firstNmse = T.nmse_db(1);
lastNmse = T.nmse_db(end);
firstRuntime = T.avg_runtime_s(1);
lastRuntime = T.avg_runtime_s(end);
fprintf(fid, '- Kruskal/target-count: as `L` rises from `%d` to `%d`, NMSE changes from `%.2f dB` to `%.2f dB`, and runtime from `%.4f s` to `%.4f s`.\n', ...
    T.num_targets(1), T.num_targets(end), firstNmse, lastNmse, firstRuntime, lastRuntime);
end

function write_mismatch_evidence(fid, resultsDir)
csvPath = fullfile(resultsDir, 'offgrid_mismatch_lemma', 'offgrid_mismatch_lemma_summary.csv');
if ~exist(csvPath, 'file')
    fprintf(fid, '- Off-grid mismatch lemma: CSV missing.\n');
    return;
end

T = readtable(csvPath);
fprintf(fid, '- Off-grid mismatch lemma: median fitted/reference beta ratio is `%.4g`; median corrected/grid beta ratio is `%.4g`.\n', ...
    median(T.grid_to_lemma_ratio), median(T.corrected_to_grid_ratio));
end

function write_cdl_evidence(fid, resultsDir)
csvPath = fullfile(resultsDir, 'cdl_profile_generalization_smoke', 'cdl_profile_generalization_smoke.csv');
if ~exist(csvPath, 'file')
    fprintf(fid, '- CDL profile generalization: CSV missing.\n');
    return;
end

T = readtable(csvPath);
snrRows = T.snr_db == 10;
meanGain = mean(T.improvement_db(snrRows));
fprintf(fid, '- CDL profile smoke: at `10 dB`, delay-sparse denoising improves NMSE by a mean `%.2f dB` across CDL-A/C/D-like profiles.\n', ...
    meanGain);
end

function write_crlb_evidence(fid, resultsDir)
csvPath = fullfile(resultsDir, 'crlb_delay_asymptotic_smoke', 'crlb_delay_asymptotic_smoke.csv');
if ~exist(csvPath, 'file')
    fprintf(fid, '- CRLB delay smoke: CSV missing.\n');
    return;
end

T = readtable(csvPath);
highRows = T.snr_db >= 20;
meanRatio = mean(T.rmse_to_crlb_ratio(highRows));
fprintf(fid, '- CRLB delay smoke: for `SNR >= 20 dB`, mean RMSE/sqrt(CRLB) ratio is `%.3f`.\n', ...
    meanRatio);
end

function write_deepmimo_evidence(fid, resultsDir)
csvPath = fullfile(resultsDir, 'deepmimo_set_e_access_audit', 'deepmimo_set_e_access_audit.csv');
if ~exist(csvPath, 'file')
    fprintf(fid, '- DeepMIMO Set E audit: CSV missing.\n');
    return;
end

T = readtable(csvPath);
datasetRow = strcmp(T.item, 'Dataset file count');
o1ParamRow = strcmp(T.item, 'O1/O1_60 parameter references');
i3ParamRow = strcmp(T.item, 'I3/I3_60 parameter references');
fprintf(fid, '- DeepMIMO Set E audit: dataset files `%s`, O1 parameter refs `%s`, I3 parameter refs `%s`; readiness remains partial until O1/I3 scenario data are installed.\n', ...
    first_table_value(T.value, datasetRow), first_table_value(T.value, o1ParamRow), first_table_value(T.value, i3ParamRow));
end

function value = first_table_value(column, mask)
idx = find(mask, 1);
if isempty(idx)
    value = 'missing';
    return;
end
value = char(string(column(idx)));
end

function rel = relative_path(rootDir, pathValue)
rel = erase(string(pathValue), string(rootDir) + filesep);
rel = strrep(char(rel), '\', '/');
end
