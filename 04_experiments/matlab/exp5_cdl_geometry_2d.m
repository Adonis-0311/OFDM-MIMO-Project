function exp5_cdl_geometry_2d(budget_s)
%EXP5 64x4 delay-angle geometry domain (mechanism side-evidence for Sec. VI-D):
% shows axis coupling -- shared scalar alpha vs axis-specific alphas vs oracle
% axis pair. Motivates the feature-conditioned controller without Sionna.
  if nargin < 1, budget_s = inf; end
  addpath(fullfile(fileparts(mfilename('fullpath')), 'common'));
  t0 = tic;
  shape = [64 4 1]; roff = 0.35; radius = [0.45 0.45 0]; pts = 5;
  agrid = 0:0.2:1.2;
  fcsv = fullfile(results_dir(), 'geometry2d_rows.csv');
  hdr = 'seed,snr_db,L,scene,method,nmse_db,rmse_delay,rmse_angle,alpha_delay,alpha_angle';
  for seed = 1:3
    for snr = [0 10 20 30]
      for L = [2 4]
        key = sprintf('geo_s%d_snr%d_L%d', seed, snr, L);
        fdone = fullfile(results_dir(), 'geometry2d_done.csv');
        if csv_has_key(fdone, key), continue; end
        if toc(t0) > budget_s, fprintf('BUDGET\n'); return; end
        for sc = 1:10
          S = gen_offgrid_sample(13e7 + seed*1e6 + snr*1e4 + L*1e3 + sc, shape, L, snr, roff);
          coarse = topk_grid_bins(S.measurement, L);
          refined = refine_bins_local(S.measurement, shape, coarse, radius, pts);
          tb = S.grid_bins + S.offsets;
          run_case(fcsv, hdr, S, shape, tb, seed, snr, L, sc, 'grid', coarse, [0 0]);
          run_case(fcsv, hdr, S, shape, tb, seed, snr, L, sc, 'deterministic', refined, [1 1]);
          run_case(fcsv, hdr, S, shape, tb, seed, snr, L, sc, 'shared_alpha', ...
            interpolate_bins(coarse, refined, 0.64), [0.64 0.64]);
          run_case(fcsv, hdr, S, shape, tb, seed, snr, L, sc, 'delay_only_alpha', ...
            interpolate_bins(coarse, refined, [0.64 0 0]), [0.64 0]); % axis1=delay? see note
          % oracle axis pair (diagnostic, clean reference)
          bestv = inf; bb = coarse; ba = [0 0];
          for ad = agrid
            for aa = agrid
              bins = interpolate_bins(coarse, refined, [ad aa 0]);
              v = nmse_db(estimate_lstsq(S.measurement, shape, bins), S.clean);
              if v < bestv, bestv = v; bb = bins; ba = [ad aa]; end
            end
          end
          run_case(fcsv, hdr, S, shape, tb, seed, snr, L, sc, 'oracle_axis_pair', bb, ba);
        end
        csv_append(fdone, 'key', key);
        fprintf('done %s\n', key);
      end
    end
  end
  fprintf('EXP5 DONE\n');
end
function run_case(fcsv, hdr, S, shape, tb, seed, snr, L, sc, name, bins, al)
  est = estimate_lstsq(S.measurement, shape, bins);
  [rax, ~] = matched_bin_rmse(bins, tb, shape);
  csv_append(fcsv, hdr, sprintf('%d,%d,%d,%d,%s,%.6f,%.6f,%.6f,%.2f,%.2f', ...
    seed, snr, L, sc, name, nmse_db(est, S.clean), rax(1), rax(2), al(1), al(2)));
end
