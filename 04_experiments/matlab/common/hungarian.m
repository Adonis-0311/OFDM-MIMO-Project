function a = hungarian(C)
%HUNGARIAN thin wrapper kept for API compatibility; exact for n<=8.
  a = min_cost_match(C);
end
