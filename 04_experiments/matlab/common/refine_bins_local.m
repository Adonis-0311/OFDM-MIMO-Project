function refined = refine_bins_local(Y, shape, coarse, radius, points)
%REFINE_BINS_LOCAL exhaustive separable local search, mirrors refine_bins_local.
% radius may be scalar or per-axis [ra rt rv] (0 disables an axis).
  if isscalar(radius), radius = radius * [1 1 1]; end
  Tmat = reshape(Y, shape(1), []);
  refined = zeros(size(coarse,1), 3);
  offs = cell(1,3);
  for d = 1:3
    if radius(d) > 0, offs{d} = linspace(-radius(d), radius(d), points);
    else, offs{d} = 0; end
  end
  for l = 1:size(coarse,1)
    c = coarse(l,:);
    Pa = numel(offs{1}); Pt = numel(offs{2}); Pv = numel(offs{3});
    % stage 1: contract angle axis for each angle offset
    S1 = zeros(Pa, shape(2)*shape(3));
    for p = 1:Pa
      a = steering_axis(shape(1), c(1)+offs{1}(p));
      S1(p,:) = a' * Tmat;
    end
    best = -inf; bestb = c;
    for p = 1:Pa
      M1 = reshape(S1(p,:), shape(2), shape(3));
      for q = 1:Pt
        b = steering_axis(shape(2), c(2)+offs{2}(q));
        v = b' * M1;                                  % 1 x Nv
        for s = 1:Pv
          cc = steering_axis(shape(3), c(3)+offs{3}(s));
          sc = abs(v * conj(cc))^2;
          if sc > best
            best = sc;
            bestb = [c(1)+offs{1}(p), c(2)+offs{2}(q), c(3)+offs{3}(s)];
          end
        end
      end
    end
    refined(l,:) = bestb;
  end
end
