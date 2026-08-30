function S = gen_offgrid_sample(seed, shape, L, snr_db, offset_radius)
%GEN_OFFGRID_SAMPLE Mirrors data/offgrid_tensor.generate_offgrid_tensor_sample.
% Deterministic given seed (portable RNG). Support: unique flat indices;
% gains CN(0,1); per-axis offsets U(-r,r); AWGN at requested SNR.
  n_atoms = prod(shape);
  % --- support (rejection for uniqueness; collisions negligible) ---
  u = pr_stream(seed*8+1, 4*L);
  cand = floor(u * n_atoms); support = unique_stable(cand, L);
  % --- gains ---
  g = pr_randn(seed*8+2, 2*L);
  gains = complex(g(1:L), g(L+1:2*L)) / sqrt(2);
  % --- offsets ---
  off = reshape(pr_stream(seed*8+3, 3*L), L, 3) * 2*offset_radius - offset_radius;
  % --- targets & clean ---
  bins0 = zeros(L,3); clean = zeros(shape);
  for l = 1:L
    f = support(l);                       % 0-based flat index, C-order
    ba = floor(f/(shape(2)*shape(3)));
    rem_ = f - ba*shape(2)*shape(3);
    bt = floor(rem_/shape(3)); bv = rem_ - bt*shape(3);
    bins0(l,:) = [ba bt bv];
    clean = clean + gains(l) * tensor_atom(shape, bins0(l,:) + off(l,:));
  end
  sig_pow = mean(abs(clean(:)).^2);
  nvar = sig_pow / 10^(snr_db/10);
  wn = pr_randn(seed*8+4, 2*n_atoms);
  noise = sqrt(nvar/2) * reshape(complex(wn(1:n_atoms), wn(n_atoms+1:end)), shape);
  S = struct('measurement', clean + noise, 'clean', clean, ...
             'grid_bins', bins0, 'offsets', off, 'gains', gains, ...
             'noise_variance', nvar, 'snr_db', snr_db, 'shape', shape);
end
function out = unique_stable(cand, L)
  out = []; i = 1;
  while numel(out) < L && i <= numel(cand)
    if ~any(out == cand(i)), out(end+1) = cand(i); end %#ok<AGROW>
    i = i + 1;
  end
  if numel(out) < L, error('support draw exhausted'); end
  out = out(:);
end
