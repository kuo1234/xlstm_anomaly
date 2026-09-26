# Stage-1A protocol and futility audit

**Scope:** static review of the frozen amendment, machine selection artifacts, committed result, and commit history at AUDITED_M1_SHA.

## Verdict

The train-only selection algorithm and recorded nine-machine futility decision match the amendment. The result is not confirmatory. At AUDITED_M1_SHA there is no committed Stage1B-R execution record or score seal; the feasibility note self-reports that it preceded model execution. This audit did not inspect live/untracked runtime outputs. The claimed global non-exposure of the other 19 labels is unsupported because an earlier committed manifest inventories labels for all 28; see data_leakage_audit.md.

## Machine selection

The amendment selects nearest 25th, 50th, and 75th percentile ranks within each of the three groups, ordered by train rows then machine name, with a deterministic collision rule. It excludes labels, anomaly properties, and detector outcomes. Evidence: research/adaptive_normality_m1_smd/stage1a_futility_amendment.md:7-11.

The Stage-1A code recomputes selection from train_rows and cross-checks the committed machine list. Evidence: scripts/adaptive_normality_m1_stage1a.py:77-97. The nine selected machine IDs/ranks in the JSON match the amendment: research/adaptive_normality_m1_smd/stage1a_machines.json.

This demonstrates the selection function is train-row based. It does not demonstrate the broader M1 preparation process was blind to labels, since the all-machine descriptive label inventory predates the amendment.

## Frozen screen and futility decision

The amendment freezes the Stage-1A arms, excludes R from this nine-machine screen, retains the existing split/transform/context/seed/batch/optimizer/epoch cap, fixes q=.99/higher calibration, and defines STOP only when both routes have mean delta <= 0 and at most 3/9 positive deltas. Evidence: research/adaptive_normality_m1_smd/stage1a_futility_amendment.md:13-21.

The committed futility_gate.json reports standalone mean delta +0.0293071741 with 3 positive machines, and complement mean delta -0.0191779527 with 4 positive machines. Under the frozen conjunction, neither route is futile; CONTINUE_TO_STAGE1B is mechanically correct. The artifact records stage1b_started=false and LSTM diagnostic as not affecting the decision; this is the artifact’s claim, not an independent runtime trace.

## No post-result method edit found

Commit history places the pre-label score seal at bcdd348e and metric result at 2792b1e. The diff adds only the gate, access log, and result artifacts. The diff from that result to AUDITED_M1_SHA adds a feasibility note and Stage1B-R implementation/tests; the frozen M1 protocol, baseline specification, Stage-1A amendment, and machine list are unchanged.

The feasibility note says standalone xLSTMAD-F cannot pass two already-frozen full-cohort FPR conditions because three of nine observed machines exceed 5%, while the minimum possible macro FPR across 28 still exceeds 2%. It says the complement route remains under the original gate. Evidence: research/adaptive_normality_m1_smd/stage1b_gate_feasibility.md:3-34. This is a result-derived feasibility conclusion that may guide resource use, but the tracked protocol did not change. R and fusion were predeclared controls; the note adds no threshold or detector.

## Label-boundary caveat

The self-reported access log identifies nine machines and says other_19_unopened=true. Scope this to the Stage-1A post-seal evaluator. The initial committed dataset manifest reports parsed test-label inventories for all 28 before this screen amendment. Therefore the Stage-1A results cover only the selected nine; the log claims zero metric reads before the pre-label seal and nine after it; the project cannot claim the other 19 were globally never opened; and exact historical file-open counts cannot be independently verified from committed application logs.
