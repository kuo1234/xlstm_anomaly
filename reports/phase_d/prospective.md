# Phase D — controlled H1 prospective freeze

Authorized after C3 review of 3d66ae7. H1-admission GO is NOT H1-harm.
Commit/push this document before any harm outcomes. No natural-SMD harm,
H4a/H4b, xLSTM/LSTM, probes, H3b or reversible-memory system is authorized.

## Operator and parity gate

Pinned official CANDI 28c9679e503832f59e351208cde63657fcb51cad remains immutable.
Window10, stride1, MLP reconstruction MSE, SMD_1-8 alpha5 operator: SANA
TCN_iTrans d_model512/heads8/layers1/d_ff512/dropout0/gelu, gating0.5;
SGD lr0.03, momentum0.9, weight_decay0.0001, dampening0, NesterovTrue;
MIN_SAMPLES16, STEPS1. Preserve official lack of gradient-clipping call despite
config flag. This is distinct from the later W64 probe track.

The controlled harness calls official MLPAdapter.calculate_loss on the supplied
committed buffer and reproduces the official train/eval, zero_grad/backward/step
sequence. Oracle composition replaces FPM candidate selection ONLY for this
operator intervention. One 100-window moderate queue is precomposed and committed
once (>=16); no preceding online updates, no pending second queue. Queue identity
does not change official MLP loss/optimizer. No-update control executes no steps.

D0 capture: existing seed0 1-8 alpha5 first update (moderate, update1,242 windows,
commit window255). Reexecute native default path to capture model/SANA/optimizer,
RNG and ordered buffer immediately before calculate_loss; capture official loss,
post-step tensors and scores on the next native batch (window starts256–511)
before its adaptation. Verify native committed IDs against the sealed trace.
Replay the captured buffer/state/RNG through the new harness. Require exact
buffer/order and step count; float32 loss/parameter/score tolerance atol1e-7,
rtol1e-6 AND bitwise tensor/model/score equality on this deterministic backend.
Any failure STOPs D; do not broaden tolerances or silently switch operators.
Replay probes score-before-update and restored model train/eval/RNG state too.

## D8 synthetic backbone and frozen initial state

Official MLP class unchanged except N_VAR8 and synthetic dataset wiring: W10
gives 80→40→20→128→20→40→80 with original ReLUs and MSE objective. No released
D38 checkpoint transplantation. Five detectors use seeds11,22,33,44,55.

Training data: initial clean fit [0,4096) from stationary/none source seeds
1000–1009, each used once (other scenarios share the same prefix; no duplication).
StandardScaler mean/variance fitted on these pooled raw fit observations only.
Train overlapping windows within each source, never across source boundaries.
Validation: clean [0,4096) prefixes of seeds2000–2004, same scaler, no labels or
test segments. Train30 epochs, shuffled batch256/drop_last=True, official Adam
lr1e-4/weight_decay1e-4, native cosine schedule/warmup5, per-batch epoch fraction.
Use official MLPTrainer.train_step and native optimizer/lr routines. Evaluate
mean window MSE at epochs5,10,15,20,25,30; lowest validation MSE wins, ties keep
earlier epoch. No hyperparameter/architecture search or harm-informed retraining.

For each chosen backbone: reset global RNG to its detector seed, freeze backbone,
instantiate official SANA-in then SANA-out in official order, initialize native
SGD with empty state, save full model/optimizer/RNG/config/scaler. This explicit
synthetic initialization differs from release-main RNG history and is NOT called
official reproduction. Reference/threshold calibration uses only [4096,5120)
from train source seeds1000–1009 (W10 windows entirely within interval).
Threshold is fixed 95th percentile of pre-intervention SANA-enabled scores.
Backbone, full pre-state, calibration threshold, scaler and all hashes are sealed
before evaluating any source3000–3009 harm. All causal arms clone the exact same
full pre-state, optimizer and RNG, including no-update. No test-fit scaling.

## Deterministic paired buffer (new controlled corruption schedule)

Use existing generator's clean latent observation realization via condition=none,
unaltered dynamics, for every test source3000–3009 and abrupt/gradual/recurring/
correlation scenario. A separate controlled buffer corruption schedule is needed
so all severity/duration margins fit BEFORE a nonempty held-out evaluation tail;
do not move or alter the sealed generator's evaluation event schedule.

Let T=5120 and shift onset S=T+4096. Buffer availability cutoff U=S+3000.
Nine disjoint controlled events j=0..8 start at S+32+300*j. Channel=j mod8;
severity=1+floor(j/3); duration (nonspike)=[16,64,256][(j+floor(j/3)) mod3].
Single-type arms assign all nine events that type. Mixture cycles spike,
collective,dependency by j mod3: each type has all three severity levels and
nonspike duration levels. Spike duration1. Use sealed generator corruption
equations: additive severity for spike/collective; dependency adds
severity*(independent N(0,1)−clean_channel)/sqrt(2), with local NumPy RNG
SeedSequence([source_seed,j,812,4]). Never modify latent recurrence.

Construct 30 potential anomalous window endpoints by round-robin sequence
(offset0,event0..8),(offset1,event0..8),(offset2,event0..8),(offset3,event0..2).
Each window [endpoint−9,endpoint] includes its event onset; all endpoints are
unique. Complete to100 with70 uniformly spaced (floor linspace index) endpoints
from [S+9,U−1] whose W10 windows overlap no controlled event of ANY type (use
max-duration event envelopes for the common layout). Sort all100 endpoints
chronologically for buffer order. Replacement priority is the stated round-robin
order mapped to chronological slots; c replaces first c slots in that priority,
c∈{0,5,10,20,30}. Remaining slots always use the clean counterpart at identical
time. Assert exactly c anomaly windows, identical slot times and normal latent
source, nested replacement sets, no changed unselected slots, no event overlap.
At c not divisible by3, mixture type counts differ by at most1; exact equal thirds
are mathematically impossible for5/10/20. Report counts, never relabel as exact
equality. The mixture is equal-type in event schedule and maximally balanced in
selected windows. Events/severity/duration/age stay paired across arms. These
onset-window interventions do NOT independently estimate long-duration effects;
overlapping windows within an event are not independent events.

## Evaluation, grid, statistics

Following the prescribed update, score the identical unmodified generator's
condition-specific evaluation observations from raw index U+10 through its end,
using W10 windows wholly inside that suffix; no further adaptation. Exclude any
window intersecting the separately flagged persistent-fault interval from primary
metrics, retaining separate stress metrics. All other original event types,
severities/durations and regime transitions remain; no retrospective point filling.
The recurring regime return occurs in the held-out suffix. Evaluation truth is
window-any anomaly. AP primary; AUROC, fixed-threshold FPR/recall, anomaly-free
window FPR (same definition as clean-normal FPR), score mean/std/quantiles and
paired score changes, trainable parameter delta norm, loss and actual anomalous
gradient exposures also reported. No test-best thresholds or point adjustment.

Grid:10 sources×4 scenarios×4 anomaly conditions×5 detector seeds×(5 c arms+
no-update)=4800 rows. c0 may be computationally reused across conditions only if
buffers/state/evaluation are identical; never manufacture independent evidence.
All arms restore exact pre-state, and evaluation is identical within each pair.

Unchanged H1 gate: for each of16 (positive c,type) comparisons, average paired
AP(clean)−AP(contaminated) equally over4 scenarios within source and5 detector
seeds; sources are primary clusters. Bootstrap10,000 draws, RNG901, resample10
sources first then5 detector seeds within sampled source, preserving entire
scenario/event vectors. Percentile95% CI. Exact source-cluster sign-flip across
2^10 signs on source-mean differences; two-sided p (conservative), Holm across
16 controlled +6 unavailable natural comparisons (p=1) at0.05. Require mean≥.02,
CI lower>0, Holm p<.05, positive source/scenario-averaged direction in≥4/5 detector
seeds and source/seed-averaged direction in≥3/4 scenarios. Only c<=20 qualifies;
c30 stress-only. c0 self-comparison is a zero-effect control. No per-window n or
repeated-exposure independence. Report every negative/null comparison.
No qualifying result: INCONCLUSIVE if any eligible comparison's CI includes the
.02 practical margin; otherwise STOP for this frozen intervention. Neither is
proof of universal safety or grounds to retune. H1-admission remains separate.

## Compute preflight

After D0 parity, measure one backbone seed11 training and one-source dry-run
(source3000,abrupt,spike,seed11,all c+no-update). Backbone training can be timed
before test outcomes; freeze all five backbone states before any test harm read.
Project remaining backbone training, data generation and4800 evaluation rows
using measured time; use2× projected experiment runtime as conservative bound.
If projected full Phase D exceeds24 GPU/wall hours, or parity cannot be established,
STOP expansion and report. Do not shrink the grid or select seeds. Complete grid
only when parity and measured compute gate PASS; dry-run rows remain included,
not an independent replicate. Hash every buffer manifest and arm scores/state.
