# Stage 3 Synthetic Cross-Scene Generalization Evaluation Summary

## Outcome Summary

This run is a local synthetic cross-scene sanity check for the bounded off-grid alpha path. It trains alpha on one synthetic source scene and evaluates that same alpha on held-out synthetic target scenes with lower SNR, larger off-grid offsets, and higher target count.

It is not DeepMIMO evidence. DeepMIMO Set E remains externally blocked until O1/I3 scenario data and toolbox readiness are available.

## evaluation_summary

- `research_question`: Does a source-trained bounded off-grid alpha retain useful NMSE gain under local synthetic scene shifts?
- `claim_update`: local-synthetic-pass for local synthetic fallback evidence; no DeepMIMO claim.
- `baseline_relation`: Grid Tensor-OMP alpha=0 is the deployment baseline; source-trained alpha is compared against target-oracle alpha retuned on the target scene.
- `failure_mode`: No execution failure; limitation is synthetic distribution shift rather than external ray-traced DeepMIMO validation.
- `mechanism_note`: source-trained alpha keeps at least 3 dB gain over grid and stays within 1 dB of target-oracle across synthetic target scenes.
- `next_action`: Keep this as a fallback sanity row only; rerun the true DeepMIMO Set E channel NMSE plus angle/delay RMSE evaluation once external data/toolbox readiness changes.
- `evidence_level`: Stage-3 local synthetic fallback evidence only.

## Key Metrics

- Source-trained alpha: 0.8000
- Minimum target gain versus grid: 5.8504 dB
- Maximum target gap versus target-oracle: 0.4077 dB
- Wall-clock elapsed time: 28.31 s
