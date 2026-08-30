function q = fxp_quantize(x, frac_bits, word_bits)
%FXP_QUANTIZE round-half-away-from-zero to Q(word-frac-1).frac, symmetric saturation.
  s = 2^frac_bits;
  q = sign(x) .* floor(abs(x)*s + 0.5);
  lim = 2^(word_bits-1) - 1;
  q = max(min(q, lim), -lim) / s;
end
