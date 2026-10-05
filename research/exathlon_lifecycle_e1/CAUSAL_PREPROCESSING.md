# Causal preprocessing contract

[Feature definitions](configs/features.json) derive from pinned Exathlon SPARK_BUNDLES[0]:3 delay gauges,10 backward-differenced driver/node metrics,6 backward-differenced active-executor means. This is explicitly a causal variant, not native feature-pipeline reproduction.

Source row order must be nondecreasing. Retain first duplicate timestamp, record duplicate/gap counts. Insert integer1s history grid; target-observed mask stays false at missing source times. Sentinel−1/nonfinite values are missing. Never backward fill/interpolate/normalize test traces. Forward fill at most5 seconds; unavailable initial/long-gap values remain NaN. Average active raw executor slots before causal fill so inactive slots do not become active. Derivatives use t minus t−1.

PCA targets need an observed timestamp and finite current19 features. LSTM requires32 finite past feature vectors plus observed finite current target. History fill is allowed; scoring a missing target is forbidden. No window crosses a trace boundary. All missing score support is explicit. Training mean/population std from fit rows; zero std becomes1, no test-informed clipping.

Artificial prefix-invariance tests include missing timestamps, sentinels and duplicates. They exercise transformations only before seal; no detector inference occurs before pushed seal. Native full-test scaling, backfill and future-enclosing-window AE readout are not used.
