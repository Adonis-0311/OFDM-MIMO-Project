function out = interpolate_bins(coarse, refined, alpha)
%INTERPOLATE_BINS bounded interpolation b0 + alpha.*(b*-b0); alpha scalar or [1x3]
  if isscalar(alpha), alpha = alpha*[1 1 1]; end
  out = coarse + (refined - coarse) .* alpha;
end
