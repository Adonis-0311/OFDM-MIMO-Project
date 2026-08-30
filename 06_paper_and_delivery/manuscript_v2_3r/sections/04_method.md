# 4. Proposed Method

The method is designed around one constraint: the estimator should improve off-grid recovery without discarding the sparse tensor structure that makes the problem interpretable. It therefore keeps Tensor-OMP as the algorithmic scaffold and learns only the local refinement behavior around selected atoms. This section describes the estimator as a sequence of design choices rather than as a collection of independent modules.

## 4.1 Tensor-OMP as the Scaffold

Let the received ISAC observation be represented on an angle-delay-Doppler tensor dictionary. Grid Tensor-OMP repeatedly selects the atom with the largest residual correlation, augments the active support, solves a least-squares coefficient update over the selected atoms, and updates the residual. This baseline has two useful properties for the present paper. First, every selected atom has a physical meaning: angle, delay, and Doppler can be read from the support. Second, the residual update exposes a layer-by-layer refinement process that can be unfolded into a trainable estimator.

The weakness of the grid estimator is equally important. When a true target lies between tensor grid points, a purely discrete support can select a nearby atom while still retaining a structured mismatch. This is the error mode targeted by T-OMP-Net. The goal is not to replace sparse recovery with an opaque predictor; it is to repair the local continuous error that remains after a plausible sparse support has been selected.

## 4.2 Unfolding the Sparse-Recovery Path

T-OMP-Net represents a finite-depth Tensor-OMP recovery path as an unfolded estimator. Each layer preserves the same three operations as the baseline: support-oriented residual inspection, coefficient reconstruction, and residual update. The trainable component appears in the refinement step around selected atoms. This keeps the layer interpretable: a layer changes the physical support estimate and then recomputes the measurement-domain reconstruction, rather than passing through an unconstrained latent state.

This structure also makes the empirical comparison clean. Grid Tensor-OMP and T-OMP-Net operate on the same tensor representation and are evaluated on matched held-out samples. The measured gain in Section 6 can therefore be attributed to bounded local refinement under the local synthetic/off-grid protocol, rather than to a change in dataset, evaluator, or problem definition.

## 4.3 Physically Bounded Off-Grid Refinement

The bounded refinement step adjusts selected angle, delay, and Doppler coordinates inside local neighborhoods around their coarse grid locations. The bound has two roles. It prevents the learned correction from drifting into an uninterpretable latent offset, and it makes the correction compatible with the off-grid mismatch argument in Section 5. If the coarse support is near the correct physical component, local refinement can reduce the discretization error. If the selected support is wrong, the bound prevents the method from pretending that local refinement alone can solve a global support failure.

For the standards-aligned delay--angle experiment, a lightweight controller predicts bounded delay and angle refinement scales from estimator-internal features, including support density, spectral energy concentration, grid residual energy, local displacement statistics, support collisions, and dictionary conditioning. These quantities are available at inference and do not use channel labels. A physics safety rule locks angle refinement when the coarse spatial bin lies at the ULA Nyquist boundary, where the broadside mapping has an endfire alias. This prevents an infinitesimal continuous update from destroying an otherwise valid $\pm90^\circ$ grid representation.

Operationally, each refinement layer searches or learns within a small neighborhood, reconstructs the tensor response from the refined atoms, and measures the residual improvement. The current G2 evidence supports this mechanism at tensor shape `128x16x32`, SNR=20 dB, and L={2,4,8}; it does not establish performance on external ray-traced or measured channels.

## 4.4 Permutation-Invariant Target Supervision

Multi-target scenes introduce a labeling issue that does not exist in single-target recovery. A predicted set of targets can be physically correct even if the target order differs from the reference order. The training loss therefore uses a Hungarian assignment between predicted and reference target sets before computing parameter errors. This makes the supervision invariant to target permutation and avoids penalizing equivalent target sets.

This loss is not claimed as a new matching algorithm. Its purpose here is to align the learning objective with the physical output of the sparse tensor estimator. The network is trained to improve channel/measurement reconstruction and target-parameter consistency without depending on arbitrary list ordering.

For CDL training, the assignment is recomputed from the current prediction before evaluating the parameter loss. The angle term is measured after the alias-aware broadside mapping rather than in raw FFT-bin distance. This makes the training objective identical to the physical delay/projected-angle evaluator used at test time.

## 4.5 Plateau Early Stopping for High-Load Samples

The unfolded estimator has a natural computational question: how many refinement layers are worth running for a given sample? The paper treats this as an operational trade-off rather than as a global optimal-depth theorem. A fixed K=8 path is used as the quality reference. The plateau gate tracks the incremental NMSE improvement from one refinement depth to the next and stops after a minimum depth when the improvement falls below a learned scalar threshold.

Depth is used as the FLOPs proxy because each layer applies the same local-search kernel. Under the current evidence, the positive early-stop statement is restricted to high-load cells at the core SNR setting: for L>=32 and SNR=20 dB, the gate reaches at least 25% mean depth saving while keeping the maximum mean gap to fixed K=8 at 0.4008 dB. The SNR sensitivity and threshold-frontier diagnostics do not support a broader SNR-axis statement. The method is therefore framed as a high-load plateau gate, not as a universal depth controller.

## 4.6 Algorithm Summary

The resulting estimator follows four steps:

1. Run Tensor-OMP-style support selection on the angle-delay-Doppler tensor.
2. Refine selected support atoms inside bounded physical neighborhoods and recompute the least-squares reconstruction.
3. Train the refinement path with measurement-domain reconstruction loss and permutation-invariant target supervision.
4. Optionally apply the plateau gate in the restricted high-load regime where the evidence supports the depth-quality trade-off.

This summary also defines the method boundary. The main estimator is T-OMP-Net with bounded off-grid refinement. The plateau gate is an efficiency add-on with restricted evidence. Robust hardware-impairment training and DeepMIMO validation are not part of the current supported method claim.
