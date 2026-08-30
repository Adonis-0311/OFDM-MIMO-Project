%% 数据准备
methods = {'LS估计', 'OMP', '传统ResNet', '本文CAE'};
metrics = {
    '参数量(M)',  [0,    0,      5.2,    0.78];  % 单位：百万
    'FLOPs(G)',  [0.002,0.15,   3.8,    0.45];  % 单位：Giga FLOPs
    'NMSE(dB)',  [-8.7, -14.2,  -18.9,  -21.5]; % 单位：dB
    '弱径恢复率',[12.3, 37.5,   63.1,   82.4]   % 单位：%
};

%% 创建多指标对比图
figure('Position', [200 200 1000 600], 'Color','w')

% ==========================
% 复杂度指标可视化（参数量+FLOPs）
% ==========================
subplot(2,1,1) 

% 双Y轴初始化
yyaxis left
b1 = bar([metrics{1,2}; metrics{2,2}]', 'BarWidth', 0.8);
set(b1(1), 'FaceColor', [0.7 0.7 0.7], 'DisplayName','参数量(M)')
set(b1(2), 'FaceColor', [0.4 0.4 0.4], 'DisplayName','FLOPs(G)')
ylabel('参数量 / FLOPs', 'FontSize',12)

% 左轴标注
text(3.8, 5.5, '← 复杂度降低83%', 'Color','r','FontSize',12, 'Rotation',90)
plot([3.7 3.7], [0 6], 'r--', 'LineWidth',1.5)

% 右轴（对数坐标）
yyaxis right
semilogy(metrics{2,2}, 's-', 'LineWidth',2, 'MarkerSize',10,...
    'MarkerFaceColor','b', 'Color','b', 'DisplayName','FLOPs趋势')
ylabel('FLOPs对数尺度', 'FontSize',12)
set(gca, 'YScale','log', 'YTick',10.^(-3:1:1))

% 图形修饰
set(gca, 'XTick',1:4, 'XTickLabel',methods, 'FontSize',12)
title('(a) 计算复杂度对比', 'FontSize',14)
legend('Location','northwest')
grid on

% ==========================
% 精度指标可视化（NMSE+弱径恢复）
% ==========================
subplot(2,1,2)

% 双柱状图绘制
width = 0.35;
x = 1:4;
b2 = bar(x - width/2, metrics{3,2}, width, 'FaceColor',[0.2 0.6 0.8]); 
hold on
b3 = bar(x + width/2, metrics{4,2}, width, 'FaceColor',[0.8 0.4 0.2]);

% 数据标注
for i = 1:4
    text(x(i)-0.2, metrics{3,2}(i)+2, sprintf('%.1fdB',metrics{3,2}(i)),...
        'FontSize',10, 'Color','b')
    text(x(i)+0.1, metrics{4,2}(i)+2, sprintf('%.1f%%',metrics{4,2}(i)),...
        'FontSize',10, 'Color','r') 
end

% 精度提升标注
annotation('arrow',[0.65 0.75],[0.35 0.27], 'Color','g','LineWidth',2)
text(3.5, -5, 'NMSE提升2.6dB', 'FontSize',12, 'Color','g')

% 图形修饰
set(gca, 'XTick',1:4, 'XTickLabel',methods, 'FontSize',12)
ylabel('性能指标值', 'FontSize',12)
title('(b) 估计精度对比', 'FontSize',14)
legend([b2,b3], {'NMSE (越小越好)','弱径恢复率 (越大越好)'}, 'Location','northwest')
grid on

% 保存图像
exportgraphics(gcf, 'method_comparison.png', 'Resolution',300)