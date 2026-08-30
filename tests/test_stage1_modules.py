from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03_active_modules"))

from common.config import ExperimentConfig, GridConfig
from common.seed import seed_all
from baseline.crlb_5l import coefficient_crlb_proxy
from baseline.crlb_5l import five_param_fim_crlb
from baseline.tensor_fft_omp import generate_sparse_fft_sample, recover_topk_fft
from baseline.tensor_omp import evaluate_tensor_omp, run_tensor_omp
from baseline.subspace_tensor import (
    complex_parafac_als,
    cp_reconstruct,
    separable_forward_backward_esprit,
)
from data.impairments import apply_iq_imbalance, apply_phase_noise, mutual_coupling_matrix
from data.offgrid_tensor import (
    estimate_from_bins,
    estimate_from_bins_lstsq,
    estimate_single_target_multiresolution,
    generate_offgrid_tensor_sample,
    measurement_nmse_db,
    refine_bins_local,
    topk_grid_bins,
)
from data.set_a_generator import build_dictionary, generate_set_a_sample
from tompnet.hungarian_loss import permutation_invariant_mse
from tompnet.layer import TOMPNetSmokeConfig, run_minimal_tompnet_smoke
from tompnet.trainable import interpolate_bins, train_alpha_grid
from tompnet.torch_layer import TorchOffgridRefinementLayer
from tompnet.torch_layer import TorchAxiswiseOffgridRefinementLayer
from tompnet.torch_layer import normal_equation_nmse_loss
from tompnet.torch_layer import prepare_torch_sample
from tompnet.feature_controller import (
    FeatureConditionedRefinementController,
    apply_nyquist_alias_lock,
    estimator_features,
    match_truth_to_coarse,
)


def test_config_hash_is_stable() -> None:
    config = ExperimentConfig(seed=7, grid=GridConfig(4, 4, 4))
    assert config.stable_hash() == ExperimentConfig(seed=7, grid=GridConfig(4, 4, 4)).stable_hash()


def test_set_a_generation_is_reproducible() -> None:
    grid = GridConfig(angle_bins=4, delay_bins=4, doppler_bins=4)
    dictionary = build_dictionary(grid)
    first = generate_set_a_sample(
        rng=seed_all(123), grid=grid, n_targets=2, snr_db=30, dictionary=dictionary
    )
    second = generate_set_a_sample(
        rng=seed_all(123), grid=grid, n_targets=2, snr_db=30, dictionary=dictionary
    )
    np.testing.assert_allclose(first.measurement, second.measurement)
    np.testing.assert_allclose(first.truth.sparse_coefficients, second.truth.sparse_coefficients)


def test_tensor_omp_recovers_high_snr_support() -> None:
    grid = GridConfig(angle_bins=4, delay_bins=4, doppler_bins=4)
    dictionary = build_dictionary(grid)
    sample = generate_set_a_sample(
        rng=seed_all(456), grid=grid, n_targets=2, snr_db=50, dictionary=dictionary
    )
    result = run_tensor_omp(sample)
    metrics = evaluate_tensor_omp(sample, result)
    assert metrics.support_recall == 1.0
    assert metrics.nmse_db < -25.0


def test_crlb_proxy_is_finite_and_positive() -> None:
    grid = GridConfig(angle_bins=4, delay_bins=4, doppler_bins=4)
    sample = generate_set_a_sample(
        rng=seed_all(789),
        grid=grid,
        n_targets=2,
        snr_db=20,
        dictionary=build_dictionary(grid),
    )
    proxy = coefficient_crlb_proxy(sample)
    assert np.isfinite(proxy.coefficient_nmse_floor_db)
    assert proxy.coefficient_nmse_floor > 0.0


def test_impairments_preserve_shape_and_physical_coupling() -> None:
    rng = seed_all(42)
    signal = np.ones((4, 3), dtype=np.complex128)
    assert apply_phase_noise(signal, 2.0, rng).shape == signal.shape
    assert apply_iq_imbalance(signal, 1.02, 1.0).shape == signal.shape
    coupling = mutual_coupling_matrix(4, rho=0.2, phi0_degrees=5.0)
    assert coupling.shape == (4, 4)
    np.testing.assert_allclose(np.diag(coupling), np.ones(4))


def test_fft_tensor_omp_recovers_paper_scale_style_sample() -> None:
    rng = seed_all(314)
    sample = generate_sparse_fft_sample(rng=rng, shape=(16, 4, 8), n_targets=4, snr_db=40)
    result = recover_topk_fft(sample, n_targets=4)
    assert result.support_recall == 1.0
    assert result.nmse_db < -30.0


def test_offgrid_refinement_improves_measurement_nmse() -> None:
    rng = seed_all(2718)
    sample = generate_offgrid_tensor_sample(
        rng=rng, shape=(16, 4, 8), n_targets=1, snr_db=50, offset_radius=0.3
    )
    coarse_bins = topk_grid_bins(sample.measurement, 1)
    coarse = estimate_from_bins(
        sample.measurement,
        sample.shape,
        [(float(a), float(d), float(v)) for a, d, v in coarse_bins],
    )
    refined_bins = refine_bins_local(
        sample.measurement, sample.shape, coarse_bins, search_radius=0.4, search_points=5
    )
    refined = estimate_from_bins(sample.measurement, sample.shape, refined_bins)
    assert measurement_nmse_db(refined, sample.clean) < measurement_nmse_db(coarse, sample.clean)
    assert estimate_from_bins_lstsq(sample.measurement, sample.shape, refined_bins).shape == sample.shape


def test_5l_fim_matches_finite_difference() -> None:
    result = five_param_fim_crlb(
        shape=(16, 4, 8),
        params=np.array([3.2, 1.4, 2.7, 1.0, -0.2]),
        noise_variance=0.01,
    )
    assert result.relative_error < 1e-7
    assert np.all(np.diag(result.crlb) > 0.0)


def test_single_target_multiresolution_estimator_tracks_bins() -> None:
    rng = seed_all(1618)
    sample = generate_offgrid_tensor_sample(
        rng=rng, shape=(16, 4, 8), n_targets=1, snr_db=50, offset_radius=0.2
    )
    target = sample.targets[0]
    estimate = estimate_single_target_multiresolution(
        sample.measurement, sample.shape, search_points=5, radii=(0.5, 0.15)
    )
    truth = np.array(
        [
            target.angle_bin + target.angle_offset,
            target.delay_bin + target.delay_offset,
            target.doppler_bin + target.doppler_offset,
        ]
    )
    error = np.linalg.norm(np.array(estimate.bins) - truth)
    assert error < 0.35


def test_minimal_tompnet_smoke_improves_offgrid_grid_estimate() -> None:
    rng = seed_all(2024)
    sample = generate_offgrid_tensor_sample(
        rng=rng, shape=(16, 4, 8), n_targets=2, snr_db=40, offset_radius=0.3
    )
    grid = run_minimal_tompnet_smoke(sample, TOMPNetSmokeConfig(n_targets=2, enable_offgrid=False))
    refined = run_minimal_tompnet_smoke(sample, TOMPNetSmokeConfig(n_targets=2, enable_offgrid=True))
    assert refined.measurement_nmse_db < grid.measurement_nmse_db


def test_permutation_invariant_loss_is_order_stable() -> None:
    target = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    predicted = target[::-1]
    assert permutation_invariant_mse(predicted, target) == 0.0


def test_trainable_alpha_selects_refinement_on_clean_samples() -> None:
    rng = seed_all(2025)
    samples = [
        generate_offgrid_tensor_sample(
            rng=rng, shape=(16, 4, 8), n_targets=1, snr_db=50, offset_radius=0.25
        )
        for _ in range(2)
    ]
    result = train_alpha_grid(samples, n_targets=1, candidate_alphas=np.array([0.0, 0.5, 1.0]))
    assert result.alpha > 0.0


def test_interpolate_bins_midpoint() -> None:
    bins = interpolate_bins([(1, 2, 3)], [(3.0, 4.0, 5.0)], 0.5)
    assert bins == [(2.0, 3.0, 4.0)]


def test_torch_refinement_layer_alpha_is_bounded() -> None:
    layer = TorchOffgridRefinementLayer(initial_alpha=0.5)
    alpha = float(layer.alpha().detach().cpu().item())
    assert 0.0 < alpha < 1.2


def test_torch_axiswise_refinement_layer_alphas_are_bounded() -> None:
    layer = TorchAxiswiseOffgridRefinementLayer(initial_alpha=(0.3, 0.6, 0.9))
    alpha = layer.alpha().detach().cpu().numpy()
    assert alpha.shape == (3,)
    assert np.all(alpha > 0.0)
    assert np.all(alpha < 1.2)


def test_torch_fast_loss_matches_forward_estimate() -> None:
    import torch

    rng = seed_all(5150)
    sample = generate_offgrid_tensor_sample(
        rng=rng, shape=(16, 4, 8), n_targets=2, snr_db=40, offset_radius=0.25
    )
    prepared = prepare_torch_sample(sample, n_targets=2)
    layer = TorchOffgridRefinementLayer(initial_alpha=0.7)
    coarse = torch.as_tensor(prepared.coarse_bins, dtype=torch.float64)
    refined = torch.as_tensor(prepared.refined_bins, dtype=torch.float64)
    measurement = torch.as_tensor(prepared.measurement, dtype=torch.complex128)
    clean = torch.as_tensor(prepared.clean, dtype=torch.complex128)
    estimate = layer(coarse, refined, measurement, sample.shape)
    slow_loss = torch.sum(torch.abs(estimate - clean) ** 2) / torch.sum(torch.abs(clean) ** 2)
    fast_loss = normal_equation_nmse_loss(
        coarse,
        refined,
        measurement,
        clean,
        sample.shape,
        layer.alpha(),
    )
    assert abs(float((slow_loss - fast_loss).detach())) < 1e-8


def test_feature_controller_contract_is_finite_bounded_and_permutation_stable() -> None:
    import torch

    shape = (8, 4)
    coarse = np.asarray([[1.0, 0.0], [6.0, 3.0]])
    refined = np.asarray([[1.2, -0.2], [5.8, 3.2]])
    truth = np.asarray([[5.9, -0.9], [1.1, 0.1]])
    measurement = sum(
        np.exp(2j * np.pi * np.arange(shape[0])[:, None] * pair[0] / shape[0])
        * np.exp(2j * np.pi * np.arange(shape[1])[None, :] * pair[1] / shape[1])
        for pair in truth
    )
    features = estimator_features(
        measurement, coarse, refined, search_radius=0.45
    )
    assert features.shape == (10,)
    assert np.all(np.isfinite(features))
    matched = match_truth_to_coarse(coarse, truth, shape=shape)
    np.testing.assert_allclose(matched[0], np.asarray([1.1, 0.1]))
    controller = FeatureConditionedRefinementController(hidden_dim=8)
    output = controller(torch.as_tensor(features, dtype=torch.float64))
    assert output.shape == (2,)
    assert torch.all(output > 0.0)
    assert torch.all(output < 1.2)
    output.sum().backward()
    assert all(parameter.grad is not None for parameter in controller.parameters())


def test_nyquist_alias_lock_preserves_only_boundary_angle_bins() -> None:
    coarse = np.asarray([[1.0, 2.0], [3.0, 1.0]])
    predicted = np.asarray([[1.2, 2.3], [2.8, 1.3]])
    locked = apply_nyquist_alias_lock(
        coarse, predicted, angle_bin_count=4
    )
    np.testing.assert_allclose(locked, np.asarray([[1.2, 2.0], [2.8, 1.3]]))


def test_separable_esprit_recovers_single_tensor_frequency() -> None:
    shape = (12, 6, 8)
    bins = (2.3, 1.4, 5.2)
    tensor = (
        np.exp(2j * np.pi * np.arange(shape[0])[:, None, None] * bins[0] / shape[0])
        * np.exp(2j * np.pi * np.arange(shape[1])[None, :, None] * bins[1] / shape[1])
        * np.exp(2j * np.pi * np.arange(shape[2])[None, None, :] * bins[2] / shape[2])
    )
    result = separable_forward_backward_esprit(tensor, rank=1)
    for estimate, truth in zip(result.frequency_bins, bins):
        assert abs(float(estimate[0]) - truth) < 1e-6


def test_complex_parafac_als_reconstructs_rank_one_tensor() -> None:
    rng = np.random.default_rng(77)
    factors = tuple(
        rng.standard_normal((size, 1)) + 1j * rng.standard_normal((size, 1))
        for size in (7, 5, 6)
    )
    tensor = cp_reconstruct(np.ones(1), factors)
    weights, estimated = complex_parafac_als(
        tensor, rank=1, iterations=6, seed=88
    )
    relative_error = np.linalg.norm(cp_reconstruct(weights, estimated) - tensor) / np.linalg.norm(tensor)
    assert relative_error < 1e-8
