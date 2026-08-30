function exp4_crlb_check(budget_s)
%EXP4 Independent single-target CRLB tightness cross-check (MATLAB domain):
% multiresolution continuous estimator RMSE vs sqrt(CRLB) across SNR.
  if nargin < 1, budget_s = inf; end
  addpath(fullfile(fileparts(mfilename('fullpath')), 'common'));
  t0 = tic;
  shape = [128 16 32]; roff = 0.35; ntrials = 200;
  fcsv = fullfile(results_dir(), 'crlb_check.csv');
  hdr = 'snr_db,axis,rmse,sqrt_crlb_mean,ratio,n_trials';
  for snr = [10 15 20 25 30 35 40]
    if csv_has_key(fcsv, sprintf('%d,doppler', snr)), continue; end
    if toc(t0) > budget_s, fprintf('BUDGET\n'); return; end
    err = zeros(ntrials, 3); cr = zeros(ntrials, 3);
    for tr = 1:ntrials
      S = gen_offgrid_sample(11e7 + snr*1e4 + tr, shape, 1, snr, roff);
      [bins, ~] = estimate_single_target_multires(S.measurement, shape);
      tb = S.grid_bins + S.offsets;
      d = abs(bins - tb); d = min(d, shape - d);
      err(tr,:) = d;
      cr(tr,:) = crlb_single_target(shape, tb, S.gains(1), S.noise_variance);
    end
    names = {'angle','delay','doppler'};
    for d = 1:3
      rmse = sqrt(mean(err(:,d).^2));
      scr = mean(sqrt(cr(:,d)));
      csv_append(fcsv, hdr, sprintf('%d,%s,%.8g,%.8g,%.4f,%d', snr, names{d}, rmse, scr, rmse/scr, ntrials));
    end
    fprintf('done crlb snr %d\n', snr);
  end
  fprintf('EXP4 DONE\n');
end
