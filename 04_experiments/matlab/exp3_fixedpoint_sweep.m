function exp3_fixedpoint_sweep(budget_s)
%EXP3 Fixed-point word-length study of the refinement kernel (T3.1):
% local 3-D case (128x16x32, L=4, 20 dB) and CDL-geometry 2-D case (64x4, L=4).
% Emulates: bounded interpolation -> LUT atom synthesis -> correlation MAC ->
% gain shift -> residual update. Writes fixedpoint_sweep.csv + RTL test vectors.
  if nargin < 1, budget_s = inf; end
  addpath(fullfile(fileparts(mfilename('fullpath')), 'common'));
  t0 = tic;
  Ws = [6 8 10 12 14 16 18];
  fcsv = fullfile(results_dir(), 'fixedpoint_sweep.csv');
  hdr = 'domain,scene,W,F,nmse_fxp_db,nmse_float_kernel_db,nmse_ls_db,delta_vs_float_db';
  doms = {'local3d', [128 16 32], 0.45*[1 1 1]; 'cdl2d', [64 4 1], [0.45 0.45 0]};
  for di = 1:2
    [dom, shape, radius] = deal(doms{di,:});
    for sc = 1:20
      key = sprintf('%s,%d,18,', dom, sc);
      if csv_has_key(fcsv, key), continue; end
      if toc(t0) > budget_s, fprintf('BUDGET\n'); return; end
      S = gen_offgrid_sample(7e7 + di*1e6 + sc, shape, 4, 20, 0.35);
      coarse = topk_grid_bins(S.measurement, 4);
      refined = refine_bins_local(S.measurement, shape, coarse, radius, 5);
      outF = fxp_refine_kernel(S.measurement, shape, coarse, refined, 1.0, struct('float', true));
      nF = nmse_db(outF.reconstruction, S.clean);
      eL = estimate_lstsq(S.measurement, shape, refined);
      nL = nmse_db(eL, S.clean);
      for W = Ws
        cfg = struct('W', W, 'F', W-2, 'PHASE_BITS', 16, 'LUT_ADDR_BITS', 10, 'COORD_FRAC', 14);
        out = fxp_refine_kernel(S.measurement, shape, coarse, refined, 1.0, cfg);
        nQ = nmse_db(out.reconstruction, S.clean);
        csv_append(fcsv, hdr, sprintf('%s,%d,%d,%d,%.6f,%.6f,%.6f,%.6f', ...
          dom, sc, W, W-2, nQ, nF, nL, nQ - nF));
      end
      fprintf('done fxp %s scene %d\n', dom, sc);
    end
  end
  dump_rtl_vectors();
  fprintf('EXP3 DONE\n');
end
function dump_rtl_vectors()
% golden vectors for the Vivado/iverilog testbench: 2-D case, W=12/F=10, 3 scenes
  here = fileparts(mfilename('fullpath'));
  vdir = fullfile(here, '..', '..', '07_ops', 'fpga', 'vivado_xc7k325t', 'tb', 'vectors');
  if ~exist(vdir, 'dir'), mkdir(vdir); end
  shape = [64 4 1]; W = 12; F = 10;
  cfg = struct('W', W, 'F', F, 'PHASE_BITS', 16, 'LUT_ADDR_BITS', 10, 'COORD_FRAC', 14);
  for sc = 1:3
    S = gen_offgrid_sample(9e7 + sc, shape, 4, 20, 0.35);
    coarse = topk_grid_bins(S.measurement, 4);
    refined = refine_bins_local(S.measurement, shape, coarse, [0.45 0.45 0], 5);
    out = fxp_refine_kernel(S.measurement, shape, coarse, refined, 1.0, cfg);
    q = @(x, f, w) max(min(sign(x).*floor(abs(x)*2^f + 0.5), 2^(w-1)-1), -(2^(w-1)-1));
    fid = fopen(fullfile(vdir, sprintf('tv_scene%d.txt', sc)), 'w');
    fprintf(fid, '%% N Ncomp W F PHASE_BITS LUT_ADDR\n%d 4 %d %d 16 10\n', prod(shape), W, F);
    fprintf(fid, '%% coarse(3) refined(3) per component (Q7.14 coords as 22-bit ints)\n');
    for l = 1:4
      fprintf(fid, '%d %d %d %d %d %d\n', q(coarse(l,:), 14, 22), q(refined(l,:), 14, 22));
    end
    fprintf(fid, '%% alpha Q2.14\n%d\n', q(1.0, 14, 18));
    fprintf(fid, '%% input residual I Q (W-bit ints), N lines\n');
    ri = q(real(S.measurement(:)), F, W); rq = q(imag(S.measurement(:)), F, W);
    fprintf(fid, '%d %d\n', [ri rq]');
    fprintf(fid, '%% expected gains I Q per component (W+4-bit ints, F frac)\n');
    gi = q(real(out.gains), F, W+4); gq = q(imag(out.gains), F, W+4);
    fprintf(fid, '%d %d\n', [gi gq]');
    fprintf(fid, '%% expected final residual I Q (W-bit ints), N lines\n');
    fi = q(real(out.residual(:)), F, W); fq = q(imag(out.residual(:)), F, W);
    fprintf(fid, '%d %d\n', [fi fq]');
    fclose(fid);
  end
end
