function tf = csv_has_key(fname, key)
  tf = false;
  if ~exist(fname, 'file'), return; end
  fid = fopen(fname, 'r');
  txt = fread(fid, inf, 'char=>char')'; fclose(fid);
  tf = ~isempty(strfind(txt, key)); %#ok<STREMP>
end
