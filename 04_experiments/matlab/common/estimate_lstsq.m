function [est, gains] = estimate_lstsq(Y, shape, bins)
%ESTIMATE_LSTSQ LS reconstruction from refined bins, mirrors estimate_from_bins_lstsq.
  if isempty(bins), est = zeros(shape); gains = []; return; end
  A = design_matrix(shape, bins);
  gains = A \ Y(:);
  est = reshape(A * gains, shape);
end
