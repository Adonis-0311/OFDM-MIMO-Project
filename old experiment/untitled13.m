%% 数据准备
methods = {'LS估计', 'OMP', '传统ResNet', '本文CAE'};
metrics = {
    '参数量(M)',  [0,    0,      5.2,    0.78];  % 单位：百万
    'FLOPs(G)',  [0.002,0.15,   3.8,    0.45];  % 单位：Giga FLOPs
    'NMSE(dB)',  [-8.7, -14.2,  -18.9,  -21.5]; % 单位：dB
    '弱径恢复率',[12.3, 37.5,   63.1,   82.4]   % 单位：%
};

%% 创建多指标对比图（美化版）
figure('Position', [200 200 1200 700], 'Color','w')

% 设置全局字体
set(groot, 'DefaultAxesFontName', 'Helvetica')
set(groot, 'DefaultTextFontName', 'Helvetica')

% ==========================
% 子图1：复杂度指标可视化（参数量+FLOPs）
% ==========================
subplot(2,2,[1 2])  % 上半部分占两列

% 左Y轴：柱状图
yyaxis left
b1 = bar([metrics{1,2}; metrics{2,2}]', 0.7);
b1(1).FaceColor = [0.3 0.75 0.93];  % 柔和蓝色
b1(1).EdgeColor = 'none';
b1(1).FaceAlpha = 0.8;
b1(2).FaceColor = [0.95 0.6 0.2];   % 暖橙色
b1(2).EdgeColor = 'none';
b1(2).FaceAlpha = 0.8;

ylabel('参数量 (M) / FLOPs (G)', 'FontSize', 13, 'FontWeight', 'bold')
ylim([0 6])

% 在CAE柱子上添加标注
text(3.8, 5.2, '↓ 83%', 'Color', [0.8 0.2 0.2], 'FontSize', 14, 'FontWeight', 'bold', ...
    'HorizontalAlignment', 'center', 'BackgroundColor', [1 1 1 0.8], 'EdgeColor', [0.8 0.2 0.2])
annotation('arrow', [0.72 0.68], [0.82 0.78], 'Color', [0.8 0.2 0.2], 'LineWidth', 2, 'HeadStyle', 'cback1')

% 右Y轴：折线图（对数坐标）
yyaxis right
semilogy(1:4, metrics{2,2}, 'o-', 'LineWidth', 2.5, 'MarkerSize', 10, ...
    'Color', [0.5 0.5 0.5], 'MarkerFaceColor', [0.95 0.6 0.2], 'MarkerEdgeColor', 'w', ...
    'LineWidth', 2)
ylabel('FLOPs (G) 对数尺度', 'FontSize', 13, 'FontWeight', 'bold', 'Color', [0.5 0.5 0.5])
set(gca, 'YScale', 'log', 'YTick', [0.001 0.01 0.1 1 10], 'YMinorGrid', 'off')
ylim([0.001 10])

% X轴设置
set(gca, 'XTick', 1:4, 'XTickLabel', methods, 'FontSize', 12, 'FontWeight', 'bold')
xlim([0.5 4.5])

% 图例和标题
legend([b1(1), b1(2)], {'参数量 (M)', 'FLOPs (G)'}, ...
    'Location', 'northwest', 'FontSize', 11, 'Box', 'off')
title('(a) 计算复杂度对比', 'FontSize', 15, 'FontWeight', 'bold', 'Color', [0.2 0.2 0.5])

% 网格线
grid on
ax = gca;
ax.GridLineStyle = ':';
ax.GridAlpha = 0.3;

% ==========================
% 子图2：NMSE对比（左下图）
% ==========================
subplot(2,2,3)

% 创建渐变色柱状图
x = 1:4;
colors_nmse = [0.2 0.4 0.8; 0.3 0.5 0.9; 0.4 0.6 1.0; 0.1 0.8 1.0];
b_nmse = bar(x, metrics{3,2}, 0.6);

% 设置每个柱子的颜色
for i = 1:4
    b_nmse.FaceColor = 'flat';
    b_nmse.CData(i,:) = colors_nmse(i,:);
end
b_nmse.EdgeColor = 'none';

% 添加数据标签
for i = 1:4
    text(x(i), metrics{3,2}(i) + 0.8, sprintf('%.1f dB', metrics{3,2}(i)), ...
        'FontSize', 11, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', ...
        'Color', [0 0.3 0.6])
end

% 标注NMSE提升
annotation('doublearrow', [0.35 0.45], [0.32 0.32], 'Color', [0.8 0.2 0.2], 'LineWidth', 2)
text(2.8, -5, '↑ 2.6 dB', 'FontSize', 12, 'FontWeight', 'bold', 'Color', [0.8 0.2 0.2], ...
    'BackgroundColor', [1 1 0.9], 'EdgeColor', [0.8 0.2 0.2])

% 图形设置
set(gca, 'XTick', 1:4, 'XTickLabel', methods, 'FontSize', 11, 'FontWeight', 'bold')
ylabel('NMSE (dB)', 'FontSize', 13, 'FontWeight', 'bold')
title('(b) 归一化均方误差', 'FontSize', 13, 'FontWeight', 'bold', 'Color', [0.2 0.2 0.5])
ylim([-25 0])
grid on
ax = gca;
ax.GridLineStyle = ':';
ax.GridAlpha = 0.3;

% ==========================
% 子图3：弱径恢复率对比（右下）
% ==========================
subplot(2,2,4)

% 创建渐变色柱状图
colors_recovery = [0.9 0.4 0.2; 0.95 0.5 0.25; 1.0 0.6 0.3; 1.0 0.7 0.4];
b_rec = bar(x, metrics{4,2}, 0.6);

% 设置每个柱子的颜色
for i = 1:4
    b_rec.FaceColor = 'flat';
    b_rec.CData(i,:) = colors_recovery(i,:);
end
b_rec.EdgeColor = 'none';

% 添加数据标签
for i = 1:4
    text(x(i), metrics{4,2}(i) + 3, sprintf('%.1f%%', metrics{4,2}(i)), ...
        'FontSize', 11, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', ...
        'Color', [0.8 0.3 0])
end

% 标注恢复率提升
annotation('doublearrow', [0.8 0.92], [0.32 0.32], 'Color', [0.2 0.6 0.2], 'LineWidth', 2)
text(3.2, 70, '↑ 19.3%', 'FontSize', 12, 'FontWeight', 'bold', 'Color', [0.2 0.6 0.2], ...
    'BackgroundColor', [0.9 1 0.9], 'EdgeColor', [0.2 0.6 0.2])

% 图形设置
set(gca, 'XTick', 1:4, 'XTickLabel', methods, 'FontSize', 11, 'FontWeight', 'bold')
ylabel('弱径恢复率 (%)', 'FontSize', 13, 'FontWeight', 'bold')
title('(c) 弱径恢复能力', 'FontSize', 13, 'FontWeight', 'bold', 'Color', [0.2 0.2 0.5])
ylim([0 100])
grid on
ax = gca;
ax.GridLineStyle = ':';
ax.GridAlpha = 0.3;

% ==========================
% 整体美化
% ==========================
% 添加整体标题
sgtitle('信道估计方法性能对比分析', 'FontSize', 18, 'FontWeight', 'bold', 'Color', [0.1 0.1 0.3])

% 添加背景色
annotation('rectangle', [0.02 0.02 0.96 0.96], 'Color', 'none', 'FaceColor', [0.98 0.98 0.98], 'FaceAlpha', 0.3)

% 调整子图间距
set(gcf, 'Color', 'w')

% 保存高清图像
exportgraphics(gcf, 'method_comparison_beautified.png', 'Resolution', 300)
exportgraphics(gcf, 'method_comparison_beautified.pdf', 'ContentType', 'vector')

% 显示完成信息
disp('图像已生成并保存为 method_comparison_beautified.png 和 .pdf')