# Abandon or continue?

## Decision

**Continue only with a reframed, gated research question. Do not continue the broad novelty story.**

The research direction is not justified as a claim that gated adaptation, protected normality, multiple regimes, quarantine, or xLSTM are individually new. Prior art covers these components and several important combinations. A narrower lifecycle question remains potentially worthwhile because the inspected direct TSAD sources do not establish one complete recurrent-state quarantine → candidate → promotion → old-regime recovery system with explicit contamination and recovery evaluation. This is a limited gap, not a novelty finding.

## Abandon these claims now

- “Existing TSAD does not keep multiple recoverable normal regimes.”
- “xLSTM is uniquely suitable.”
- “Persistent hidden state contains information beyond the complete observable history.”
- “A time-series-only learner can in general identify benign new normality versus persistent anomaly.”
- “No existing method filters or quarantines uncertain observations before adaptation.”
- Any claim that simple gating, memory, protected parameters, or delayed updates are novel by themselves.

## Continue only if all conditions are met

1. The method has a precise state lifecycle, not a renamed score threshold.
2. Confirmed-state protection and candidate writes are structurally separated and auditable.
3. Promotion and reversal behavior are explicit, measurable and bounded.
4. AnDri, METER, CANDI, M2N2, ARCUS, MemStream, and the smart-building drift buffer are addressed in the design and comparator plan.
5. The unresolved SCALE lead and recent relevant records are checked before submission.
6. The study states what contextual assumptions permit semantic drift handling and includes a defer path when they do not.
7. Empirical gates, data manifests, and compute limits follow reports/m0_protocol.md.

## Stop or pivot if

- A direct prior method is found with the same recurrent-state quarantine, promotion and regime reactivation semantics.
- The implementation cannot prevent candidate writes from mutating confirmed states.
- Promotion has no defensible evidence rule without labels or external context.
- Matched baselines show the same contamination/recovery frontier at lower complexity.
- The benefit disappears when representation capacity, history window and adaptation frequency are controlled.

## Authorization boundary

This document records research disposition only. It does not authorize detector changes, anomaly experiments, GPU usage, data/label access, or expansion beyond existing M0 gates.
