function R = tensor_nomp_known_order(Y, L, varargin)
%TENSOR_NOMP_KNOWN_ORDER mirrors baseline/tensor_nomp.tensor_nomp_known_order:
% FFT residual detection -> local oversampled init -> safeguarded Newton ->
% cyclic re-refinement, joint-LS accept/reject (monotone residual energy).
  p = struct('local_iterations',5,'cyclic_passes',2,'cyclic_iterations',2, ...
             'max_step_bins',0.5,'det_points',5,'det_radius',0.5);
  for i = 1:2:numel(varargin), p.(varargin{i}) = varargin{i+1}; end
  shape = size(Y); if numel(shape)==2, shape(3)=1; end
  yvec = Y(:);
  bins = zeros(0,3); newton_updates = 0;
  [~, ~, rvec, ~] = ls_state(yvec, shape, bins);
  for t = 1:L
    Rres = reshape(rvec, shape);
    F = fftn(Rres)/sqrt(numel(Rres));
    [~, mx] = max(abs(F(:)));
    idx0 = mx - 1;
    ia = mod(idx0, shape(1)); r_ = floor(idx0/shape(1));
    it = mod(r_, shape(2)); iv = floor(r_/shape(2));
    coarse = [ia it iv];
    init = oversampled_init(rvec, shape, coarse, p.det_radius, p.det_points);
    bins(end+1,:) = init; %#ok<AGROW>
    [gains, ~, rvec, energy] = ls_state(yvec, shape, bins);
    for pass = 0:p.cyclic_passes
      if pass == 0, idxs = size(bins,1); iters = p.local_iterations;
      else, idxs = 1:size(bins,1); iters = p.cyclic_iterations; end
      for k = idxs
        A = design_matrix(shape, bins);
        partial = rvec + gains(k) * A(:,k);
        [prop, upd] = newton_refine(partial, shape, bins(k,:), iters, p.max_step_bins);
        if upd == 0, continue; end
        prev = bins(k,:); bins(k,:) = prop;
        [g2, ~, r2, e2] = ls_state(yvec, shape, bins);
        if e2 <= energy + 1e-12*max(energy,1)
          gains = g2; rvec = r2; energy = e2; newton_updates = newton_updates + upd;
        else
          bins(k,:) = prev;
        end
      end
    end
  end
  [gains, recon, ~, energy] = ls_state(yvec, shape, bins);
  R = struct('bins', bins, 'gains', gains, 'reconstruction', reshape(recon,shape), ...
             'residual_energy', energy, 'newton_updates', newton_updates);
end

function [gains, recon, rvec, energy] = ls_state(yvec, shape, bins)
  if isempty(bins)
    gains = []; recon = zeros(size(yvec)); rvec = yvec; energy = real(rvec'*rvec); return;
  end
  A = design_matrix(shape, bins);
  gains = A \ yvec;
  recon = A * gains;
  rvec = yvec - recon;
  energy = real(rvec'*rvec);
end

function best = oversampled_init(rvec, shape, coarse, radius, points)
  offs = linspace(-radius, radius, points);
  Rt = reshape(rvec, shape);
  best = mod(coarse, shape); bests = -inf;
  Tmat = reshape(Rt, shape(1), []);
  for pa = 1:points
    a = steering_axis(shape(1), coarse(1)+offs(pa));
    S1 = reshape(a' * Tmat, shape(2), shape(3));
    for pt = 1:points
      b = steering_axis(shape(2), coarse(2)+offs(pt));
      v = b' * S1;
      for pv = 1:points
        c = steering_axis(shape(3), coarse(3)+offs(pv));
        sc = abs(v * conj(c))^2;
        if sc > bests
          bests = sc;
          best = mod(coarse + [offs(pa) offs(pt) offs(pv)], shape);
        end
      end
    end
  end
end

function [bins, updates] = newton_refine(rvec, shape, bins, iterations, max_step)
  bins = mod(bins, shape);
  updates = 0;
  [score, ~, ~] = score_grad_hess(rvec, shape, bins);
  for it = 1:iterations
    [~, g, H] = score_grad_hess(rvec, shape, bins);
    if ~all(isfinite(g)) || ~all(isfinite(H(:))), break; end
    step = -pinv(H, 1e-10) * g(:);
    ma = max(abs(step));
    if ~isfinite(ma) || ma == 0, break; end
    if ma > max_step, step = step * (max_step/ma); end
    accepted = false;
    for bt = 0:5
      cand = mod(bins + (0.5^bt)*step', shape);
      [cs, ~, ~] = score_grad_hess(rvec, shape, cand);
      if cs > score + 1e-12*max(score,1)
        bins = cand; score = cs; updates = updates + 1; accepted = true; break;
      end
    end
    if ~accepted, break; end
  end
end

function [score, grad, hess] = score_grad_hess(rvec, shape, bins)
%Analytic |a(b)^H r|^2 derivatives via separable weighted contractions.
  Rt = reshape(rvec, shape);
  V = cell(3,3);                          % V{axis, level}: level1=v,2=w.*v,3=w.^2.*v
  for d = 1:3
    v = steering_axis(shape(d), bins(d));
    w = 2*pi*(0:shape(d)-1)'/shape(d);
    V{d,1} = v; V{d,2} = w.*v; V{d,3} = (w.^2).*v;
  end
  C = zeros(3,3,3);                       % contraction over level index per axis (1..3)
  Tmat = reshape(Rt, shape(1), []);
  for la = 1:3
    S1 = reshape(V{1,la}' * Tmat, shape(2), shape(3));
    for lt = 1:3
      v2 = V{2,lt}' * S1;
      for lv = 1:3
        C(la,lt,lv) = v2 * conj(V{3,lv});
      end
    end
  end
  c0 = C(1,1,1);
  first = zeros(3,1);
  first(1) = -1i*C(2,1,1); first(2) = -1i*C(1,2,1); first(3) = -1i*C(1,1,2);
  second = zeros(3,3);
  for d1 = 1:3
    for d2 = 1:3
      lev = [1 1 1];
      lev(d1) = lev(d1) + 1; lev(d2) = lev(d2) + 1;
      second(d1,d2) = -C(lev(1), lev(2), lev(3));
    end
  end
  score = abs(c0)^2;
  grad = 2*real(conj(c0) * first);
  hess = 2*real(conj(first)*first.' + conj(c0)*second);
end
