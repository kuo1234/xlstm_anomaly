# G1 outcome branches — discussion skeletons

Three pre-written skeletons, one per adjudicated outcome. They exist so that the interpretation is
chosen before the number is known, which is the only way a negative result stays publishable and a
positive one stays honest.

**No numbers appear in this file, and no branch is treated as more likely than another.** At the
time of writing the recovered G1 continuation is still executing; `g1_results.json`,
`g1_statistics.json` and `g1_decision.json` become authoritative only after the run completes *and*
the independent recovered post-run audit passes.

A reminder that applies to all three branches: the four confirmatory members compare **probe**
average precision on the task "window contains an anomaly" versus "anomaly-free window inside an
early transition or active gradual drift", using features from *frozen* detectors. No member
measures the detectors' own anomaly-detection performance.

---

## Shared reviewer objections (all branches)

These arrive regardless of outcome and should be answered in the paper's limitations, not in a
rebuttal:

1. **"This is confidence estimation with extra steps."** The history control is built from the
   reconstruction score and its rolling statistics, so a gain from internal features must be shown
   to be more than a better-conditioned version of the same uncertainty signal. The project's answer
   is structural (equal column budgets, equal rolling widths, one shared frozen CANDI history arm),
   not empirical, and that should be stated plainly.
2. **"Synthetic streams are not evidence."** D=8 stable VAR with five scenario families is a
   controlled identifiability instrument, not a realism claim. The protocol already forbids calling
   TSB-drift results cross-dataset validation and declares real drift-vs-anomaly truth unavailable.
3. **"The task is partly non-identifiable by construction."** The generator deliberately includes
   identical-observation/opposite-semantic pairs and legitimate excursions with matched
   perturbations and matching durations. Any reported AP therefore sits above an irreducible Bayes
   error floor that the design created on purpose. This weakens absolute numbers and strengthens
   *relative* comparisons — which is why every member is a difference, not a level.
4. **"Windows are not independent replicates."** Stride-1 windows overlap; the protocol answers with
   source-realization macro units, hierarchical bootstrap resampling sources before detector seeds,
   source-cluster sign-flips, and a 96-observation purge for any temporal split.
5. **"An offline supervised probe says nothing about an online decision."** Correct, and the project
   should say so first: the probe receives evaluator labels in fitting, has no operating point, no
   latency budget and no cost asymmetry, and is forbidden from controlling adaptation.
6. **"Isn't this an existing admission gate with a different statistic?"** Internal-quantity admission
   control for a normality buffer is published TSAD practice (latent-distance curation,
   codebook-activation evidence, score-masked updating, threshold-gated memory), and a conformal
   test martingale on a filter's own innovation already feeds a drift-versus-anomaly decision with an
   explicit skip action. The answer cannot be "we introduce internal state as evidence"; it has to be
   the controlled measurement and the accounting. See `positioning_table.md`.
7. **"Why AP rather than a range- or volume-based measure?"** The TSAD evaluation literature has moved
   toward range-based precision/recall and VUS-family measures, and the project's own Phase B report
   lists VUS-PR as not implemented. The honest answer is that AP was pre-registered as the primary
   metric and that every confirmatory member is a *difference* in AP between arms on identical
   windows, which is insensitive to the level-inflation the critique targets — and that the project
   does not use point adjustment, does not tune thresholds on test data, and reports trapezoidal
   PR-AUC separately and only for baseline reproduction.

---

## Case A — H2 = STOP

### What is actually established

That *under this frozen schema, probe, metric and stream*, window-local internal summaries do not
add ≥0.02 AP over a 14-column score/history control with the required consistency and robustness.
Nothing more. In particular this is not a statement that xLSTM internals are uninformative, nor that
no internal-state representation could work.

### Diagnosis before interpretation

An H2 STOP has at least five distinguishable causes, and the run's own pre-registered descriptive
outputs (not post-hoc rescue analyses) can separate most of them. The interpretation differs sharply
by cause, so the discussion must name which pattern was observed:

| Pattern in the frozen outputs | Reading | Implication |
|---|---|---|
| History control already high; combined arm similar | **Redundancy / near-sufficiency.** The reconstruction score and its causal history are close to a sufficient statistic for this task in this regime. | The interesting question moves from "which features" to "what evidence exists at all beyond the score" — i.e. toward delayed evidence (H4a-style) rather than richer instantaneous features. |
| Both arms near chance | **Weak identifiability in this observation regime.** The drift/anomaly distinction is largely not decidable from a 64-step window at these severities. | Re-examine the regime (window length, severities, drift rates) before re-examining features. A features paper is not the right paper. |
| Pooled gain present but sign inconsistent across seeds/scenarios | **Unstable information.** Whatever signal exists is not reproducible under the frozen reproducibility rule. | Variance reduction and a stability-first design; do not chase the scenario where it worked. |
| Pooled gain reaches margin but duration/severity macro fails | **Regime-restricted gain.** Information concentrated in a subset of event durations or severities. | A pre-registered restriction of the claim to that regime is a legitimate *new* hypothesis; it may not be reported as H2 GO. |
| Strata return `INSUFFICIENT_SUPPORT` | **Underpowered subgroups**, not absence of effect. | Power/design problem: more test sources or a coarser pre-registered stratification in a future amendment. |

### Strongest defensible claim

"On a controlled non-stationary multivariate stream with evaluator-side truth, a capacity-matched
internal-state feature schema extracted from a frozen xLSTM reconstruction detector did not improve
drift-versus-anomaly discrimination beyond a causal score/history control, under a pre-registered
confirmatory test with practical, confidence, multiplicity, reproducibility and robustness gates."

### Prohibited claims

- "xLSTM internal dynamics contain no information about drift versus anomaly." (Tested one schema,
  one pooling rule, one window length, one probe family.)
- "Internal states are useless for adaptation decisions." (Never tested — see the L1→L2 gap in
  `claim_map.md`.)
- "Drift and anomaly are indistinguishable." (The design contains a non-identifiable region by
  construction; a negative result on the remainder is not a general impossibility result.)
- Any promotion of a descriptive per-family ablation (hidden/gate/memory) that happened to look
  positive.

### Why the negative result is still worth publishing

Three reasons, in decreasing order of strength:

1. **It constrains a live hypothesis in the literature.** "Recurrent internals as drift evidence" is
   an appealing intuition that is asserted more often than tested with a matched control; a
   pre-registered null with an explicit power/robustness account is a contribution.
2. **The measuring instrument is reusable.** A verified causal evaluator, a Lyapunov-verified
   correlation-only shift, a 4/13-attribute capacity-matched internal schema, and an execution
   protocol with stable-ID contamination accounting outlive the negative result.
3. **It redirects the field's attention to the harder question.** If instantaneous internal evidence
   adds nothing, the remaining candidates are *temporal* evidence (wait and see) and *structural*
   evidence (compare against an explicit model of the new normal) — both cheaper to test than a new
   architecture.

### What the project should stop doing

- Stop building features from window-local internal state; stop the H3a/H3b branch entirely
  (H3a is not interpretable without H2, H3b is locked behind H3a).
- Stop treating architecture choice as the lever; nothing in an H2 STOP implicates xLSTM specifically.

### Surviving alternative hypotheses (each needs a fresh pre-registered amendment)

- **Delayed evidence.** Does waiting K windows add information that no instantaneous feature has?
  This is H4a's question and it is backbone-independent by design — but note it is currently locked
  behind unresolved H1 harm, which is a protocol dependency the project should revisit rather than
  route around.
- **Longer state horizon.** Would cross-window carried state (the H3b construction) help where
  window-local summaries did not? Currently gated on H3a; an H2 STOP makes that gate itself
  questionable, since carry is a different information question, not a specificity question.
- **Explicit new-normal modelling.** Does maintaining a candidate "new normal" representation and
  scoring against *both* it and the incumbent normal separate the classes better than any
  single-model internal summary?

### STOP criteria for the branch

Abandon the internal-state line if, after a pre-registered follow-up in the same regime (e.g. longer
horizon or delayed evidence), the gain over the score/history control again fails the practical
margin with adequate stratum support. Two independent nulls with adequate power are a result, not a
reason for a third schema.

---

## Case B — H2 = GO, H3a = STOP

### What is actually established

Recurrent internal state carries incremental drift-versus-anomaly information beyond the
score/history control — and that information is **not** demonstrably architecture-specific under the
matched schema. The natural reading: the contribution is *model-agnostic recurrent-state evidence*,
and the matched LSTM is a sufficient carrier.

Note which sub-members failed, because they mean different things:

- **A fails, B/C pass** — level difference absent but incremental structure differs; weak and
  fragile, and per protocol H3a as a whole is STOP.
- **B/C fail** — the incremental gain over history is not larger for xLSTM; the cleanest
  architecture-agnostic reading.
- **C fails alone** — when both arms share one frozen CANDI history, the apparent advantage
  disappears, i.e. the earlier gap was a *score-source* artifact rather than a backbone property.
  This is the most informative single failure in the whole family and deserves its own paragraph.

### Strongest defensible claim

"Window-local recurrent internal summaries add pre-registered, reproducible drift-versus-anomaly
information beyond a matched causal score/history control, and this information is obtainable from a
conventional LSTM of matched capacity; we find no evidence that it is specific to xLSTM gating or
memory under an equal-column, equal-pooling schema."

### Prohibited claims

- "xLSTM is not better." (Failure to reject under one matched schema is not equivalence; state it as
  no evidence of specificity, with the power caveat.)
- "Any recurrent model will do." (Two architectures were compared, both reconstruction-trained under
  one contract.)
- "Internal state can gate adaptation." (Still L2.)

### Reviewer objections specific to this branch

1. **"Then why recurrent at all?"** The comparison lacks a non-recurrent control. A reviewer will
   ask whether a feed-forward or classical statistical model's residual structure would supply the
   same information — and the current design cannot answer it.
2. **"Your matched LSTM pools six layers while xLSTM pools four scalar cells."** The pooling rule is
   an honest pre-registered choice, but it is a structural asymmetry, and a null on specificity is
   exactly where that asymmetry gets attacked.
3. **"Is the gain just error magnitude?"** If the internal summaries are largely monotone in
   reconstruction error, the "internal-state" framing is decoration on a score feature.
4. **"Underpowered specificity test."** Five detector seeds and ten test sources give a limited
   ability to detect a small architecture difference; the paper should report the detectable effect
   size rather than implying equivalence.

### Next experiments (in priority order)

1. **Minimal sufficient internal summary.** Which of the 18 base columns carry the gain? A
   pre-registered nested comparison (not a post-hoc winner) tells whether the effect is a handful of
   scale/uncertainty statistics or genuinely distributed.
2. **Non-recurrent control arm.** Add an explicitly matched non-recurrent carrier (e.g. residual
   statistics from a window-local model with no recurrent state) to test whether "recurrent" is
   load-bearing at all.
3. **Error-magnitude confound test.** Pre-register a partialling analysis: does the internal gain
   survive conditioning on a richer *score-only* feature family with the same column budget? This
   must be designed as its own hypothesis, because widening the control after the fact would
   retroactively weaken H2.
4. **Detector-agnostic replication.** Repeat the incremental test with internals from a third
   reconstruction detector to check the claim is about recurrent state rather than about xLSTMAD's
   particular readout.

### Research redirection

The project's title changes: from "xLSTM internal dynamics as drift evidence" to "recurrent-state
evidence for selective normality updating". That is a *better* direction in one respect — a
model-agnostic mechanism is more deployable and more citable than an architecture-specific one — and
worse in another: it removes the architectural novelty and puts the work directly next to the
existing selective-adaptation and uncertainty-guided-adaptation literature, where the bar is a
mechanism with a demonstrated safety/utility trade-off rather than an information result.

### STOP criteria

Stop the xLSTM-specific line immediately (H3b is locked by protocol anyway). Stop the
model-agnostic line if the minimal-summary and error-magnitude analyses together show the gain is
explained by score-derived quantities available without any internal access.

---

## Case C — H2 = GO and H3a = GO

### What may legitimately be called "xLSTM-specific"

Only this: under an equal column count, equal rolling-window budget, equal pooling rule, equal probe
family and C grid, and a capacity match within −2.33% of trainable parameters, the scalar-cell
summaries of *this* xLSTM implementation carried more of *this* drift-versus-anomaly information than
the matched LSTM's recurrent summaries — including when both arms share one frozen CANDI history
control. Everything outside that sentence is extrapolation.

### Plausible mechanisms (hypotheses, not conclusions)

Each is a candidate explanation and each implies a different follow-up test:

| Mechanism | Why it could produce the result | How to test it |
|---|---|---|
| **Exponential gating with a stabilizer state.** sLSTM's input/forget gates are exponential with a running stabilizer `m`; the effective-gate summaries may therefore encode a scale-normalized "surprise" that a sigmoid-gated LSTM compresses. | The gate-family columns would carry most of the gain, and the stabilizer-related statistics would be the discriminative ones. | Pre-registered nested test of the gate family versus hidden/memory families; a fixed-`m` ablation. |
| **Explicit normalizer state.** sLSTM maintains a normalizer `n` alongside cell state `c`; a ratio-like readout can separate "larger inputs" from "differently distributed inputs". | Memory-family columns (`c`, `n` summaries) carry the gain; the effect survives conditioning on error magnitude. | Add a pre-registered arm using only `c`/`n` ratios; test against the error-magnitude control. |
| **Different effective time constants.** Gate dynamics change the decay profile of the internal trace, so the same rolling widths summarize a different history length. | The gain would concentrate at the longer rolling widths (16, 32). | Pre-registered per-width decomposition; equalize effective horizon rather than column count. |
| **Fit-quality confound.** The two backbones trained under one contract need not reach equal reconstruction quality; a better-fitting model can produce more informative residual internals for reasons unrelated to gating. | The gain correlates with the training/validation reconstruction gap between arms. | Report both models' validation reconstruction curves; consider a fit-matched (rather than parameter-matched) comparison as a separate hypothesis. |
| **Numerical scale interacting with standardization.** Internal magnitudes differ across architectures; per-statistic standardization on probe-train may not equalize their conditioning for an L2-regularized logistic probe. | The gain would shrink under a different regularization strength or feature transform. | Sensitivity analysis over the C grid and an alternative scaling, reported descriptively. |

A paper that reports H3a GO without at least one of these mechanism tests is reporting a
coincidence with a confidence interval.

### Strongest defensible claim

"On a controlled non-stationary multivariate stream, frozen xLSTM scalar-cell internal summaries
carry pre-registered, reproducible incremental information for distinguishing anomaly windows from
anomaly-free drift, beyond a causal score/history control and beyond a capacity-matched LSTM's
recurrent summaries — including under a shared frozen external history control. The result is an
information-content finding on synthetic streams; it does not establish that this information can be
used safely, online, or without labels."

### Prohibited claims

- "xLSTM is the right architecture for continual anomaly detection." (No adaptation was run, and no
  detection-performance comparison is in the family.)
- "Gate values indicate drift." (Statistical summaries; semantics untested.)
- "This enables safe adaptation." (L2/L5 — neither is touched.)
- Any statement that H3b is expected to pass, before it is run.

### What H3b must establish, and what it cannot

H3b asks a *different* question: whether carrying recurrent state across chunks adds information
relative to independent per-window resets, for the same frozen weights and the same input/history
budget, on synthetic data with no optimizer updates and carry only within a source stream. It must
show a ≥0.02 gain with CI > 0, ≥4/5 seeds, ≥3/4 shifted scenarios and duration-matched support. It
cannot show that persistent state is *safe* to adapt on, and it must not be compared against
overlapping-window replay, which would double-consume observations.

### Why observational separability still does not prove safe adaptation

Four independent gaps, each of which can kill the deployment claim on its own:

1. **Label supply.** The probe is fit with evaluator labels. An online mechanism has none.
2. **Operating point.** Separability is a ranking property (AP); an adaptation decision needs a
   threshold with an explicit cost asymmetry between absorbing an anomaly and delaying a legitimate
   new normal. That cost model does not exist in the project yet.
3. **Feedback.** The probe observes a *frozen* detector. Once adaptation acts on the detector, the
   internal features become endogenous — the very signal the gate consumes is changed by the gate's
   own past decisions. Nothing in an offline probe bounds that loop.
4. **Harm baseline.** `H1_harm_overall` is UNRESOLVED. A mechanism that prevents contamination has
   no demonstrated harm to prevent, so its value would have to be argued on a stream where harm is
   first established.

### The intervention that would be needed before any deployment relevance

A pre-registered online experiment with: no label access in the decision path; a gate calibrated on
the frozen clean prefix only; a fixed update budget; paired comparison against always-adapt and
never-adapt arms on identical streams and identical committed-window budgets; contamination measured
with stable IDs over candidate / admitted / committed / gradient-exposed denominators; and both
sides of the trade-off reported (post-shift false-positive recovery *and* missed-anomaly cost),
with latency censoring made explicit.

### STOP criteria

Stop the mechanism branch if that intervention shows no improvement in the safety/utility frontier
at a fixed update budget, or if the mechanism's advantage disappears once the gate's own feedback is
included. Stop the xLSTM-specific framing if the mechanism tests above localize the gain to a
property any architecture can be given cheaply (e.g. a scale-normalized surprise statistic).

---

## Branch-independent next step

Whatever the outcome, one thing is already decidable and should be decided deliberately rather than
by default: **the H4a lock.** Delayed-evidence value is a backbone-independent question with its own
matched-capacity design, and it is currently gated behind an unresolved H1 harm route that the
project has not run. See `future_decision_tree.md` for the two ways out (run the natural-SMD
counterfactual, or amend the lock with an explicit, pre-registered rationale) — and note that
amending a lock is a protocol change that must be justified on design grounds, never by an outcome.
