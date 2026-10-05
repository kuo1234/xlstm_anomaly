# Issue #23 — M0-S controlled history-staleness falsification

**Pre-result protocol freeze. Experiments are authorized only after Commit A is pushed and its remote SHA verified.**

This study tests whether incompatible remote history harms a frozen one-step recurrent forecaster after recent observations are identical, despite both stationary regimes being represented during training. It compares xLSTM and matched LSTM, complete carry/oracle reset and fixed-L replay. No deployable controller or novelty claim follows.

- [PROTOCOL.md](PROTOCOL.md): authority, predeclared support/effect/context/AD gates, seeds and exact execution.
- [GENERATOR.md](GENERATOR.md): three stationary D8 VAR mechanisms, five process groups per mechanism, paired suffix and independent split seeds.
- [MODEL_CONTRACT.md](MODEL_CONTRACT.md): encoder-only forecasting, parameter/update matching, full state and scoring clock.
- [METRICS.md](METRICS.md): physical-group units, curves, censoring and AD metrics.
- [configs/protocol.json](configs/protocol.json), [scripts](scripts/), [tests/test_contract.py](tests/test_contract.py): executable frozen definitions.

90 stationary training runs (15 group/mechanism units ×2 backbones ×3 seeds). Same A/B training support, observation sequence resets, validation-only selection and frozen train scaler. Support gates precede incompatible inference; AD is conditionally executed only after valid forecasting mechanism evidence. Any protocol fault stops and requires amendment; difficulty/configuration cannot change after outcomes.

All original M0/E2/F/H3b and M0-E files remain historical evidence. This independently authorized track begins at Issue #22 audit commit `cdcb8f2`. Issue #23 has a GO in its task body and no task comments at initial retrieval; the user's explicit request authorizes completion and experiments. Raw checkpoints/generated arrays remain under ignored data; tracked outputs will include results, hashes and gate records in Commit B. Completion requires both remote-verified SHAs, Issue summary and STOP for reviewer.
