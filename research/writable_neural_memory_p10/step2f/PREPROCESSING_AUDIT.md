# Step2f preprocessing audit

Primary scaler/M0/manifold use first80% FIT_NORMAL only (SP319/fault320 points). Last80points CAL only q.99 threshold; TEST1601 never fits/writes. Historical full-train scaler is Step2e regression-only, explicitly reproducing its old scaler/calibration overlap. No clip/scale selection by labels.

Frozen clip±20/no-clip comparison. Fixed-prediction value-no-clip isolates value saturation; full no-clip also changes keys/predictions. Whole-state CV includes transients, unlike checkpoint CV.

Primary W1/seed11 state results:

| case | seed | op | view | state | n_points | cell_clip_fraction | any_channel_clip_fraction | mean_score | fixed_prediction_no_clip_score_mean | fixed_prediction_no_clip_score_CV | state_pooled_score_CV | near_constant_channels | near_constant_energy_share | manipulated_energy_share | top5_channels | top5_energy_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| case01 | 11 | W1 | fit_only_clip | NORMAL_A | 200 | 0.000000 | 0.000000 | 7.725031 | 7.725031 | 0.127278 | 0.127278 | 11 | 0.059734 | 0.192853 | 19,17,39,42,29 | 0.182144 |
| case01 | 11 | W1 | fit_only_clip | NORMAL_B | 601 | 0.174395 | 1.000000 | 71.898894 | 200.250644 | 0.010097 | 0.010889 | 11 | 0.158304 | 0.460530 | 41,50,20,44,47 | 0.392513 |
| case01 | 11 | W1 | fit_only_clip | TRANSITION | 800 | 0.154858 | 0.952500 | 66.019209 | 174.041858 | 0.322943 | 0.209930 | 11 | 0.169272 | 0.478551 | 41,20,44,48,47 | 0.406214 |
| case02 | 11 | W1 | fit_only_clip | NORMAL_A | 200 | 0.000000 | 0.000000 | 7.725031 | 7.725031 | 0.127278 | 0.127278 | 11 | 0.059734 | 0.192853 | 19,17,39,42,29 | 0.182144 |
| case02 | 11 | W1 | fit_only_clip | NORMAL_B | 601 | 0.173955 | 1.000000 | 71.186330 | 197.533158 | 0.006548 | 0.009601 | 11 | 0.167438 | 0.468092 | 48,20,42,41,50 | 0.397352 |
| case02 | 11 | W1 | fit_only_clip | TRANSITION | 800 | 0.155613 | 0.955000 | 65.668283 | 171.449015 | 0.311855 | 0.203521 | 11 | 0.177118 | 0.483193 | 48,20,41,42,44 | 0.411499 |
| case03 | 11 | W1 | fit_only_clip | NORMAL_A | 200 | 0.000000 | 0.000000 | 7.725031 | 7.725031 | 0.127278 | 0.127278 | 11 | 0.059734 | 0.192853 | 19,17,39,42,29 | 0.182144 |
| case03 | 11 | W1 | fit_only_clip | NORMAL_B | 601 | 0.000000 | 0.000000 | 7.942988 | 7.942988 | 0.124319 | 0.124319 | 11 | 0.053906 | 0.163997 | 14,17,19,23,24 | 0.249828 |
| case03 | 11 | W1 | fit_only_clip | TRANSITION | 800 | 0.000000 | 0.000000 | 8.051515 | 8.051515 | 0.123162 | 0.123162 | 11 | 0.057768 | 0.184425 | 14,19,17,23,41 | 0.241919 |
| case04 | 11 | W1 | fit_only_clip | FAULT | 1401 | 0.068482 | 0.992148 | 44.026625 | 125.961314 | 0.174908 | 0.271073 | 11 | 0.220117 | 0.438023 | 44,0,43,17,3 | 0.707415 |
| case04 | 11 | W1 | fit_only_clip | NORMAL_A | 200 | 0.000000 | 0.000000 | 7.143558 | 7.143558 | 0.105063 | 0.105063 | 11 | 0.072348 | 0.201713 | 14,18,34,4,50 | 0.151015 |
| case05 | 11 | W1 | fit_only_clip | FAULT | 1401 | 0.035096 | 0.932191 | 43.997327 | 75.889776 | 0.215653 | 0.124617 | 10 | 0.063501 | 0.306982 | 27,33,46,29,47 | 0.658022 |
| case05 | 11 | W1 | fit_only_clip | NORMAL_A | 200 | 0.000000 | 0.000000 | 6.933927 | 6.933927 | 0.117954 | 0.117954 | 10 | 0.051358 | 0.181883 | 40,39,41,42,13 | 0.161169 |

Full no-clip matched late-window medians:

| view | seed | op | case | state | log_score | cv | maha_mean | maha_centroid | cov_distance | corr_distance | manip_energy | near_constant_energy | top5_energy | direction_cosine |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fit_only_no_clip | 11 | W1 | case01 | NORMAL_B | 5.293925 | 0.009864 | 345.427381 | 345.272703 | 1.976132 | 0.133667 | 0.732318 | 0.439588 | 0.843406 | -0.174371 |
| fit_only_no_clip | 11 | W1 | case02 | NORMAL_B | 5.290369 | 0.006050 | 342.742129 | 342.591224 | 1.128582 | 0.106895 | 0.735960 | 0.445689 | 0.843530 | 0.161355 |
| fit_only_no_clip | 11 | W1 | case03 | NORMAL_B | 2.056817 | 0.115523 | 11.215486 | 4.096179 | 1.218325 | 0.105843 | 0.166135 | 0.055187 | 0.250223 | -0.108930 |
| fit_only_no_clip | 11 | W1 | case04 | FAULT | 4.813018 | 0.011990 | 212.571433 | 212.300965 | 1.648842 | 0.106308 | 0.933122 | 0.042440 | 0.994478 | 0.288811 |
| fit_only_no_clip | 11 | W1 | case05 | FAULT | 4.445162 | 0.010754 | 156.413472 | 156.067791 | 1.267400 | 0.102132 | 0.088857 | 0.018444 | 0.893459 | -0.083946 |

SP1± NORMAL_B clips17.44%/17.40% cells and every point; fault IDV1/2 full states clip6.85%/3.51%, SP2 NORMAL_B none. Magnitudes/ranks/energy concentrations change. Raw FIT sd<.02 identifies11 near-constant channels in01–04 and10 in05; all retained, scale floor fixed. Channel-specific clipping, signed residual means/sd/direction/energy groups: results/channel_residual_summary.csv.gz. State covariance matrices: results/state_covariances.npz.

Both faults still pass existing CV<=.10 at54/54 matched late windows with clip AND no-clip:2runs×3ages×3seeds×3operators, NOT54independent samples. Benign54/81 pass both (SP1± pass; SP2 fails). Primary fault median CV clip .013104/.015741 versus no-clip .011990/.010754. Whole-fault CV .271/.125 hides late stationarity.

Clipping materially distorts magnitudes but does not principally explain stable-fault aliasing; PREPROCESSING_CONFOUND_FOUND as its main explanation is NOT supported. No selected replacement preprocessing, tuning or Step2e policy rerun.
