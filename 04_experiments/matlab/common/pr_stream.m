function u = pr_stream(seed, n)
%PR_STREAM Portable counter-based uniform RNG in (0,1). Bit-identical in
% MATLAB and Octave (exact double integer arithmetic, murmur3-style mixer).
%   u = pr_stream(seed, n) returns n uniforms for integer seed >= 0.
  k = (0:n-1)';
  z = mod(k + mulmod32(mod(seed,2^32), 2654435761), 2^32);
  z = mulmod32(bitxor(z, floor(z/2^16)), 2246822507);   % 0x85EBCA6B
  z = mulmod32(bitxor(z, floor(z/2^13)), 3266489909);   % 0xC2B2AE35
  z = bitxor(z, floor(z/2^16));
  u = (z + 0.5) / 2^32;
end
function r = mulmod32(a, b)
% exact (a.*b) mod 2^32 for 32-bit doubles via 16-bit limbs
  al = mod(a, 65536); ah = floor(a/65536);
  r = mod(al.*b + mod(ah.*b, 65536)*65536, 2^32);
end
