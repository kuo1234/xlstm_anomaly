# Experiment lineage — Phase A to Phase G

Scope: the *scientific* evolution of the project, not its commit history. For each phase: the
question it asked, the protocol it froze, the implementation problem it exposed, the gate it
returned, and what that gate unlocked or locked. Failures appear where they changed what the
project was allowed to do — which, in this project, is most of them.

Sources are the sealed phase reports under `reports/`. Nothing here restates a G1 outcome: at the
time of writing the recovered G1 continuation is still executing and no H2/H3a result has been
adjudicated.

---

## Why the lineage looks like this

Two structural choices explain almost every branch below.

1. **The protocol is fail-closed and frozen before outcomes.** `reports/m0_protocol.md` plus its
   versioned amendments fix datasets, features, statistics and GO thresholds *before* the
   corresponding results can be inspected. A phase may therefore end in STOP for reasons that have
   nothing to do with the scientific hypothesis — an unresolved data provenance, a numerical
   mismatch in a validity check — and that STOP is recorded rather than engineered away.
2. **Implementation validity is treated as a separate, hypothesis-free layer.** Phases D, E and F
   each failed at least once on execution-validity grounds while the scientific question was never
   reached. The project's convention is that such a failure is *not* evidence about H1/H2/H3, and
   that repaired artifacts may not be relabelled as reproductions.

The cost of this design is visible: three phase families needed two or more versions
(A → A-v3 → A-v4; C → C-v2 → C3; F → F-v2 → F-v3 → F-v4). The benefit is that every surviving
artifact has a stated provenance and a stated limitation.

---

## Phase A — can a defensible real-data manifest exist at all?

**Question.** Which real multivariate series may serve as (A1) a strict reproduction/natural-harm
anchor and (A2) an external non-stationarity stress set, under a selection rule frozen before any
model was run?

**Protocol.** SMD is fixed *a priori* to `machine-1-8` and `machine-2-1` with sealed raw and
CANDI-preprocessed hashes. For A2, TSB-drift CD=1 candidates are audited for eligibility
(multivariate, finite numerics, binary labels, verified train cutoff, entirely normal training
prefix, minimum lengths), grouped by exact duplicate/same-origin evidence, and then assigned by a
deterministic global optimization — not greedy selection.

**What the audit found.** Of 75 candidates, 65 passed the numeric/prefix checks; ten prefixes were
label-contaminated (SMD 078, LTDB 080 and all eight TAO files); CATSv2 was excluded as simulated;
Exathlon 188/190/198/199 formed one exact duplicate group. Fifteen SMD traces were resolved to
native machine identities by exact full-row containment against all 28 original test traces, and 60
of 75 rows were left flagged `native_provenance_unresolved`.

**Gate: STOP.** Not for lack of eligible files per bucket (5/12/3/3) but because the periodic and
random-walk eligible pools were *the same three SMD files*: the frozen global assignment had no
solution. The report states explicitly that this is a provenance and feasibility blocker, not
evidence against any modeling hypothesis.

**A-v3 — the correction that made it worse.** An evidence-tier amendment made native provenance
nullable (unresolved rows stay eligible but must be clustered by source family). A provisional
twelve-file list was produced — then invalidated by primary-source verification that GHL is itself
simulated (Modelica gasoil-plant simulation; the A-v3 report records this as `arXiv:1612.06676`,
a citation taken from that report and not independently re-verified here), removing 23 further rows. With 37
eligible rows the unchanged solver was again infeasible. A1 was sealed PASS; A2 returned STOP a
second time, and the rejected provisional files were retained under
`reports/phase_a_v3/rejected_provisional/` explicitly marked not for experiments.

**A-v4 — the amendment that resolved it.** The hard within-bucket family-diversity constraint was
replaced (pre-outcome, user-approved) by lexicographic objectives: maximize global family diversity
(9), then within-bucket unique-family count (9), then minimize the sum of squared global family
counts (20), with a filename tie-break. That yields the twelve released files now used, with
denominators kept in the open: inventory 75, eligible 37, unresolved 60 overall and 23 among
eligible, selected 12 of which 9 remain unresolved. The periodic bucket is SMD×3 — single-family
descriptive evidence only.

**What it enabled / prevented.** Enabled: Phase B scaffolding and, later, real-data reproduction on
the strict A1 anchor. Prevented: any claim that TSB-drift provides independent native traces, and
any use of A2 as causal evidence for H2/H3/H4a.

**Lesson carried forward.** "Released benchmark file" and "independent data source" are different
objects. The project's habit of separating *what an artifact is* from *what it licenses* starts here.

---

## Phase B — build the evaluator before the detector

**Question.** Can the causal evaluation contract and the controlled generator be implemented and
tested without any detector, so that later model results are measured by something already frozen?

**Protocol / implementation.** Four small modules: `m0/causal.py` (immutable decision records,
W=64/stride=1 right-edge stream, score-then-update ordering, fit-only scaler and calibration
threshold, separate candidate/committed/pending denominators, latency accounting; algorithm
callbacks receive `x`/time/state/score and never labels); `m0/synthetic.py` +
`configs/synthetic_v1.json` (D=8 VAR with temporal and cross-channel dependence, five scenarios,
source-disjoint seed folds, spike/collective/dependency events plus equal-type mixture, severity and
duration controls, paired legitimate excursions, persistent-fault stress stratum, stationary and
identical-observation/opposite-semantic controls); `m0/correlation.py` (analytic covariance
construction with an independent SciPy discrete-Lyapunov solve); `m0/metrics.py` (AP, separately
named trapezoidal PR-AUC, AUROC with tied scores grouped, fixed-threshold FPR/recall, censored
post-shift recovery).

**Gate: PASS (software only).** 25 tests: Lyapunov residual ≤1e-10, independently solved stationary
moments equal to ≤1e-10, off-diagonal correlation difference ≥0.2, all 256 transition steps with
diagonal deviation ≤1e-10, exact regeneration, fold disjointness, label-permutation invariance of
scores/selections/commits, and future-observation invariance of earlier outputs.

**What it enabled / prevented.** Enabled: everything downstream has an evaluator that was tested
before it could be tuned. Prevented: the report lists what is *not* established — no
model/optimizer/RNG adapter parity, no VUS-PR, no probes, no real-data adapters — so Phase B is
never citable as evidence for a hypothesis.

**A deliberate limitation worth keeping in view.** Only the latent correlation-shift scenario has
analytically matched marginal moments; dependency anomalies can change marginal variance. Short
legitimate excursions are constructed to have exactly paired anomalous counterparts, which caps how
much any duration-based identifiability claim can ever say.

---

## Phase C — reproduce the adaptation baseline, and discover it has two fidelities

**Question.** Does the pinned CANDI release (`28c9679e`) reproduce, and does its test-time
adaptation actually admit true anomalies into its update path?

**Protocol.** Official modules executed unmodified through `main.py` with each author script's exact
arguments, released checkpoint, native preprocessing, W=10, native FPM/SANA/counters and
`TRAIN.ENABLE=False`; metrics computed with window-any truth, sklearn AUROC and *trapezoidal*
PR-AUC, no point adjustment; a >0.02 absolute discrepancy against the published table is a
reproduction-investigation trigger, not a licence to tune.

**What it found.** On `machine-1-8`, observed AUROC/PR-AUC tracked the paper within 0.02 for
alpha 0.5 and 1, but alpha 5 PR-AUC differed by 0.026996 — so native expansion stopped immediately
and five-seed replication stayed locked. A read-only investigation then showed the *author-committed
cached* arrays also give ≈0.4500 rather than the published 0.423 (and 0.367750 rather than 0.332 for
the static variant). The cached run configs carry `TRAIN.ENABLE=True` while the release default with
a supplied checkpoint is `False`. Conclusion recorded: a paper-versus-release lineage mismatch,
`UNRESOLVED_LINEAGE` — not an identified root cause, and explicitly not permission to move the gate.

**The admission audit (bounded to 1-8 alpha 5 seed 0).** With stable external window IDs and
evaluator-only labels: hard queue 237/1275 anomalous (18.59%), identical across candidate, committed
and gradient-exposure denominators; moderate 199/9747 candidates versus 199/9746 committed; total
436/11022 (3.96%); 101 updates and 101 optimizer steps; 531 unique raw anomalous timestamps covered.
A label-isolation overlay that deletes only the diagnostic label reads reproduced bitwise-equal
scores and final model-state hash.

**Native defects deliberately preserved.** Variable final-batch offset misindexing (last batch
length 138, actual offset 23552 versus `iter*len(scores)` = 12696); the official moderate admission
counter (9747) differing from actual committed (9746) because it counts queue admissions; the Q1–Q3
moderate test mask overwritten by `scores<threshold`; representation computed with the *current*
SANA input module, so queries are not adaptation-invariant; `USE_FPM=False` returning before the
iteration counter increments; a configured gradient-clip flag never called. None was fixed — they
are baseline properties, and the project measures contamination with its own stable IDs instead.

**C-v2 — separating the two fidelities.** An externally authorized pre-execution amendment split
**C1-P** (paper fidelity: paper vs author cache vs local execution, reported separately per row)
from **C1-R** (released-artifact operational fidelity: the sealed checkpoint under release defaults),
with three ordered gates — bitwise replay equality, then the second machine, then a native
label-permutation control. Outcome: **C1-R PASS, C1-P MISMATCH/UNRESOLVED_LINEAGE**, and C2's
independent audit accepted.

**C3 — is the adaptation seed even active?** `CANDIAdapter.__init__` constructs fresh SANA
input/output modules *after* loading the pretrained backbone, so their initialization consumes the
seeded RNG: the released backbone is identical while the adaptation trajectory genuinely varies with
`SEED` (**SEED-ACTIVE**). Across five effective seeds × six machine/alpha conditions, committed
contamination ranged 1.58–4.06% and anomaly admission was reproducible in **5/5 seeds for all six
conditions**. Repeated anomalous loss exposures were 0 on `machine-1-8` but 660–1252 on
`machine-2-1` (the same committed windows re-exposed under native `STEPS`).

**Gate: H1-admission GO; H1-harm NOT TESTED.**

**What it enabled / prevented.** Enabled: the controlled H1 intervention (Phase D), with a real
operator to imitate and real admission rates to compare against. Prevented: any inference from
admission to harm — a distinction the README still enforces in its "reading results safely" list.

---

## Phase D — does contaminated adaptation actually hurt?

**Question.** Holding everything else identical, does one native SANA update on a buffer containing
anomaly windows degrade subsequent detection relative to a clean-buffer counterfactual?

**Protocol.** Paired arms from a cloned pre-intervention state (model, SANA, optimizer, RNG, buffer
order, step count); oracle access confined to buffer composition; the *official* update operator
rather than generic fine-tuning; contamination c ∈ {0,5,10,20,30}% with c=30 stress-only; four
anomaly conditions; five detector seeds; evaluation on an identical subsequent stream before further
updates; no-update controls reported.

**D-v1 gate: implementation-validity STOP.** The captured real-SMD operator replay itself passed
bitwise (loss `0.20451687276363373` over 242 ordered moderate windows, matching
post-model/optimizer/RNG state and the next 256 window scores). What failed was *repeatability in a
fresh process*: the grid restored RNG states but not `torch.backends.cudnn.deterministic=True`,
which the official `set_seeds` path enables and a new process defaults to `False`. Identical
checkpoints and RNG did not give identical execution — maximum parameter difference 7.45e-9,
maximum score difference 2.62e-6. Equally important is *when* the check ran: the repeat and
label-isolation tests were executed after grid expansion rather than before it. The grid was
terminated with 83 complete pairs (498 rows) plus one partial, all quarantined; the report states
that an empty qualifying list means NOT EVALUATED, never a negative result.

**D-v2 gate: D0 PASS; controlled H1-harm STOP.** With the backend state restored and the ordering
corrected, four parity gates and twelve canaries passed bitwise and the full 4,800-row grid was
regenerated from scratch (zero quarantined rows reused). None of the twelve c≤20 comparisons reached
the frozen 0.02 practical margin — the largest mean loss was collective c20 at ≈0.000028
(CI [1.7e-5, 4.0e-5], Holm p=0.0430, positive in 5/5 seeds and 3/4 scenarios): statistically
detectable, practically negligible. The accompanying interpretation file refuses the symmetric
over-reading too: with spike macro AP ≈0.008 and fixed-threshold post-shift normal FPR ≈0.49, this
intervention has limited sensitivity and cannot be cited as evidence that the backbone is robust or
that contamination is harmless.

**Route-qualified status (`reports/h1_status.json`).** `H1_admission=GO`,
`H1_controlled_harm=STOP`, `H1_natural_harm=NOT_RUN`, `H1_harm_overall=UNRESOLVED`, H4a/H4b LOCKED.
The natural-SMD counterfactual was never waived — it was never run.

**What it enabled / prevented.** Enabled: an honest statement that the *mechanism* branch has no
demonstrated harm to fix yet, which is why the project turned to the information question instead of
building an adaptation gate. Prevented: H4a/H4b, and any "safe adaptation solves a demonstrated
problem" framing.

---

## Phase E — audit the xLSTM detector before trusting anything it emits

**Question.** Can the pinned xLSTMAD submission version supply the internal-state observations that
H2/H3a require, with a valid architecture, valid batching and reference parity?

**What E resolved.** The v1 architecture at D=8: encoder and decoder each `[mLSTM, sLSTM, mLSTM]`
(4 matrix + 2 scalar cells), sLSTM with 4 heads × 10 hidden scalars, mLSTM with 4 memory heads of
20 dimensions, 78,080 trainable parameters, input projection D→40, encoder keeping only the last
embedding, and a decoder applying its stack W times to singleton embeddings without passing state
between calls.

**Gate: BLOCKED — two independent blockers, neither a hypothesis result.**
1. **Readout layout defect.** Raw model output is `[W,B,D]` while the target is `[B,W,D]`, and both
   training and scoring flatten with `view(-1, W*D)` without a transpose. Native score batch
   permutation therefore fails (max absolute difference 0.08668685 at W=64), and a CPU marker
   fixture proves that changing only window 3's output changes window 0's score. The model tensor
   permutation itself is bitwise correct — this is an original readout/loss-layout defect.
2. **Native kernel parity not establishable.** The CUDA build first lacked `Python.h`; after headers
   were supplied, CUDA 13 linking failed on undefined `SLSTMPointwiseForward<false/true>` for both
   bfloat16 and explicit float32. No cell or kernel source was patched.

Two further behaviours were documented rather than inherited: the original multivariate dataset
repeats the final window over the last W positions (so those are not independent causal endpoint
decisions), and the native wrapper fits a MinMaxScaler on *test* scores.

**Decision of principle.** v1 was retained as immutable validity evidence and *not* repaired and
relabelled a reproduction — transposing the output would change the original training loss and
scoring semantics, which is a different model, not a fixed one.

**E2 — the valid track.** The improved official implementation (`e8b56ba2`, `xlstm==2.0.5`,
`lightning==2.6.1`, vanilla float32) has encoder/decoder `[sLSTM, sLSTM, mLSTM]`: 4 scalar layers ×
4 heads × 10 scalars (hidden 40), 2 matrix layers, 73,504 parameters, `[B,W,D]` coordinate-aligned
reconstruction MSE, fresh recurrent/conv reset per window with full within-window decoder history,
and a `SlidingWindowDataset` yielding 131 unique chronological windows from N=194 at W=64 with no
tail repeat. All 40 validity checks passed, including output/score batch permutation, B128-vs-B3/B1
score agreement (bitwise in two cases, ≤2.4e-7 on repartition), reset with no carry, prefix
causality, observer OFF/ON bitwise parity, label isolation, and no test-fitted scaler or threshold
in the common path.

One honest detail from E2: an internal *reporting* checker produced a false positive by
string-matching the word "threshold" inside a docstring; it was replaced with an AST check. The
original log and validity JSON were kept intact and no scientific check changed — recorded as a
checker error, not a waived gate.

**Gate: E BLOCKED (immutable evidence); E2 PASS (bounded validity/instrumentation only).**

**What it enabled / prevented.** Enabled: a frozen, executable 18-column internal schema and a
detector whose scores are verifiably causal and permutation-invariant. Prevented: any use of v1
artifacts, and any claim that E2 says something about detection performance.

---

## Phase F — train the matched pair, and keep failing the validity contract

**Question.** Can xLSTM and a capacity-matched LSTM be trained under one identical contract, with
recurrent internals verified against an independent reference, so that a later H3a comparison
isolates architecture rather than implementation?

**Protocol.** Matched baseline: standard full-window encoder-decoder `nn.LSTM`, three encoder and
three decoder layers, H=38, GELU, H→D projection, 71,790 parameters (−2.33% versus 73,504) — chosen
before results, per the ±10% parameter rule. Shared contract: W=64, batch 128, Adam lr=0.001, 50
epochs, sealed source folds and orders, detector seeds {11,22,33,44,55}, `atol=1e-5, rtol=1e-4`.

**F-v1: STOP before the first optimizer step.** The matched LSTM's manual recurrence disagreed with
the native `h`/`c` reference in all six layers (encoder-0 max sequence-h error 1.9206e-4, final-c
1.9745e-4). A bounded diagnostic localized the cause to backend numerics — frozen CUDA path with
cuDNN TF32 allowed FAIL; TF32 disabled PASS; CPU PASS — with final-output effects around 6.7e-6.
The report refused to switch backend on the strength of a passing diagnostic and required a
pre-training amendment instead.

**F-v2: STOP after one completed run.** Under `allow_tf32=False` the pre-training gates passed, the
grid started, and `lstm_11` completed its 50 epochs — then its best checkpoint failed the mandatory
post-training B128-vs-B1 output partition check by 2.9087067e-5. The launcher terminated the
concurrent `xlstm_11` at epoch 2 and never started seeds 22–55. Everything generated was permanently
quarantined.

**F-v3: STOP mid-grid, then a diagnostic replay.** A per-epoch canary caught `lstm_33` failing the
raw-output check after epoch 28 (exit code 1 at 770.13 s), and the fail-fast queue terminated
`xlstm_11`; `lstm_11` and `lstm_22` had completed and passed post-training parity. The sealed
seed-33 replay (F3-R) reproduced epochs 1–28 exactly and localized the failure precisely: **one**
raw-output element outside the allclose rule, first failing stage `output_projection`, while GELU,
all six recurrent stages, the reconstruction score, the common18 features, observer on/off, reset
and prefix causality all passed.

**F-v4: PASS.** A pre-outcome amendment reclassified raw `[B,W,D]` partition allclose as
*diagnostic-only* — still logged every epoch with max/mean absolute error and failed-element counts,
still hard on finite/shape — while keeping score, common18, six-layer recurrent/reference, observer,
reset and prefix checks hard and symmetric across both architectures. Nothing else moved: same
architecture, initialization, backend flags, data, optimizer, epochs, seeds and tolerances. Eight
fresh runs completed 50 epochs and passed every hard gate; `lstm_11`/`lstm_22` were carried forward
*by reference* (F3 checkpoints neither copied nor retrained), and the F3 partials for `lstm_33` and
`xlstm_11` stayed quarantined and forbidden.

**Why F-v4 is defensible rather than a relaxation.** The gate that moved is the one the diagnosis
showed to be measuring backend rounding in a tensor that no downstream scientific quantity consumes
— the probe consumes reconstruction scores and the common18 internal summaries, both of which
stayed hard. The amendment was committed before any F-v4 optimizer step, applies identically to both
models, and preserved the failing statistic as a logged diagnostic instead of deleting it. That is
the narrowest defensible change; a reviewer may still ask why a raw-output element can drift when
the derived score does not, and the F3-R localization to `output_projection` is the answer on record.

**What it enabled / prevented.** Enabled: ten sealed inference-only checkpoints, matched in contract
and verified in internals — the only artifacts Phase G may consume. Prevented: reuse of any
F-v1/F-v2/F-v3 partial weights, and any claim that the two backbones were compared under a
still-unverified numerical path.

---

## Phase G — the information question, under a label-access seal

**G0 / G0.1 — freeze everything that could otherwise be chosen after seeing labels.** The ten
eligible checkpoints, the feature schema (history 14; internal base 18; hidden 52, gate 130,
memory 52; combined 234; history+combined 248; rolling widths 4/8/16/32; xLSTM restricted to its
four scalar sLSTM cells, LSTM pooling all six recurrent layers equally; no learned pooling, no
zero-padding, no mLSTM-only confirmatory feature), the probe (L2 logistic, StandardScaler on train,
C grid {0.01,0.1,1,10} by validation AP, temporal purge 96) and the confirmatory family (exactly
four Holm members: H2, H3a-A/B/C) were sealed *before* any label access, and the label-blind
preflight was allowed to load checkpoints and random unlabeled tensors only.

G0's first attempt deliberately failed closed on a real ambiguity: more than one artifact could
serve as the "frozen CANDI history control" (five D=8 seed-wise `pre_intervention.pth` states at
native W=10, plus several SMD/native sources), and the protocol had pre-registered none of them.
Recorded as `UNRESOLVED_PRELABEL`, it blocked labeled extraction until the **G0.1** amendment pinned
the choice by construction rather than by outcome: the Phase-D D=8 family mapped by detector seed,
CANDI keeping W=10 while xLSTM/LSTM use W=64, both aligned to the same right-edge timestamp with the
common decision stream starting at t=63 and earlier CANDI scores forbidden. The alignment preflight
then verified timestamps 63–191, 97 valid history rows after NaN warmup, byte-identical row keys
reused across both backbone arms, future-perturbation causality, reset, and dummy-label invariance —
for all five seed mappings. **G0 status: PASS.**

**G1 — execution under seal, and what happened to it.** The implementation was committed first
(`fe50708`) *without* a passing self-review; a separate report-only commit carried the
`PASS_FOR_LABEL_ACCESS` review and became the seal (`5622376`), which the labeled launcher requires
together with an explicit `--label-access` flag and byte-identical scientific files across the two
commits and the working tree. The G1.1 amendment had already resolved the duration/severity
robustness estimand (test-only subgroup evaluation of the frozen pooled probe, with
`INSUFFICIENT_SUPPORT` as a real outcome) and kept the semantic non-identifiability pair as a
separate negative control that can never support H2.

The first labeled execution completed all 2,625 labelled stream extractions and then raised a
`ValueError` while serializing the primary-cache path (`relative_to(ROOT)` on a relative
`--output-dir`) — *before* probe fitting, AP, statistics, the secondary pass and decision writing.
Because evaluator labels had already been joined, this was recorded as a **post-label incident**:
status `QUARANTINED / STOP_RESULT_UNRESOLVED`, with the 118 GB cache and the execution ledger
preserved read-only and explicitly barred from estimation.

The recovery path was then built one reviewed step at a time, each with its own report-only seal: a
narrowly scoped reporting patch (`2c79cbf`, whose only scientific-path change is canonicalizing
`output_dir` once at entry, with an AST/source-diff audit required to prove nothing else moved); a
cache-integrity audit returning `PASS_CACHE_REUSABLE` (120,000 expected files as 40,000 NPZ
triplets, 2,500 shifted primary streams, 2,625 labelled-stream completions, a fixed replay over 48
stream/backbone pairs and 384 feature-arm comparisons with zero failures, and ten deliberate
fail-closed fixtures all rejected); a continuation gate whose own first seal was invalidated — it
fail-closed on a missing `_sha_bytes` helper before touching the cache — and was re-reviewed at
`25a67ad`; and finally a recovered post-run auditor (`bf093c4`, report seal `069cdd2`) that
independently replays scaler/probe primitives, validation-C selection, predictions, AP, all four
effects, bootstrap, sign-flip, Holm, robustness, the semantic control and the Boolean decision
consequences, and that requires `current HEAD == continuation seal`.

**Current status: executing; no adjudicated outcome.** The single authorized recovered continuation
is running under that seal. Per protocol, `g1_results.json` / `g1_statistics.json` /
`g1_decision.json` become authoritative only after the run completes *and* the independent recovered
post-run audit passes. Nothing in this document, and nothing in the branch skeletons in
`g1_outcome_branches.md`, assumes a direction.

**What G is designed to enable / prevent.** Enable: a pre-registered answer to the *information*
question — does window-local internal state add drift-versus-anomaly information beyond
score/history, and is any such gain xLSTM-specific. Prevent, by construction: post-hoc promotion of
a winning ablation, test-informed feature or C selection, interpretation of H3a without H2, rescue
of a failed primary comparison by a subgroup analysis, and any slide from "information exists in a
frozen synthetic probe" to "safe adaptation works".

---

## The lineage in one table

| Phase | Question | Gate | Why it mattered |
|---|---|---|---|
| A | Is there a defensible real-data manifest? | STOP → (v3) A1 PASS / A2 STOP → (v4) A2 PASS | Separated "released file" from "independent source"; fixed the strict SMD anchor |
| B | Can the evaluator/generator be frozen before detectors? | PASS (software only) | Gave later results a pre-tested measuring instrument |
| C | Does the adaptation baseline reproduce, and does it admit anomalies? | C1-P MISMATCH/UNRESOLVED_LINEAGE; C1-R PASS; C2 accepted | Split paper fidelity from artifact fidelity; established stable-ID contamination accounting |
| C3 | Is adaptation seed-active and is admission reproducible? | PASS, SEED-ACTIVE → H1-admission GO | Admission is real, and is still not harm |
| D | Does contaminated adaptation cause harm? | v1 implementation STOP → v2 D0 PASS, controlled harm STOP | Backend determinism is part of the experiment; harm remains UNRESOLVED, not absent |
| E | Can the xLSTM detector be trusted to emit internals? | v1 BLOCKED (readout layout, kernel parity) → E2 PASS | Invalid implementations are evidence, not drafts |
| F | Can the matched pair be trained under one verified contract? | v1/v2/v3 STOP → v4 PASS | The comparison isolates architecture only if internals are verified first |
| G | Does internal state add drift-vs-anomaly information? | G0/G0.1 PASS; G1 executing | Everything choosable was frozen before label access |
