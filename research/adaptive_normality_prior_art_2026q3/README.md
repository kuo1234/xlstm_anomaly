# Adaptive normality: prior-art and novelty audit

**Issue:** [#1](https://github.com/kuo1234/xlstm_anomaly/issues/1)
**Research cutoff:** 2026-09-26
**Disposition:** **NOVELTY_REFRAME_REQUIRED**

## Decision in one paragraph

The broad combination “protected recurrent normal-state memory + selective state update + quarantine/candidate regime + controlled promotion/transition” is not novel by component or by a plain conjunction of known components. Online test-time adaptation already gates which observations update a detector; anomaly systems already keep normal reference memories and reject some writes; drift systems already defer uncertain cases, buffer evidence, create candidates, and recover prior patterns or models. The audited evidence did not establish an exact prior TSAD method that combines all of those controls with a persistent recurrent hidden-state bank and an explicit candidate-to-promoted-regime lifecycle. That gap is a possible, narrow contribution, not proof of novelty. The direction should be reframed around a formally specified lifecycle and its contamination-versus-recovery tradeoff, with semantic assumptions made explicit and direct comparisons to the closest systems. The claims that xLSTM is uniquely suitable, hidden state contains information beyond the full observed history, or time-series-only logic can identify benign drift versus a persistent fault should be abandoned as stated.

## Scope and research procedure

This is a literature and claim audit only. It includes online/test-time adaptation, continual learning, memory-based TSAD, concept drift, recurrent/state-space anomaly detection, and nearby continual anomaly detection. It prioritizes primary papers, proceedings, author repositories, and institutional records. The 24 records in papers.json include fully audited papers and clearly marked leads with incomplete access; the count is a source inventory count, not a claim that all 24 are equally close or equally verified.

The audit cutoff is 2026-09-26. Later publication records are excluded even when a preprint was available earlier. For each candidate, the review separates a paper's explicit mechanism from our interpretation. “Not found in the inspected source” is not treated as proof of universal absence. No detector was trained; no GPU job, anomaly experiment, target dataset inspection, or label inspection was performed.

## Required deliverables

- literature_inventory.md — scoped evidence inventory and coverage caveats.
- component_matrix.md — a 20-field mechanism matrix for the closest systems.
- novelty_threats.md — red-team assessment of overlap and residual gap.
- claim_audit.md — six claims with the requested exact statuses.
- closest_competitors.md — strongest direct and cross-domain competitors.
- recommended_positioning.md — defensible contribution framing and minimum evidence.
- abandon_or_continue.md — explicit stop, reframe, and continuation decisions.
- sources.md — source register with evidence level, access notes, and direct links.
- papers.json — machine-readable inventory of the 24 records.

## How to read the conclusion

“No exact conjunction located” means only that the searched and inspected sources did not document the complete proposed lifecycle. It does not establish priority. The novelty case must be rechecked against the current literature before submission, especially recent online AD and drift work. The research gate in reports/m0_protocol.md remains controlling: this report does not authorize a detector change, training, or a larger experiment. Any later empirical work requires its own gate and data manifest.

## Reproduction notes

The evidence register records official or primary-source links and uncertainty. DOI pages, proceedings, preprints, and author repositories were checked as available. For methods where only an abstract or catalog record was accessible, component-level unknowns are preserved as unknown. The source register distinguishes peer-reviewed work, thesis, preprint, and metadata-only lead.
