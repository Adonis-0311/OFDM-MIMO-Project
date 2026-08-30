function bins = topk_grid_bins(Y, k)
%TOPK_GRID_BINS orthonormal FFT magnitude top-k, mirrors topk_grid_bins (C-order flat).
  F = fftn(Y) / sqrt(numel(Y));
  sz = size(Y);
  mag = abs(F);
  [~, order] = sort(mag(:), 'descend');
  bins = zeros(k,3);
  for i = 1:k
    idx = order(i) - 1;                          % MATLAB column-major flat
    [ia, it, iv] = ind2sub_c(sz, idx);
    bins(i,:) = [ia it iv];
  end
end
function [ia, it, iv] = ind2sub_c(sz, idx0)
% column-major 0-based decode (MATLAB native), returns 0-based subs
  ia = mod(idx0, sz(1));
  r  = floor(idx0 / sz(1));
  it = mod(r, sz(2));
  iv = floor(r / sz(2));
end
