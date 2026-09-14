"""Seal the prospective G0.1 CANDI-control amendment.

This script is deliberately pre-outcome.  It reads only the already sealed
Phase-D backbone manifest and the existing G0 protocol artifacts.  It does
not load observations, evaluator truth, score arrays, labels, or model
outputs, and it does not run a detector.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "phase_g"
PHASE_D = ROOT / "reports" / "phase_d"
CONFIG_PATH = ROOT / "configs" / "phase_g.json"
SCHEMA_PATH = REPORT / "schema_binding.json"
PROSPECTIVE_PATH = REPORT / "prospective.md"

BASE_G0_COMMIT = "ddb8e3c"
OFFICIAL_CANDI_COMMIT = "28c9679e503832f59e351208cde63657fcb51cad"
PHASE_D_MANIFEST = PHASE_D / "synthetic_backbone_manifest.json"
SEEDS = (11, 22, 33, 44, 55)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         allow_nan=False).encode()
    return hashlib.sha256(payload).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def selected_controls(manifest: dict) -> list[dict]:
    assert manifest["prospective_commit"] == "9018e86"
    rows = {int(row["detector_seed"]): row for row in manifest["rows"]}
    assert set(rows) == set(SEEDS)
    selected = []
    for seed in SEEDS:
        row = rows[seed]
        assert row["authorized_test_sources_used"] is False
        assert row["preprocessing"]["train_seeds"] == list(range(1000, 1010))
        assert row["preprocessing"]["validation_seeds"] == list(range(2000, 2005))
        assert row["preprocessing"]["fit_interval"] == [0, 4096]
        assert row["preprocessing"]["calibration_interval"] == [4096, 5120]
        assert row["resolved_config"].count("WIN_SIZE: 10") == 1
        assert row["resolved_config"].count("N_VAR: 8") == 1
        artifacts = {}
        for relative, expected in sorted(row["artifacts"].items()):
            path = ROOT / relative
            assert path.exists(), relative
            actual = sha(path)
            assert actual == expected, (relative, actual, expected)
            artifacts[relative] = {"sha256": actual, "bytes": path.stat().st_size}
        preprocessing = row["preprocessing"]
        selected.append({
            "detector_seed": seed,
            "pre_intervention": f"data/phase_d/backbone_{seed}/pre_intervention.pth",
            "checkpoint": f"data/phase_d/backbone_{seed}/checkpoint_best.pth",
            "calibration": f"data/phase_d/backbone_{seed}/calibration_scores.npy",
            "artifacts": artifacts,
            "backbone_tensor_sha256": row["backbone_tensor_sha256"],
            "sana_in_sha256": row["sana_in_sha256"],
            "sana_out_sha256": row["sana_out_sha256"],
            "optimizer_sha256": row["optimizer_sha256"],
            "rng_sha256": row["rng_sha256"],
            "threshold": row["threshold"],
            "preprocessing": preprocessing,
            "preprocessing_object_sha256": canonical_hash(preprocessing),
            "score_semantics": (
                "official MLPAdapter.get_anomaly_scores reconstruction MSE "
                "after frozen SANA-in/out; no adaptation"
            ),
            "official_candi_commit": OFFICIAL_CANDI_COMMIT,
            "native_window": 10,
            "dimension": 8,
            "test_or_truth_access": False,
        })
    return selected


def amendment_manifest(selected: list[dict]) -> dict:
    return {
        "status": "SEALED_PROSPECTIVE_PENDING_PREFLIGHT",
        "amendment": "G0.1",
        "base_g0_commit": BASE_G0_COMMIT,
        "phase_d_manifest": str(PHASE_D_MANIFEST.relative_to(ROOT)),
        "phase_d_manifest_sha256": sha(PHASE_D_MANIFEST),
        "phase_d_backbone_prospective_commit": "9018e86",
        "official_candi_commit": OFFICIAL_CANDI_COMMIT,
        "control_family": "Phase-D D=8 synthetic seed-wise CANDI controls",
        "seed_mapping": {
            str(row["detector_seed"]): row["pre_intervention"]
            for row in selected
        },
        "controls": selected,
        "operator": {
            "model": "official CANDI MLP with frozen pre_intervention model/SANA state",
            "score": "MLPAdapter.get_anomaly_scores",
            "adaptation": False,
            "optimizer_steps": False,
            "fpm_candidate_selection": False,
            "labels_or_truth_to_extractor": False,
        },
        "alignment": {
            "common_track_first_timestamp": 63,
            "common_track_timestamp_rule": "right edge t",
            "xlstm_lstm_window": "raw[t-63:t+1]",
            "candi_window": "raw[t-9:t+1]",
            "candi_window_length": 10,
            "stride": 1,
            "pre_common_scores_forbidden": True,
            "history_source": "CANDI scores only at t >= 63",
            "history_columns": 14,
            "rolling_widths": [4, 8, 16, 32],
            "warmup": "NaN for incomplete history; no padding or imputation",
        },
        "paired_reuse": {
            "history_vector_once_per_key": True,
            "reused_arms": [
                "CANDI_history14 + xLSTM_internal234",
                "CANDI_history14 + LSTM_internal234",
            ],
            "row_key": ["detector_seed", "source_seed", "scenario",
                        "condition", "timestamp"],
            "keys_byte_identical": True,
        },
        "excluded_controls": {
            "SMD_native_phase_c": (
                "excluded before outcomes: SMD/domain and W10 native artifacts "
                "cannot form D8 synthetic source-paired H3a controls"
            ),
        },
        "selection_basis": (
            "External protocol resolution made before Phase-G labels/AP/results: "
            "D8 synthetic Phase-D controls match the Phase-G source family and "
            "provide deterministic detector-seed pairing; native W10 is retained."
        ),
        "labels_read": False,
        "probe_results_read": False,
        "metrics_computed": False,
    }


def update_protocol_files(control_manifest: dict, manifest_file_sha256: str) -> None:
    config = json.loads(CONFIG_PATH.read_text())
    assert config["protocol_status"] in ("SEALED_PROSPECTIVE", "SEALED_PROSPECTIVE_AMENDMENT")
    config["protocol_status"] = "SEALED_PROSPECTIVE_AMENDMENT"
    config["g0_status"] = "PENDING_CANDI_PREFLIGHT"
    config["g0_base_commit"] = BASE_G0_COMMIT
    config["candi_history_control"].update({
        "resolution_status": "RESOLVED_PROSPECTIVE_PENDING_PREFLIGHT",
        "stop_rule": "G0.1 resolves the control before labels; CANDI alignment preflight remains mandatory",
        "selected_control": "D8_synthetic_seedwise",
        "selected_manifest": "reports/phase_g/candi_control_manifest.json",
        "official_candi_commit": OFFICIAL_CANDI_COMMIT,
        "seed_mapping": control_manifest["seed_mapping"],
        "window_alignment": control_manifest["alignment"],
        "paired_reuse": control_manifest["paired_reuse"],
        "excluded_controls": control_manifest["excluded_controls"],
        "canonical_seedwise_interpretation_not_selected": False,
        "reason": control_manifest["selection_basis"],
    })
    config["g0_stop_boundary"].update({
        "unresolved_candi_control_stops_before_labels": False,
        "candi_alignment_preflight_required": True,
        "pending_until_candi_preflight": True,
        "no_outcome_based_choice": True,
    })
    config["g01_amendment"] = {
        "manifest": "reports/phase_g/candi_control_manifest.json",
        "manifest_sha256": manifest_file_sha256,
        "manifest_canonical_sha256": canonical_hash(control_manifest),
        "status": "prospective; no labels/results read",
    }
    write_json(CONFIG_PATH, config)

    schema = json.loads(SCHEMA_PATH.read_text())
    assert schema["status"] in (
        "SEALED_WITH_CANDI_CONTROL_UNRESOLVED",
        "SEALED_WITH_CANDI_CONTROL_RESOLVED_PENDING_PREFLIGHT",
    )
    schema["status"] = "SEALED_WITH_CANDI_CONTROL_RESOLVED_PENDING_PREFLIGHT"
    schema["g0_status"] = "PENDING_CANDI_PREFLIGHT"
    schema["g0_base_commit"] = BASE_G0_COMMIT
    schema["candi_control_manifest"] = "reports/phase_g/candi_control_manifest.json"
    schema["candi_control_manifest_sha256"] = manifest_file_sha256
    schema["candi_history_control"].update({
        "resolution_status": "RESOLVED_PROSPECTIVE_PENDING_PREFLIGHT",
        "selected_control": "D8_synthetic_seedwise",
        "selected_manifest": "reports/phase_g/candi_control_manifest.json",
        "official_candi_commit": OFFICIAL_CANDI_COMMIT,
        "seed_mapping": control_manifest["seed_mapping"],
        "window_alignment": control_manifest["alignment"],
        "paired_reuse": control_manifest["paired_reuse"],
        "excluded_controls": control_manifest["excluded_controls"],
        "canonical_seedwise_interpretation_not_selected": False,
        "reason": control_manifest["selection_basis"],
    })
    write_json(SCHEMA_PATH, schema)

    amendment = """

## G0.1 prospective CANDI-control amendment

The external protocol resolution supersedes the earlier unresolved-control
paragraph above, before any Phase-G labels, feature extraction, scaler fitting,
classifier fitting, or metric computation. The shared H3a-C history control is
the existing Phase-D D=8 synthetic CANDI family, paired by detector seed:

| detector seed | frozen pre-intervention state |
|---:|---|
| 11 | `data/phase_d/backbone_11/pre_intervention.pth` |
| 22 | `data/phase_d/backbone_22/pre_intervention.pth` |
| 33 | `data/phase_d/backbone_33/pre_intervention.pth` |
| 44 | `data/phase_d/backbone_44/pre_intervention.pth` |
| 55 | `data/phase_d/backbone_55/pre_intervention.pth` |

These are the official CANDI commit
`28c9679e503832f59e351208cde63657fcb51cad` with frozen pre-intervention
MLP/SANA states, no adaptation, no optimizer step, no FPM selection, and no
truth access. The native CANDI window remains W=10; it is not retrained or
converted to W=64. At each shared right-edge timestamp `t >= 63`, xLSTM/LSTM
consume `raw[t-63:t+1]` and CANDI consumes `raw[t-9:t+1]`. Only CANDI scores
at those common timestamps enter the 14-column causal history; all earlier
scores are forbidden and incomplete rolling histories remain NaN warmup.

The exact mapping, Phase-D manifest hash, preprocessing/scaler values and
derived preprocessing hashes are sealed in
[`candi_control_manifest.json`](candi_control_manifest.json). SMD/Phase-C
native controls are explicitly excluded because they are domain/dimension
mismatched for the D=8 synthetic source-paired track. The amendment status is
`PENDING_CANDI_PREFLIGHT`; G0 becomes PASS only if the original ten-backbone
preflight remains PASS and the alignment preflight passes.
"""
    existing = PROSPECTIVE_PATH.read_text()
    marker = "## G0.1 prospective CANDI-control amendment"
    if marker not in existing:
        PROSPECTIVE_PATH.write_text(existing.rstrip() + amendment)


def main() -> None:
    prior = json.loads(CONFIG_PATH.read_text())
    assert prior["version"] == "phase_g0_v1"
    manifest = json.loads(PHASE_D_MANIFEST.read_text())
    selected = selected_controls(manifest)
    control_manifest = amendment_manifest(selected)
    write_json(REPORT / "candi_control_manifest.json", control_manifest)
    manifest_file_sha256 = sha(REPORT / "candi_control_manifest.json")
    update_protocol_files(control_manifest, manifest_file_sha256)
    write_json(REPORT / "g01_amendment_seal.json", {
        "status": "SEALED_PROSPECTIVE_PENDING_PREFLIGHT",
        "amendment_manifest": "reports/phase_g/candi_control_manifest.json",
        "amendment_manifest_sha256": manifest_file_sha256,
        "amendment_manifest_canonical_sha256": canonical_hash(control_manifest),
        "base_g0_commit": BASE_G0_COMMIT,
        "labels_read": False,
        "probe_results_read": False,
        "metrics_computed": False,
    })
    print(json.dumps({
        "status": control_manifest["status"],
        "seed_mapping": control_manifest["seed_mapping"],
        "manifest": "reports/phase_g/candi_control_manifest.json",
    }))


if __name__ == "__main__":
    main()
