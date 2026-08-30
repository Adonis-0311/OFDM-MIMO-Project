function make_local_family(p, outDir)
c = tsp_palette();
S = readtable(fullfile(p.cost, 'local_family_summary.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');
R = readtable(fullfile(p.runtime, 'summary.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');
P = readtable(fullfile(p.projectionRuntime, 'summary.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');
methods = ["grid_fft_topL_joint_ls", "axiswise_quadratic_peak_joint_ls", ...
    "axiswise_candan_joint_ls", "one_step_fixed_support_newton_joint_ls", ...
    "cartesian_local_joint_ls", "axiswise_candan_joint_ls"];
labels = {'Grid', 'Quadratic power', 'Candan', 'One-step Newton', ...
    'Cartesian local', 'Projection-selected Candan'};
colors = [c.gray; c.gold; c.orange; c.blue; c.green; c.purple];
markers = {'o', 'd', 'v', '^', 's', 'p'};
runtimeMs = zeros(size(methods));
for k = 1:numel(methods)
    if k == 3
        runtimeMs(k) = P.median_wall_clock_ms(P.method == "axiswise_candan_joint_ls");
    elseif k == 6
        runtimeMs(k) = P.median_wall_clock_ms(P.method == "projection_energy_gate");
    else
        runtimeMs(k) = R.median_wall_clock_ms(R.method == methods(k));
    end
end

fig = tsp_new_figure(18.0, 7.0);
tl = tiledlayout(fig, 1, 2, 'TileSpacing', 'compact', 'Padding', 'loose');
axesList = gobjects(2,1);
for panel = 1:2
    ax = nexttile(tl); axesList(panel) = ax; hold(ax, 'on');
    for k = 1:numel(methods)
        sr = S(S.method == methods(k), :);
        if panel == 1
            y = sr.mean_measurement_nmse_db;
            lo = sr.measurement_nmse_ci95_low_db;
            hi = sr.measurement_nmse_ci95_high_db;
        else
            y = 100*sr.mean_all_axis_half_bin_hit;
            lo = 100*sr.half_bin_hit_ci95_low;
            hi = 100*sr.half_bin_hit_ci95_high;
        end
        markerFace = colors(k,:);
        markerSize = 6.2;
        markerEdge = 'white';
        if k == 6
            markerFace = 'none';
            markerSize = 8.2;
            markerEdge = colors(k,:);
        end
        errorbar(ax, runtimeMs(k), y, y-lo, hi-y, markers{k}, ...
            'Color', colors(k,:), 'MarkerFaceColor', markerFace, ...
            'MarkerEdgeColor', markerEdge, 'MarkerSize', markerSize, 'CapSize', 4, ...
            'LineWidth', 0.9, 'DisplayName', labels{k});
    end
    set(ax, 'XScale', 'log', 'XLim', [7 45], 'XTick', [8 10 18 33]);
    xlabel(ax, 'Median end-to-end CPU time (ms)');
    grid(ax, 'on'); ax.GridColor = c.grid; ax.GridAlpha = 1;
    tsp_style_axes(ax); tsp_panel_label(ax, panel);
end
ylabel(axesList(1), 'NMSE (dB; lower is better)');
ylabel(axesList(2), 'All-axis half-bin hit rate (%)'); ylim(axesList(2), [68 82.5]);
lgd = legend(axesList(1), 'Location', 'southoutside', 'NumColumns', 3);
lgd.Layout.Tile = 'south';
tsp_export_bundle(fig, outDir, 'tsp_local_family');
end
