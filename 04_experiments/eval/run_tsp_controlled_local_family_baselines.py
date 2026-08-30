"""Official entry point for the common-contract local-family comparison."""

from run_tsp_cost_matched_local_baselines import calibrate_residual_threshold, main


__all__ = ["calibrate_residual_threshold", "main"]


if __name__ == "__main__":
    main()
