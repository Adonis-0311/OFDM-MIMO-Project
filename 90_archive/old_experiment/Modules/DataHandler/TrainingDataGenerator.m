classdef TrainingDataGenerator
    methods (Static)
        function [H_train, H_train_noisy] = GenerateDataset(params, numSamples)
            % 生成含噪声的信道数据集
            H_train = zeros(params.sys.Nr, params.sys.Nt, params.sys.NumSubcarriers, numSamples);
            H_train_noisy = zeros(size(H_train));
            
            parfor i = 1:numSamples
                % 生成原始信道
                [H_true, ~] = CDL_Channel(params);
                
                % 添加噪声模拟CS估计误差
                H_noisy = awgn(H_true, params.algo.CS_SNR);
                
                H_train(:,:,:,i) = H_true;
                H_train_noisy(:,:,:,i) = H_noisy;
            end
            
            % 保存数据集
            save(fullfile(params.path.DataDir, 'TrainingData.mat'),...
                'H_train', 'H_train_noisy', '-v7.3');
        end
        
        function [inputBatch, targetBatch] = PreprocessData(H_noisy, H_true)
            % 数据预处理：归一化与格式转换
            inputBatch = single(real(H_noisy)); 
            targetBatch = single(real(H_true));
            
            % 添加复数部分作为额外通道
            inputBatch = cat(4, inputBatch, imag(H_noisy));
            targetBatch = cat(4, targetBatch, imag(H_true));
        end
    end
end