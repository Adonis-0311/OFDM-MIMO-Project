function d = results_dir()
  here = fileparts(mfilename('fullpath'));
  d = fullfile(here, '..', '..', '..', '05_results', 'matlab_taes_supplement');
  if ~exist(d, 'dir'), mkdir(d); end
end
