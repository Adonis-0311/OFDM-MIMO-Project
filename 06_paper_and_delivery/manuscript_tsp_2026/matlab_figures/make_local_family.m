function make_local_family(p, outDir)
%MAKE_LOCAL_FAMILY Headline accuracy, coverage, and runtime evidence.
%   Panel (a) reports seed-paired NMSE gains with seed-level 95% t-CIs.
%   Panel (b) resolves the Candan gain over the tested SNR-by-L grid.
%   Panel (c) keeps the common runtime ledger separate from the dedicated
%   projection-gate ledger shown in the inset card.

c = tsp_palette();
T = readtable(fullfile(p.cost, 'local_family_rows.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');
R = readtable(fullfile(p.runtime, 'summary.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');
P = readtable(fullfile(p.projectionRuntime, 'summary.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');

gridMethod = "grid_fft_topL_joint_ls";
refinementMethods = ["axiswise_quadratic_peak_joint_ls", ...
    "one_step_fixed_support_newton_joint_ls", ...
    "cartesian_local_joint_ls", "axiswise_candan_joint_ls"];
refinementLabels = {'Quadratic', 'Newton', 'Cartesian', 'Candan'};
refinementColors = [c.gold; c.orange; c.green; c.blue];

gainMean = zeros(numel(refinementMethods), 1);
gainLow = zeros(size(gainMean));
gainHigh = zeros(size(gainMean));
seedCount = zeros(size(gainMean));
for k = 1:numel(refinementMethods)
    seedGains = seedPairedGain(T, gridMethod, refinementMethods(k));
    [gainMean(k), gainLow(k), gainHigh(k)] = meanTInterval(seedGains);
    seedCount(k) = numel(seedGains);
end

snrValues = unique(T.snr_db, 'sorted');
targetCounts = unique(T.n_targets, 'sorted');
candanGain = zeros(numel(targetCounts), numel(snrValues));
for i = 1:numel(targetCounts)
    for j = 1:numel(snrValues)
        condition = T.snr_db == snrValues(j) & ...
            T.n_targets == targetCounts(i);
        gridNmse = T.measurement_nmse_db(condition & T.method == gridMethod);
        candanNmse = T.measurement_nmse_db(condition & ...
            T.method == "axiswise_candan_joint_ls");
        candanGain(i,j) = mean(gridNmse, 'omitnan') - ...
            mean(candanNmse, 'omitnan');
    end
end

fig = tsp_new_figure(18.0, 7.6);

%% (a) Seed-paired accuracy gain
axA = axes(fig, 'Position', [0.090 0.155 0.265 0.750]);
hold(axA, 'on');
y = (1:numel(refinementMethods))';
for k = 1:numel(refinementMethods)
    plot(axA, [gainLow(k) gainHigh(k)], [y(k) y(k)], '-', ...
        'Color', refinementColors(k,:), 'LineWidth', 1.45);
    plot(axA, [gainLow(k) gainLow(k)], y(k) + [-0.075 0.075], '-', ...
        'Color', refinementColors(k,:), 'LineWidth', 0.85);
    plot(axA, [gainHigh(k) gainHigh(k)], y(k) + [-0.075 0.075], '-', ...
        'Color', refinementColors(k,:), 'LineWidth', 0.85);
    scatter(axA, gainMean(k), y(k), 31, refinementColors(k,:), ...
        'filled', 'MarkerEdgeColor', 'white', 'LineWidth', 0.6);
    if gainHigh(k) > 20
        labelX = gainLow(k) - 0.55;
        labelAlign = 'right';
    else
        labelX = gainHigh(k) + 0.55;
        labelAlign = 'left';
    end
    text(axA, labelX, y(k), ...
        sprintf('%.2f [%.2f, %.2f]', gainMean(k), gainLow(k), gainHigh(k)), ...
        'HorizontalAlignment', labelAlign, 'VerticalAlignment', 'middle', ...
        'Color', c.text, 'FontSize', 6.8);
end
xline(axA, 0, '-', 'Color', c.gray, 'LineWidth', 0.75);
set(axA, 'YDir', 'reverse', 'YTick', y, 'YTickLabel', refinementLabels, ...
    'XLim', [0 31.5], 'XTick', 0:10:30, 'YLim', [0.45 4.55]);
xlabel(axA, 'Paired NMSE gain over grid (dB)');
title(axA, sprintf('Paired NMSE gain (95%% CI; %d seeds)', ...
    min(seedCount)));
grid(axA, 'on'); axA.YGrid = 'off';
axA.GridColor = c.grid; axA.GridAlpha = 1;
tsp_style_axes(axA); tsp_panel_label(axA, 1);

%% (b) Candan gain over the tested operating grid
axB = axes(fig, 'Position', [0.405 0.155 0.235 0.750]);
imagesc(axB, candanGain);
set(axB, 'YDir', 'normal');
colormap(axB, tsp_colormap(c.blue));
heatLimits = [10 50];
clim(axB, heatLimits);
xticks(axB, 1:numel(snrValues));
xticklabels(axB, compose('%g', snrValues));
yticks(axB, 1:numel(targetCounts));
yticklabels(axB, compose('%g', targetCounts));
xlabel(axB, 'SNR (dB)');
ylabel(axB, 'Target count, L');
title(axB, 'Candan gain over grid (dB)');
for i = 1:size(candanGain, 1)
    for j = 1:size(candanGain, 2)
        text(axB, j, i, sprintf('%.1f', candanGain(i,j)), ...
            'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
            'Color', heatTextColor(candanGain(i,j), heatLimits, c), ...
            'FontSize', 7.2, 'FontWeight', 'bold');
    end
end
cb = colorbar(axB, 'Location', 'eastoutside');
cb.Label.String = 'NMSE gain (dB)';
cb.FontSize = 7;
axis(axB, 'tight');
tsp_style_axes(axB); tsp_panel_label(axB, 2);

%% (c) Runtime: common ledger plus a separate projection-gate card
runtimeMethods = [gridMethod, "cartesian_local_joint_ls", ...
    "axiswise_quadratic_peak_joint_ls", "axiswise_candan_joint_ls", ...
    "one_step_fixed_support_newton_joint_ls"];
runtimeLabels = {'Grid', 'Cartesian', 'Quadratic', 'Candan', 'Newton'};
runtimeColors = [c.gray; c.green; c.gold; c.blue; c.orange];
runtimeMs = zeros(numel(runtimeMethods), 1);
for k = 1:numel(runtimeMethods)
    runtimeMs(k) = tableScalar(R, runtimeMethods(k), ...
        'median_wall_clock_ms');
end

axC = axes(fig, 'Position', [0.720 0.365 0.260 0.540]);
hold(axC, 'on');
yRuntime = (1:numel(runtimeMethods))';
for k = 1:numel(runtimeMethods)
    plot(axC, [0 runtimeMs(k)], [yRuntime(k) yRuntime(k)], '-', ...
        'Color', c.grid, 'LineWidth', 1.45);
    scatter(axC, runtimeMs(k), yRuntime(k), 29, runtimeColors(k,:), ...
        'filled', 'MarkerEdgeColor', 'white', 'LineWidth', 0.55);
    text(axC, runtimeMs(k) + 0.65, yRuntime(k), ...
        sprintf('%.2f', runtimeMs(k)), 'VerticalAlignment', 'middle', ...
        'Color', c.text, 'FontSize', 7.0);
end
set(axC, 'YDir', 'reverse', 'YTick', yRuntime, ...
    'YTickLabel', runtimeLabels, 'YLim', [0.45 5.55], ...
    'XLim', [0 38], 'XTick', 0:10:30);
xlabel(axC, 'Median wall-clock time (ms)');
title(axC, 'Common-ledger runtime');
grid(axC, 'on'); axC.YGrid = 'off';
axC.GridColor = c.grid; axC.GridAlpha = 1;
tsp_style_axes(axC); tsp_panel_label(axC, 3);

baseRuntime = tableScalar(P, "axiswise_candan_joint_ls", ...
    'median_wall_clock_ms');
gateRuntime = tableScalar(P, "projection_energy_gate", ...
    'median_wall_clock_ms');
gateDelta = gateRuntime - baseRuntime;
gatePercent = 100 * gateDelta / baseRuntime;
axCard = axes(fig, 'Position', [0.720 0.040 0.260 0.175], ...
    'Color', c.lightBlue, 'Box', 'on', 'XColor', c.blue, ...
    'YColor', c.blue, 'LineWidth', 0.8);
set(axCard, 'XLim', [0 1], 'YLim', [0 1], 'XTick', [], 'YTick', []);
text(axCard, 0.04, 0.78, 'Projection gate (dedicated ledger)', ...
    'FontWeight', 'bold', 'FontSize', 7.3, 'Color', c.text, ...
    'VerticalAlignment', 'middle');
text(axCard, 0.04, 0.47, ...
    sprintf('Candan %.2f ms  |  gated %.2f ms', ...
    baseRuntime, gateRuntime), ...
    'FontSize', 7.0, 'Color', c.text, 'VerticalAlignment', 'middle');
text(axCard, 0.04, 0.18, ...
    sprintf('Overhead: +%.2f ms  (+%.2f%%)', gateDelta, gatePercent), ...
    'FontSize', 7.0, 'FontWeight', 'bold', 'Color', c.blue, ...
    'VerticalAlignment', 'middle');

tsp_export_bundle(fig, outDir, 'tsp_local_family');
end

function gains = seedPairedGain(T, gridMethod, refinementMethod)
% Average within each seed before pairing, so the CI reflects seed variation.
seeds = unique(T.seed, 'sorted');
gains = nan(numel(seeds), 1);
for i = 1:numel(seeds)
    gridNmse = T.measurement_nmse_db(T.seed == seeds(i) & ...
        T.method == gridMethod);
    refinedNmse = T.measurement_nmse_db(T.seed == seeds(i) & ...
        T.method == refinementMethod);
    if ~isempty(gridNmse) && ~isempty(refinedNmse)
        gains(i) = mean(gridNmse, 'omitnan') - ...
            mean(refinedNmse, 'omitnan');
    end
end
gains = gains(isfinite(gains));
end

function [center, low, high] = meanTInterval(values)
% Two-sided 95% Student-t interval without requiring Statistics Toolbox.
values = values(isfinite(values));
n = numel(values);
center = mean(values);
if n < 2
    low = center;
    high = center;
    return;
end
t95 = [12.7062 4.3027 3.1824 2.7764 2.5706 2.4469 2.3646 ...
    2.3060 2.2622 2.2281 2.2010 2.1788 2.1604 2.1448 2.1314 ...
    2.1199 2.1098 2.1009 2.0930 2.0860 2.0796 2.0739 2.0687 ...
    2.0639 2.0595 2.0555 2.0518 2.0484 2.0452 2.0423];
df = n - 1;
if df <= numel(t95)
    critical = t95(df);
else
    critical = 1.96;
end
halfWidth = critical * std(values, 0) / sqrt(n);
low = center - halfWidth;
high = center + halfWidth;
end

function value = tableScalar(T, method, variableName)
row = T(T.method == method, :);
if height(row) ~= 1
    error('Expected one runtime row for method "%s"; found %d.', ...
        method, height(row));
end
value = row.(variableName);
end

function color = heatTextColor(value, limits, c)
normalized = (value - limits(1)) / diff(limits);
if normalized > 0.57
    color = [1 1 1];
else
    color = c.text;
end
end
