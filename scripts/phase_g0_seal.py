"""Create the prospective, label-blind Phase-G0 seal.

This script only reads already sealed F-v4/E2/Phase-C-D metadata and artifact
bytes.  It never opens synthetic truth, test labels, score-result arrays, or
fits a scaler/classifier.  The generated files are the protocol boundary for
the later labelled probe work.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "phase_g"
F4 = ROOT / "reports" / "phase_f_v4"
PHASE_D = ROOT / "reports" / "phase_d"
PHASE_C = ROOT / "reports" / "phase_c"
E2 = ROOT / "reports" / "phase_e2"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def sorted_unique(values):
    return list(dict.fromkeys(values))


def history_columns() -> list[str]:
    columns = ["score", "score_first_difference"]
    for width in (4, 8, 16, 32):
        columns.extend(
            [
                f"score_trailing_{width}_mean",
                f"score_trailing_{width}_std",
                f"score_trailing_{width}_slope",
            ]
        )
    assert len(columns) == 14
    return columns


def expanded_columns(base: list[str]) -> list[str]:
    result: list[str] = []
    for column in base:
        result.append(column)
        for width in (4, 8, 16, 32):
            result.extend(
                [
                    f"{column}_trailing_{width}_mean",
                    f"{column}_trailing_{width}_std",
                    f"{column}_trailing_{width}_slope",
                ]
            )
    return result


def candi_candidates() -> dict:
    synthetic = json.loads((PHASE_D / "synthetic_backbone_manifest.json").read_text())
    candi_rows = []
    for row in synthetic["rows"]:
        seed = int(row["detector_seed"])
        artifacts = {}
        for relative, expected in sorted(row["artifacts"].items()):
            path = ROOT / relative
            assert path.exists(), relative
            actual = sha(path)
            assert actual == expected, (relative, actual, expected)
            artifacts[relative] = {"sha256": actual, "bytes": path.stat().st_size}
        cfg = row["resolved_config"]
        assert "WIN_SIZE: 10" in cfg and "N_VAR: 8" in cfg
        candi_rows.append(
            {
                "detector_seed": seed,
                "source_family": "phase_d_synthetic_candi_backbone",
                "window": 10,
                "dimension": 8,
                "operator": "MLPAdapter.get_anomaly_scores with frozen pre_intervention SANA state",
                "official_commit": "28c9679e503832f59e351208cde63657fcb51cad",
                "manifest": "reports/phase_d/synthetic_backbone_manifest.json",
                "pre_intervention": f"data/phase_d/backbone_{seed}/pre_intervention.pth",
                "checkpoint": f"data/phase_d/backbone_{seed}/checkpoint_best.pth",
                "calibration": f"data/phase_d/backbone_{seed}/calibration_scores.npy",
                "artifacts": artifacts,
                "score_semantics": "native CANDI reconstruction MSE after frozen SANA-in/out; no adaptation during history extraction",
                "test_or_truth_access": False,
            }
        )

    phase_c_runs = []
    for path in sorted((PHASE_C / "runs").glob("SMD_*_native.json")):
        row = json.loads(path.read_text())
        if row.get("run_type") not in (None, "native"):
            continue
        phase_c_runs.append(
            {
                "run": path.stem,
                "artifact": str(path.relative_to(ROOT)),
                "machine": row.get("machine"),
                "alpha": row.get("alpha"),
                "official_commit": row.get("official_commit", "28c9679e503832f59e351208cde63657fcb51cad"),
                "score_window": 10,
                "source_family": "SMD_native_CANDI",
                "score_result_paths_present": sorted(
                    key for key in row.get("artifacts", {}) if "score" in key.lower()
                ),
            }
        )

    return {
        "resolution_status": "UNRESOLVED_PRELABEL",
        "stop_rule": "G0 stops before labels when more than one plausible frozen CANDI control is not uniquely resolved by the existing M0 text",
        "candidate_sets": {
            "D8_synthetic_seedwise": {
                "count": len(candi_rows),
                "rows": candi_rows,
                "compatibility": "D=8 compatible, but native W=10 rather than common-track W=64; five seed-keyed controls, not one singular stream",
            },
            "SMD_native_phase_c": {
                "count": len(phase_c_runs),
                "rows": phase_c_runs,
                "compatibility": "native CANDI evidence, but SMD dimension/domain and W=10 score artifacts are not a sealed D=8/W=64 synthetic control",
            },
        },
        "canonical_seedwise_interpretation_not_selected": True,
        "reason": "Existing artifacts contain multiple CANDI score/control candidates and no pre-outcome rule choosing a singular stream or resolving W=10-to-W=64 alignment.",
    }


def checkpoint_manifest() -> dict:
    source_path = F4 / "final_manifest.json"
    source = json.loads(source_path.read_text())
    assert source["status"] == "PASS"
    expected = {
        "lstm_11": {"path": "data/phase_f_v3/runs/lstm_11/best.pt", "architecture": "lstm", "seed": 11},
        "lstm_22": {"path": "data/phase_f_v3/runs/lstm_22/best.pt", "architecture": "lstm", "seed": 22},
        "lstm_33": {"path": "data/phase_f_v4/runs/lstm_33/best.pt", "architecture": "lstm", "seed": 33},
        "lstm_44": {"path": "data/phase_f_v4/runs/lstm_44/best.pt", "architecture": "lstm", "seed": 44},
        "lstm_55": {"path": "data/phase_f_v4/runs/lstm_55/best.pt", "architecture": "lstm", "seed": 55},
        "xlstm_11": {"path": "data/phase_f_v4/runs/xlstm_11/best.pt", "architecture": "xlstm", "seed": 11},
        "xlstm_22": {"path": "data/phase_f_v4/runs/xlstm_22/best.pt", "architecture": "xlstm", "seed": 22},
        "xlstm_33": {"path": "data/phase_f_v4/runs/xlstm_33/best.pt", "architecture": "xlstm", "seed": 33},
        "xlstm_44": {"path": "data/phase_f_v4/runs/xlstm_44/best.pt", "architecture": "xlstm", "seed": 44},
        "xlstm_55": {"path": "data/phase_f_v4/runs/xlstm_55/best.pt", "architecture": "xlstm", "seed": 55},
    }
    rows = []
    by_name = {row["run"]: row for row in source["runs"]}
    assert set(expected) == set(by_name)
    for name in sorted(expected):
        row = by_name[name]
        spec = expected[name]
        path = ROOT / spec["path"]
        assert path.exists(), spec["path"]
        assert row["status"] in ("PASS", "CARRIED_FORWARD")
        assert row["architecture"] == spec["architecture"]
        assert int(row["seed"]) == spec["seed"]
        actual_sha = sha(path)
        expected_sha = row["checkpoint_sha256"]["best.pt"]
        assert actual_sha == expected_sha, (name, actual_sha, expected_sha)
        rows.append(
            {
                "run": name,
                "architecture": spec["architecture"],
                "detector_seed": spec["seed"],
                "path": spec["path"],
                "sha256": actual_sha,
                "model_hash": row["best_model_hash"],
                "selected_epoch": row["selected_epoch"],
                "source_status": row["status"],
                "carry_forward_reference": row.get("type") == "carry_forward_reference",
                "best_only": True,
            }
        )
    return {
        "status": "PASS",
        "source_manifest": str(source_path.relative_to(ROOT)),
        "source_manifest_sha256": sha(source_path),
        "f4_commit": "a7fa42ff2c0c339c242167c525c39e8ae49184b1",
        "entries": rows,
        "forbidden_paths": [
            "data/phase_f_v3/runs/lstm_33",
            "data/phase_f_v3/runs/xlstm_11",
            "data/phase_f_v3/runs/lstm_33/epoch29_replay_diagnostic.pt",
            "data/phase_f_v4/runs/*/final.pt when best.pt differs",
            "all F-v1/F-v2 checkpoints",
        ],
        "model_policy": "frozen inference only; no optimizer object or update is permitted",
    }


def main() -> None:
    REPORT.mkdir(parents=True, exist_ok=True)
    ckpt = checkpoint_manifest()
    candi = candi_candidates()
    e2_schema = json.loads((E2 / "schema.json").read_text())
    e2_arch = json.loads((E2 / "architecture.json").read_text())
    base = list(e2_schema["base_columns"])
    expanded = expanded_columns(base)
    assert len(base) == 18 and len(expanded) == 234
    history = history_columns()

    write_json(REPORT / "checkpoint_manifest.json", ckpt)
    write_json(
        REPORT / "schema_binding.json",
        {
            "status": "SEALED_WITH_CANDI_CONTROL_UNRESOLVED",
            "schema_version": "G0-H3a-common18-v1",
            "source_e2_schema": "reports/phase_e2/schema.json",
            "source_e2_schema_sha256": sha(E2 / "schema.json"),
            "causal_track": {"window": 64, "stride": 1, "decision_timestamp": "right_edge", "warmup": 32},
            "history_control": {
                "columns": history,
                "dimension": 14,
                "rolling_widths": [4, 8, 16, 32],
                "statistics": ["mean", "population_std", "OLS_slope"],
                "first_difference": "current_score - immediately_previous_score; first row warmup/undefined",
                "causal_rule": "trailing windows include current decision and never future decisions",
            },
            "internal_base_columns": base,
            "internal_expanded_columns": expanded,
            "dimensions": {"hidden": 52, "gate": 130, "memory": 52, "combined": 234, "history_plus_combined": 248},
            "groups": {
                "hidden": base[:4],
                "gate": base[4:14],
                "memory": base[14:18],
                "combined": expanded,
                "history_plus_combined_order": "history14 followed by internal combined234",
            },
            "xLSTM": {
                "implementation": "improved official xLSTMAD",
                "commit": "e8b56ba27352733bb83729e85b1d6196dca70c99",
                "architecture_sha256": sha(E2 / "architecture.json"),
                "eligible_scalar_cells": e2_schema["scalar_cells"],
                "pooling": "equal heads and equal four scalar cells; no learned pooling",
                "memory": "actual sLSTM c/n",
                "mLSTM_confirmatory_features": False,
            },
            "LSTM": {
                "layers": ["encoder.0", "encoder.1", "encoder.2", "decoder.0", "decoder.1", "decoder.2"],
                "pooling": "equal all six actual layers; no layer selection or fake heads",
                "memory": "c",
                "hidden": "h_t",
                "input_gate": "sigmoid(i_t)",
                "retention_gate": "sigmoid(f_t)",
            },
            "candi_history_control": candi,
            "exploratory_only": ["xLSTM mLSTM matrix/readout summaries", "raw gate logits", "sLSTM stabilizer/n summaries"],
            "labels_extracted": False,
            "scaler_fit": False,
        },
    )
    write_json(
        REPORT / "confirmatory_family.json",
        {
            "status": "SEALED_PROSPECTIVE",
            "family_id": "G0_H2_H3a_combined",
            "familywise_method": "Holm",
            "alpha": 0.05,
            "family_size": 4,
            "members": [
                {
                    "id": "H2_history_increment",
                    "estimand": "AP(xLSTM history+combined248) - AP(xLSTM history14)",
                    "conditional_on": None,
                    "description": "primary additional window-local internal signal",
                },
                {
                    "id": "H3a_A_combined_backbone",
                    "estimand": "AP(xLSTM combined234) - AP(LSTM combined234)",
                    "conditional_on": "H2_history_increment GO",
                    "description": "matched-capacity combined internal features",
                },
                {
                    "id": "H3a_B_incremental_backbone",
                    "estimand": "(AP(xLSTM history+combined)-AP(xLSTM history)) - (AP(LSTM history+combined)-AP(LSTM history))",
                    "conditional_on": "H2_history_increment GO",
                    "description": "incremental gain beyond common history control",
                },
                {
                    "id": "H3a_C_shared_candi_history",
                    "estimand": "same incremental-gain contrast using one shared frozen CANDI 14-column history control",
                    "conditional_on": "H2_history_increment GO and CANDI control uniquely resolved",
                    "description": "score-source separation; unresolved CANDI control blocks this member",
                },
            ],
            "h2_practical_gate": {
                "mean_gain_min": 0.02,
                "paired_ci_lower_gt": 0,
                "positive_detector_seeds_min": 4,
                "positive_shifted_scenarios_min": 3,
                "duration_severity_matched": True,
            },
            "h3a_requires_h2": True,
            "descriptive_not_confirmatory": ["history14", "hidden52", "gate130", "memory52", "combined234 ablations"],
            "labels_read": False,
            "test_ap_computed": False,
        },
    )
    write_json(
        ROOT / "configs" / "phase_g.json",
        {
            "version": "phase_g0_v1",
            "phase": "G0",
            "protocol_status": "SEALED_PROSPECTIVE",
            "f4_seal_commit": "a7fa42ff2c0c339c242167c525c39e8ae49184b1",
            "f4_final_manifest": "reports/phase_f_v4/final_manifest.json",
            "f4_final_manifest_sha256": sha(F4 / "final_manifest.json"),
            "checkpoint_manifest": "reports/phase_g/checkpoint_manifest.json",
            "schema_binding": "reports/phase_g/schema_binding.json",
            "confirmatory_family": "reports/phase_g/confirmatory_family.json",
            "probe_folds": {
                "train": {"generator_seeds": list(range(1000, 1010)), "source_fold": "probe_train"},
                "validation": {"generator_seeds": list(range(2000, 2005)), "source_fold": "probe_validation"},
                "test": {"generator_seeds": list(range(3000, 3010)), "source_fold": "probe_test"},
                "source_fold_separation": True,
                "generator_config": "configs/synthetic_v1.json",
                "generator_config_sha256": sha(ROOT / "configs/synthetic_v1.json"),
                "generator_validation_sha256": sha(ROOT / "reports/generator_validation_v4/SHA256SUMS"),
            },
            "scenarios": {
                "confirmatory_shifted": ["abrupt", "gradual", "recurring", "correlation"],
                "stationary_controls": ["stationary"],
                "conditions": ["none", "spike", "collective", "dependency", "mixture"],
                "regenerate_or_tune": False,
            },
            "causal_track": {
                "window": 64,
                "stride": 1,
                "decision_timestamp": "right_edge",
                "independent_window_reset": True,
                "optimizer_updates": False,
                "future_observations": False,
            },
            "label_construction": {
                "positive": "anomaly window containing frozen evaluator anomaly activity",
                "negative": "anomaly-free window in first 256 samples after regime change or active gradual transition",
                "mixed": "separate stress stratum; never double-labelled or used in primary binary probe",
                "stable_new_normal_specificity": True,
                "stationary_normal_specificity": True,
                "natural_prevalence": True,
                "labels_to_extractor": False,
            },
            "feature_schema": {
                "history": 14,
                "internal_base": 18,
                "hidden": 52,
                "gate": 130,
                "memory": 52,
                "combined": 234,
                "history_plus_combined": 248,
                "schema_file": "reports/phase_g/schema_binding.json",
            },
            "probe_fitting": {
                "classifier": "L2 logistic regression",
                "scaler": "StandardScaler fit on probe-train only",
                "c_grid": [0.01, 0.1, 1, 10],
                "selection": "highest validation AP; exact tie smaller C",
                "split": "source realization/event grouped; no random overlapping-window split",
                "temporal_purge": 96,
            },
            "statistics": {
                "detector_seeds": [11, 22, 33, 44, 55],
                "macro_unit": "test source realization, paired across backbones",
                "hierarchical_bootstrap_draws": 10000,
                "hierarchical_bootstrap_seed": 901,
                "sign_flip_seed": 902,
                "holm_family_alpha": 0.05,
                "family_file": "reports/phase_g/confirmatory_family.json",
            },
            "candi_history_control": candi,
            "g0_stop_boundary": {
                "unresolved_candi_control_stops_before_labels": True,
                "no_outcome_based_choice": True,
                "no_labels": True,
                "no_scaler": True,
                "no_classifier": True,
                "no_ap_or_auroc": True,
            },
            "forbidden_until_external_review": [
                "labeled feature extraction",
                "StandardScaler fitting",
                "logistic fitting or C selection",
                "AP/AUROC/VUS computation",
                "bootstrap/sign-flip",
                "H2/H3a declaration",
                "H3b/H4/natural-H1",
                "optimizer updates",
            ],
        },
    )
    prospective = f"""# Phase G0 prospective seal\n\nThis is a pre-label protocol seal for H2/H3a. It was generated only from the accepted Phase F-v4 seal, the improved official xLSTMAD E2 schema, and already committed Phase C/D metadata/artifact hashes. No anomaly labels, regime/event truth, test-result arrays, scaler fitting, classifier fitting, AP/AUROC, or optimizer update was read or executed.\n\n## Frozen checkpoints\n\nThe ten best checkpoints are exactly those in [checkpoint_manifest.json](checkpoint_manifest.json). LSTM seeds 11/22 are the F-v3 carry-forward references; all other entries are F-v4 best checkpoints. `final.pt` is forbidden when it differs from `best.pt`; F-v1/F-v2, F-v3 partial, and F3-R diagnostic artifacts are forbidden. Models are inference-only in G.\n\n## Frozen probe track\n\nSynthetic folds remain source-disjoint: train 1000--1009, validation 2000--2004, test 3000--3009. Confirmatory shifted scenarios are abrupt, gradual, recurring A→B→A, and correlation-only; stationary/none is a specificity control. The common track is W=64, stride=1, right-edge decisions, with no cross-window state carry and no optimizer updates.\n\nThe primary binary labels are evaluator-only: anomaly windows are positive; anomaly-free early-transition/gradual windows are negative. Mixed drift+anomaly windows are a separate stress stratum. The feature extractor API receives observations only.\n\n## Frozen features and statistics\n\nThe schema is sealed in [schema_binding.json](schema_binding.json): history control 14, internal base 18, hidden 52, gate 130, memory 52, combined 234, and history+combined 248. xLSTM uses only the four actual scalar sLSTM cells/heads; LSTM pools all six actual recurrent layers. Rolling summaries (4/8/16/32) are causal trailing mean/population standard deviation/OLS slope. No learned pooling, layer selection, zero padding, or mLSTM-only confirmatory feature is allowed.\n\nThe confirmatory p-value family is sealed in [confirmatory_family.json](confirmatory_family.json): H2 primary plus H3a A/B/C (four Holm members). H3a is interpreted only after H2 passes. Practical/reproducibility/duration-severity gates remain those in `reports/m0_protocol.md`; descriptive ablations cannot be promoted post-outcome.\n\n## CANDI history-control resolution\n\nThe existing artifacts expose more than one plausible frozen CANDI control: five D=8 synthetic seed-wise `pre_intervention.pth` states (native W=10) and multiple SMD/native W=10 score sources. None is a sealed singular D=8/W=64 common-track stream, and the existing M0 text does not pre-register a choice or a W=10-to-W=64 alignment. This is recorded as `UNRESOLVED_PRELABEL` in the schema/config. The G0 stop rule therefore blocks labeled extraction until an external protocol amendment resolves the exact artifact, seed pairing, and timestamp/window alignment. No probe outcome is used to choose among them.\n\n## Label-blind preflight and stop boundary\n\nThe accompanying preflight is allowed to load frozen checkpoints and use random unlabeled tensors only. It verifies hashes, finite output/score/features, dimensions, causal rolling transforms, reset, permutation/partition invariance, observer OFF/ON parity, no native `predict_step`, no optimizer/parameter mutation, and identical-observation/dummy-opposite-label invariance. It must not calculate a test metric or join labels. If the CANDI control remains unresolved, the report is a fail-closed pre-label STOP even if backbone-only checks pass.\n\nPhase G0 does not authorize any labeled feature extraction, StandardScaler/logistic fitting, C selection, AP/AUROC/statistics, H3b, H4, natural-H1, or architecture/backend change.\n"""
    (REPORT / "prospective.md").write_text(prospective)
    print(json.dumps({"status": "SEALED_PROSPECTIVE", "report": str(REPORT), "candi_resolution": candi["resolution_status"], "checkpoints": len(ckpt["entries"]), "history": len(history), "internal": len(expanded)}))


if __name__ == "__main__":
    main()
