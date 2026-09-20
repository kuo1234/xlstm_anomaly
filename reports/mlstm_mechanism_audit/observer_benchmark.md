# Observer extraction benchmark

The benchmark uses the trained seed-11 checkpoint, CUDA SM121 overlay,
float32, W=64, and B=128.  It includes warmup and synchronized wall timing;
the result is in `observer_benchmark.json`.

Measured decisions/sec on the DGX Spark fixture:

* score-only: approximately 18.5k;
* sLSTM FastObserver: approximately 14.0k;
* mLSTM observer: approximately 3.9k;
* combined sLSTM+mLSTM observer: approximately 3.7k.

At B=256, a supplemental five-step timing gave approximately 36.5k
score-only and 7.45k combined-observer decisions/sec.  This is a throughput
measurement, not a change to the fixed scientific W=64 protocol.

The mLSTM observer is therefore the new bottleneck, but it remains bounded and
usable for the fixed seed-11 funnel.  The cost is expected: the pinned
implementation exposes no C/n/m history, so the observer must run the
64-step read-only replay and matrix reductions.  No multiprocessing or stateful
cross-window shortcut was introduced.
