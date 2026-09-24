# R0 execution red-team

Outcome under review: execution stopped fail-closed at a checkpoint parity gate. The question is whether anything
done so far is a protocol violation, and whether the stop was applied correctly.

| check | finding | status |
|---|---|---|
| Protocol HEAD unchanged | `research/real-data-r0-protocol` still `d7708586`; protocol, config, library, preflight and tests byte-identical on the execution branch (only run records and these documents added) | OK |
| All three machines retained | Yes; the stop occurred on machine-2-1 and applies to R0 as a whole; no machine was dropped, added or reordered | OK |
| 18 planned fits executed unless fail-closed | 6 of 18 trained; 12 not started because the protocol-defined stop occurred | OK (fail-closed) |
| No test labels before feature-cache sealing | No stage that reads labels ran; every train/extract record has `labels_read: false`; runner tests assert `load_test_labels` is absent from train/extract/schedule/seal code | OK |
| Checkpoint parity for every detector | 5/6 PASS; 1 FAIL → R0 stopped; the failing checkpoint was not replaced and the gate was not re-run or relaxed | OK (stop applied) |
| Probe boundaries / embargo 96 | Not reached; unchanged in the sealed library | OK |
| HGB selection on validation only; probe-test labels after prediction | Not reached | n/a |
| No weak detector removed | Detector sanity not reached; nothing removed | OK |
| No near-constant channel repaired | Sealed scaler used unchanged (zero-std channels recorded in every train record) | OK |
| Bootstrap matches sealed code | Not reached; runner calls the sealed functions (tested) | n/a |
| Wording matches claim_boundary.md | No outcome wording issued; the stop is not described as null, positive or negative | OK |
| No zero-shot / TTA / HAI code | None added (runner test scans for these terms); no zero-shot branch or protocol created; HAI not acquired | OK |
| Concurrency | At most two detector processes at any time; schedule stopped launching new units at the first failure | OK |
| Post-stop diagnostic | One result-blind diagnostic on the failed checkpoint (canary + fit windows, no labels, no test data); it informs the owner only and changes no record or rule | OK (disclosed) |
| Git chronology | Runner pushed before training; each unit committed and pushed on completion; nothing merged to `main`; protocol branch not deleted | OK |

No result-affecting violation occurred (`R0_PROTOCOL_VIOLATION` does not apply). Status: **`R0_EXECUTION_BLOCKED`**
pending an owner decision (see `execution.md`, "Owner decision required").
