function make_triplet_mechanism(outDir)
%MAKE_TRIPLET_MECHANISM Theory schematic for separable Candan refinement.
%   The figure contains only analytic and symbolic content: an illustrative
%   finite-length Dirichlet response, exact common-factor cancellation, and
%   the error-propagation chain used by the manuscript analysis.

c = tsp_palette();
fig = tsp_new_figure(18.0, 7.1);

%% (a) Three adjacent samples of an analytic Dirichlet response
axA = axes(fig, 'Position', [0.055 0.17 0.275 0.72]);
hold(axA, 'on');
N = 32;
delta = 0.28;
q = linspace(-1.65, 1.65, 1001);
mu = dirichlet_magnitude(delta-q, N);
plot(axA, q, mu, 'Color', c.blue, 'LineWidth', 1.55);

sampleQ = [-1 0 1];
sampleMu = dirichlet_magnitude(delta-sampleQ, N);
for k = 1:numel(sampleQ)
    plot(axA, [sampleQ(k) sampleQ(k)], [0 sampleMu(k)], '-', ...
        'Color', c.orange, 'LineWidth', 0.95);
    plot(axA, sampleQ(k), sampleMu(k), 'o', 'Color', c.orange, ...
        'MarkerFaceColor', 'white', 'MarkerSize', 5.2, 'LineWidth', 1.0);
end

plot(axA, [delta delta], [0 1.02], '--', 'Color', c.green, ...
    'LineWidth', 0.9);
arrow_y = 0.105;
plot(axA, [0 delta], [arrow_y arrow_y], '-', 'Color', c.green, ...
    'LineWidth', 1.0);
plot(axA, 0, arrow_y, '<', 'Color', c.green, 'MarkerFaceColor', c.green, ...
    'MarkerSize', 4.2);
plot(axA, delta, arrow_y, '>', 'Color', c.green, ...
    'MarkerFaceColor', c.green, 'MarkerSize', 4.2);
text(axA, delta/2, arrow_y+0.065, '$\delta_d$', 'Interpreter', 'latex', ...
    'HorizontalAlignment', 'center', 'Color', c.green, 'FontSize', 7.3);

labels = {'$|Z_{d,-}|$', '$|Z_{d,0}|$', '$|Z_{d,+}|$'};
labelX = [-1.00 -0.08 1.00];
align = {'center', 'right', 'center'};
for k = 1:numel(sampleQ)
    text(axA, labelX(k), min(sampleMu(k)+0.11, 1.055), labels{k}, ...
        'Interpreter', 'latex', 'HorizontalAlignment', align{k}, ...
        'Color', c.orange, 'FontSize', 7.1);
end
text(axA, 0.62, 0.73, '$|g_{N_d}(\delta_d-q)|$', ...
    'Interpreter', 'latex', 'Color', c.blue, 'FontSize', 7.1);
text(axA, delta+0.035, 1.015, 'true offset', 'Color', c.green, ...
    'FontSize', 6.7, 'VerticalAlignment', 'bottom');

set(axA, 'XLim', [-1.65 1.65], 'YLim', [0 1.12], ...
    'XTick', [-1 0 1], 'YTick', [0 0.5 1]);
xlabel(axA, '$q$ (FFT-bin offset)', 'Interpreter', 'latex');
ylabel(axA, '$|Z_{d,q}|/|C_{-d,\ell}|$', 'Interpreter', 'latex');
grid(axA, 'on');
axA.GridColor = c.grid;
axA.GridAlpha = 1;
tsp_style_axes(axA);
panel_heading(axA, '(a) Three FFT samples');

%% (b) The non-updated tensor axes form one common complex factor
axB = axes(fig, 'Position', [0.365 0.13 0.285 0.76]);
axis(axB, [0 1 0 1]);
axis(axB, 'off');
hold(axB, 'on');
panel_heading(axB, '(b) Exact separable cancellation');

rowY = [0.75 0.57 0.39];
rowName = {'$Z_{d,-}=$', '$Z_{d,0}=$', '$Z_{d,+}=$'};
axisTerm = {'$g_{N_d}(\delta_d+1)$', '$g_{N_d}(\delta_d)$', ...
    '$g_{N_d}(\delta_d-1)$'};
for k = 1:3
    text(axB, 0.01, rowY(k), rowName{k}, 'Interpreter', 'latex', ...
        'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle', ...
        'Color', c.text, 'FontSize', 7.0);
    simple_box(axB, 0.19, rowY(k)-0.065, 0.26, 0.13, c.lightBlue, c.blue);
    text(axB, 0.32, rowY(k), '$C_{-d,\ell}$', 'Interpreter', 'latex', ...
        'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
        'Color', c.blue, 'FontSize', 7.4);
    text(axB, 0.49, rowY(k), '$\times$', 'Interpreter', 'latex', ...
        'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
        'Color', c.text, 'FontSize', 7.2);
    simple_box(axB, 0.54, rowY(k)-0.065, 0.45, 0.13, c.lightGreen, c.green);
    text(axB, 0.765, rowY(k), axisTerm{k}, 'Interpreter', 'latex', ...
        'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
        'Color', c.text, 'FontSize', 7.0);
end

plot(axB, [0.16 0.99], [0.285 0.285], '-', 'Color', c.grid, ...
    'LineWidth', 0.8);
text(axB, 0.50, 0.235, ...
    '$C_{-d,\ell}=\beta_\ell\prod_{r\ne d}g_{N_r}(\delta_{r,\ell})$', ...
    'Interpreter', 'latex', 'HorizontalAlignment', 'center', ...
    'Color', c.blue, 'FontSize', 6.9);
text(axB, 0.50, 0.135, ...
    ['$\frac{Z_{d,-}-Z_{d,+}}{2Z_{d,0}-Z_{d,-}-Z_{d,+}}' ...
    '=\frac{\tan(\pi\delta_d/N_d)}{\tan(\pi/N_d)}$'], ...
    'Interpreter', 'latex', 'HorizontalAlignment', 'center', ...
    'VerticalAlignment', 'middle', 'Color', c.text, 'FontSize', 6.6);
text(axB, 0.50, 0.045, 'The shared complex factor cancels exactly.', ...
    'HorizontalAlignment', 'center', 'Color', c.green, ...
    'FontWeight', 'bold', 'FontSize', 6.8);

%% (c) Coordinate perturbations propagate through the joint fit
axC = axes(fig, 'Position', [0.685 0.13 0.285 0.76]);
axis(axC, [0 1 0 1]);
axis(axC, 'off');
hold(axC, 'on');
panel_heading(axC, '(c) Error propagation to joint LS');

boxX = 0.08;
boxW = 0.84;
boxH = 0.135;
boxY = [0.745 0.525 0.305 0.085];
faces = {c.lightGold, c.lightBlue, c.lightGreen, soft_tint(c.purple)};
edges = {c.gold, c.blue, c.green, c.purple};
titles = {'Triplet perturbation', 'Coordinate error', ...
    'Dictionary perturbation', 'Joint-LS error'};
mathText = {'$B_{n,d,\ell},\ B_{d,d,\ell}$', ...
    '$\epsilon_{d,\ell}=|\widehat\delta_{d,\ell}-\delta_{d,\ell}|$', ...
    '$\|\mathbf A_0-\widehat{\mathbf A}\|_2\leq E_A$', ...
    '$\|\widehat{\beta}-\beta\|_2$'};
for k = 1:4
    equation_box(axC, boxX, boxY(k), boxW, boxH, faces{k}, edges{k}, ...
        titles{k}, mathText{k});
end

arrowLabels = {'quotient bound', '$\Lambda_{N_d}$ Lipschitz', ...
    '$\sigma_{\min}(\widehat{\mathbf A})$'};
arrowLatex = [false true true];
for k = 1:3
    yTop = boxY(k);
    yBottom = boxY(k+1)+boxH;
    vertical_arrow(axC, 0.50, yTop-0.012, yBottom+0.012, c.text);
    if arrowLatex(k)
        interpreter = 'latex';
    else
        interpreter = 'none';
    end
    text(axC, 0.96, (yTop+yBottom)/2, arrowLabels{k}, ...
        'Interpreter', interpreter, 'HorizontalAlignment', 'right', ...
        'VerticalAlignment', 'middle', 'Color', c.gray, 'FontSize', 6.4);
end

tsp_export_bundle(fig, outDir, 'tsp_triplet_mechanism');
end

function mu = dirichlet_magnitude(x, N)
denominator = N*sin(pi*x/N);
mu = abs(sin(pi*x)./denominator);
nearZero = abs(x) < 10*eps;
mu(nearZero) = 1;
end

function panel_heading(ax, label)
c = tsp_palette();
text(ax, 0, 1.065, label, 'Units', 'normalized', ...
    'HorizontalAlignment', 'left', 'VerticalAlignment', 'bottom', ...
    'FontWeight', 'bold', 'FontSize', 8.2, 'Color', c.text, ...
    'Clipping', 'off');
end

function simple_box(ax, x, y, w, h, face, edge)
patch(ax, [x x+w x+w x], [y y y+h y+h], face, ...
    'EdgeColor', edge, 'LineWidth', 0.8);
end

function equation_box(ax, x, y, w, h, face, edge, titleText, equationText)
simple_box(ax, x, y, w, h, face, edge);
text(ax, x+w/2, y+0.69*h, titleText, 'HorizontalAlignment', 'center', ...
    'VerticalAlignment', 'middle', 'FontWeight', 'bold', 'FontSize', 6.9);
text(ax, x+w/2, y+0.31*h, equationText, 'Interpreter', 'latex', ...
    'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
    'FontSize', 7.1);
end

function vertical_arrow(ax, x, yStart, yEnd, color)
headHalfWidth = 0.018;
headHeight = 0.018;
plot(ax, [x x], [yStart yEnd+headHeight], '-', 'Color', color, ...
    'LineWidth', 0.85);
patch(ax, [x x-headHalfWidth x+headHalfWidth], ...
    [yEnd yEnd+headHeight yEnd+headHeight], color, 'EdgeColor', color);
end

function color = soft_tint(color)
color = color + (1-color)*0.88;
end
