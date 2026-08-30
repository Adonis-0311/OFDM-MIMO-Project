function make_full_offset_support(p, outDir)
c = tsp_palette();
radius = readtable(fullfile(p.fullOffset, 'radius_summary.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');
edge = readtable(fullfile(p.fullOffset, 'edge_offset_summary.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');
support = readtable(fullfile(p.support, 'support_quality_strata.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');
theory = readtable(fullfile(p.stressLegacy, 'theory_component_summary.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');

fig = tsp_new_figure(18.0, 11.0);
tl = tiledlayout(fig, 2, 2, 'TileSpacing', 'compact', 'Padding', 'compact');

ax = nexttile(tl); hold(ax, 'on');
yyaxis(ax, 'left');
plot(ax, radius.search_radius, radius.mean_gain_vs_grid_db, '-o', ...
    'Color', c.green, 'MarkerFaceColor', c.green);
ylabel(ax, 'Gain over grid (dB)'); ax.YColor = c.green;
yyaxis(ax, 'right');
plot(ax, radius.search_radius, 100*radius.mean_boundary_saturation_rate, '--s', ...
    'Color', c.gold, 'MarkerFaceColor', c.gold);
ylabel(ax, 'Boundary selections (%)'); ax.YColor = c.gold;
xlabel(ax, 'Search radius (bins)'); title(ax, 'Full-offset radius sweep');
grid(ax, 'on'); tsp_style_axes(ax); tsp_panel_label(ax, 1);

ax = nexttile(tl); hold(ax, 'on');
edge = edge(edge.method == "cartesian_local_joint_ls", :);
axisNames = ["angle", "delay", "doppler"];
axisLabels = {'Angle', 'Delay', 'Doppler'};
colors = [c.blue; c.green; c.gold]; markers = {'o', 's', '^'};
for k = 1:3
    selected = edge(edge.axis == axisNames(k), :);
    plot(ax, 1:5, 100*selected.half_bin_axis_hit_rate, ['-' markers{k}], ...
        'Color', colors(k,:), 'MarkerFaceColor', colors(k,:), ...
        'DisplayName', axisLabels{k});
end
xticks(ax, 1:5); xticklabels(ax, {'0-.1', '.1-.2', '.2-.3', '.3-.4', '.4-.49'});
xlabel(ax, 'Absolute fractional-bin offset');
ylabel(ax, 'Axis half-bin hit rate (%)'); ylim(ax, [45 103]);
title(ax, 'Edge-offset behavior');
legend(ax, 'Location', 'southwest', 'NumColumns', 3);
grid(ax, 'on'); tsp_style_axes(ax); tsp_panel_label(ax, 2);

ax = nexttile(tl); hold(ax, 'on');
support = support(support.stratum_type == "coarse_support_quality", :);
quality = zeros(height(support),1);
for k = 1:height(support)
    token = split(support.stratum(k), '=');
    quality(k) = str2double(token(2));
end
[quality, order] = sort(quality); support = support(order,:);
yyaxis(ax, 'left');
errorbar(ax, quality, support.mean_local_gain_vs_grid_db, ...
    support.mean_local_gain_vs_grid_db-support.local_gain_ci95_low_db, ...
    support.local_gain_ci95_high_db-support.mean_local_gain_vs_grid_db, ...
    '-o', 'Color', c.green, 'MarkerFaceColor', c.green, 'CapSize', 3);
ylabel(ax, 'Gain over grid (dB)'); ax.YColor = c.green;
yyaxis(ax, 'right');
errorbar(ax, quality, 100*support.mean_candidate_axis_correctness, ...
    100*(support.mean_candidate_axis_correctness-support.candidate_axis_correctness_ci95_low), ...
    100*(support.candidate_axis_correctness_ci95_high-support.mean_candidate_axis_correctness), ...
    '--s', 'Color', c.blue, 'MarkerFaceColor', c.blue, 'CapSize', 3);
ylabel(ax, 'Candidate-axis correctness (%)'); ax.YColor = c.blue;
xlabel(ax, 'Coarse support quality q_{sup}');
title(ax, 'Support-quality stratification');
grid(ax, 'on'); tsp_style_axes(ax); tsp_panel_label(ax, 3);

ax = nexttile(tl); hold(ax, 'on');
holdRow = theory(theory.score_gap_condition == "satisfied", :);
otherRow = theory(theory.score_gap_condition == "not_satisfied", :);
values = 100*[otherRow.mean_candidate_axis_correctness, otherRow.local_half_bin_hit_rate; ...
    holdRow.mean_candidate_axis_correctness, holdRow.local_half_bin_hit_rate];
b = bar(ax, values, 'grouped');
b(1).FaceColor = c.blue; b(2).FaceColor = c.green;
xticks(ax, 1:2); xticklabels(ax, {'Other components', 'Condition holds'});
ylabel(ax, 'Rate (%)'); ylim(ax, [0 108]);
legend(ax, {'Candidate axes correct', 'Local half-bin hit'}, ...
    'Location', 'southoutside', 'NumColumns', 2);
text(ax, 0.98, 0.97, sprintf('n = %d', holdRow.component_count), ...
    'Units', 'normalized', 'HorizontalAlignment', 'right', ...
    'VerticalAlignment', 'top', 'FontSize', 7.1);
title(ax, 'Score-gap sufficient-condition grouping');
grid(ax, 'on'); tsp_style_axes(ax); tsp_panel_label(ax, 4);
tsp_export_bundle(fig, outDir, 'tsp_full_offset_support');
end
