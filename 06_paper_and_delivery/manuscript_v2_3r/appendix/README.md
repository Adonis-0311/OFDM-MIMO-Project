# Appendix Plan

## Appendix A: Reproducibility Manifest

Use `../../05_results/v2_3r_paper_evidence_table/` as the top-level evidence map. Include script paths and result directories.

## Appendix B: G2 Seed and Cell Details

Source:

```text
../../05_results/stage2_torch_locked_scale_g2_seed_sweep/
```

## Appendix C: A4 Cross-L Boundary

Source:

```text
../../05_results/stage3_a4_cross_l_plateau_gate_seed_sweep/
```

This appendix must preserve the L=16 boundary result.

## Appendix D: Off-Grid Mismatch Lemma

Provide detailed proof under the support-correct or near-support-correct condition.

## Appendix E: Depth Trade-Off

Provide the corrected `J(K) = E[NMSE_K] + lambda_FLOPs K` interpretation. Do not include the old closed-form optimal-depth claim.

## Appendix F: A5 Stress Profiles

Source:

```text
../../05_results/stage3_a5_combined_impairment_presmoke/
```

Use this as downgrade/failure-mode evidence.

## Appendix G: DeepMIMO Access Audit

Source:

```text
../../05_results/deepmimo_set_e_access_audit/
```

State exactly what is missing before any future DeepMIMO performance run can be claimed.
