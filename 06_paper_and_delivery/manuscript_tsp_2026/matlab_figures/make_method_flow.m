function make_method_flow(outDir)
c = tsp_palette();
fig = tsp_new_figure(18.0, 5.8);
box(fig, [0.02 0.36 0.12 0.28], {'Dense observation', '$\mathbf{y}$'}, c.lightBlue);
box(fig, [0.18 0.36 0.13 0.28], {'FFT top-$L$', 'coarse support'}, c.lightBlue);
box(fig, [0.35 0.36 0.17 0.28], {'Axis-wise Candan', '$3DL$ complex samples'}, c.lightBlue);
box(fig, [0.56 0.36 0.13 0.28], {'Joint LS', 'Candan estimate'}, c.lightGreen);
box(fig, [0.73 0.36 0.13 0.28], {'Projection selection', '$\Delta\rho\geq0$?'}, c.lightGold);
box(fig, [0.89 0.60 0.10 0.23], {'Return local', 'coordinates'}, c.lightGreen);
box(fig, [0.89 0.16 0.10 0.23], {'Return grid', 'coordinates'}, tint(c.orange));
for x = [0.14 0.31 0.52 0.69]
    annotation(fig, 'arrow', [x x+0.04], [0.50 0.50], 'Color', c.text, 'LineWidth', 0.9);
end
annotation(fig, 'arrow', [0.86 0.89], [0.54 0.69], 'Color', c.green, 'LineWidth', 1.0);
annotation(fig, 'arrow', [0.86 0.89], [0.45 0.28], 'Color', c.orange, 'LineWidth', 1.0);
annotation(fig, 'textbox', [0.855 0.64 0.04 0.08], 'String', 'yes', ...
    'EdgeColor', 'none', 'Color', c.green, 'HorizontalAlignment', 'center');
annotation(fig, 'textbox', [0.855 0.27 0.04 0.08], 'String', 'no', ...
    'EdgeColor', 'none', 'Color', c.orange, 'HorizontalAlignment', 'center');
annotation(fig, 'textbox', [0.28 0.79 0.52 0.13], 'String', ...
    '$\widehat\delta_d=\frac{\tan(\pi/N_d)}{\pi/N_d}\Re\!\left\{\frac{Z_- - Z_+}{2Z_0-Z_- -Z_+}\right\}$', ...
    'Interpreter', 'latex', 'EdgeColor', 'none', 'HorizontalAlignment', 'center', 'FontSize', 8.5);
annotation(fig, 'textbox', [0.16 0.05 0.70 0.10], 'String', ...
    '$\Delta\rho=(\|P_{\rm C}y\|^2-\|P_0y\|^2)/\|y\|^2$ uses fitted-subspace energies.', ...
    'Interpreter', 'latex', 'EdgeColor', 'none', 'Color', c.gray, ...
    'HorizontalAlignment', 'center', 'FontSize', 7.4);
tsp_export_bundle(fig, outDir, 'tsp_method_flow');
end

function box(fig, position, lines, background)
c = tsp_palette();
annotation(fig, 'textbox', position, 'String', lines, 'Interpreter', 'latex', ...
    'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
    'EdgeColor', c.text, 'BackgroundColor', background, 'LineWidth', 0.85, 'Margin', 3);
end

function color = tint(color)
color = color + (1-color)*0.88;
end
