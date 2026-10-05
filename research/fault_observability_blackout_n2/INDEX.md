# N2 final evidence index

Main finding: **FAULT_SELECTIVE_BLACKOUT_REPLICATED** under the frozen causal19-feature/full-history contract. Five prospectively controlled events across4 apps lose39–50percentage points of scoring opportunity, while15 fixed pre-controls lose0 extra targets.

- [Results and figure](RESULTS.md)
- [Research decision](RESEARCH_DECISION.md)
- [Prior-art/novelty boundary](PRIOR_ART.md)
- [Completion audit](COMPLETION_AUDIT.md)
- [Independent verification](provenance/verification.json)
- [Actual reference eligibility parity](provenance/reference_eligibility_parity.json)
- [Deterministic scientific replay](provenance/replay.json)
- [Frozen protocol](configs/protocol.json)

Cached-evidence verification from repository root:

```sh
/tmp/m0e-issue22/venv/bin/python research/fault_observability_blackout_n2/scripts/check_results.py
/tmp/m0e-issue22/venv/bin/python research/fault_observability_blackout_n2/scripts/check_reference_parity.py
```

`acquire.py` restores exact public raw/prepared inputs. `execute.py` intentionally requires a verified execution seal at the remote branch before new analysis; after result delivery, another execution requires an appropriate new authorized seal. The scientific replay was already performed before results were pushed. Raw/mask/article assets remain ignored, with hashes tracked. Numerical verification is independent code by the same agent; external scientific review is still welcome and not implied.
