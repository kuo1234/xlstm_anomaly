# Phase D — implementation-validity STOP

D0 as an end-to-end gate: **STOP**. The captured real SMD official-operator
replay itself **PASSes bitwise**, but synthetic fresh-process repeat parity fails.
H1-harm: **INCONCLUSIVE / not validly tested**. H1-admission remains GO separately.
This is not a modeling-hypothesis STOP and not evidence of absence of harm.

## Evidence and root cause

Prospective protocol9018e86 was committed/pushed before harm. D0 captured native
SMD_1-8 alpha5 seed0 update1 (242 ordered moderate windows). Native and harness
loss0.20451687276363373, post-model/optimizer/RNG and next256-window scores match
exactly. An independent official dataset reconstruction also confirms buffer
order and fixed score segment. The official checkout remains immutable.

All five D8 backbone/scaler/calibration/SANA/optimizer/RNG states and160 buffer
layouts were committed/pushed (combined manifest3485a61) before the first harm
arm. The first dry preflight failed closed because the combined manifest had
not reached the earlier commit; no arm ran then. After sealing, the dry-run
took2.696s and projected4397.705s (1.22h) conservatively, passing the24h gate.

Engineering failure: the synthetic grid restored random generator states but
did not restore `torch.backends.cudnn.deterministic=True`. Native main and
backbone training call official set_seeds and enable it; a new grid process
defaults to False. Equal checkpoint/RNG states did not guarantee equal execution.
The extra D8 repeat/label-isolation test was run after grid expansion rather than
before it; this ordering was insufficient and must be corrected in a new version.

Unpermuted identical-buffer diagnosis reproduces the failure: identical pre-model,
optimizer and RNG, same loss, but post-tensors/optimizer/scores differ. Maximum
parameter difference 7.45058059692e-09; maximum score difference 2.62260437012e-06.
Thus this is not evidence that evaluator labels affect adaptation. In the bounded
diagnostic ONLY, setting the native cuDNN deterministic flag produced three exact
repeats. No tolerance was widened and the production grid was not repaired/restarted.

## Quarantine and missing results

The grid was terminated with83 complete pairs (498 rows) and one partial pair,
not4800 completed rows. All existing positives/negatives/null outcomes and raw
scores remain retained in rows/, quarantined_partial_results.csv and the local
artifact manifest; none is admissible for confirmatory H1 inference. No qualifying
comparison, hierarchical CI/Holm test or valid contamination-performance curve is
reported. An empty qualifying list means NOT EVALUATED, not a negative result.
Do not combine these rows with any corrected rerun or retain only convenient arms.

## Minimal proposed correction (requires review)

1. Version the harness and explicitly pin/assert/capture backend determinism,
   cuDNN benchmark and relevant precision settings alongside model/optimizer/RNG.
2. Run official real parity plus D8 identical-buffer and actual label-permutation
   closure BEFORE any new dry-run/expansion; include both positive and zero-update
   controls. One successful diagnostic is not sufficient full validation.
3. Preserve current quarantine, backbones and protocol. Verify whether sealed
   backbone states/calibration remain reusable under the corrected flags. Reuse
   only after integrity tests; no outcome-based retraining/config changes.
4. Obtain approval, reseal the corrected implementation and rerun the entire grid
   in new paths. Keep all original hypotheses, slots, seeds and statistical gates.

## Runtime and scope

Completed-pair generation/update/evaluation sum: 126.273s;
completed-arm sum: 100.170s. Completed-grid peak
allocated/reserved: 0.170/
0.203GiB (per-process allocator,
not total device peak). Full per-process training/parity/dry/grid/diagnostic wall
times are in logs; overlapping trainings must not be summed as elapsed wall.

Five score-free buffer/metric tests and CPU statistical fixture tests pass.
Original C/Cv2/C3 seals and official code remain unchanged. No natural-SMD harm,
H4a/H4b, xLSTM/LSTM, probes, H3b, rollback or dual memory ran. Return for external
review; the launcher and statistical finalizer now reject execution_stop.json.
