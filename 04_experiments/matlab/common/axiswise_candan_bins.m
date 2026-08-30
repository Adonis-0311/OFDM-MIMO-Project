function [bins, diag] = axiswise_candan_bins(Y, coarse_bins, maximum_offset)
%AXISWISE_CANDAN_BINS Independent Candan three-DFT-sample implementation.
% Bins are zero-based and periodic, matching the repository tensor atoms.
  if nargin < 3, maximum_offset = 0.5; end
  spectrum = fftn(Y) / sqrt(numel(Y));
  shape = size(Y);
  bins = double(coarse_bins);
  offsets = zeros(size(bins));
  raw_offsets = zeros(size(bins));
  stability = zeros(size(bins));
  for row = 1:size(bins,1)
    center0 = mod(round(coarse_bins(row,:)), shape);
    center_sub = num2cell(center0 + 1);
    center_value = spectrum(center_sub{:});
    for axis = 1:numel(shape)
      left0 = center0; right0 = center0;
      left0(axis) = mod(left0(axis)-1, shape(axis));
      right0(axis) = mod(right0(axis)+1, shape(axis));
      left_sub = num2cell(left0 + 1); right_sub = num2cell(right0 + 1);
      left_value = spectrum(left_sub{:}); right_value = spectrum(right_sub{:});
      denominator = 2*center_value - left_value - right_value;
      triplet_scale = abs(left_value) + 2*abs(center_value) + abs(right_value);
      stability(row,axis) = abs(denominator) / max(triplet_scale, realmin);
      numerical_scale = max([abs(left_value), abs(center_value), abs(right_value), 1]);
      if abs(denominator) <= 1e-14*numerical_scale
        raw = 0;
      else
        correction = tan(pi/shape(axis)) / (pi/shape(axis));
        raw = correction * real((left_value-right_value)/denominator);
      end
      offset = min(max(raw, -maximum_offset), maximum_offset);
      raw_offsets(row,axis) = raw; offsets(row,axis) = offset;
      bins(row,axis) = mod(coarse_bins(row,axis)+offset, shape(axis));
    end
  end
  diag = struct( ...
    'offsets', offsets, ...
    'raw_offsets', raw_offsets, ...
    'denominator_stability', stability, ...
    'minimum_denominator_stability', min(stability,[],'all'), ...
    'mean_denominator_stability', mean(stability,'all'), ...
    'maximum_absolute_unclipped_offset', max(abs(raw_offsets),[],'all'), ...
    'clipping_rate', mean(abs(raw_offsets) > maximum_offset+1e-12,'all'));
end
