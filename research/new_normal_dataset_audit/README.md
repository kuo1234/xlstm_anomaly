# Benign new-normal dataset audit

Audit date: 2026-09-26
Repository issue: [#2](https://github.com/kuo1234/xlstm_anomaly/issues/2)
Audit branch: research/new-normal-dataset-audit
Audit base: origin/main at 537fc7d4a15ae603f285c3511b80ce0c0eba3e99
Active M1 worktree observed at audit start: research/adaptive-normality-m1-smd, 2eda60d024d2a9149d62de5161ca76916a085942

## Decision

SEMANTIC_M6_DATA_PARTIALLY_AVAILABLE

Several public or documented datasets contain useful pieces of the target question. The strongest real-data lead is the 2026 drift-aware smart-building dataset, whose row labels distinguish normal operation, author-labeled normal drift, and attack. PreDist separately supplies declared normal-event intervals and reported service-fault records for many substations. The extended Tennessee Eastman Process release provides controlled simulated mode changes and fault scenarios. None is verified to contain, in one released and usable stream, all of: independently grounded benign regime-change events, transient anomaly labels, persistent-fault episode identity and duration, A→B→A recurrence labels, aligned operating-command/context truth, and a fixed event-disjoint evaluation split. Thus evidence supports partial availability and dataset-specific follow-up, not an M6 go decision.

## What this audit means by A, B, and C

- **A — semantic new-normal candidate:** source documentation gives an author/operator-grounded label or protocol for a permitted benign operating change and separates it from fault/attack cases. A is a candidate designation, not proof that every M6 annotation requirement is met. Each candidate's missing event-level fields are listed explicitly.
- **B — adaptation/transfer only:** useful variation in normal data, modes, recipes, workloads or fault labels exists, but benign new-normal truth is not independently labeled. These data can study transfer or normal-only adaptation, not answer whether an unlabeled change is benign.
- **C — detector-only for this question:** anomaly detection labels may exist, but a suitable streaming mode/normal-shift evaluation is absent, discrete-run semantics are insufficient, or the source is otherwise not a defensible new-normal benchmark.

Classes describe suitability for this issue, not overall dataset quality. “Known benign” means the source identifies the relevant behavior as intended/allowed, not merely that the measured distribution changes. “Persistent fault” requires a separable fault episode with identity and temporal extent; repeated anomalous rows alone do not establish it.

## Scope and safeguards

This is a metadata, documentation, provenance, and license audit. We did not train or execute a model, use a GPU, download a full dataset, or inspect unopened SMD labels. The only raw-data network probe was an HTTP byte-range request for the first 1,200 bytes of one smart-building CSV to verify its header and cadence. A HEAD request checked the legacy C-MAPSS resource size. No Stage1A/B artifact was opened or modified. The repository's revised M0 protocol remains controlling: no synthetic or observational drift label is promoted to a real benign-shift label, and the fixed same-dataset SMD M4 design is not replaced by an external dataset.

## Files

- [dataset_inventory.md](dataset_inventory.md): dataset-by-dataset technical inventory.
- [semantic_label_audit.md](semantic_label_audit.md): label meaning, event identity, and A/B/C decisions.
- [context_metadata_matrix.md](context_metadata_matrix.md): operating context and metadata coverage.
- [acquisition_status.md](acquisition_status.md): public access, versioning, storage, and checks performed.
- [license_audit.md](license_audit.md): dataset licenses and unresolved reuse terms.
- [recommended_experimental_roles.md](recommended_experimental_roles.md): conditional roles for M6 and normal-only transfer.
- [limitations.md](limitations.md): evidence gaps and stop conditions.
- [sources.md](sources.md): primary sources and claim map.
- [datasets.json](datasets.json): machine-readable inventory, unknowns, and role decisions.

The structured inventory intentionally retains unknowns rather than inferring sample rates, event identities, label semantics, or licenses from familiar dataset names. Source and access facts were checked on 2026-09-26; links and repositories can change.
