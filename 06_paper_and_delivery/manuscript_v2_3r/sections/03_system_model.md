# 3. System Model and Problem Formulation

We consider a monostatic mmWave MIMO-OFDM ISAC receiver whose observation is organized over virtual-array, subcarrier, and slow-time dimensions. After waveform separation, the received samples form a third-order tensor. Each dominant path or target contributes a structured component parameterized by angle, delay, Doppler, and complex gain. This representation creates the common estimation surface used by the baseline Tensor-OMP estimator and the unfolded T-OMP-Net refinement path.

## 3.1 Observation Tensor

Let `Y` denote the received tensor over angle-aperture, frequency, and slow-time dimensions. Under the FDMA virtual-array construction used in the current evidence package, the measurement can be written conceptually as a sparse superposition

```text
Y = sum_{l=1}^{L} alpha_l a(theta_l) o b(tau_l) o c(nu_l) + W,
```

where `alpha_l` is the complex gain of the l-th component, `theta_l` is angle, `tau_l` is delay, `nu_l` is Doppler, `o` denotes an outer product, and `W` is measurement noise. The three factor vectors correspond to array steering, delay response, and Doppler response. The exact implementation uses the discretized tensor dictionary implied by the evaluation scripts, with tensor shape `128x16x32` for the paper-facing local experiments.

## 3.2 Sparse Tensor Recovery Objective

The discrete dictionary defines atoms indexed by angle-delay-Doppler bins. The sparse support `S` contains the active atoms, and the coefficient vector contains their complex gains. Grid Tensor-OMP estimates `S` by selecting atoms that explain the residual and then solving a least-squares coefficient update. T-OMP-Net keeps this recovery objective but refines selected atoms within bounded physical neighborhoods.

The problem can therefore be stated in two layers:

1. Recover a sparse support and coefficients that reconstruct the measurement tensor.
2. Refine the selected angle, delay, and Doppler coordinates so that off-grid physical parameters are represented more accurately than by the nearest grid bin alone.

This formulation matches the Method section: support selection supplies an interpretable sparse scaffold, while bounded off-grid refinement targets the continuous mismatch left by grid quantization.

## 3.3 Target Parameter Output

For sensing, the estimated support is mapped back to target parameters. Angle comes from the array-domain coordinate, delay maps to range, and Doppler maps to radial velocity under the standard OFDM sensing interpretation. In multi-target scenes, the output is a set of target tuples rather than an ordered list. This is why the training objective uses permutation-invariant matching: two outputs that represent the same physical target set are equivalent even if their order differs.

## 3.4 FDMA Scope and Waveform Boundary

The current derivation uses FDMA orthogonality because it gives a clean virtual-array tensor and a reproducible sparse-recovery pipeline. This choice is part of the evidence boundary. FDMA has a spectral-efficiency cost because transmitters occupy disjoint subcarrier groups, while DDM and TDM provide different trade-offs. The current paper does not compare orthogonal waveform families experimentally; it evaluates the proposed estimator under the FDMA-style tensor model.

## 3.5 Evaluation Regimes

The evidence uses two regimes. Local synthetic/off-grid experiments at tensor shape `128x16x32` isolate the G2 refinement and A4 early-stop mechanisms. Standards-aligned Sionna CDL experiments use a 64-by-4 frequency/ULA observation, CIR delay truth, and the identifiable projected broadside angle. The controller is trained and validated on disjoint CDL-A/C seeds, then frozen for held-out A/C evaluation; CDL-D is reserved for zero-shot profile-shift testing.

DeepMIMO O1/I3 files and scalar-transfer proxies are available, but they do not yet implement the trained physical delay/angle contract used for CDL. They therefore remain supporting readiness evidence rather than the main external result.
