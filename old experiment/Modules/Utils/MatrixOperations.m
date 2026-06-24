classdef MatrixOperations
    methods (Static)
        function H = ApplyDoppler(H_true, dopplerShift, timeVector)
            % 应用多普勒频移
            phaseShift = exp(1j*2*pi*dopplerShift*timeVector);
            H = H_true .* reshape(phaseShift,1,1,1,[]);
        end
        
        function H_flat = FlattenChannelMatrix(H)
            % 将信道矩阵展平为向量
            H_flat = reshape(H, [], size(H,4));
        end
    end
end