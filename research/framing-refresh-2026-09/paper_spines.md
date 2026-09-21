# Paper spines — evaluation

Four candidate spines, scored against the current evidence (`evidence_red_team.md` §0) and the
refreshed prior art (`direct_prior_art.md`).

## Summary

| spine | novelty strength | evidence completeness | prior-art threat | missing experiment | venue-level strength |
|---|---|---|---|---|---|
| **A. Recurrent internal-state evidence** | **medium** — construct occupied (MD-RS, CANDI, iADCPS), *measurement* unoccupied | **60%** — L1a confirmatory, L1b exploratory, L1c missing | **medium** | temporally matched observable control (+ input arm), then a bounded nonlinear probe on both arms | workshop / mid-tier now; strong mid-tier with E1+E2; top-tier only with a real dataset |
| **B. xLSTM hybrid-state** | low-medium — empty literature, but an empty literature nobody is reading | **20%** — one seed, no dimension control, no residual control, replayed state | low | three-seed replication *with* random-feature dimension control and O1 residual control | weak; an ablation section, not a paper |
| **C. Safe continual normality adaptation** | **low** — every primitive published; two full instantiations on simple detectors and one on a GRU autoencoder | **0%** | **high** | essentially all of it: harm baseline, label-free rule, cost model, paired comparison | not viable now |
| **D. Evidence + adaptation** | medium-high if both halves land | **30%** (A's half only) | medium-high | A completed, then C's intervention | the target; 12–18 months away at the current rate |

**Recommendation: pursue A. Demote B to an ablation subsection of A. Defer C and D.**

---

## A. Recurrent internal-state evidence paper

*"Observable residuals are insufficient under matched low-capacity probes; recurrent internal
dynamics provide complementary anomaly-vs-drift evidence."*

**Novelty.** The defensible sentence is narrower than the one above, and the word that has to
change is *insufficient*. What the project can own is the estimand and the protocol: frozen
detectors (so adaptation cannot confound the estimate), evaluator-side per-timestamp truth about
which changes are legitimate, an observable control ladder, a pre-registered practical margin, and
a reportable null — which the project demonstrated by reporting H3a STOP. No retrieved work poses
the drift-vs-anomaly question as an incremental-information measurement.

**Evidence.** L1a is confirmatory and replicated across two architectures and eight backbones-seeds.
L1b is a real exploratory result with 30/30 positive source×seed units per backbone. L1c does not
exist, and L1c is what the title sentence asserts.

**Prior-art threat: medium.** MD-RS is the precedent for the construct and must be cited as such in
the introduction, not buried. CANDI/COMET/M2N2/MemStream are baselines, not related work. The
distinguishing move is to say plainly: *these methods use internal quantities as gates and validate
them downstream; we measure the quantity they assume.*

**Missing experiment.** E1 (temporally matched observable control) is mandatory — without it the
title claim is not supported by the protocol. E2 (bounded nonlinear probe, both arms) is required
by a careful reviewer and is second in line.

**Venue.** With E1 and E2 positive: a solid methods contribution at a mid-tier data-mining or
time-series venue, or a strong workshop paper at a top-tier one. Synthetic-only caps it there; the
cap is honest and should be stated in the abstract rather than defended in rebuttal.

**Failure mode to plan for.** If E1 kills the increment, spine A does not die — it inverts into a
publishable negative: *"a widely assumed internal-state advantage for drift-vs-anomaly evidence
disappears once the observable control is matched on temporal span."* That is a useful paper and it
is cheap to write, because the protocol is already frozen.

---

## B. xLSTM hybrid-state paper

*"Common recurrent evidence is generic, but mLSTM adds additional complementary state information."*

**First half: supported in a narrower form, and worth saying.** The supportable version is
"replicated in both xLSTM and a capacity-matched LSTM — not xLSTM-specific within the two tested
recurrent backbones"; *generic across recurrent architectures* is not supportable on two backbones.
In that narrower form it is a clean, replicated, slightly counter-intuitive result (H3a STOP plus the matched-LSTM reconstruction at `+0.142966`,
50/50 units) that most of this literature never bothers to test.

**Second half: not supportable today.** `M_full|H+S = +0.016657` on one seed, against a 234-column
dimension increase, with no random-feature control, no residual control, and a state that the
observer *replays from zero state* because the native implementation exposes no `C`/`n`/`m` history.
The study's own dimension-matched contrast is `+0.002034`. And matrix memory `C` — the only
architecturally distinctive component — is `−0.000592` unconditionally and `+0.006610`
conditionally.

**Prior-art threat: low**, and that is not good news. An empty literature (two papers, neither on
internals) means no reviewer has a prior stake in the question. A small unreplicated effect in an
unpopulated corner is a hard sell.

**Verdict.** Not a spine. The first half belongs in spine A as the architecture-generality result;
the second half belongs in spine A's appendix as an ablation, if and only if the three-seed
replication clears its two missing controls.

---

## C. Safe continual normality adaptation paper

*"Internal-state evidence drives selective adaptation."*

**Not viable, and the gap widened during this refresh.** There is no adaptation mechanism in the
repository, no demonstrated harm to improve on (H1 natural harm `NOT_RUN`; D-v2's single controlled
step is below the `0.02` margin at c ≤ 20%), and no label-free decision rule. Meanwhile the
published field now contains a safety-gated, drift-aware, controlled-online-adaptation framework on
a GRU autoencoder in a CPS benchmark (`10.1109/icaiset66439.2026.11541767`), a dynamic normal model
with pattern deactivation (AnDri), drift-type-conditioned replay (ADA-ADF), risk-aware TTA under
normality shift (RTTAD), and an online drift/anomaly separator with its own benchmark (SCALE).

Writing this paper now would mean entering a crowded mechanism space with no mechanism.

---

## D. Evidence + adaptation paper

*Measurement contribution plus selective/deferred intervention contribution.*

The right long-term target and the only one that reaches a top venue. It requires spine A finished
(E1 + E2), a harm baseline that does not yet exist, and an intervention that does not yet exist.
Attempting it before A closes would make both halves weaker: the measurement would be reported as a
motivation section rather than a result, and the intervention would be evaluated against no
established harm.

---

## OUTPUT 3 — paper position

**Strongest defensible current contribution**

> A controlled measurement of how much anomaly-versus-legitimate-drift information a frozen
> recurrent detector's internal summaries carry beyond its own score history and beyond a rich
> within-window reconstruction-residual description — including the negative finding that the
> effect is not xLSTM-specific, with a capacity-matched LSTM showing an equal or larger increment.

**Strongest plausible future contribution**

> Contamination-harm accounting for normality adaptation: the causal cost of admitting a true
> anomaly into a normality buffer, measured against a pre-specified margin with separate exposure
> denominators, and the internal-state evidence that would be needed to reduce it. Still zero
> retrieved records measure this, and it survives a null on the measurement claim.

**One-sentence novelty statement**

> We measure, rather than assume, how much drift-versus-anomaly evidence a frozen recurrent
> detector's internal state carries beyond its own residual, and find the effect large, replicated
> in both xLSTM and a capacity-matched LSTM, and substantially reducible by stronger observable
> controls.

**Top 3 reviewer attacks**

1. *"Your internal arm gets a 13x multi-scale causal rolling expansion and your residual arms get
   none, so you have measured temporal context, not internal state."* — Currently unanswerable. See
   `evidence_red_team.md` §1a and the scenario strata, which are consistent with exactly this.
2. *"A gradient-boosted tree on your 128 engineered residual statistics would close the gap."* —
   Partly conceded already: the engineered O1 beats the raw 1024-column O2 by ≈0.035 AP under the
   same linear probe, so the probe, not the information, is doing part of the work.
3. *"MD-RS showed recurrent state beats prediction error on the same model in 2023, and CANDI
   already gates adaptation on a latent criterion. What is new?"* — Answerable, but only if the
   paper leads with the measurement contract rather than the construct.

**Three claims we must NOT make**

1. "Observable residuals are insufficient" / "under matched observable controls" — the controls are
   not matched on temporal span and contain no observations (`E10`, `E11`).
2. "xLSTM internal state is more informative / more robust to residual controls" — the increment
   gap tracks a `0.033339` weaker xLSTM observable baseline, and the absolute ceiling favours the
   matched LSTM (`0.946744` vs `0.937717`) (`E12`).
3. "The mLSTM layer contributes a complementary state channel" — one seed, no dimension control, no
   residual control, and a state replayed from zero rather than read from the trained forward pass
   (`E13`).

---

## 5. Safe-adaptation differentiation — what a real contribution would need

Assessed against CANDI, M2N2, COMET, MemStream, METER, HTM+SPRT, martingale gating, AnDri, ADA-ADF,
RTTAD and the safety-gated CPS framework.

| candidate primitive | status in the refreshed literature | verdict for the project |
|---|---|---|
| **Internal-state-conditioned update permission** | **Occupied, densely.** CANDI (latent Mahalanobis + score), COMET (codebook activation), M2N2 (self-predicted-label loss mask), MemStream (score-gated memory writes), EATA (entropy), safety-gated CPS ("high-confidence adaptation region"), SCALE (SLR routing). | Cannot be the contribution. Must appear as a baseline family. |
| **Explicit DEFER / quarantine state** | **Occupied as a construct.** METER, HTM+SPRT, Quilt, verification-latency active learning, RL pending-transition buffer, drift-aware online dynamic learning (cooldown). | Only what deferral *buys* can be new — and the pre-G1 protocol's own observation still holds: for a fixed cohort that is eventually fully committed, FIFO delay cannot change the contamination fraction. A quarantine without a rejecting exit rule is a latency change. |
| **Delayed commitment** | **Occupied.** METER accumulate-then-commit; martingale skip/sustain actions. | Same as above. |
| **Contamination-aware evidence accumulation** | **Weakly occupied.** No retrieved method accumulates evidence *about contamination itself*; EPHAD works post-hoc on an already-contaminated model, from the opposite direction. | **Genuinely open.** This is the strongest remaining mechanism slot. |
| **Learned-normality rollback** (reverse one commitment, keep the others) | **Now occupied.** AnDri activates, deactivates and adds normal patterns; STAD revisits previously seen states. The CTTA reset family still only reverts toward a fixed source model, but the *normality-level* operation exists. | **Withdraw.** This was the pre-G1 map's cleanest gap and it is no longer one. Only its accounting is open. |
| **Bounded-risk update policy** | **Partly occupied.** Bounded-movement machinery exists (Fisher weighting, stochastic restore, orthogonal-subspace LoRA), but no retrieved TSAD work derives an update budget from an explicit cost asymmetry between absorbing an anomaly and delaying a legitimate adaptation. | **Open**, and cheap — it is a modelling decision, not an experiment. Still the highest-value unoccupied move identified in the pre-G1 design space. |
| **Calibrated adaptation confidence** | **Open, and now demonstrably hard.** `arXiv:2608.30502` measured the canonical route — a conformal test martingale over a deployed detector's own score stream — and reports 135/135 clean-stream fires at α = 0.05 on real data (≤1/60 on exchangeable synthetic), with the gated filter amplifying the transient it was meant to suppress. | **Open**, and now the most scientifically interesting of the three, because the obvious answer has a published failure. |

**Conclusion.** A differentiated safe-adaptation contribution would have to be built from the three
surviving slots — contamination-aware evidence accumulation, a cost-derived bounded-risk update
policy, and calibrated adaptation confidence that survives non-exchangeable streams — and **not**
from admission control, deferral, or rollback. All three are accounting-and-calibration
contributions rather than mechanism contributions, which is consistent with where the project's
actual comparative advantage lies: it is unusually good at protocol, freezing, denominators and
reportable nulls, and that is what those three slots reward.
