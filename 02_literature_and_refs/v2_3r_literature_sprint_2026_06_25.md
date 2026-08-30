# v2.3R Literature Sprint

Generated: 2026-06-25

Purpose: close the most urgent Related Work citation gap for the v2.3R manuscript without expanding the paper beyond the current evidence boundary.

## Verified Core References

| Key | Use in paper | Verification status | Boundary for our manuscript |
|---|---|---|---|
| `zhang2024unified_tensor_isac` | Tensor ISAC channel/target parameter estimation; closest tensor-modeling neighbor | Verified from arXiv, IEEE DOI, and public code README | Cite as evidence that tensor formulations are established; do not claim tensor modeling itself is novel. |
| `nguyen2024jcas_deep_unfolding_hbf` | Deep unfolding for joint communications and sensing beamforming | Verified from Oulu repository / DOI metadata | Cite as deep-unfolding JCAS precedent; distinguish our sparse tensor recovery / off-grid estimation setting from hybrid beamforming design. |
| `yang2026radar_cenet` | Sensing-assisted deep-unfolded sparse channel estimation | Verified from DBLP / DOI-indexed metadata; issue/date metadata requires a camera-ready recheck | Cite as close learning-based channel-estimation work; distinguish our FDMA virtual-array tensor recovery and permutation-invariant target supervision. |
| `deka2025deep_unfolding_review` | Broad deep unfolding background in wireless systems | Verified from arXiv page, v4 dated 2026-01-14 | Use as survey/background support only; not a closest comparator. |
| `vaezi2025ai_empowered_isac_tutorial` | AI-enabled ISAC design context | Verified from arXiv page, v3 dated 2026-02-13 | Use for motivation/context; not evidence for our estimator. |
| `alkhateeb2019deepmimo` | DeepMIMO dataset origin and reproducibility context | Verified from arXiv and DeepMIMO GitHub citation | Cite when explaining the external-data target and current access blocker. |
| `deepmimo2026toolchain` | Current DeepMIMOv4 repository/toolchain status | Verified from DeepMIMO GitHub repository metadata | Use only for data/tooling context; no performance claim. |
| `yang2013ogsbi` | Foundational off-grid sparse Bayesian inference | Verified through DOI-indexed citation trail; older anchor | Use as a methodological ancestor for off-grid sparse recovery, not as 2024-2026 SOTA. |

## Expanded Reference Checkpoint

The bibliography was expanded from 8 to 26 entries on 2026-06-25. The added entries cover the core technical neighborhoods needed for a stronger manuscript spine:

| Category | Added keys | Paper role |
|---|---|---|
| Greedy sparse recovery and MMV | `mallat1993matching`, `pati1993omp`, `tropp2007omp`, `cotter2005mmv` | Explain why Tensor-OMP is a reasonable interpretable baseline while making clear that classical OMP/MMV does not solve the off-grid, trainable, multi-target objective by itself. |
| Tensor factorization and uniqueness | `sidiropoulos2000parallel`, `sidiropoulos2000unique`, `kolda2009tensor` | Support the separable tensor-modeling background and keep the novelty boundary away from generic tensor decomposition. |
| Sparse mmWave MIMO modeling | `alkhateeb2014channel`, `ayach2014spatially`, `heath2016overview`, `rangan2014mmwave` | Connect the channel/target sparsity assumption to established mmWave MIMO estimation and signal-processing literature. |
| ISAC waveform and dual-functional context | `sturm2011waveform`, `liu2022isac`, `gaudio2019ofdm_otfs` | Place the work in OFDM/OTFS radar-communication and modern ISAC context without claiming external waveform benchmarking. |
| Assignment, estimation theory, and robustness boundaries | `kuhn1955hungarian`, `munkres1957assignment`, `kay1993fundamentals`, `bjornson2014nonideal` | Anchor Hungarian matching, the CRLB sanity check, and the hardware-impairment limitation/future-work boundary. |

Verification note: DOI-indexed entries were checked through DOI/Crossref metadata. The Kay estimation-theory book was checked through public bibliographic metadata and is used only as a standard estimation-theory anchor. This checkpoint improves citation coverage, but it is still not a final camera-ready bibliography.

## Literature Positioning

The current Related Work is organized around four claims:

1. Tensor ISAC parameter estimation is already a strong prior line. The closest reference is `zhang2024unified_tensor_isac`, which formulates joint channel and target estimation through tensor decomposition. The paper positions T-OMP-Net as a trainable sparse-recovery path with bounded local off-grid refinement, not as the invention of tensor ISAC.
2. Deep unfolding is established in wireless and now appears inside JCAS design. `nguyen2024jcas_deep_unfolding_hbf` is a close deep-unfolding JCAS reference, but its object is hybrid beamforming rather than sparse angle-delay-Doppler estimation.
3. Sensing-assisted deep-unfolded channel estimation is close enough to require explicit distinction. `yang2026radar_cenet` uses radar-derived angle priors and a deep-unfolded channel-estimation network; our boundary is FDMA virtual-array tensor recovery, multi-target parameter loss, and local off-grid refinement.
4. DeepMIMO remains an external validation target, not achieved evidence. `alkhateeb2019deepmimo` and `deepmimo2026toolchain` should support the dataset context while the manuscript states that Set E is currently blocked in this workspace.

## Still Needed Before Submission

- Expand from this 26-entry core set toward a final venue-scale bibliography, likely 30-50 verified references once the target venue and exact scope are fixed.
- Recheck exact volume/issue/pages for `yang2026radar_cenet` when the final IEEE issue metadata settles.
- Recheck any final camera-ready spelling, accents, and publisher metadata after the target BibTeX style is selected.
- Add a closest-comparator table once the final venue is chosen. Recommended columns: problem, signal model, tensor structure, trainable unfolding, off-grid handling, target permutation handling, external validation, efficiency/depth adaptation.
- Do not cite any paper as evidence that our DeepMIMO evaluation is complete; current project evidence says the opposite.
