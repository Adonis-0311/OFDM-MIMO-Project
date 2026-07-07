function out = fxp_refine_kernel(Y, shape, coarse, refined, alpha, cfg)
%FXP_REFINE_KERNEL Fixed-point emulation of the FPGA refinement kernel:
% bounded interpolation -> phase-accumulated atom synthesis (sin/cos LUT) ->
% correlation MAC -> gain scaling -> residual update, sequential per component.
% cfg fields: W (data word bits), F (data frac bits), PHASE_BITS, LUT_ADDR_BITS,
% COORD_FRAC. Set cfg.float=true for the float reference of the SAME kernel.
  N = prod(shape); L = size(coarse,1);
  isfl = isfield(cfg,'float') && cfg.float;
  if ~isfl
    r = fxp_quantize(real(Y(:)), cfg.F, cfg.W) + 1i*fxp_quantize(imag(Y(:)), cfg.F, cfg.W);
  else
    r = Y(:);
  end
  recon = zeros(N,1);
  bins_out = zeros(L,3); gains = zeros(L,1);
  logN = round(log2(N));
  for l = 1:L
    % --- bounded interpolation (Q coords) ---
    delta = refined(l,:) - coarse(l,:);
    if ~isfl
      a_q = fxp_quantize(alpha, cfg.COORD_FRAC, 18);
      d_q = fxp_quantize(delta, cfg.COORD_FRAC, 18);
      b = coarse(l,:) + fxp_quantize(a_q.*d_q, cfg.COORD_FRAC, 18);
    else
      b = coarse(l,:) + alpha.*delta;
    end
    bins_out(l,:) = b;
    % --- atom synthesis (unit amplitude; 1/sqrt(N) folded into gain shift) ---
    a = atom_stream(shape, b, isfl, cfg);
    % --- correlation MAC: full-precision accumulate, then shift by log2(N) ---
    g = (a' * r) / 2^logN;                 % exact when N=2^k (mirrors barrel shift)
    if ~isfl
      g = fxp_quantize(real(g), cfg.F, cfg.W+4) + 1i*fxp_quantize(imag(g), cfg.F, cfg.W+4);
    end
    gains(l) = g;
    % --- residual update with rounding ---
    upd = g * a;
    if ~isfl
      upd = fxp_quantize(real(upd), cfg.F, cfg.W) + 1i*fxp_quantize(imag(upd), cfg.F, cfg.W);
      r = fxp_quantize(real(r - upd), cfg.F, cfg.W) + 1i*fxp_quantize(imag(r - upd), cfg.F, cfg.W);
    else
      r = r - upd;
    end
    recon = recon + upd;
  end
  out = struct('reconstruction', reshape(recon, shape), ...
               'residual', reshape(r, shape), 'bins', bins_out, 'gains', gains);
  % note: atoms are unit-amplitude; reconstruction is already in measurement scale
end
function a = atom_stream(shape, b, isfl, cfg)
% flattened MATLAB column-major stream: angle index fastest (axis 1)
  N = prod(shape);
  if isfl
    A = tensor_atom(shape, b) * sqrt(N);   % unit amplitude
    a = A(:);
    return;
  end
  [lc, lsn] = fxp_sincos_lut(cfg.LUT_ADDR_BITS, cfg.F, cfg.W);
  a = zeros(N,1);
  % per-axis quantized phase increments (turns, Q0.PHASE_BITS)
  incs = round(mod(b ./ shape, 1) * 2^cfg.PHASE_BITS);
  ax = cell(1,3);
  for d = 1:3
    ph = mod((0:shape(d)-1)' * incs(d), 2^cfg.PHASE_BITS);
    addr = floor(ph / 2^(cfg.PHASE_BITS - cfg.LUT_ADDR_BITS));
    ax{d} = lc(addr+1) + 1i*lsn(addr+1);
  end
  % complex products with post-multiply rounding (mirrors RTL truncation stage)
  qz = @(z) fxp_quantize(real(z), cfg.F, cfg.W) + 1i*fxp_quantize(imag(z), cfg.F, cfg.W);
  AB = qz(ax{1} * ax{2}.');                 % Na x Nt
  for k = 1:shape(3)
    blk = qz(AB * ax{3}(k));
    a((k-1)*shape(1)*shape(2)+(1:shape(1)*shape(2))) = blk(:);
  end
end
