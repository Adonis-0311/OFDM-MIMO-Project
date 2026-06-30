function TrainCAEWithAdam(params)
    % 初始化CAE模型
    CAE_model = InitializeCAE(params);
    
    % 定义损失函数和Adam优化器
    loss_fn = MSE_Loss();
    optimizer = AdamOptimizer(CAE_model.params, params.algo.lr);
    
    % 训练循环
    for epoch = 1:params.algo.epochs
        for batch in DataLoader(params.path.data)
            H_initial = batch.initial
            H_target = batch.target
            
            % 前向传播
            H_est = CAE_model(H_initial)
            
            % 计算损失
            loss = loss_fn(H_est, H_target)
            
            % 反向传播和优化
            optimizer.update_params(grad(loss))
        end
    end
end