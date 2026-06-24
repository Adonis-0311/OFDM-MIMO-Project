function run_deepmimo_set_e_access_audit()
%RUN_DEEPMIMO_SET_E_ACCESS_AUDIT
% Audit local DeepMIMO assets for TechnicalDesign v2.2 Section 6.2 Set E.
%
% This is an access/readiness audit, not a performance experiment. It checks
% whether the local workspace contains enough DeepMIMO O1/I3 assets to run the
% required channel NMSE and angle-delay generalization experiments.

rootDir = fileparts(fileparts(mfilename('fullpath')));
outDir = fullfile(rootDir, 'Results', 'deepmimo_set_e_access_audit');
if ~exist(outDir, 'dir')
    mkdir(outDir);
end

referenceRoot = locate_reference_root(rootDir);
legacyDir = fullfile(referenceRoot, 'DeepMIMO-matlab-master');
nrDir = fullfile(referenceRoot, 'DeepMIMO-5GNR');
datasetDir = fullfile(nrDir, 'DeepMIMO_dataset');

rows = {};
rows(end+1, :) = audit_path('DeepMIMO MATLAB package', legacyDir, true); %#ok<AGROW>
rows(end+1, :) = audit_path('DeepMIMO 5GNR package', nrDir, true); %#ok<AGROW>
rows(end+1, :) = audit_path('DeepMIMO 5GNR dataset folder', datasetDir, true); %#ok<AGROW>
rows(end+1, :) = audit_path('Legacy generator', fullfile(legacyDir, 'DeepMIMO_Dataset_Generator.m'), false); %#ok<AGROW>
rows(end+1, :) = audit_path('5GNR generator', fullfile(nrDir, 'DeepMIMO_Dataset_Generator.m'), false); %#ok<AGROW>
rows(end+1, :) = audit_path('Legacy parameters', fullfile(legacyDir, 'parameters.m'), false); %#ok<AGROW>
rows(end+1, :) = audit_path('5GNR parameters', fullfile(nrDir, 'parameters.m'), false); %#ok<AGROW>

datasetFiles = list_files(datasetDir);
o1Hits = find_name_hits(referenceRoot, {'O1', 'O1_60'});
i3Hits = find_name_hits(referenceRoot, {'I3', 'I3_60'});
o1ParamHits = find_file_content_hits(referenceRoot, {'O1', 'O1_60'});
i3ParamHits = find_file_content_hits(referenceRoot, {'I3', 'I3_60'});

rows(end+1, :) = {'Dataset file count', char(string(numel(datasetFiles))), status_from_count(numel(datasetFiles)), datasetDir}; %#ok<AGROW>
rows(end+1, :) = {'O1/O1_60 local asset hits', char(string(numel(o1Hits))), status_from_count(numel(o1Hits)), strjoin(o1Hits(1:min(end, 5)), '; ')}; %#ok<AGROW>
rows(end+1, :) = {'I3/I3_60 local asset hits', char(string(numel(i3Hits))), status_from_count(numel(i3Hits)), strjoin(i3Hits(1:min(end, 5)), '; ')}; %#ok<AGROW>
rows(end+1, :) = {'O1/O1_60 parameter references', char(string(numel(o1ParamHits))), status_from_count(numel(o1ParamHits)), strjoin(o1ParamHits(1:min(end, 5)), '; ')}; %#ok<AGROW>
rows(end+1, :) = {'I3/I3_60 parameter references', char(string(numel(i3ParamHits))), status_from_count(numel(i3ParamHits)), strjoin(i3ParamHits(1:min(end, 5)), '; ')}; %#ok<AGROW>

rows(end+1, :) = {'MATLAB 5G Toolbox license', bool_to_text(license('test', '5G_Toolbox')), bool_to_status(license('test', '5G_Toolbox')), 'license(''test'', ''5G_Toolbox'')'}; %#ok<AGROW>
rows(end+1, :) = {'nrCDLChannel availability', bool_to_text(~isempty(which('nrCDLChannel'))), bool_to_status(~isempty(which('nrCDLChannel'))), which('nrCDLChannel')}; %#ok<AGROW>

auditTable = cell2table(rows, 'VariableNames', {'item', 'value', 'status', 'evidence'});
writetable(auditTable, fullfile(outDir, 'deepmimo_set_e_access_audit.csv'));
write_summary(auditTable, referenceRoot, datasetFiles, o1Hits, i3Hits, o1ParamHits, i3ParamHits, outDir);

fprintf('Saved DeepMIMO Set E audit to %s\n', outDir);
end

function referenceRoot = locate_reference_root(rootDir)
candidates = dir(fullfile(rootDir, '2025*'));
referenceRoot = '';
for i = 1:numel(candidates)
    candidate = fullfile(rootDir, candidates(i).name, '参考');
    if exist(fullfile(candidate, 'DeepMIMO-5GNR'), 'dir') || exist(fullfile(candidate, 'DeepMIMO-matlab-master'), 'dir')
        referenceRoot = candidate;
        return;
    end
end
referenceRoot = fullfile(rootDir, '2025刘雨辉毕设', '参考');
end

function row = audit_path(label, pathValue, isDir)
if isDir
    existsFlag = exist(pathValue, 'dir') == 7;
else
    existsFlag = exist(pathValue, 'file') == 2;
end
row = {label, bool_to_text(existsFlag), bool_to_status(existsFlag), pathValue};
end

function files = list_files(pathValue)
if exist(pathValue, 'dir') ~= 7
    files = {};
    return;
end
listing = dir(fullfile(pathValue, '**', '*'));
listing = listing(~[listing.isdir]);
files = arrayfun(@(x) fullfile(x.folder, x.name), listing, 'UniformOutput', false);
end

function hits = find_name_hits(rootPath, patterns)
hits = {};
if exist(rootPath, 'dir') ~= 7
    return;
end
listing = dir(fullfile(rootPath, '**', '*'));
for i = 1:numel(listing)
    name = listing(i).name;
    for p = 1:numel(patterns)
        if contains(upper(name), upper(patterns{p}))
            hits{end+1} = fullfile(listing(i).folder, listing(i).name); %#ok<AGROW>
            break;
        end
    end
end
end

function hits = find_file_content_hits(rootPath, patterns)
hits = {};
if exist(rootPath, 'dir') ~= 7
    return;
end
listing = dir(fullfile(rootPath, '**', '*.m'));
for i = 1:numel(listing)
    pathValue = fullfile(listing(i).folder, listing(i).name);
    textValue = fileread(pathValue);
    for p = 1:numel(patterns)
        if contains(upper(textValue), upper(patterns{p}))
            hits{end+1} = pathValue; %#ok<AGROW>
            break;
        end
    end
end
end

function out = bool_to_text(flag)
if flag
    out = 'yes';
else
    out = 'no';
end
end

function out = bool_to_status(flag)
if flag
    out = 'ok';
else
    out = 'missing';
end
end

function out = status_from_count(countValue)
if countValue > 0
    out = 'ok';
else
    out = 'missing';
end
end

function write_summary(auditTable, referenceRoot, datasetFiles, o1Hits, i3Hits, o1ParamHits, i3ParamHits, outDir)
summaryPath = fullfile(outDir, 'summary.md');
fid = fopen(summaryPath, 'w');
cleanup = onCleanup(@() fclose(fid));

hasLegacy = any(strcmp(auditTable.item, 'DeepMIMO MATLAB package') & strcmp(auditTable.status, 'ok'));
has5gnr = any(strcmp(auditTable.item, 'DeepMIMO 5GNR package') & strcmp(auditTable.status, 'ok'));
hasDataset = ~isempty(datasetFiles);
hasO1 = ~isempty(o1Hits) || ~isempty(o1ParamHits);
hasI3 = ~isempty(i3Hits) || ~isempty(i3ParamHits);
hasNrCdl = any(strcmp(auditTable.item, 'nrCDLChannel availability') & strcmp(auditTable.status, 'ok'));

if hasLegacy && has5gnr && hasDataset && hasO1 && hasI3 && hasNrCdl
    readiness = 'ready';
elseif hasLegacy || has5gnr
    readiness = 'partial';
else
    readiness = 'blocked';
end

fprintf(fid, '# DeepMIMO Set E Access Audit\n\n');
fprintf(fid, 'This audit supports TechnicalDesign v2.2 Section 6.2 Set E. It checks whether local DeepMIMO assets are sufficient for channel NMSE and angle-delay cross-scene validation.\n\n');
fprintf(fid, '- Reference root: `%s`\n', referenceRoot);
fprintf(fid, '- Readiness: `%s`\n', readiness);
fprintf(fid, '- Dataset files found: `%d`\n', numel(datasetFiles));
fprintf(fid, '- O1/O1_60 asset hits: `%d`\n', numel(o1Hits));
fprintf(fid, '- O1/O1_60 parameter references: `%d`\n', numel(o1ParamHits));
fprintf(fid, '- I3/I3_60 asset hits: `%d`\n', numel(i3Hits));
fprintf(fid, '- I3/I3_60 parameter references: `%d`\n\n', numel(i3ParamHits));

fprintf(fid, '## Audit Table\n\n');
fprintf(fid, '| Item | Value | Status | Evidence |\n');
fprintf(fid, '|---|---:|---|---|\n');
for i = 1:height(auditTable)
    fprintf(fid, '| %s | %s | %s | `%s` |\n', auditTable.item{i}, auditTable.value{i}, auditTable.status{i}, auditTable.evidence{i});
end

fprintf(fid, '\n## Interpretation\n\n');
if strcmp(readiness, 'ready')
    fprintf(fid, 'Local DeepMIMO assets appear sufficient for a first O1/I3 access run. Next step: generate a compact channel subset and export channel NMSE plus angle-delay labels.\n');
elseif strcmp(readiness, 'partial')
    fprintf(fid, 'Local DeepMIMO code is present, but scenario data/toolbox readiness is incomplete. Next step: download/install the required O1/I3 scenario data and verify MATLAB 5G Toolbox support before claiming Set E performance.\n');
else
    fprintf(fid, 'DeepMIMO code and scenario data are missing. Set E performance experiments are blocked until the dataset package is installed.\n');
end

fprintf(fid, '\nThis audit does not validate velocity RMSE, consistent with v2.2: DeepMIMO Set E is for channel NMSE, angle RMSE, delay RMSE, and cross-scene generalization only.\n');
end
