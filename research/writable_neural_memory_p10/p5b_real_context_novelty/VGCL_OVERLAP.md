# Validation-Gated CL — strong overlap, bounded resolution

[Publisher](https://www.sciencedirect.com/science/article/pii/S0094576526005187), DOI10.1016/j.actaastro.2026.07.065. Full article request403; introduction/problem/strategy/experiment previews read through web search. Official [code pin636ac059](https://github.com/DerKuhno/validation-gated-continual-learning/tree/636ac05995f52d3a12b6c7186646757a28c900eb) reacquired and statically read, all six advertised rehearsal strategies and finetuning. No execution.

Publisher explicitly targets one nonstationary satellite stream, no pre-existing new-condition data, episodic updates and validation before deployment; framework model-agnostic. Broad unknown-condition adaptation and validate-before-deploy are unavailable as novelty. Its characterization of ConCord remains competing authors' evidence.

## Required matrix

Paths below mean pinned upstream src/.

| Question | Verified answer | Boundary / evidence |
|---|---|---|
| New operating condition without prior data? |Yes, declared setting; stream buffering in code |Not certification of every unknown-regime detector or non-oracle clean selection |
| Update data selection? |Chronological buffered first positions; scheduled experience batches; remove nonzero supplied flags; rehearsal/AL retain examples |Main_loop.py131–144; dataset_manager.py146–214. Not stable-fault legitimacy |
| Labels/flags used? |**Yes in inspected native ESA loop.** Target columns >0 OR to test flag; dataset returns tensor; update filtering consumes it |esaadb_dataset.py238–283; dataset.py176–208. Not merely final metric labels. No feedback receipt contract here |
| Rare nominal treatment? |Positive labels filtered too. Official ESA enum Rare Event=2; test combines >0 |If prepared columns retain encoded values, rare nominal joins excluded pool. Clean coverage of new rare regimes not demonstrated |
| Validation source? |Initial train-derived validation plus accumulated flag-filtered stream segments; split index from pre-filter length |dataset_manager.py146–225. Validation mutates before training; not independent health/authority evidence |
| Accept/reject? |Initial model checkpoint; improvement in validation loss replaces checkpoint; final load selects weights |Six rehearsal strategies plus finetuning. Default fixed_epochs=False, delta=.0003. Configurable fixed-epoch path saves final weights instead |
| Rollback scope? |Model state_dict restored |Initial/best selection; not exact full transaction |
| Model vs optimizer/buffer/scaler? |Weights/registered module buffers included; optimizer and dataset/replay/validation outside saved object |Manager extends validation first and replay afterward regardless selected checkpoint. Train-derived scaler; no adaptive scaler recovery proven or needed there |
| Explicit regime admission? |No normative persistent-reference eligibility object established |Scheduled update is not certified regime decision |
| Formal commit? |Selected model deployed, partial overlap |No immutable eligible payload/reference lineage/full-state commit boundary established |
| Commands for legitimacy? |Default inputs/targets numeric channel subsets; override possible |experiment_config.py9–15,157–184. No command authority/receipt gate inspected |
| Indefinite abstention? |No improvement may retain old weights while buffers still change |Not unresolved WAIT preserving all state; no identical-(X,C) guarantee |
| Benign vs stable fault? |Annotation filtering assists clean update; validation measures fit |Fit is not proof of permitted healthy operation; label availability at deployment UNKNOWN |

## State boundary evidence

CL_methods/continual_learning_manager.py78–91 extends dataset before training and clears staging;97–229 trains current self.model;236–242 adds processed data to replay without accepted/rejected transaction. CL_methods/utils.py7–31 averages validation-step loss. dataset_manager.py173 computes split before filtering; reported, not fixed.

BaseModel inherits torch.nn.Module; TelemanomModel holds Adam as an optimizer attribute, with no state_dict override in inspected classes (reused pinned files in provenance/reused_sources.json). Checkpoint/restores inspected: AGEM135–174, GEM170–209, MIR133–172, ER90–129, DER87–126, SER89–128, FINETUNING72–111. All save model.state_dict and load it; fixed-epoch branches also read. LOWER_BOUND/UPPER_BOUND have different loops and are not used to assert this initial-weight guarantee.

**Validation-gated deployment overlaps heavily with containment; it does not establish legitimacy admission by itself.** Inspected code gives a concrete state-boundary mismatch and label-assisted update contract. It does not prove a P5 transactional implementation would be research novelty rather than engineering. Full-paper feedback assumptions and experimental configurations remain UNKNOWN.

Later comparison, if authorized, needs same information/arrival budget, native label-assisted vs non-oracle tracks, and weight-selection metrics separate from formal reference commit. No modified baseline constructed.
