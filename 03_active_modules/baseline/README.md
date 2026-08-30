# Baseline Plan

Planned baselines for the v2.2 experiment matrix:

- LS / LMMSE channel estimation
- OMP / SOMP sparse recovery
- Tensor-OMP
- ANN / CS-DL prototype cleanup
- CRLB reference curves

## Paper-facing continuous comparator

`tensor_nomp.py` implements a known-order 3-D cyclic NOMP-inspired comparator:
FFT residual detection with local oversampling, safeguarded Newton refinement,
cyclic feedback over all active atoms, and joint least-squares amplitude updates.  It adapts
the NOMP mechanism to the dense three-dimensional tensor contract; it is not a
reproduction of the cited sparse-resource two-dimensional OFDM algorithm or
its CFAR termination rule.
