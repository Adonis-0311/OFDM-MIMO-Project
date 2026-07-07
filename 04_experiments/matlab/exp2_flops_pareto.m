function exp2_flops_pareto(budget_s)
%EXP2 Matched mini-campaign for the FLOP-based Pareto (T1.1/T1.2):
% methods {grid, deterministic, learned scalar, NOMP-inspired, PARAFAC-ALS},
% 3 seeds x SNR {0,10,20,30} x L {2,4,8} x 5 scenes. Writes pareto_rows.csv and,
% after completion, complexity_table.csv with measured-iteration FLOP plug-ins.
  if nargin < 1, budget_s = inf; end
  addpath(fullfile(fileparts(mfilename('fullpath')), 'common'));
  t0 = tic;
  shape = [128 16 32]; roff = 0.35; radius = 0.45; pts = 5;
  alpha_frozen = frozen_alpha();
  fcsv = fullfile(results_dir(), 'pareto_rows.csv');
  hdr = 'seed,snr_db,L,scene,method,nmse_db,wall_ms,newton_updates';
  for seed = 1:3
    for snr = [0 10 20 30]
      for L = [2 4 8]
        key = sprintf(',pareto_s%d_snr%d_L%d,', seed, snr, L);
        fdone = fullfile(results_dir(), 'pareto_done.csv');
        if csv_has_key(fdone, key), continue; end
        if toc(t0) > budget_s, fprintf('BUDGET\n'); return; end
        for sc = 1:5
          S = gen_offgrid_sample(3e7 + seed*1e6 + snr*1e4 + L*1e3 + sc, shape, L, snr, roff);
          tic; coarse = topk_grid_bins(S.measurement, L);
          eg = estimate_lstsq(S.measurement, shape, coarse); tg = toc*1000;
          row(fcsv, hdr, seed, snr, L, sc, 'grid', nmse_db(eg, S.clean), tg, 0);
          tic; refined = refine_bins_local(S.measurement, shape, coarse, radius, pts);
          ed = estimate_lstsq(S.measurement, shape, refined); td = toc*1000;
          row(fcsv, hdr, seed, snr, L, sc, 'deterministic', nmse_db(ed, S.clean), tg+td, 0);
          tic; el = estimate_lstsq(S.measurement, shape, interpolate_bins(coarse, refined, alpha_frozen)); tl = toc*1000;
          row(fcsv, hdr, seed, snr, L, sc, 'learned_scalar', nmse_db(el, S.clean), tg+td+tl, 0);
          tic; R = tensor_nomp_known_order(S.measurement, L); tn = toc*1000;
          row(fcsv, hdr, seed, snr, L, sc, 'nomp_inspired', nmse_db(R.reconstruction, S.clean), tn, R.newton_updates);
          tic; [ea, ~] = cp_als_complex(S.measurement, L, 10, 5e7 + seed*1e6 + snr*1e4 + L*1e3 + sc); ta = toc*1000;
          row(fcsv, hdr, seed, snr, L, sc, 'parafac_als', nmse_db(ea, S.clean), ta, 0);
        end
        csv_append(fdone, 'key', sprintf(',pareto_s%d_snr%d_L%d,', seed, snr, L));
        fprintf('done pareto s%d snr%d L%d\n', seed, snr, L);
      end
    end
  end
  write_complexity_table(shape, pts, fcsv);
  fprintf('EXP2 DONE\n');
end
function row(fcsv, hdr, seed, snr, L, sc, m, v, w, nu)
  csv_append(fcsv, hdr, sprintf('%d,%d,%d,%d,%s,%.6f,%.3f,%d', seed, snr, L, sc, m, v, w, nu));
end
function a = frozen_alpha()
% frozen source-trained scalar: mean alpha_hat from exp1 (falls back to 0.64)
  f = fullfile(results_dir(), 'learning_marginal_alpha.csv');
  a = 0.64;
  if exist(f, 'file')
    fid = fopen(f); C = textscan(fid, '%s%f%f%f%f', 'Delimiter', ',', 'HeaderLines', 1); fclose(fid);
    if ~isempty(C{4}), a = mean(C{4}); end
  end
end
function write_complexity_table(shape, pts, fcsv)
% analytic FLOPs with measured NOMP iteration counts plugged in
  fid = fopen(fcsv); C = textscan(fid, '%f%f%f%f%s%f%f%f', 'Delimiter', ',', 'HeaderLines', 1); fclose(fid);
  out = fullfile(results_dir(), 'complexity_table.csv');
  if exist(out,'file'), delete(out); end
  hdr = 'L,method,flops,mean_nmse_db,median_wall_ms';
  for L = [2 4 8]
    sel = @(m) strcmp(C{5}, m) & C{3} == L;
    nomp_sel = sel('nomp_inspired');
    mean_updates = mean(C{8}(nomp_sel));
    cfg = struct('search_points', pts, 'feature_flops', 500, ...
                 'nomp_newton_iters', max(mean_updates / L, 1), ...
                 'nomp_backtrack_avg', 1.5, 'nomp_ls_evals_per_target', max(mean_updates / L, 1), ...
                 'als_sweeps', 10);
    T = flops_model(shape, L, cfg);
    methods = {'grid', T.grid; 'deterministic', T.deterministic; ...
               'learned_scalar', T.learned_scalar; 'nomp_inspired', T.nomp; 'parafac_als', T.parafac_als};
    for i = 1:size(methods,1)
      s = sel(methods{i,1});
      csv_append(out, hdr, sprintf('%d,%s,%.4g,%.4f,%.3f', L, methods{i,1}, ...
        methods{i,2}, mean(C{6}(s)), median(C{7}(s))));
    end
  end
end
