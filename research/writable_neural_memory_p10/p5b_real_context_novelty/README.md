# P5-B — ESA real context and novelty qualification

**Final gate: ESA_CONTEXT_INSUFFICIENT. Pending review; STOP.** Issue [#20](https://github.com/kuo1234/xlstm_anomaly/issues/20) authorizes bounded source/method qualification only. P5-A was accepted as CONTROLLED_CONTEXT_ONLY in [review5988610414](https://github.com/kuo1234/xlstm_anomaly/issues/19#issuecomment-5988610414).

ESA's released event metadata does not establish a causal receipt contract or legitimate persistent changed-reference target. This conclusion applies to inspected Mission1/2 metadata and documented schema, not all possible ESA sources. Novelty remains unresolved under substantial prior-art overlap; blocked full methods supply no positive gap evidence. Thus CONTROLLED_ONLY_CONFIRMED, PRIOR_ART_SATURATED and BOTH_BLOCKED are not justified.

- [Context qualification](ESA_CONTEXT_QUALIFICATION.md)
- [Rare-event audit](ESA_RARE_NOMINAL_AUDIT.md): all691 rare-event IDs, not favorable-case selection.
- [VGCL method/code matrix](VGCL_OVERLAP.md) and [ConCord matrix](CONCORD_OVERLAP.md)
- [Nine atomic claims](CLAIM_OVERLAP_MATRIX.md)
- [Gate and reviewer decisions](FINAL_GATE.md)
- [Source inventory](source_inventory.json), [provenance](provenance/README.md), [verification](provenance/verification.json)

All acquisition/inspection occurred on ssh kuo. HTTP Range read367,577 response-body bytes from two official archives, extracting nine small CSV members. No channel/telecommand arrays, complete archive, detector, adaptation, policy, shadow/rollback implementation, Q sweep, or RL. Interval labels are now exposed; no strict confirmatory claim. Raw/source bytes remain ignored on the remote host.
