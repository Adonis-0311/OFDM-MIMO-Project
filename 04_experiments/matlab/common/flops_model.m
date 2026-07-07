function T = flops_model(shape, L, cfg)
%FLOPS_MODEL Analytic per-scene real-FLOP model for all matched-campaign methods.
% One complex mult = 6 real FLOPs, one complex add = 2. Atom evaluation over N
% samples = one complex exponential recurrence + scaling ~ C_ATOM_PER_SAMPLE
% real FLOPs/sample (documented in complexity_model.md).
  N = prod(shape);
  CM = 6; C_ATOM = 8;                         % per-sample atom synthesis cost
  fft_flops = 5 * N * log2(N);                % standard split-radix estimate
  ls = @(k) 8*N*k^2 + (8/3)*k^3;              % complex QR lstsq, k columns
  % --- grid Tensor-OMP (FFT top-k + one joint LS) ---
  grid = fft_flops + L*C_ATOM*N + ls(L);
  % --- deterministic local refinement (5^3 separable search per component) ---
  P = cfg.search_points;
  search_per_comp = P*C_ATOM*shape(1) + P*2*N ...          % angle-stage contractions
                  + P^2*(C_ATOM*shape(2) + 2*shape(2)*shape(3)) ...
                  + P^3*(C_ATOM*shape(3) + 2*shape(3));
  det = grid + L*search_per_comp + ls(L);
  % --- learned scalar: deterministic + 1 FLOP inference + interp + LS rebuild ---
  learned_scalar = det + 1 + 3*L*2 + L*C_ATOM*N + ls(L);
  % --- learned controller (10->16->2 MLP): + feature build + 384 MAC FLOPs ---
  controller = det + cfg.feature_flops + 2*(10*16 + 16*2) + 3*L*2 + L*C_ATOM*N + ls(L);
  % --- NOMP-inspired: detect (FFT+5^3 init) + Newton + cyclic, LS accept each ---
  R = cfg.nomp_newton_iters; B = cfg.nomp_backtrack_avg;
  ghe = 3*(C_ATOM*shape(1) + 2*N) + 9*(2*shape(2)*shape(3)) + 27*2*shape(3); % grad/hess eval
  newton_iter = ghe*(1+B) + 200;                    % + 3x3 pinv/step overhead
  per_target = fft_flops + P^3*(2*N) ...            % detection + oversampled init
             + R*newton_iter;
  ls_accepts = cfg.nomp_ls_evals_per_target;
  nomp = 0;
  for t = 1:L
    nomp = nomp + per_target + ls_accepts*ls(t) + t*C_ATOM*N;
  end
  % --- PARAFAC-ALS fixed sweeps ---
  S = cfg.als_sweeps;
  als_sweep = 0;
  for d = 1:3
    nd = shape(d); nother = N/nd;
    als_sweep = als_sweep + nother*L*CM ...           % khatri-rao
      + 8*nd*nother*L ...                             % unfolding product
      + 2*(3*L*L*8) + (8/3)*L^3 + 8*nd*L*L;           % gram, solve
  end
  als = S*als_sweep + 8*N*L;
  T = struct('grid',grid,'deterministic',det,'learned_scalar',learned_scalar, ...
             'controller',controller,'nomp',nomp,'parafac_als',als,'fft',fft_flops, ...
             'ls_L',ls(L),'search_per_component',search_per_comp);
end
