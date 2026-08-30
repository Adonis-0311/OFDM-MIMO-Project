function [bins, gain] = estimate_single_target_multires(Y, shape)
%Mirrors estimate_single_target_multiresolution (7-point, 6 shrinking radii).
  radii = [0.5 0.12 0.03 0.006 0.0012 0.00024]; points = 7;
  coarse = topk_grid_bins(Y, 1);
  center = coarse(1,:);
  best = -inf; bestb = center;
  Tmat = reshape(Y, shape(1), []);
  for radius = radii
    offs = linspace(-radius, radius, points);
    for pa = 1:points
      a = steering_axis(shape(1), center(1)+offs(pa));
      S1 = reshape(a' * Tmat, shape(2), shape(3));
      for pt = 1:points
        b = steering_axis(shape(2), center(2)+offs(pt));
        v = b' * S1;
        for pv = 1:points
          c = steering_axis(shape(3), center(3)+offs(pv));
          sc = abs(v * conj(c))^2;
          if sc > best, best = sc; bestb = center + [offs(pa) offs(pt) offs(pv)]; end
        end
      end
    end
    center = bestb;
  end
  bins = bestb;
  A = tensor_atom(shape, bins);
  gain = A(:)' * Y(:);
end
