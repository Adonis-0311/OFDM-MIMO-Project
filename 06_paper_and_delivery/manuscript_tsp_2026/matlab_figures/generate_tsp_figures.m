function generate_tsp_figures()
%GENERATE_TSP_FIGURES Rebuild all figures used by the TSP paper.
scriptDir = fileparts(mfilename('fullpath'));
manuscriptDir = fileparts(scriptDir);
workspaceRoot = fileparts(fileparts(manuscriptDir));
outDir = fullfile(manuscriptDir, 'figures');
if ~isfolder(outDir), mkdir(outDir); end

p = struct();
p.root = workspaceRoot;
p.data = fullfile(workspaceRoot, '05_results', 'matlab_taes_supplement');
p.cost = fullfile(workspaceRoot, '05_results', 'tsp_controlled_local_family_paper');
p.runtime = fullfile(workspaceRoot, '05_results', 'tsp_unified_runtime_paper');
p.fullOffset = fullfile(workspaceRoot, '05_results', 'tsp_full_offset_sweep_paper');
p.support = fullfile(workspaceRoot, '05_results', 'tsp_support_quality_stratification_paper');
p.stress = fullfile(workspaceRoot, '05_results', 'tsp_candan_stress_zeta_audit_paper');
p.stressLegacy = fullfile(workspaceRoot, '05_results', 'tsp_separation_nearfar_metrics_v2_paper');
p.gate = fullfile(workspaceRoot, '05_results', 'tsp_reliability_gate_round2_paper');
p.gateAnalysis = fullfile(workspaceRoot, '05_results', 'tsp_gate_reliability_curve_paper');
p.transfer = fullfile(workspaceRoot, '05_results', 'tsp_cross_geometry_threshold_transfer_paper');
p.bootstrap = fullfile(workspaceRoot, '05_results', 'tsp_seed_cluster_bootstrap_paper');
p.boundary = fullfile(workspaceRoot, '05_results', 'tsp_fifth_round_boundary_audit_paper');
p.candanRoute = fullfile(workspaceRoot, '05_results', 'tsp_candan_route_audit_paper');
p.gateProtocol = fullfile(workspaceRoot, '05_results', 'tsp_candan_gate_protocol_seventh_round');
p.projectionRuntime = fullfile(workspaceRoot, '05_results', 'tsp_projection_gate_runtime_seventh_round');

tsp_figure_setup();
% The two page-wide workflow diagrams are maintained as editable Visio
% sources in ../visio_figures to provide text-safe routing at IEEE scale.
make_local_family(p, outDir);
make_full_offset_support(p, outDir);
make_stress_mechanism(p, outDir);
make_candan_gate_profiles(p, outDir);
fprintf('Generated six active MATLAB figure bundles in %s\n', outDir);
end
