# Research onboarding — safe normality adaptation for non-stationary multivariate TSAD

This is the research-facing entry point: what the project is trying to learn, why the problem is
hard, what has already failed, and what may currently be claimed. It is written to stay accurate
whatever the current experiment returns.

For the code and evidence ledger, see the repository `README.md`. For the protocol itself, read
`reports/m0_protocol.md` first — it is the source of truth, and it outranks every narrative
document including this one.

---

## 1. The scientific problem

A deployed anomaly detector's notion of "normal" does not stay fixed. When the input distribution
moves, the detector faces three possibilities and cannot tell them apart from the observation alone:

1. a genuine anomaly or fault,
2. a legitimate new normal (a re-configured plant, a new operating regime, a seasonal shift),
3. an ambiguous shift that has not yet resolved into either.

Both naive responses fail. Adapt immediately and the detector absorbs anomalies into its model of
normality — it learns the fault and stops reporting it. Never adapt and the post-shift false-positive
rate grows until the alarm channel is worthless. The long-term framing is

> **Safe Continual Normality Adaptation** — learn the new normal without learning the anomaly,

and the project's position is that this cannot be approached as an architecture problem until a
prior, more basic question is answered.

**That framing is not itself a contribution.** A literature sweep of 78 papers (see
`positioning_table.md`) finds it anticipated — most directly by an online method that separates domain
drift from true anomalies with two decoupled model-derived criteria — and finds three of the four
components the project assumes (internal-quantity admission control, deferred commitment,
reset-on-drift-evidence) already published, two of them already combined in a single mechanism on
simpler detectors. What the sweep does *not* find is the measurement this project is actually doing,
or any causal accounting of contamination harm. Read `positioning_table.md` before writing a novelty
claim.

## 2. Why anomaly-versus-new-normal is genuinely hard

- **It is not identifiable in general.** Over a bounded observation window, a short legitimate
  excursion and a collective anomaly can be *observationally identical*. The project's generator
  makes this explicit: it contains identical-observation pairs with opposite semantic truth as a
  negative control, and legitimate excursions with matched perturbation magnitudes and matched
  durations. Any achievable discrimination performance therefore sits above an irreducible error
  floor that exists by construction, and no method can remove it.
- **The evidence that would settle it arrives later.** Persistence is the natural discriminator, but
  waiting costs latency and, in an adaptive system, the wait is not free: what the detector observes
  next depends on what it has already adapted to.
- **Real data does not carry the labels this question needs.** Public TSAD benchmarks label anomalies,
  not "legitimate regime changes"; timestamp-level drift-versus-anomaly truth does not exist for
  them. The protocol declares those metrics N/A on real data rather than inventing them, which is
  why the current information experiment is synthetic with evaluator-side truth.
- **Adaptation mechanisms are hard to evaluate honestly.** Nonzero anomaly admission is not harm;
  zero updates are not "0% contamination"; a delay that changes which samples get committed is not
  decontamination. The project keeps four separate exposure denominators (candidate, queue-admitted,
  committed-for-update, optimizer-loss-exposed) because conflating them is the standard way this
  literature overstates safety.

## 3. Why xLSTM internal dynamics are being examined

Not because xLSTM is expected to be a better detector. The hypothesis is narrower and deliberately
falsifiable:

> xLSTM gate and recurrent-memory dynamics may contain additional historical information for
> distinguishing persistent drift from transient anomalies.

The reasoning: a reconstruction detector's scalar score is a lossy summary of what its recurrent
state has been doing. If gating and memory dynamics respond differently to "inputs that are large"
versus "inputs that are differently distributed", then internal summaries could carry evidence the
score discards. xLSTM is a reasonable place to look because its scalar cells use exponential gating
with an explicit stabilizer and normalizer state — but that is a motivation, not a mechanism claim,
and the confirmatory design compares it against a capacity-matched conventional LSTM precisely so
that a null result is informative.

**A negative result is a valid outcome and is planned for.** See `g1_outcome_branches.md`.

## 4. H1, H2, H3 — and what each does *not* ask

The protocol separates three questions that are usually merged:

**Admission** — do candidate windows actually enter an adaptation buffer and get exposed to
optimization?
**Information** — do internal recurrent summaries add drift-versus-anomaly information beyond
score/history controls?
**Mechanism** — only if the information question is answered positively, can delayed, reversible
normality adaptation be studied.

| Hypothesis | Question | GO threshold (abbreviated) | Status |
|---|---|---|---|
| **H1-admission** | Does a released adaptive detector commit true anomaly windows? | Nonzero independently audited committed anomaly windows on a fixed SMD anchor, reproducible in ≥4/5 seeds | **GO** |
| **H1-harm** | Does contaminated adaptation cause measurable harm? | Clean-versus-contaminated AP loss ≥0.02 with CI > 0, multiplicity control, ≥4/5 seeds and ≥3/4 shifted scenarios — on a controlled route at c ≤ 20% or the natural-SMD counterfactual | controlled **STOP**; natural **NOT_RUN**; overall **UNRESOLVED** |
| **H2** | Do window-local internal summaries add information beyond score/history? | `AP(history+combined248) − AP(history14) ≥ 0.02`, CI > 0, Holm p < 0.05, ≥4/5 seeds, ≥3/4 shifted scenarios, plus duration and severity macro support | **under test** |
| **H3a** | Is that information xLSTM-specific? | Three comparisons (A: combined-vs-combined ≥0.02; B: incremental gain difference > 0; C: same under one shared frozen CANDI history), interpreted only if H2 passes | **conditional, not yet interpretable** |
| **H3b** | Does carried recurrent state add information over per-window resets? | carry − reset ≥ 0.02 with the same consistency rules | **LOCKED** unless H3a passes |
| **H4a / H4b** | Does waiting add evidence / how does FIFO scheduling trade off? | H4a: ≥0.02 at some K ∈ {4,8,16,32} with the same rules; H4b has **no** decontamination threshold by design | **LOCKED** behind H1-harm |

All four confirmatory members of the current experiment compare the **probe's** average precision on
"anomaly window versus anomaly-free drift/transition window", using features from *frozen* detectors.
None of them measures the detectors' anomaly-detection performance. The probe is an offline
diagnostic and never controls adaptation.

Deliberately **not** implemented at this stage: rollback, stable/plastic dual memory, a learned
adaptation gate, a new xLSTM cell, a paper architecture, or a production continual-learning system.

## 5. What has already failed (and why that is load-bearing)

The project's failures are part of its evidence, not a private debugging history:

- **Dataset selection failed twice.** The frozen global assignment had no feasible solution — first
  because the periodic and random-walk pools were the same three SMD files, then again after
  primary-source verification showed GHL is simulated. Only a pre-outcome amendment to the
  *objective* (not the eligibility rules) produced the current twelve-file external stress set, of
  which 9/12 still carry unresolved native provenance.
- **The baseline has two different fidelities.** CANDI reproduces its *released artifact* behaviour
  (C1-R PASS) but not its *published table* within tolerance (C1-P MISMATCH, UNRESOLVED_LINEAGE) —
  and the author-committed cache disagrees with the paper too. Those are separate objects and are
  reported separately.
- **The first contamination experiment was invalidated by a backend flag.** Identical checkpoints and
  RNG state did not reproduce because a fresh process defaulted `cudnn.deterministic` to False. The
  grid was quarantined at 83 of 400 pairs and rerun from scratch after the ordering of validity
  checks was corrected.
- **The original xLSTMAD implementation is invalid for this use.** Its raw output `[W,B,D]` is
  flattened against `[B,W,D]` targets in both training and scoring, so one window's output changes
  another window's score; its dataset repeats the final window. It is retained as immutable evidence
  and was *not* repaired and relabelled a reproduction.
- **Matched training failed three times before passing.** A cuDNN TF32 reference mismatch, then a
  post-training batch-partition failure, then a per-epoch canary failure localized to a single
  `output_projection` element. F-v4 passed only after a pre-outcome amendment reclassified that raw
  tensor check as diagnostic while keeping every score/feature/recurrent check hard.
- **The first labeled run of the current experiment died on a path bug** after completing all stream
  extraction but before any estimation, and — because labels had already been joined — was
  quarantined rather than patched and resumed. The recovery route (reporting patch → cache integrity
  audit → continuation gate → independent recovered auditor) is itself a reviewed chain of seals.

The pattern is deliberate: **implementation validity is treated as a separate layer from the
scientific hypothesis**, and a failure in that layer never counts as evidence for or against H1/H2/H3.

## 6. What is currently unresolved

- **Whether contaminated adaptation actually harms anything.** The controlled single-update route
  found no effect reaching the practical margin; the natural-SMD counterfactual was never run. Both
  "harmful" and "harmless" are unsupported.
- **Whether internal state carries information at all** (H2) and whether any such information is
  architecture-specific (H3a) — the question currently under test.
- **Paper-versus-release lineage of the CANDI baseline.**
- **Everything about mechanism.** No adaptation policy has been implemented, so nothing is known
  about delay, rollback or consolidation in this project's own hands.

## 7. What experiment is running now

The labeled H2/H3a probe (Phase G1), executing as the single authorized recovered continuation from
an integrity-audited cache, under an execution seal that pins the repository `HEAD`. Its result files
(`g1_results.json`, `g1_statistics.json`, `g1_decision.json`) become authoritative **only** after the
run completes *and* the independent recovered post-run audit passes. Until then H2/H3a have no truth
value in any document.

Two practical consequences while it runs: do not commit on that checkout (the post-run audit requires
`HEAD` to equal the execution seal), and do not read partial outputs — progress logs and caches are
operational artifacts, not scientific outcomes.

## 8. What may currently be claimed

The full tiering is in `claim_map.md`. In brief — **may** claim: that a released adaptive TSAD
baseline demonstrably commits true anomaly windows across seeds; that a controlled single-update
contamination did not reach a pre-registered harm margin (with its low-sensitivity caveat); that a
matched xLSTM/LSTM pair was trained under one verified contract; that the original xLSTMAD submission
implementation is invalid for internal-state observation.

**May not** claim: that xLSTM is a better detector; that internal state can decide when to adapt;
that gate values have drift semantics; that delay decontaminates; that adaptation is harmful or
harmless; that synthetic results transfer to deployment; or that TSB-drift constitutes cross-dataset
validation.

## 9. Likely next branches

From `future_decision_tree.md`, the branches that matter most regardless of the current outcome:

1. **Resolve the H1 lock.** Delayed-evidence value (H4a) is blocked behind an *unexecuted* natural-SMD
   counterfactual, not behind a negative finding. Either run it, run a pre-registered multi-step
   controlled version, or amend the lock on explicit design grounds.
2. **Get one real-data foothold.** Semi-synthetic injection into verified-normal real prefixes is the
   cheapest defensible route to any real-data claim, and it tests every synthetic conclusion.
3. **If internal-state information exists, localize its mechanism before extending it** — gate versus
   memory versus hidden family, rolling-width decomposition, and a fit-quality confound check, since
   the two backbones are parameter-matched but not reconstruction-quality-matched.
4. **If it does not, move from features to temporal evidence or to explicit new-normal modelling**
   rather than to another feature schema.

---

## Reading order for a new researcher

1. `reports/m0_protocol.md` — the frozen protocol and its decision rules.
2. `research/experiment_lineage.md` — how the project got here, and what each gate unlocked.
3. `research/claim_map.md` — what may and may not be said today.
4. `research/protocol_provenance.md` — which artifact determines what, and which choices predate
   outcome access.
5. `research/related_work_map.md` + `research/positioning_table.md` — where this sits in the
   literature and what would remain novel.
6. `research/g1_outcome_branches.md` and `research/future_decision_tree.md` — what happens next under
   each outcome.
7. `research/safe_adaptation_design_space.md` — the design space for the eventual mechanism, and the
   parts of it that are already known under other names.
