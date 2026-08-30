# Seventh-round Candan gate audit

## Protocol decision

- The A/C-calibrated primary rule uses no normalization and never accesses a
  CDL-D row.  It selects `tau=-0.0209598826`; on the five-seed test it changes
  aggregate gain from 5.1383 to 5.1435 dB (paired increment 0.0052 dB, 95% CI
  [-0.0038, 0.0142]) and zero-shot D from 0.2842 to 0.2862 dB (increment
  0.0020 dB, 95% CI [-0.0027, 0.0067]).  This calibrated rule does not support
  a strong profile-transfer claim.
- The theory-fixed `tau=0` rule needs no calibration.  It changes aggregate
  gain to 5.2798 dB (paired increment 0.1414 dB, 95% CI [0.0968, 0.1861]) and
  zero-shot D to 0.7125 dB (increment 0.4283 dB, 95% CI [0.3207, 0.5358]).
  D beneficial retention is 73.85% and harmful rejection is 74.87%.
- A/C/D-pooled calibration also selects `tau=0`; it is a same-profile
  secondary protocol and is numerically identical to the theory-fixed rule.

## Stability and extensions

- Leave-one-validation-seed-out thresholds range from -0.01678 to -0.00449;
  one of three held-out increments is negative.
- Leave-one-profile-out thresholds are -0.00770 (fit C) and -0.02645 (fit A).
- The A/C-calibrated min-zeta/clipping Stage-1 rule skips 0% of LS fits and is
  not supported for promotion.
- The leakage-free two-fold predictive gate has a maximum held-out algebraic
  identity error of 1.56e-13, but its aggregate paired increment is -0.0009 dB
  (95% CI [-0.0051, 0.0033]); it is an audit result, not a proposed method.

## Projection-energy implementation

- Across 60 identity scenes, explicit residual and projection-energy decisions
  agree to a maximum absolute error of 5.44e-15; QR and reconstruction-based
  projection energies agree in normalized decision value to 1.09e-14.
- Under the one-thread complex128 1200-scene protocol, median complete times
  are 11.07 ms (ungated Candan), 18.98 ms (legacy explicit residual gate), and
  11.24 ms (projection-energy gate).  Projection gating removes 40.75% of the
  legacy gated time and costs 1.57% over ungated Candan in this campaign.

The CSV/JSON ledgers and run manifests in this directory and the sibling
`tsp_projection_gate_runtime_seventh_round` and
`tsp_crossfit_predictive_gate_seventh_round` directories are authoritative.
