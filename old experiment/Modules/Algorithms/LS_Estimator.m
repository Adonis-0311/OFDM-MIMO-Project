function [H_est, timeCost] = LS_Estimator(rxPilot, txPilot, params)
    tic;
    H_est = zeros(params.sys.Nr, params.sys.Nt, params.sys.NumSubcarriers);
    for sc = 1:length(params.pilotIndices)
        Y = rxPilot(:,:,sc);
        X = diag(txPilot(sc,:));
        H_est(:,:,sc) = Y * pinv(X);
    end
    timeCost = toc;
end