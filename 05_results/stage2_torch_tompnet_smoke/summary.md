# Stage 2 PyTorch T-OMP-Net Smoke

- Config hash: `stage2-torch-tompnet-20260624`

## Metrics

- `tensor_shape`: `32x4x8`
- `snr_db`: 20
- `torch_version`: `2.8.0+cpu`
- `epochs`: `8`
- `n_train_per_l`: `2`
- `n_test_per_l`: `2`
- `mean_test_gain_vs_grid_db`: 8.09537
- `min_test_gain_vs_grid_db`: 7.56776
- `mean_train_improvement_db`: 2.17457

## Notes

- PyTorch CPU trainable smoke uses nn.Module + Adam to learn bounded off-grid alpha from train samples.
- Top-k support initialization is fixed from Tensor-OMP; differentiability covers off-grid atom positions and LS reconstruction.
- This is a bounded G2 smoke, not the final full T-OMP-Net training campaign.

## Artifacts

- `05_results\stage2_torch_tompnet_smoke\stage2_torch_tompnet_smoke.csv`
- `05_results\stage2_torch_tompnet_smoke\run_manifest.json`
