% 初始化系统
params = SystemParams();
transceiver = OFDM_Transceiver(params);
evaluator = PerfEvaluation;

% 生成信道
[H_true, pathInfo] = CDL_Channel(params);

% 信号传输
[txSignal, pilotIndices] = transceiver.Transmit(randi([0 1],1e4,1));

% 通过信道
rxSignal = awgn(H_true .* txSignal, params.sys.SNR);

% 信道估计
ls_est = LS_Estimator(rxSignal(pilotIndices), txSignal(pilotIndices), params);
ann_est = ANN_Estimator(rxSignal, params);
csdl_est = CS_DL_Estimator(rxSignal, params);

% 性能评估
results = struct();
results.NMSE.LS = evaluator.CalculateNMSE(H_true, ls_est);
results.NMSE.ANN = evaluator.CalculateNMSE(H_true, ann_est);
results.NMSE.CS_DL = evaluator.CalculateNMSE(H_true, csdl_est);

% 可视化
evaluator.PlotComparison(results);