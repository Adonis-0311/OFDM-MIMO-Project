classdef ANN_Estimator
    properties
        net
        params
    end
    
    methods
        function obj = ANN_Estimator(params)
            obj.params = params;
            if exist(fullfile(params.path.ModelDir,'ANN_Model.mat'),'file')
                load(fullfile(params.path.ModelDir,'ANN_Model.mat'),'net');
            else
                obj.net = obj.TrainANN();
            end
        end
        
        function net = TrainANN(obj)
            layers = [...
                sequenceInputLayer(2*params.sys.Nr*params.sys.Nt)
                fullyConnectedLayer(256)
                reluLayer
                fullyConnectedLayer(128)
                reluLayer
                fullyConnectedLayer(2*params.sys.Nr*params.sys.Nt)
                regressionLayer];
            
            options = trainingOptions('adam',...
                'MaxEpochs',50,...
                'Plots','training-progress');
            
            % 生成训练数据
            [trainData, trainLabels] = GenerateTrainingData(obj);
            
            net = trainNetwork(trainData, trainLabels, layers, options);
            save(fullfile(params.path.ModelDir,'ANN_Model.mat'),'net');
        end
        
        function H_est = Estimate(obj, rxSignal)
            H_est = predict(obj.net, rxSignal);
        end
    end
end