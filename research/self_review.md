# Adversarial self-review of this research package

Reviewed: `README.md`, `experiment_lineage.md`, `protocol_provenance.md`, `claim_map.md`,
`g1_outcome_branches.md`, `future_decision_tree.md`, `related_work_map.md`, `positioning_table.md`,
`safe_adaptation_design_space.md`. Findings that required a change were fixed in place; the fix is
named below. Findings that could not be fixed are recorded as residual limitations rather than
silently dropped.

---

## 1. Does anything overstate novelty?

**Yes, in two places — both fixed.**

- `README.md` introduced "Safe Continual Normality Adaptation" as the project's framing without
  saying that the framing is anticipated. Fixed: the section now states that three of the four
  assumed components are published, that two of them already appear combined in a single mechanism on
  simpler detectors, and that the framing itself cannot be the contribution.
- `claim_map.md` tier B described H2/H3a purely as the project's own hypotheses. Fixed: a note now
  records that using an internal quantity as adaptation evidence is the majority practice in the
  retrieved literature (34 of 78 records), that a published method already feeds an internal signal
  into a drift-versus-anomaly decision with a non-commit action, and that the defensible framing is
  therefore the controlled measurement, not the construct.

`safe_adaptation_design_space.md` argued *against* the project's assumed shape from the start, so it
needed only a pointer to the prior-art mapping in §7.

## 2. Is any obvious prior art missing?

**Two known gaps and two out-of-scope areas; none concealed.**

- The closest framing prior art was read at abstract level only, and a 2026 safety-gated
  continual-learning paper for drift-aware anomaly detection was retrieved as metadata only. Both are
  flagged in `positioning_table.md` as required reading before any novelty claim, and the second is
  named as the single largest unquantified novelty risk.
- Adversarial anomaly poisoning and cross-entity/fleet drift evidence were **not** among the 16
  searched families. `safe_adaptation_design_space.md` §7 now says so explicitly, which downgrades my
  own §5.2 suggestion from "an unused evidence axis" to "an axis whose literature status is
  unassessed". This was the single most self-serving claim in the package before review.
- The internal-state gap (F6) rests partly on zero-result keyword queries and on two abstract-only
  readings. Stated as weak evidence of a gap in both `related_work_map.md` and `positioning_table.md`.

## 3. Does anything presume G1 will succeed?

**No.** Checked every forward-looking statement:

- `experiment_lineage.md` ends Phase G with "executing; no adjudicated outcome" and names the audit
  as the precondition for authority.
- `claim_map.md` tier B states that B1–B4 have no truth value in text until the recovered post-run
  audit passes.
- `g1_outcome_branches.md` carries all three outcomes at equal weight and contains no numbers.
- `future_decision_tree.md` opens with two branches in which there is *no* result at all (failed
  audit; failed semantic control), which is the opposite of presuming success.
- No partial output of the running execution was read at any point in producing this package.

## 4. Does anything confuse observational evidence with causal adaptation evidence?

**No, and this is the package's main structural defence** — the L1–L5 ladder in `claim_map.md` §0
separates separability, usability, architecture specificity, delayed-adaptation benefit and
deployment, and names what each level additionally requires. `g1_outcome_branches.md` Case C lists
four independent reasons observational separability does not imply safe adaptation (label supply,
operating point, feedback endogeneity, absent harm baseline). `README.md` §4 states that the probe is
forbidden from controlling adaptation.

One residual risk worth naming: the *feedback endogeneity* argument (once a gate acts, the internal
features it consumes are changed by its own past decisions) appears only in the Case C discussion. It
applies to any mechanism built on this evidence and would be easy to lose when the text is reused.

## 5. Does anything over-interpret gate or memory values?

**No.** `claim_map.md` E3 prohibits semantic readings and states that a positive result is equally
consistent with gate summaries proxying reconstruction-error magnitude or input scale.
`g1_outcome_branches.md` Case C presents five candidate mechanisms explicitly as hypotheses, each with
the test that would localize it, and says that reporting H3a GO without at least one mechanism test
is "reporting a coincidence with a confidence interval".

## 6. Are any proposed experiments unfalsifiable?

**One was underspecified — fixed by reclassification.** Every branch in `future_decision_tree.md` now
carries an explicit falsification criterion for its own next experiment. The weakest item was the
recommendation to write down a cost model (`safe_adaptation_design_space.md` §6, item 2), which is a
modelling decision rather than an experiment; it is presented as such, and §7 notes that it is the
only formalization in §2 with no retrieved TSAD instance.

The genuinely awkward case is Branch L option L3 (amend the H4a lock). Amending a protocol lock is
not falsifiable by construction — it is a design decision. It is labelled as a protocol change that
must be justified on design grounds and committed before any outcome is seen, which is the only
safeguard available.

## 7. Are the decision branches genuinely distinct?

**One taxonomy error — fixed.** "Statistically significant but practically tiny" was listed as B3, a
branch of the H3a-STOP family, but under the frozen margin rule it resolves to STOP under *any*
outcome. It is now X1, an explicitly cross-cutting pattern, and the diagram and summary table were
updated.

The remaining branches are distinct in *interpretation and next action*, which is the relevant test:
A1 (control near-sufficient) versus A2 (both arms near chance) differ in whether the next step is a
temporal-evidence experiment or a regime study; A3 (unstable sign) versus A4 (regime-restricted) differ
in whether the problem is variance or scope; B1 (general specificity null) versus B2 (shared-history
member fails alone) differ in whether the finding is architecture-agnostic information or a
score-source artifact. C2 (fit-quality confound) is a discovered condition rather than an outcome
branch and is labelled as such.

## 8. Are there obvious reviewer attacks the package does not anticipate?

**Two were missing — both added** to the shared-objections list in `g1_outcome_branches.md`:

- *"Isn't this an existing admission gate with a different statistic?"* — with the honest answer that
  internal-quantity admission control is published TSAD practice and that only the measurement and
  the accounting can be the contribution.
- *"Why average precision rather than a range- or volume-based measure?"* — with the answer that AP
  was pre-registered, that every confirmatory member is a *difference* in AP between arms on
  identical windows, and that the project uses no point adjustment and no test-tuned thresholds,
  while noting that its own Phase B report lists VUS-PR as not implemented.

Attacks the package anticipates but cannot answer: synthetic-only external validity; the
non-identifiable region built into the generator by design; overlapping-window dependence (answered
structurally, not empirically); and the limited power of a five-seed specificity test.

---

## Residual limitations of this package

1. **Coverage is bounded by one literature sweep.** 78 records, 61 full texts; 17 records read at
   abstract or metadata level; full text unobtainable for seven works; attribute extraction read
   roughly the first 55–60k characters per paper, and 23 of 61 extractions were truncated (14
   recovered by direct keyword reading, 9 partially populated). Every `?` in
   `positioning_table.md` means "not retrieved", never "no".
2. **Two areas were never searched** (adversarial poisoning; cross-entity/fleet evidence), so nothing
   in this package establishes novelty there.
3. **One repository citation could not be resolved.** The external drift benchmark named in the
   protocol did not resolve to a drift-benchmark publication under that name. The A2 files themselves
   are real and hashed in the repository, so this is a citation question — but it must be settled at
   source before publication.
4. **No G1 result is reflected anywhere**, by design. When the recovered post-run audit passes, the
   branch skeletons in `g1_outcome_branches.md` should be instantiated against the adjudicated
   decision, and `claim_map.md` tiers B/C updated — those are the only two files that need to change.
5. **This review is a self-review.** It was performed by the same agent that wrote the documents,
   with the repository reports and the retrieved literature as the only external checks. It is not a
   substitute for the project's own adversarial review process.
