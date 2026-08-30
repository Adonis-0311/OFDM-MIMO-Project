function [rmse_axis, half_bin_rate] = matched_bin_rmse(est_bins, true_bins, shape)
%MATCHED_BIN_RMSE Hungarian match then per-axis RMSE with circular bin distance.
  L = size(true_bins,1);
  C = zeros(L,L);
  for i = 1:L
    for j = 1:L
      d = circ_dist(est_bins(i,:), true_bins(j,:), shape);
      C(i,j) = sum(d.^2);
    end
  end
  a = min_cost_match(C);
  D = zeros(L,3);
  for i = 1:L, D(i,:) = circ_dist(est_bins(i,:), true_bins(a(i),:), shape); end
  rmse_axis = sqrt(mean(D.^2, 1));
  half_bin_rate = mean(all(D <= 0.5, 2));
end
function d = circ_dist(x, y, shape)
  d = abs(x - y);
  d = min(d, shape - d);
end
