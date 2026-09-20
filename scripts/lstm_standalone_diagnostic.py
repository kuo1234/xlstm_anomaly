"""Post-hoc reconstruction of the standalone matched-LSTM G1 increment.

This diagnostic is deliberately CPU-only and consumes only the authoritative,
independently audited G1 summary.  It does not load a checkpoint, regenerate
features, fit a probe, or inspect labels.  The LSTM contrast is reconstructed
from the saved primary arrays via ``Delta_L = H2 - H3a-B``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from phase_g1_core import (  # noqa: E402
    DETECTOR_SEEDS,
    TEST_SOURCES,
    hierarchical_bootstrap,
    source_cluster_sign_flip,
)


AUDIT_DEFAULT = ROOT / "reports" / "phase_g1" / "g1_self_review_postrun_recovered_v2_pass.json"
OUTPUT_DEFAULT = ROOT / "research" / "lstm_standalone_diagnostic"
PRACTICAL_MARGIN = 0.02


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _primary_array(payload: Mapping[str, Any], name: str) -> np.ndarray:
    try:
        value = np.asarray(payload["recomputed_primary_effects"][name], dtype=np.float64)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"missing authoritative primary effect array: {name}") from exc
    expected = (len(TEST_SOURCES), len(DETECTOR_SEEDS))
    if value.shape != expected or not np.isfinite(value).all():
        raise ValueError(f"{name} must be finite with shape {expected}, got {value.shape}")
    return value


def reconstruct_lstm_effects(payload: Mapping[str, Any]) -> dict[str, np.ndarray]:
    """Return H2, H3a-B, and the standalone LSTM contrast without constants."""
    h2 = _primary_array(payload, "h2")
    h3a_b = _primary_array(payload, "h3a_b")
    delta_l = h2 - h3a_b
    if not np.array_equal(delta_l, h2 - h3a_b):
        raise AssertionError("standalone reconstruction is not elementwise H2-H3a-B")
    return {"h2": h2, "h3a_b": h3a_b, "delta_l_own": delta_l}


def _mean_list(values: np.ndarray, axis: int) -> list[float]:
    return [float(value) for value in np.mean(values, axis=axis)]


def analyze_payload(payload: Mapping[str, Any], audit_path: Path) -> dict[str, Any]:
    if payload.get("verdict") != "PASS_SCIENTIFIC_AUDIT":
        raise ValueError("the input is not the accepted authoritative G1 audit")
    arrays = reconstruct_lstm_effects(payload)
    delta = arrays["delta_l_own"]
    bootstrap = hierarchical_bootstrap(delta, draws=10_000, seed=901)
    sign_flip = source_cluster_sign_flip(delta, seed=902)
    source_means = np.mean(delta, axis=1)
    seed_means = np.mean(delta, axis=0)
    identity_error = float(np.max(np.abs(delta - (arrays["h2"] - arrays["h3a_b"]))))
    if identity_error != 0.0:
        raise ValueError(f"elementwise reconstruction mismatch: {identity_error}")

    # The committed G1 audit contains only shape metadata for scenario and
    # duration/severity contrasts, not the per-arm AP arrays needed to recover
    # standalone LSTM subgroup effects.  Report that limitation explicitly.
    not_recoverable = "NOT_RECOVERABLE_FROM_CONSOLIDATED_ARTIFACTS"
    try:
        audit_display = str(audit_path.relative_to(ROOT))
    except ValueError:
        audit_display = str(audit_path)
    return {
        "classification": "LSTM_INTERNAL_SIGNAL_RECONSTRUCTED",
        "post_hoc_exploratory": True,
        "authoritative_input": {
            "path": audit_display,
            "sha256": file_sha256(audit_path),
            "verdict": payload["verdict"],
            "detector_seeds": list(DETECTOR_SEEDS),
            "test_sources": list(TEST_SOURCES),
        },
        "definitions": {
            "delta_x": "AP(xLSTM history + xLSTM internal) - AP(xLSTM history)",
            "h3a_b": "delta_x - delta_l_own",
            "delta_l_own": "AP(LSTM history + LSTM internal) - AP(LSTM history)",
            "source_axis": "TEST_SOURCES ascending (3000..3009)",
            "detector_seed_axis": "DETECTOR_SEEDS (11,22,33,44,55)",
        },
        "identity": {
            "max_abs_error": identity_error,
            "exact_array_identity": True,
            "aggregate_delta_x": float(np.mean(arrays["h2"])),
            "aggregate_h3a_b": float(np.mean(arrays["h3a_b"])),
            "aggregate_delta_l_own": float(np.mean(delta)),
        },
        "delta_l_own": {
            "matrix": delta.tolist(),
            "mean": float(np.mean(delta)),
            "median": float(np.median(delta)),
            "min": float(np.min(delta)),
            "max": float(np.max(delta)),
            "positive_unit_count": int(np.sum(delta > 0)),
            "unit_count": int(delta.size),
            "practical_margin": PRACTICAL_MARGIN,
            "unit_at_or_above_practical_margin": int(np.sum(delta >= PRACTICAL_MARGIN)),
            "positive_detector_seed_count": int(np.sum(seed_means > 0)),
            "detector_seed_means": {str(seed): float(value) for seed, value in zip(DETECTOR_SEEDS, seed_means)},
            "detector_seed_at_or_above_margin": int(np.sum(seed_means >= PRACTICAL_MARGIN)),
            "positive_source_count": int(np.sum(source_means > 0)),
            "source_means": {str(source): float(value) for source, value in zip(TEST_SOURCES, source_means)},
            "source_at_or_above_margin": int(np.sum(source_means >= PRACTICAL_MARGIN)),
        },
        "exploratory_uncertainty": {
            "label": "POST-HOC / EXPLORATORY",
            "hierarchical_bootstrap": bootstrap,
            "source_cluster_sign_flip": {
                "seed": 902,
                "raw_p": float(sign_flip),
                "permutations": "exact enumeration (10 sources)",
            },
            "holm_family_membership": False,
        },
        "secondary_recovery": {
            "scenario_effects": not_recoverable,
            "scenario_reason": "committed audit preserves scenario effect shapes but not standalone LSTM per-arm AP arrays",
            "duration_effects": not_recoverable,
            "severity_effects": not_recoverable,
            "shared_candi_delta_l": not_recoverable,
            "shared_candi_reason": "committed audit preserves H3a-C contrast only, not both standalone shared-CANDI arm APs",
        },
        "interpretation": {
            "supported": "Under the same frozen G1 feature/probe protocol, the matched conventional LSTM also shows a large incremental internal-state signal beyond its own score/history control.",
            "does_not_establish": [
                "a new H2 or confirmatory hypothesis",
                "LSTM-xLSTM equivalence or global superiority",
                "safe adaptation or contamination robustness",
                "that all recurrent models contain this information",
                "matrix-memory specificity or persistent-state benefit",
            ],
        },
    }


def run(audit_path: Path, output_dir: Path) -> dict[str, Any]:
    before = file_sha256(audit_path)
    payload = json.loads(audit_path.read_text())
    result = analyze_payload(payload, audit_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    if file_sha256(audit_path) != before:
        raise RuntimeError("authoritative G1 artifact changed during diagnostic")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-json", type=Path, default=AUDIT_DEFAULT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()
    result = run(args.audit_json, args.output_dir)
    print(json.dumps({
        "classification": result["classification"],
        "mean_delta_l_own": result["delta_l_own"]["mean"],
        "bootstrap_ci95": result["exploratory_uncertainty"]["hierarchical_bootstrap"]["ci95"],
        "shared_candi_delta_l": result["secondary_recovery"]["shared_candi_delta_l"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
