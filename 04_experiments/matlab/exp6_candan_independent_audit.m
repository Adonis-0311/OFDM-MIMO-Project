function exp6_candan_independent_audit(max_rows)
%EXP6_CANDAN_INDEPENDENT_AUDIT Independent 1200-scene MATLAB replication.
  if nargin < 1, max_rows = inf; end
  root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
  addpath(fullfile(root,'04_experiments','matlab','common'));
  outdir = results_dir();
  row_path = fullfile(outdir,'candan_independent_rows.csv');
  summary_path = fullfile(outdir,'candan_independent_summary.csv');
  shape = [128 16 32]; l_values = [2 4 8]; snrs = [0 10 20 30];
  seeds = [20260630 20260701 20260702 20260703 20260704];
  samples_per_cell_seed = 20; offset_radius = 0.35;
  rows = table(); count = 0;
  for seed_index = 1:numel(seeds)
    for snr_index = 1:numel(snrs)
      for l_index = 1:numel(l_values)
        for sample_index = 1:samples_per_cell_seed
          if count >= max_rows, break; end
          seed = seeds(seed_index); snr_db = snrs(snr_index); L = l_values(l_index);
          scene_seed = seed + 100000*snr_index + 10000*l_index + sample_index;
          S = gen_offgrid_sample(scene_seed,shape,L,snr_db,offset_radius);
          coarse = topk_grid_bins(S.measurement,L);
          [grid_est,~] = estimate_lstsq(S.measurement,shape,coarse);
          [candan_bins,diag] = axiswise_candan_bins(S.measurement,coarse,0.5);
          [candan_est,~] = estimate_lstsq(S.measurement,shape,candan_bins);
          grid_nmse = nmse_db(grid_est,S.clean);
          candan_nmse = nmse_db(candan_est,S.clean);
          new_row = table(seed,snr_db,L,sample_index,grid_nmse,candan_nmse, ...
            grid_nmse-candan_nmse,diag.minimum_denominator_stability, ...
            diag.mean_denominator_stability,diag.clipping_rate, ...
            'VariableNames',{'seed','snr_db','n_targets','sample_index', ...
            'grid_nmse_db','candan_nmse_db','candan_gain_vs_grid_db', ...
            'minimum_denominator_stability','mean_denominator_stability','clipping_rate'});
          rows = [rows; new_row]; %#ok<AGROW>
          count = count + 1;
        end
        if count >= max_rows, break; end
      end
      if count >= max_rows, break; end
    end
    if count >= max_rows, break; end
  end
  writetable(rows,row_path);
  unique_seeds = unique(rows.seed);
  seed_gain = zeros(numel(unique_seeds),1);
  for i = 1:numel(unique_seeds)
    seed_gain(i) = mean(rows.candan_gain_vs_grid_db(rows.seed==unique_seeds(i)));
  end
  gain = mean(seed_gain);
  if numel(seed_gain) > 1
    half = 1.959963984540054 * std(seed_gain) / sqrt(numel(seed_gain));
  else
    half = 0;
  end
  summary = table(height(rows),mean(rows.grid_nmse_db),mean(rows.candan_nmse_db), ...
    gain,gain-half,gain+half,mean(rows.candan_gain_vs_grid_db<0), ...
    mean(rows.minimum_denominator_stability),mean(rows.clipping_rate), ...
    'VariableNames',{'scene_count','mean_grid_nmse_db','mean_candan_nmse_db', ...
    'mean_candan_gain_db','gain_ci95_low_db','gain_ci95_high_db', ...
    'harmful_update_rate','mean_minimum_denominator_stability','mean_clipping_rate'});
  writetable(summary,summary_path);
  disp(summary);
end
