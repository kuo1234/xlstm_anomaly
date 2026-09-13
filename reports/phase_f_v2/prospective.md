# Phase F-v2 implementation-validity amendment

This amendment is prospective and must be committed/pushed before any
scientific optimizer step. It is caused solely by the pre-outcome manual/native
LSTM reference-validity failure in F-v1: frozen cuDNN TF32-on gave sequence/final
state errors above the fixed `atol=1e-5, rtol=1e-4`, while cuDNN TF32-off and CPU
passed. No detector, anomaly, or probe result motivated this change.

The only scientific execution-state change is:

```text
torch.backends.cudnn.allow_tf32 = False
```

for both improved official xLSTMAD and matched H38 LSTM. The unchanged flags are
cuDNN deterministic=true, benchmark=false, deterministic-algorithms=false,
float32 matmul precision=highest, CUDA matmul TF32=false, vanilla float32
xLSTM, torch threads=4. The immutable executable fingerprint is
`bae2b520ad1927ee2a89c85f342188b48e29d01b3289d58cbca7a7f6e91d517f`.

Everything else is inherited unchanged from the F-v1 prospective freeze:
improved official xLSTMAD `e8b56ba27352733bb83729e85b1d6196dca70c99`, D8/W64/
embedding40 (73,504 parameters), standard six-layer encoder/decoder LSTM H38
(71,790), train sources1000–1009, validation sources2000–2004, prefix0:4096,
sealed per-source scalers, sealed epoch orders, batch128, Adam 0.001, 50 complete
epochs, aligned B,W,D reconstruction MSE, earliest exact validation tie, and
detector seeds11/22/33/44/55. Test sources3000–3009 remain forbidden. No
preprocessing, order, scaler, architecture, tolerance, or decision rule is
regenerated or relaxed.

The existing `reports/phase_f` and `data/phase_f` seals are input evidence only
and are not overwritten. Versioned F-v2 gates write under this directory and
verify every prefix/scaler/order hash before use. The old F-v1 gate output is
not reused as a model result.

Before training, `scripts/phase_f_v2_gates.py` must pass all finite forward/
backward, recurrent-gradient, no-native-predict, no-mutation and random-
unlabeled parity checks for both architectures. It additionally compares the
sealed E2 seed11 fixture under old TF32-on versus new TF32-off for output,
reconstruction score, common18 features, scalar hidden/final traces, B3/B1
partition and prefix causality. Every comparison uses the existing
`1e-5/1e-4` tolerance; no tolerance relaxation is allowed.

Only if all gates pass may `phase_f_v2_launch.py` run the fixed ten-process
training grid. Each run is a fresh process/state with the same sealed sample
orders and no labels. A post-training parity failure stops interpretation as an
implementation-valid checkpoint; it cannot be repaired by tuning or test
performance inspection. Phase G remains locked until all ten valid checkpoints,
curves, hashes and parity reports are externally reviewed.

H1 controlled harm remains STOP, H1 natural harm NOT_RUN, and H1 overall
UNRESOLVED. No H2/H3 labels or metrics, probes, H3b, H4, natural-H1 harm,
rollback or learned commit mechanism is authorized in this amendment.
