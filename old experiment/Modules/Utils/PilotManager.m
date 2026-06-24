classdef PilotManager
    methods (Static)
        function [pilotIndices, dataIndices] = GetPilotPositions(numSubcarriers, interval)
            % 生成梳状导频位置
            pilotIndices = 1:interval:numSubcarriers;
            dataIndices = setdiff(1:numSubcarriers, pilotIndices);
        end
        
        function txGrid = InsertPilots(dataSymbols, pilotSymbols, pilotIndices)
            % 插入导频到OFDM资源网格
            txGrid = zeros(size(dataSymbols,1), numSubcarriers);
            txGrid(:, pilotIndices) = pilotSymbols;
            txGrid(:, dataIndices) = dataSymbols;
        end
    end
end