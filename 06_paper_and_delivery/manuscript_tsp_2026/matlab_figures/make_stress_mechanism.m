function make_stress_mechanism(p, outDir)
c = tsp_palette();
T = readtable(fullfile(p.stress, 'candan_48cell_summary.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');
separations = unique(T.separation_bins, 'sorted');
dynamicRanges = unique(T.dynamic_range_db, 'sorted');
keys = {'mean_grid_per_component_hit', 'mean_candan_per_component_hit', ...
    'mean_candan_designated_pair_assignment', 'mean_candan_gain_vs_grid_db'};
titles = {'Coarse per-component half-bin hit (%)', ...
    'Candan per-component half-bin hit (%)', ...
    'Candan designated-pair joint hit (%)', ...
    'Candan measurement-NMSE gain (dB)'};
maps = {tsp_colormap(c.blue), tsp_colormap(c.blue), ...
    tsp_colormap(c.green), tsp_colormap(c.green)};
scales = [100 100 100 1];

fig = tsp_new_figure(18.0, 10.7);
tl = tiledlayout(fig, 2, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
for panel = 1:4
    A = zeros(numel(separations), numel(dynamicRanges));
    for i = 1:numel(separations)
        for j = 1:numel(dynamicRanges)
            selected = T(T.separation_bins == separations(i) & ...
                T.dynamic_range_db == dynamicRanges(j), :);
            A(i,j) = scales(panel)*mean(selected.(keys{panel}));
        end
    end
    ax = nexttile(tl);
    imagesc(ax, A); colormap(ax, maps{panel});
    xticks(ax, 1:numel(dynamicRanges)); xticklabels(ax, compose('%g', dynamicRanges));
    yticks(ax, 1:numel(separations)); yticklabels(ax, compose('%g', separations));
    title(ax, titles{panel});
    if panel > 2, xlabel(ax, 'Pair dynamic range (dB)'); end
    if mod(panel,2) == 1, ylabel(ax, 'Pair separation (bins)'); end
    for i = 1:size(A,1)
        for j = 1:size(A,2)
            if panel < 4, label = sprintf('%.0f', A(i,j));
            else, label = sprintf('%.2f', A(i,j)); end
            text(ax, j, i, label, 'HorizontalAlignment', 'center', ...
                'Color', textColor(A(i,j), min(A(:)), max(A(:)), c), 'FontSize', 7.3);
        end
    end
    tsp_style_axes(ax); tsp_panel_label(ax, panel);
end
tsp_export_bundle(fig, outDir, 'tsp_stress_mechanism');
end

function color = textColor(value, low, high, c)
if high > low && (value-low)/(high-low) > 0.62, color = [1 1 1];
else, color = c.text; end
end
