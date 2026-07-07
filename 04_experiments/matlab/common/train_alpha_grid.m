function [alpha, train_nmse] = train_alpha_grid(samples, L, alphas, radius, points)
%TRAIN_ALPHA_GRID mirrors tompnet/trainable.train_alpha_grid (grid search on
% mean linear-domain-independent dB NMSE across training samples).
  cache = cell(numel(samples),1);
  for i = 1:numel(samples)
    S = samples{i};
    coarse = topk_grid_bins(S.measurement, L);
    refined = refine_bins_local(S.measurement, S.shape, coarse, radius, points);
    cache{i} = {S, coarse, refined};
  end
  best = inf; alpha = alphas(1);
  for a = alphas(:)'
    vals = zeros(numel(samples),1);
    for i = 1:numel(samples)
      [S, coarse, refined] = deal(cache{i}{:});
      bins = interpolate_bins(coarse, refined, a);
      est = estimate_lstsq(S.measurement, S.shape, bins);
      vals(i) = nmse_db(est, S.clean);
    end
    if mean(vals) < best, best = mean(vals); alpha = a; end
  end
  train_nmse = best;
end
