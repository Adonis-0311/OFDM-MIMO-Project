function make_candan_gate_profiles(p, outDir)
%MAKE_CANDAN_GATE_PROFILES Calibration-free paired increments and returns.
c = tsp_palette();
T = readtable(fullfile(p.gateProtocol, 'test_incremental_metrics.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');
T = T(T.protocol == "theory_fixed_tau_zero_no_calibration", :);
order = [find(T.profile == "A"); find(T.profile == "C"); ...
    find(T.profile == "D"); find(T.profile == "All")];
T = T(order, :);
labels = {'CDL-A','CDL-C','CDL-D','All'};
x = 1:height(T);

fig = tsp_new_figure(8.8, 11.2);
tl = tiledlayout(fig, 2, 1, 'TileSpacing', 'compact', 'Padding', 'loose');

ax1 = nexttile(tl); hold(ax1, 'on');
v = T.paired_increment_db;
lo = T.paired_increment_ci95_low_db;
hi = T.paired_increment_ci95_high_db;
bar(ax1, x, v, 0.58, 'FaceColor', c.green, 'EdgeColor', 'none');
errorbar(ax1, x, v, v-lo, hi-v, 'k', 'LineStyle', 'none', ...
    'CapSize', 3, 'LineWidth', 0.8);
yline(ax1, 0, '-', 'Color', c.text, 'LineWidth', 0.75);
ylabel(ax1, 'Projection-selected minus Candan gain (dB)');
set(ax1, 'XTick', x, 'XTickLabel', labels); ylim(ax1, [-0.08 0.58]);
grid(ax1, 'on'); ax1.GridColor = c.grid; ax1.GridAlpha = 1;
tsp_style_axes(ax1); tsp_panel_label(ax1, 1);

ax2 = nexttile(tl); hold(ax2, 'on');
pass = 100*T.pass_rate;
bar(ax2, x, pass, 0.58, 'FaceColor', c.gold, 'EdgeColor', 'none');
for k = 1:numel(x)
    text(ax2, x(k), pass(k)+2.2, sprintf('%.1f%%', pass(k)), ...
        'HorizontalAlignment', 'center', 'Color', c.text, 'FontSize', 7.5);
end
ylabel(ax2, 'Candan estimate returned (%)');
set(ax2, 'XTick', x, 'XTickLabel', labels); ylim(ax2, [0 108]);
grid(ax2, 'on'); ax2.GridColor = c.grid; ax2.GridAlpha = 1;
tsp_style_axes(ax2); tsp_panel_label(ax2, 2);
tsp_export_bundle(fig, outDir, 'tsp_candan_gate_profiles');
end
