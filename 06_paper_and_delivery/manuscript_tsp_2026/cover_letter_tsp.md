Dear Editor,

Please consider our manuscript, “Projection-Selected Multidimensional Candan Refinement after FFT Tensor Support Selection,” for publication in *IEEE Transactions on Signal Processing*.

The manuscript studies a practical estimation interface in which a multidimensional FFT supplies coarse tensor neighborhoods and a complex three-sample update estimates continuous coordinates. We apply Candan's finite-length correction along every active axis, refit the selected components jointly, and return the fitted subspace that captures more received energy. This projection principle gives a fixed-cost scene-level decision. The analysis proves exact isolated tensor-to-scalar triplet reduction, bounds multi-component Gaussian quotient error, and propagates coordinate error through joint least squares.

All methods use the same noisy tensors, support contract, and end-to-end timing protocol. On 1200 common three-dimensional scenes, Candan refinement provides 24.26 dB NMSE gain. The complete projection-selected implementation takes 11.24 ms, a 1.57% increment over Candan alone. It retains 14.45 dB gain over the complete fractional-bin interval and positive gain in all 48 controlled separation–near–far cells, with a 10.46 dB mean and 6.29 dB minimum.

On 9000 CDL tests, projection selection produces a paired aggregate increment of 0.141 dB with a 95% interval of [0.097, 0.186] dB. CDL-D rises from 0.284 to 0.712 dB, while aggregate delay RMSE falls from 428.45 to 413.52 ns and joint quarter-bin accuracy rises from 7.46% to 18.84%. The accompanying repository provides the generators, evaluation scripts, aggregate data, independent MATLAB implementation, and publication-figure sources.

An earlier version received an editorial prescreen decision from *IEEE Transactions on Aerospace and Electronic Systems* before external review. The separate disclosure included with this submission records that history. The present manuscript is organized around its signal-processing contribution and is not under consideration elsewhere.

Sincerely,

The Authors
