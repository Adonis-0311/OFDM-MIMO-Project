function csv_append(fname, header, line)
  newfile = ~exist(fname, 'file');
  fid = fopen(fname, 'a');
  if newfile, fprintf(fid, '%s\n', header); end
  fprintf(fid, '%s\n', line);
  fclose(fid);
end
