# 1. Introduction

Millimeter-wave MIMO-OFDM systems offer the bandwidth and aperture needed for high-resolution sensing while simultaneously supporting communication links. In integrated sensing and communication (ISAC), the same received waveform can carry information about both propagation channels and physical targets. This shared geometry is attractive, but it also makes estimation harder: channel taps, target angles, delays, and Doppler shifts must be recovered from a high-dimensional observation while remaining interpretable enough for both communication and sensing tasks.

A useful abstraction is to view the problem as sparse recovery over an angle-delay-Doppler tensor. Dominant paths or targets occupy only a small number of tensor atoms, so Tensor-OMP provides a natural model-driven baseline. A purely grid-based estimator, however, loses accuracy when physical parameters fall between dictionary bins. This off-grid mismatch is especially important for a paper that wants the recovered support to remain physically meaningful rather than merely reduce a black-box loss.

This work studies a Tensor-OMP unfolding estimator with physically bounded off-grid refinement. The estimator keeps the coarse support-selection and least-squares reconstruction structure of Tensor-OMP, but adds trainable local refinement inside bounded angle-delay-Doppler neighborhoods. A permutation-invariant target loss is used so that multi-target supervision does not depend on an arbitrary ordering of targets. The intended contribution is therefore not a new tensor model by itself, nor a generic neural estimator, but a constrained model-driven path that preserves sparse-recovery structure while reducing local off-grid error.

The empirical story has three layers. Local synthetic/off-grid data isolate the refinement mechanism, yielding a mean 6.1726 dB gain over grid Tensor-OMP for L={2,4,8}. Scaled held-out CDL-A/C evaluation then improves channel NMSE by 6.2286 dB, physical-delay RMSE by 10.1241 ns, and projected-angle RMSE by 0.5277 degrees on average. Zero-shot CDL-D degrades channel and delay estimates, exposing the profile-shift boundary. Finally, a plateau gate supports a narrowed high-load efficiency statement at 20 dB, while its SNR sweep prevents a broader adaptive-depth claim.

The paper makes four scoped contributions:

1. It formulates joint channel and target parameter estimation as sparse recovery over an angle-delay-Doppler tensor for mmWave MIMO-OFDM ISAC.
2. It introduces a Tensor-OMP unfolding estimator with bounded off-grid refinement and permutation-invariant multi-target supervision.
3. It provides both controlled local evidence and scaled held-out CDL-A/C physical evaluation, together with a zero-shot CDL-D failure boundary.
4. It characterizes a restricted high-load early-stop regime and reports the SNR sensitivity that prevents a broader robustness claim.

The current manuscript line remains conservative. Trained DeepMIMO physical evaluation, instrumented-receiver validation, unrestricted adaptive-depth optimality, robust hardware-impairment training, and full multi-target CRLB tightness remain validation targets. The result is a claim-bounded model-driven estimator with standards-aligned evidence, not a profile-universal deployment claim.
