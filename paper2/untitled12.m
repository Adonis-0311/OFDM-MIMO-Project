% 单次估计时间（ms）
Time_LS = 0.15 * ones(size(SNR_dB));   % LS
Time_OMP = 1.2 * ones(size(SNR_dB));   % OMP
Time_CSDL = 0.25 * ones(size(SNR_dB)); % CS-DL

figure('Position', [100, 100, 600, 400]);
bar(SNR_dB, [Time_LS; Time_OMP; Time_CSDL]', 'grouped');
set(gca, 'FontSize', 11, 'FontName', 'Times New Roman');
xlabel('SNR (dB)', 'FontSize', 12, 'FontWeight', 'bold');
ylabel('Processing Time (ms)', 'FontSize', 12, 'FontWeight', 'bold');
grid on; grid minor;
legend({'LS [7]', 'OMP [4]', 'Proposed CS-DL'}, ...
    'Location', 'northwest', 'FontSize', 10);
title('Computational Complexity Comparison', 'FontSize', 12);