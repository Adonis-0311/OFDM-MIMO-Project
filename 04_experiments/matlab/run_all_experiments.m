%RUN_ALL_EXPERIMENTS one-click reproduction of the MATLAB supplement campaign.
% Runtime: roughly 15-30 min in MATLAB R2021b+/Octave 6.4. All experiments are
% resumable; partial CSVs in 05_results/matlab_taes_supplement are extended.
exp1_learning_marginal(inf);
exp2_flops_pareto(inf);
exp3_fixedpoint_sweep(inf);
exp4_crlb_check(inf);
exp5_cdl_geometry_2d(inf);
disp('ALL MATLAB EXPERIMENTS DONE');
