# Phase F prospective matched training

This finite config is committed and pushed before any scientific Phase F
training. Authority: external acceptance of E2 `4d49f1d` and the user's Phase F
instructions. [Predict clarification](e2_predict_reporting_amendment.md) is
reporting-only; all sealed E2 evidence stays immutable.

The executable settings are [configs/phase_f.json](../../configs/phase_f.json).
Improved official xLSTMAD: pin e8b56ba27352733bb83729e85b1d6196dca70c99,
xlstm 2.0.5, lightning 2.6.1, vanilla float32, D8/W64/embedding40, 73,504
parameters. No architecture/backend changes. It is not original v1 reproduction.

Matched LSTM: Linear(8,38), three encoder then three decoder one-layer standard
LSTMs(38,38), GELU, Linear(38,8). Each layer receives the full preceding
sequence; all h/c states start at zero for each independent window. No dropout,
bidirectionality, residual connection, state carry, or learned pooling. The
mechanical formula 48H²+65H+8 selects H38 (71,790; −2.3318%); H39 has 75,551
and is farther from 73,504. Width is never selected from outcomes.

Only one stationary/none realization per source: train 1000–1009 and validation
2000–2004. Only observations 0:4096 are retained. Test sources 3000–3009 are
rejected at the data API. Generator-internal truth is never read or passed to
training/selection. Fit each source's own mean/std solely on its own fit prefix
(including validation's own prefix, as explicitly authorized); no pooled/test
normalizer. Save raw-prefix, transformed-prefix and scaler hashes. Each source
has 4,033 unique chronological W64 windows: train 40,330 and validation 20,165.
No cross-source windows or duplicate scenario prefixes.

Five detector seeds 11/22/33/44/55, BOTH models: 50 complete epochs, batch128
(train final10, validation final69), Adam lr.001 with the explicit fixed defaults
in config, no scheduler/early-stop/autocast/clipping. Loss is aligned B,W,D MSE.
Log sample-weighted whole-epoch train and validation MSE. Best is minimum
validation MSE, exact ties earliest; always finish epoch50. Precompute and hash
all seed/epoch orders; both architectures consume the identical orders. No
labels enter any batch/loss/selection API. Save initial/final/best states and
hashes, per-epoch curves, selected epoch, optimizer settings, runtime/memory,
and recurrent-parameter changes. Independent fresh process/RNG per run, at most
two concurrent processes, no training-result-dependent scheduling or tuning.

Before full training: one unlabeled batch per architecture must have finite
loss and gradients, nonzero gradient on a recurrent parameter, equal Adam
semantics, and fail-closed native-predict exclusion. A failure stops Phase F.
This gate may backpropagate but does not supply a scientific checkpoint.

Freeze LSTM common18 before labels: ALL six recurrent layers equally pooled;
h_t, sigmoid(i), sigmoid(f), c_t; statistics over full H38, no heads. Same 18
names and trailing4/8/16/32 expansion as E2. Manual standard i/f/g/o recurrence
is observation-only and must agree with native sequence h and final h/c at
atol1e-5/rtol1e-4. Encoder and decoder deltas use their own actual t−1 within
window states. No layer selection or mLSTM-specific replacement.

Every best trained checkpoint must pass finite states, reset, prefix causality,
batch permutation/partition, output and score invariance within frozen float32
tolerance. xLSTM observer OFF/ON outputs/scores must be bitwise identical and
scalar hidden/final reference must pass tolerance. LSTM manual h/c/i/f replay
must pass native hidden/cell reference checks. Include B128/B3/B1 boundaries.
Parity uses fixed random unlabeled observations, not anomaly performance.

Compute extrapolation uses the sealed E2 pilot: 6.35 forward/backward batches/s
before optimizer cost; 79,000 total xLSTM training batches imply ~3.46 GPU-hours
plus validation/optimizer overhead. This is a lower-bound estimate, not a new
measurement. Report the F mechanical timings before full launch; retain the
protocol's 160 GPU-hour escalation bound. Two-process concurrency is operational
only; record wall time separately from summed run/device time.

Phase G remains unauthorized: no labeled feature extraction, probe scaler,
logistic fit, H2/H3 AP, test-source use, H3b/H4/natural-H1 or complex adaptation.
H1 controlled STOP, natural NOT_RUN, overall UNRESOLVED remain unchanged.
