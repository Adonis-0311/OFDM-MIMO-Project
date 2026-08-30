# Frozen controller selection decision

- Candidate models: train seeds 20260620, 20260621, 20260622.
- Validation: CDL-A/C, disjoint seeds 20260623 and 20260624, 8 samples/profile/seed, SNR {0,10,20,30}, L {4,8,16}.
- Rule: among models with positive validation NMSE and delay-RMSE reductions, select the model with maximum validation physical broadside-angle RMSE reduction.
- Selected seed: 20260620.
- Validation metrics: NMSE gain 6.5818 dB; delay reduction 0.05208 bin; physical angle reduction 0.08986 deg.
- Frozen artifact: `selected_controller_checkpoint.pt`.
- The rule and checkpoint were fixed before evaluation seeds 20260626 onward.
- The Nyquist alias lock is part of both training and inference and preserves angle bins exactly at the ULA endfire ambiguity boundary.
