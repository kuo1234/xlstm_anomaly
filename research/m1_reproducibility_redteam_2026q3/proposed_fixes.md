# Proposed fixes

These are recommendations only. This audit did not alter M1 source code, data, labels, model settings, gates, or experiment outputs.

## Before making confirmatory claims

1. Correct the label-access wording. Replace unqualified “other 19 unopened” with the scoped statement that the committed Stage-1A log claims only the selected nine were read by its post-seal metric pass. Disclose that an earlier committed data audit parsed and summarized labels for all 28.
2. Treat the nine Stage-1A machines as development/exposure-visible for claims requiring labels to have remained unavailable throughout preparation. Do not describe all 19 others as untouched. Any new confirmatory cohort or label-blind claim requires an approved prospective protocol and an actually unexposed evidence source; this audit does not authorize opening further labels.
3. Preserve the frozen M1 thresholds, arms, seed, and gates. Do not use this finding as permission to tune the experiment or run Stage1B.

## Bind execution to source bytes

4. Make Stage-1A fail closed when the working tree is dirty, including untracked Python modules, or record a canonical source-tree manifest covering every loaded module and relevant configuration. Validate source blob hashes against the execution seal rather than checking only that HEAD is an ancestor of the pre-label commit.
5. Record interpreter, package lock/environment, device/backend, deterministic settings, and exact loaded module file paths/hashes in each run record. Make metrics validation check them.

## Make repository-root APIs unambiguous

6. Thread explicit repo/root through Stage-1A helpers, selection loading, artifact paths, resume validation, and sealing. Avoid module-global ROOT when a public repo argument is supported; alternatively remove the custom repo argument and reject a mismatch.
7. For Stage1B-R, bind execution to source imported from the supplied root, or assert that every imported module’s __file__ resolves inside that root and bytes match its recorded commit. Add an explicit failure for a cross-checkout module/repo mismatch.

## Coordinate concurrent runs

8. Add a lock per immutable experiment/output root, with machine-level claims and clear stale-lock handling. Keep immutable create-if-absent writes as a second defense. Record lock owner, process ID, host, start time, and run key; never recover a stale lock by overwriting artifacts.
9. Document that retries after a partial run require preserving and inspecting the partial directory before manual cleanup. A partial run should remain a hard failure until reconciled against its manifest.

## Close low-severity documentation gaps

10. Record the LSTM width candidate set and deterministic selection rule that yielded width 40, or remove the “nearest configured search range” sentence while preserving the already-frozen 81,838-vs-80,510 capacity result.
11. Describe historical parity evidence as a synthetic one-step forward parity check. Do not generalize it into training parity or an end-to-end reproducibility proof.
12. Continue to label train normality as a dataset convention/assumption, not verified fact.
