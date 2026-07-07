function exp1_learning_marginal(budget_s)
%EXP1 G2-protocol isolation of the learned contribution (T1.3):
% learned-alpha vs deterministic candidate (alpha=1) vs grid, + per-scene oracle alpha.
% Resumable; writes 05_results/matlab_taes_supplement/learning_marginal_rows.csv
  if nargin < 1, budget_s = inf; end
  addpath(fullfile(fileparts(mfilename('fullpath')), 'common'));
  t0 = tic;
  shape = [128 16 32]; snr = 20; roff = 0.35; radius = 0.45; pts = 5;
  alphas = linspace(0, 1.2, 25); oalphas = linspace(0, 1.2, 13);
  fcsv = fullfile(results_dir(), 'learning_marginal_rows.csv');
  facsv = fullfile(results_dir(), 'learning_marginal_alpha.csv');
  hdr = 'seed,L,scene,method,nmse_db,rmse_angle,rmse_delay,rmse_doppler,half_bin_rate,alpha_used';
  for seed = 1:5
    for L = [2 4 8]
      key = sprintf('cell_s%d_L%d', seed, L);
      if csv_has_key(facsv, key), continue; end
      if toc(t0) > budget_s, fprintf('BUDGET\n'); return; end
      % --- train alpha on 2 scenes ---
      tr = cell(1,2);
      for i = 1:2, tr{i} = gen_offgrid_sample(seed*1e6 + L*1e4 + i, shape, L, snr, roff); end
      [ahat, tn] = train_alpha_grid(tr, L, alphas, radius, pts);
      % --- 30 held-out test scenes ---
      for sc = 1:30
        S = gen_offgrid_sample(seed*1e6 + L*1e4 + 1000 + sc, shape, L, snr, roff);
        coarse = topk_grid_bins(S.measurement, L);
        refined = refine_bins_local(S.measurement, shape, coarse, radius, pts);
        tb = S.grid_bins + S.offsets;
        cases = {'grid', coarse, 0; 'deterministic', interpolate_bins(coarse, refined, 1.0), 1.0; ...
                 'learned', interpolate_bins(coarse, refined, ahat), ahat};
        % per-scene oracle alpha (diagnostic; uses clean reference)
        bestv = inf; besta = 0;
        for a = oalphas
          est = estimate_lstsq(S.measurement, shape, interpolate_bins(coarse, refined, a));
          v = nmse_db(est, S.clean);
          if v < bestv, bestv = v; besta = a; end
        end
        cases(4,:) = {'oracle_alpha', interpolate_bins(coarse, refined, besta), besta};
        for ci = 1:size(cases,1)
          est = estimate_lstsq(S.measurement, shape, cases{ci,2});
          [rax, hb] = matched_bin_rmse(cases{ci,2}, tb, shape);
          csv_append(fcsv, hdr, sprintf('%d,%d,%d,%s,%.6f,%.6f,%.6f,%.6f,%.4f,%.4f', ...
            seed, L, sc, cases{ci,1}, nmse_db(est, S.clean), rax(1), rax(2), rax(3), hb, cases{ci,3}));
        end
      end
      csv_append(facsv, 'key,seed,L,alpha_hat,train_nmse_db', ...
        sprintf('%s,%d,%d,%.6f,%.6f', key, seed, L, ahat, tn));
      fprintf('done %s alpha=%.3f\n', key, ahat);
    end
  end
  fprintf('EXP1 DONE\n');
end
