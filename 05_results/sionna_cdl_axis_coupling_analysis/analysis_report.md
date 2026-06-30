# Sionna CDL axis-coupling failure analysis

Generated: 2026-06-27

## Parent result and question

- Parent: `05_results/sionna_cdl_trained_refinement_dev/`
- Parent claim: the Stage-2 source-trained shared-alpha bounded-refinement layer transfers from synthetic data to Sionna CDL physical delay and projected-angle estimation.
- Question: is the mixed external result primarily caused by applying one shared alpha to both physical axes?
- Execution envelope: CPU-only, Python 3.12.10, Sionna 2.0.1, SciPy 1.18.0, Torch 2.12.1; each 288-sample slice runs in seconds.

## Slice results

| Slice | Changed | Fixed | NMSE gain vs grid | Delay RMSE reduction | Projected-angle RMSE reduction | Claim update |
|---|---|---|---:|---:|---:|---|
| Shared source alpha | None; accepted source alpha 0.64192 applied to delay and angle | A/C/D, seeds, samples, SNR, L, support, truth and Hungarian metric contract | +3.5443 dB | +5.2652 ns | **-5.6007 deg** | mixed; external physical transfer not supported |
| Delay-only diagnostic | angle alpha set to 0; delay alpha remains 0.64192 | All other parent conditions unchanged | +3.1871 dB | +4.8296 ns | +0.0599 deg | diagnostic support for axis-coupling failure |

## Failure localization

- Shared-alpha angle degradation is systematic rather than an isolated outlier: the mean is negative for CDL-A, CDL-C, and CDL-D and for every tested SNR.
- The strongest boundary is L=16, where all 24 aggregated cells have negative projected-angle reduction and the mean degradation is 11.71 deg.
- With angle refinement frozen, the mean angle degradation contracts from 5.60 deg to approximately zero while most NMSE and delay benefit remains.
- CDL-D is still a separate failure boundary: even the delay-only diagnostic averages -0.93 dB NMSE gain, -4.67 ns delay reduction, and -0.37 deg angle reduction for that profile.

## Comparability and evidence boundary

The two slices are apples-to-apples except for the explicitly ablated angle alpha. The diagnostic uses no CDL-truth optimization, but it is not a trained estimator and cannot be promoted as a method result. It identifies a structural coupling problem in the accepted scalar layer; it does not prove that an axis-specific learned layer will succeed.

## Campaign conclusion and next route

- Status: completed, negative/mixed result preserved.
- Manuscript role: comparator/negative evidence or internal steering; not main-text claim-carrying evidence.
- Claim update: do not scale or publish the shared-alpha E1 transfer as successful physical validation.
- Next route: return to `experiment` with an axis-specific layer trained only on source synthetic truth/objectives, then evaluate once on the unchanged CDL contract. If CDL-D remains negative, narrow the external claim to CDL-A/C or redesign beyond scalar refinement.

