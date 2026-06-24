classdef PerfEvaluation
    methods (Static)
        function NMSE = CalculateNMSE(H_true, H_est)
            NMSE = 10*log10(norm(H_true(:)-H_est(:))^2 / norm(H_true(:))^2);
        end
        
        function BER = CalculateBER(txBits, rxBits)
            BER = sum(txBits ~= rxBits)/numel(txBits);
        end
        
        function PlotComparison(results)
            figure;
            subplot(2,1,1);
            semilogy(results.SNR, results.NMSE.LS, '-o', ...
                     results.SNR, results.NMSE.ANN, '-s', ...
                     results.SNR, results.NMSE.CS_DL, '-d');
            legend('LS','ANN','CS-DL');
            ylabel('NMSE (dB)');
            
            subplot(2,1,2);
            semilogy(results.SNR, results.BER.LS, '-o', ...
                     results.SNR, results.BER.ANN, '-s', ...
                     results.SNR, results.BER.CS_DL, '-d');
            legend('LS','ANN','CS-DL'); 
            ylabel('BER');
        end
    end
end