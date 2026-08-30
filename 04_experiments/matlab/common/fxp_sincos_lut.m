function [lut_cos, lut_sin] = fxp_sincos_lut(addr_bits, frac_bits, word_bits)
%FXP_SINCOS_LUT quantized full-turn sin/cos tables (mirrors RTL ROM contents).
  n = 2^addr_bits;
  ph = 2*pi*(0:n-1)'/n;
  lut_cos = fxp_quantize(cos(ph), frac_bits, word_bits);
  lut_sin = fxp_quantize(sin(ph), frac_bits, word_bits);
end
