function v = nmse_db(est, clean)
  den = max(norm(clean(:))^2, 1e-300);
  v = 10*log10(max(norm(est(:)-clean(:))^2 / den, 1e-300));
end
