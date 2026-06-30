%% 性能对比可视化
figure('Position', [100 100 1200 500], 'Color','w')

% ==========================
% 性能指标柱状图对比
% ==========================
subplot(1,2,1)
metrics = {
    '平均迭代次数',  8.2, 4.7; 
    '计算耗时(ms)', 12.3, 6.8;
    'NMSE(dB)',    -18.2, -17.9
};

% 数据准备
metric_names = metrics(:,1);
traditional = cell2mat(metrics(:,2));
improved = cell2mat(metrics(:,3));
x = 1:length(metric_names);

% 绘制柱状图
b = bar([traditional, improved], 0.8);
b(1).FaceColor = [0.6 0.6 0.6];
b(2).FaceColor = [0.2 0.6 0.8];

% 标注数值
for i = 1:length(x)
    text(x(i)-0.2, traditional(i)+0.5, sprintf('%.1f',traditional(i)),...
        'FontSize',10, 'Color','k')
    text(x(i)+0.1, improved(i)+0.5, sprintf('%.1f',improved(i)),...
        'FontSize',10, 'Color','b')
end

% 图形修饰
set(gca, 'XTick',x, 'XTickLabel',metric_names, 'FontSize',11)
ylabel('性能指标值', 'FontSize',12)
title('(a) 关键指标对比', 'FontSize',14)
legend({'传统OMP','改进OMP'}, 'Location','northwest')
grid on

% ==========================
% 残差收敛过程对比
% ==========================
subplot(1,2,2)

% 生成模拟数据
iter_trad = 1:8;
res_trad = 10*exp(-0.5*(iter_trad-1)) + randn(size(iter_trad))*0.3;

iter_improved = 1:5;
res_improved = 10*exp(-0.8*(iter_improved-1)) + randn(size(iter_improved))*0.3;

% 绘制收敛曲线
semilogy(iter_trad, res_trad, 's-', 'LineWidth',2, 'Color',[0.6 0.6 0.6],...
    'MarkerSize',10, 'MarkerFaceColor',[0.8 0.8 0.8])
hold on
semilogy(iter_improved, res_improved, 'd-', 'LineWidth',2, 'Color',[0.2 0.6 0.8],...
    'MarkerSize',10, 'MarkerFaceColor',[0.4 0.8 1])

% 标注终止点
text(iter_trad(end)+0.1, res_trad(end), '传统终止点',...
    'FontSize',10, 'Color',[0.5 0.5 0.5])
text(iter_improved(end)+0.1, res_improved(end), '自适应终止点',...
    'FontSize',10, 'Color',[0.2 0.5 0.8])

% 图形修饰
xlabel('迭代次数', 'FontSize',12)
ylabel('残差范数(对数尺度)', 'FontSize',12)
title('(b) 残差收敛过程', 'FontSize',14)
legend({'传统OMP','改进OMP'}, 'Location','northeast')
grid on
set(gca, 'YScale','log', 'FontSize',11)
xlim([0.5 9])

