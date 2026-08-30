function make_system_model(outDir)
c = tsp_palette();
fig = tsp_new_figure(18.0, 6.2);
box(fig, [0.02 0.68 0.12 0.20], {'Spatial ULA', '$N_a$'}, c.blue, tint(c.blue));
box(fig, [0.02 0.40 0.12 0.20], {'Frequency', '$N_\tau$'}, c.green, tint(c.green));
box(fig, [0.02 0.12 0.12 0.20], {'Slow time', '$N_\nu$'}, c.gold, tint(c.gold));
box(fig, [0.18 0.34 0.16 0.32], ...
    {'Separable tensor', '$\mathcal{Y}: N_a\times N_\tau\times N_\nu$'}, c.text, c.lightBlue);
box(fig, [0.38 0.34 0.13 0.32], {'Orthonormal FFT', '+ top-$L$ bins'}, c.text, c.lightBlue);
box(fig, [0.55 0.34 0.14 0.32], {'$3DL$ triplet samples', '+ axis-wise Candan'}, c.text, c.lightGreen);
box(fig, [0.73 0.34 0.13 0.32], {'Candan joint LS', '+ FFT/grid energy'}, c.text, c.lightGold);
box(fig, [0.90 0.34 0.09 0.32], {'Coordinates, gains,', 'reconstruction'}, c.text, tint(c.gold));
for y = [0.78 0.50 0.22]
    annotation(fig, 'arrow', [0.14 0.18], [y 0.50], 'Color', c.text, 'LineWidth', 0.9);
end
for x = [0.34 0.51 0.69 0.86]
    annotation(fig, 'arrow', [x x+0.04], [0.50 0.50], 'Color', c.text, 'LineWidth', 0.9);
end
annotation(fig, 'textbox', [0.23 0.80 0.65 0.15], 'String', ...
    '$\mathcal{Y}=\sum_{\ell=1}^{L}\beta_\ell\,\mathbf{a}_{N_a}(b_{a,\ell})\circ\mathbf{a}_{N_\tau}(b_{\tau,\ell})\circ\mathbf{a}_{N_\nu}(b_{\nu,\ell})+\mathcal{W}$', ...
    'Interpreter', 'latex', 'EdgeColor', 'none', 'HorizontalAlignment', 'center', 'FontSize', 9);
annotation(fig, 'textbox', [0.18 0.02 0.80 0.10], 'String', ...
    '$\Delta\rho=(\|\mathbf{P}_{\rm C}\mathbf{y}\|_2^2-\|\mathbf{P}_0\mathbf{y}\|_2^2)/\|\mathbf{y}\|_2^2$ uses fitted-subspace energies.', ...
    'Interpreter', 'latex', ...
    'EdgeColor', 'none', 'Color', c.gray, 'HorizontalAlignment', 'center', 'FontSize', 7.4);
tsp_export_bundle(fig, outDir, 'tsp_system_model');
end

function box(fig, position, lines, edge, background)
annotation(fig, 'textbox', position, 'String', lines, 'Interpreter', 'latex', ...
    'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
    'EdgeColor', edge, 'BackgroundColor', background, 'LineWidth', 0.85, 'Margin', 3);
end

function color = tint(color)
color = color + (1-color)*0.88;
end
