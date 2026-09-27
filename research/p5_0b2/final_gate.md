# P5-0B2 final gate

**Astra review: PASS.** Terminal status: `P5_0B2R_REFRAME` pending Issue #9
adjudication of the disclosed initial path-metadata read.

The prior P5-0B2 seal is superseded for this result-blind amendment. No
next-stage authorization follows until the Issue #9 path-metadata adjudication
is resolved. This seal does not authorize SOURCE development or TARGET label access,
TARGET scoring, prefix adjudication, suffix evaluation, or efficacy claims.

## Gate checklist

- [x] Base and role-seal hashes pinned; immutable 74/16/3 roles and five
      eligible strata recorded.
- [x] Target start, raw looks, N_max, 64-day cap, zero purge, common suffix
      boundary, raw-count semantics, insufficient-score behavior, and no
      extension frozen.
- [x] Public EnergyFaultDetector code audited at the specified commit and
      paper-cited version; primary generic backbone selected with the version
      mismatch corrected explicitly.
- [x] Source-only grouped fold, support gate, candidate set, fit budget,
      seeds, determinism policy, objective, tie-break, and refit frozen.
- [x] Firewall inputs, row-drop order, canonical output, audit/log boundary,
      interval semantics, failure behavior, and synthetic tests specified.
- [x] Primary prefix class and minimal adjudicator output frozen; no
      adjudication run.
- [x] Readiness grid, source-only margin/parameter selection, threshold
      estimator, state transitions, post-READY freeze, evaluator metrics and
      success logic frozen.
- [x] Canonical sequence is structural seal → method seal → firewall seal →
      SOURCE-only seal → prefix adjudication → target trajectory seal → suffix
      unlock → scoring.
- [x] Exact information allowed in next SOURCE-only development documented,
      including the SOURCE-only raw-path projection boundary.
- [x] Ordered continuous feature projection sealed from common-schema
      metadata; raw union-only/status fields are discarded before strict
      projected-schema validation.
- [x] Fixed TARGET counts `5, 1, 4, 4, 2` recorded. The success denominator
      remains all 16 targets, with no impossible four-evaluable-per-stratum
      condition; unavailable outcomes count as failures.
- [x] Astra review resolved the exact manufacturer-key mismatch, traceback
      leakage, projection contradiction, bootstrap support gate, and strict
      CSV completeness/parser issues.

## Protocol correction

The handoff paired the name “paper-matched v0.3.0” with commit
`ced470e1386066931bad32f3cb6e24bac9c5bb89`. Public repository tags show that
commit is v0.7.1; the paper-cited v0.3.0 is commit
`9e0d65074c88e51e180e3bf37f580280bbb54496` and lacks the PreDist loader and
notebook. This protocol records both versions, selects the v0.7.1 generic
detector components as its exact primary reference, and excludes its
event-specific PreDist loader. No model/data outcome was used to make that
correction.

## Access and verification

This phase read public papers/repository source and committed P5-0B1R
structural metadata. It did not open any operational raw file, semantic label
payload, dataset archive, target value/score, or archive README; did not run
the label firewall; did not train an AE or PreDist model; did not adjudicate
target prefixes; and did not access suffix outcomes. During initial
integration, the inherited validator parsed `raw_path` strings from
`entity_manifest.csv` for its unique-path check but did not use them to open
operational files. The final B2R validator no longer opens that path-bearing
manifest and compares only its committed digest token. This path-metadata
access is disclosed for GPT adjudication in Issue #9.

Verification already run against synthetic data and committed structural
metadata only:

- `python3 -m unittest research.p5_0b2.tests.test_source_label_firewall -v` —
  19 firewall tests passed.
- `python3 -m research.p5_0b2.scripts.validate_protocol` — passed.
- `python3 -m unittest research.p5_0b2.tests.test_source_label_firewall research.p5_0b2.tests.test_protocol_invariants -v` —
  all 28 tests passed.
- `git diff --check` — passed.

The validator verified the immutable role counts, five eligible SOURCE
strata, pinned P5-0B1R structural digest values, live hashes of permitted
role/schema artifacts, fixed acquisition schedule, canonical phase order,
and artifact hash manifest. Path-bearing manifest contents are not opened by
the final validator. Artifact hashes are in `protocol_seal.json`.

## Next authorized stage

No next stage is authorized pending Issue #9 adjudication of the disclosed
path-metadata read. Keep `TARGET_LABEL_ACCESS=NOT_AUTHORIZED`; P5-0B3 remains
closed until a subsequent Issue comment explicitly opens it.
