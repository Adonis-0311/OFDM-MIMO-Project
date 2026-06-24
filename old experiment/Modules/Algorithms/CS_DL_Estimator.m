classdef CS_DL_Estimator
    properties
        params
        CS_Model
        DL_Model
    end
    
    methods
        function obj = CS_DL_Estimator(params)
            obj.params = params;
            obj.CS_Model = CompressedSensing(params);
            obj.DL_Model = load(fullfile(params.path.ModelDir,'DL_Model.mat'));
        end
        
        function [H_est, timeCost] = Estimate(obj, rxSignal)
            tic;
            % 第一阶段：压缩感知
            H_cs = obj.CS_Model.OMP_Estimation(rxSignal);
            
            % 第二阶段：深度学习优化
            H_est = obj.DL_Model.predict(H_cs);
            
            timeCost = toc;
        end
    end
end

classdef CompressedSensing
    methods
        function H_est = OMP_Estimation(obj, y, Phi, K)
            % 正交匹配追踪核心算法
            residual = y;
            idx = [];
            for iter = 1:K
                corr = abs(Phi'*residual);
                [~, newIdx] = max(corr);
                idx = union(idx, newIdx);
                Phi_K = Phi(:, idx);
                x_hat = pinv(Phi_K)*y;
                residual = y - Phi_K*x_hat;
            end
            H_est = zeros(size(Phi,2),1);
            H_est(idx) = x_hat;
        end
    end
end