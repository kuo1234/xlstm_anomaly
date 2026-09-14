"""Stage-C execution engine for the sealed Phase-G1 experiment.

The module is intentionally inert at import time.  ``run_labelled`` is the
only entry point that joins evaluator truth, and it requires an explicit
pre-label seal commit.  Stage-A/B can therefore import and test all fitting
and statistical logic without opening a real label file.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from phase_g1_core import (
    ATOL,
    BOOTSTRAP_DRAWS,
    BOOTSTRAP_SEED,
    C_GRID,
    DETECTOR_SEEDS,
    FIRST_COMMON_TIMESTAMP,
    G1_CONFIG,
    HOLM_ALPHA,
    HOLM_FAMILY_SIZE,
    PURGE,
    RTOL,
    SHIFTED_SCENARIOS,
    TEST_SOURCES,
    TRAIN_SOURCES,
    VALIDATION_SOURCES,
    ProtocolViolation,
    apply_scaler,
    array_sha,
    assert_candi_alignment,
    assert_duration_severity_protocol,
    assert_same_row_order,
    assert_shared_control,
    build_evaluator_rows,
    build_feature_groups,
    candi_history14,
    fit_probe_pooled,
    hierarchical_bootstrap,
    make_row_keys,
    paired_intersection,
    primary_binary_mask,
    row_key_hash,
    scale_observations,
    source_cluster_sign_flip,
    window_matrix,
)


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "phase_g1"
FEATURE_DIR = ROOT / "data" / "phase_g1" / "features"

# Scientific files whose contents are frozen by the pre-label seal.  The
# execution guard hashes these paths at label time so an unchanged Git HEAD
# cannot mask an uncommitted edit to an imported helper.
SCIENTIFIC_PRELABEL_FILES = (
    "configs/phase_g1.json",
    "reports/m0_protocol.md",
    "reports/phase_g1/g1_1_duration_severity_amendment.md",
    "configs/synthetic_v1.json",
    "reports/phase_f/preprocessing_manifest.json",
    "reports/phase_e2/source_hashes.json",
    "reports/phase_e2/environment.json",
    "data/phase_e2/dependency_install.json",
    "m0/synthetic.py",
    "m0/correlation.py",
    "scripts/phase_g1_core.py",
    "scripts/phase_g1_pipeline.py",
    "scripts/phase_g1_run.py",
    "scripts/phase_g1_stage_a.py",
    "scripts/phase_g1_adversarial.py",
    "scripts/phase_g1_postrun_audit.py",
    "scripts/phase_g0_preflight.py",
    "scripts/phase_g01_candi_preflight.py",
    "scripts/phase_e2_common.py",
    "scripts/phase_e2_observer.py",
    "scripts/phase_e2_schema.py",
    "scripts/phase_f_common.py",
    "scripts/phase_f_v2_common.py",
    "scripts/phase_f_v3_common.py",
    "scripts/phase_f_v4_common.py",
    "scripts/phase_f_lstm_observer.py",
    "tests/test_phase_g1.py",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict:
    return json.loads(path.read_text())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def current_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _validate_review_provenance(review: Mapping[str, Any], expected_commit: str) -> str:
    """Validate review provenance without requiring a self-referential SHA.

    ``expected_commit`` is the enclosing report-only review commit supplied by
    the Stage-C launcher.  A Git commit cannot embed its own SHA in a file it
    contains, so the review report records the exact implementation commit and
    the launcher derives the review-seal commit from its immutable HEAD
    argument.  An explicit ``review_commit`` field is rejected to prevent a
    caller from accidentally reintroducing the impossible self-reference.
    """
    reviewed_commit = review.get("reviewed_commit")
    implementation_commit = review.get("implementation_commit")
    if not isinstance(reviewed_commit, str) or not isinstance(implementation_commit, str):
        raise ProtocolViolation("pre-label review lacks exact implementation provenance")
    if reviewed_commit != implementation_commit:
        raise ProtocolViolation("pre-label review reviewed_commit and implementation_commit disagree")
    if "review_commit" in review:
        raise ProtocolViolation("pre-label review must derive review commit from the enclosing seal, not embed review_commit")
    if not isinstance(expected_commit, str) or not expected_commit:
        raise ProtocolViolation("pre-label seal commit is missing")
    return implementation_commit


def require_prelabel_seal(expected_commit: str) -> None:
    """Fail closed unless labelled execution uses the signed-off sealed tree.

    The requested ``expected_commit`` is the report-only ``G1_REVIEW_COMMIT``;
    its review JSON must identify the reviewed implementation commit, but may
    not contain the review commit's own SHA (which would be self-referential).
    """
    actual = current_commit()
    if actual != expected_commit:
        raise ProtocolViolation(f"labelled execution commit {actual} != seal {expected_commit}")
    review_relative = str(G1_CONFIG.get("prelabel_review_path", "reports/phase_g1/g1_self_review_prelabel_v2.json"))
    review_path = ROOT / review_relative
    if not review_path.exists():
        raise ProtocolViolation("missing PASS_FOR_LABEL_ACCESS pre-label review")
    review = _json(review_path)
    if review.get("verdict") != "PASS_FOR_LABEL_ACCESS":
        raise ProtocolViolation("pre-label review is not PASS_FOR_LABEL_ACCESS")
    implementation_commit = _validate_review_provenance(review, expected_commit)
    try:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", implementation_commit, expected_commit],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:
        raise ProtocolViolation("reviewed implementation commit is not an ancestor of the review seal") from exc
    sealed_hashes = review.get("scientific_file_sha256", {})
    if set(sealed_hashes) != set(SCIENTIFIC_PRELABEL_FILES):
        raise ProtocolViolation("pre-label review does not seal every scientific file")
    changed = []
    for relative in SCIENTIFIC_PRELABEL_FILES:
        path = ROOT / relative
        if not path.exists() or _sha(path) != sealed_hashes[relative]:
            changed.append(relative)
    if changed:
        raise ProtocolViolation(f"scientific files changed after pre-label seal: {changed}")
    try:
        committed_review = subprocess.check_output(["git", "show", f"{expected_commit}:{review_relative}"], cwd=ROOT)
    except Exception as exc:
        raise ProtocolViolation(f"pre-label review is not present in sealed commit: {exc}") from exc
    if committed_review != review_path.read_bytes():
        raise ProtocolViolation("working-tree pre-label review differs from committed seal")
    # The review commit is intentionally report-only.  Verify that every
    # scientific byte sealed by the reviewer is exactly the byte present in
    # the reviewed implementation commit and in the current review tree.
    for relative in SCIENTIFIC_PRELABEL_FILES:
        try:
            implementation_bytes = subprocess.check_output(
                ["git", "show", f"{implementation_commit}:{relative}"], cwd=ROOT
            )
            review_bytes = subprocess.check_output(["git", "show", f"{expected_commit}:{relative}"], cwd=ROOT)
        except Exception as exc:
            raise ProtocolViolation(f"scientific file missing from sealed commit history: {relative}") from exc
        if implementation_bytes != review_bytes or implementation_bytes != (ROOT / relative).read_bytes():
            raise ProtocolViolation(f"scientific file changed between implementation/review seal: {relative}")


def assert_sealed_inputs() -> dict:
    """Verify G0/F4/CANDI manifests by hash before any label join."""
    checks = []
    for relative, expected in G1_CONFIG["sealed_input_sha256"].items():
        path = ROOT / relative
        actual = _sha(path)
        checks.append({"path": relative, "expected": expected, "actual": actual, "pass_": actual == expected})
    base = ROOT / G1_CONFIG["base_g0_config"]
    base_actual = _sha(base)
    checks.append({"path": G1_CONFIG["base_g0_config"], "expected": G1_CONFIG["base_g0_config_sha256"], "actual": base_actual, "pass_": base_actual == G1_CONFIG["base_g0_config_sha256"]})
    if not all(row["pass_"] for row in checks):
        raise ProtocolViolation("sealed G0/F4 input hash mismatch")
    return {"status": "PASS", "files": checks}


def require_duration_matching_resolution() -> None:
    """Block label access unless the G1.1 robustness estimand is resolved."""
    assert_duration_severity_protocol(G1_CONFIG)


def scientific_file_sha256() -> dict[str, str]:
    """Return hashes of every scientific file frozen by the pre-label seal."""
    result: dict[str, str] = {}
    for relative in SCIENTIFIC_PRELABEL_FILES:
        path = ROOT / relative
        if not path.exists():
            raise ProtocolViolation(f"missing scientific pre-label file: {relative}")
        result[relative] = _sha(path)
    return result


def _phase_f_scaler(source_seed: int) -> dict:
    """Load the sealed train/validation scaler or fit test-prefix scaler only."""
    source = int(source_seed)
    if source in TRAIN_SOURCES or source in VALIDATION_SOURCES:
        manifest = _json(ROOT / "reports" / "phase_f" / "preprocessing_manifest.json")
        record = next(row for row in manifest["sources"] if int(row["source"]) == source)
        scaler_rel = next(path for path in record["artifacts"] if path.endswith("scaler.json"))
        scaler_path = ROOT / scaler_rel
        if _sha(scaler_path) != record["artifacts"][scaler_rel]:
            raise ProtocolViolation("sealed Phase-F scaler hash mismatch")
        scaler = _json(scaler_path)
        if scaler.get("fit") != [0, 4096]:
            raise ProtocolViolation("unexpected scaler fit interval")
        return {"mean": scaler["mean"], "scale": scaler["scale"], "fit": scaler["fit"], "sha256": _sha(scaler_path), "source": source}
    if source not in TEST_SOURCES:
        raise ProtocolViolation("unregistered source seed")
    # Test-prefix scalers are computed from the fixed, anomaly-free initial
    # fit prefix only.  No evaluator field is accessed here.
    from m0.synthetic import generate

    observations = np.asarray(generate(source, "stationary", "none").observations[:4096], dtype=np.float64)
    mean = observations.mean(axis=0)
    scale = observations.std(axis=0, ddof=0)
    scale[scale == 0] = 1.0
    scaler = {"mean": mean.tolist(), "scale": scale.tolist(), "fit": [0, 4096], "source": source, "derivation": "fixed stationary/none observation prefix"}
    scaler["sha256"] = _sha_bytes(_canonical(scaler).encode())
    return scaler


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_backbone(entry: Mapping[str, Any]) -> Any:
    """Load one exact F4 best checkpoint through the sealed G0 loader."""
    if Path(entry["path"]).name != "best.pt" or entry.get("best_only") is False:
        raise ProtocolViolation("Phase-G requires best.pt only")
    sys.path.insert(0, str(ROOT / "scripts"))
    import phase_g0_preflight as g0

    return g0._load_entry(dict(entry))


def load_backbone_entries() -> dict[int, dict[str, Any]]:
    manifest = _json(ROOT / "reports" / "phase_g" / "checkpoint_manifest.json")
    if manifest.get("status") != "PASS" or len(manifest.get("entries", [])) != 10:
        raise ProtocolViolation("checkpoint manifest is not the sealed ten-run PASS")
    forbidden = tuple(manifest.get("forbidden_paths", ()))
    entries: dict[int, dict[str, Any]] = {}
    for row in manifest["entries"]:
        seed = int(row["detector_seed"])
        architecture = row["architecture"]
        if architecture not in {"xlstm", "lstm"} or seed not in DETECTOR_SEEDS:
            raise ProtocolViolation("unexpected checkpoint entry")
        if row["path"].endswith("final.pt") or any(row["path"].startswith(p.rstrip("*")) for p in forbidden):
            raise ProtocolViolation("forbidden checkpoint selected")
        entries[(seed, architecture)] = row
    if len(entries) != 10:
        raise ProtocolViolation("checkpoint mapping is not one row per seed/backbone")
    return entries


def _candi_rows() -> dict[int, dict[str, Any]]:
    manifest = _json(ROOT / "reports" / "phase_g" / "candi_control_manifest.json")
    if manifest.get("status") not in {"SEALED_PROSPECTIVE_PENDING_PREFLIGHT", "PASS"}:
        raise ProtocolViolation("unexpected CANDI control manifest status")
    if manifest.get("official_candi_commit") != G1_CONFIG["candi_control"]["official_commit"]:
        raise ProtocolViolation("official CANDI commit drifted")
    controls = {int(row["detector_seed"]): row for row in manifest.get("controls", [])}
    if tuple(sorted(controls)) != DETECTOR_SEEDS:
        raise ProtocolViolation("CANDI seed mapping is incomplete")
    expected_mapping = G1_CONFIG["candi_control"]["seed_mapping"]
    for seed in DETECTOR_SEEDS:
        if controls[seed].get("pre_intervention") != expected_mapping[str(seed)]:
            raise ProtocolViolation(f"CANDI seed {seed} mapping drifted")
    return controls


def load_candi_controls() -> dict[int, tuple[Any, dict]]:
    """Load frozen Phase-D D8 CANDI states; no adaptation or optimizer."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from phase_g01_candi_preflight import _load_candi

    result = {}
    rows = _candi_rows()
    for seed in DETECTOR_SEEDS:
        model, state = _load_candi(seed, rows[seed])
        result[seed] = (model, rows[seed])
    return result


def extract_candi_history(model: Any, row: Mapping[str, Any], observations: np.ndarray, timestamps: Sequence[int], batch_size: int = 256) -> np.ndarray:
    """Inference-only native W10 CANDI history at common t>=63 decisions."""
    x = np.asarray(observations)
    ts = np.asarray(timestamps, dtype=np.int64)
    if len(ts) == 0 or int(ts[0]) != FIRST_COMMON_TIMESTAMP:
        raise ProtocolViolation("common CANDI stream must start at t=63")
    mean = np.asarray(row["preprocessing"]["scaler_mean"], dtype=np.float64)
    scale = np.asarray(row["preprocessing"]["scaler_scale"], dtype=np.float64)
    scaled = ((x.astype(np.float64) - mean) / scale).astype(np.float32)
    windows = window_matrix(scaled, ts, 10)
    sys.path.insert(0, str(ROOT / "scripts"))
    from phase_g01_candi_preflight import candi_score
    import torch

    device = next(model.parameters()).device
    values = []
    before = _model_state_hash(model)
    with torch.no_grad():
        for left in range(0, len(windows), batch_size):
            values.append(candi_score(model, torch.from_numpy(windows[left : left + batch_size]).to(device)).detach().cpu().numpy())
    scores = np.concatenate(values).astype(np.float64, copy=False)
    history = candi_history14(scores, ts)
    if _model_state_hash(model) != before:
        raise ProtocolViolation("CANDI state mutated during history extraction")
    return history


def _model_state_hash(model: Any) -> str:
    digest = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        value = tensor.detach().cpu().contiguous().numpy()
        digest.update(name.encode() + str(value.dtype).encode() + str(value.shape).encode() + value.tobytes())
    return digest.hexdigest()


def extract_condition_features(
    model: Any,
    architecture: str,
    candi_model: Any,
    candi_row: Mapping[str, Any],
    observations: np.ndarray,
    timestamps: Sequence[int],
    scaler: Mapping[str, Sequence[float]],
) -> dict[str, Any]:
    """Extract all six backbone/CANDI feature groups without evaluator truth."""
    if architecture not in {"xlstm", "lstm"}:
        raise ProtocolViolation("unregistered architecture")
    common = __import__("phase_g1_core").extract_backbone_rows(model, architecture, observations, scaler, timestamps)
    groups = build_feature_groups(common["scores"], common["internal_base"])
    candi = extract_candi_history(candi_model, candi_row, observations, timestamps)
    assert_candi_alignment(common["timestamps"], np.asarray(timestamps, dtype=np.int64))
    groups["candi_history14"] = candi
    groups["candi_history_plus_combined248"] = np.concatenate((candi, groups["combined234"]), axis=1)
    return {
        "timestamps": common["timestamps"],
        "scores": common["scores"],
        "internal_base": common["internal_base"],
        "groups": groups,
        "score_sha256": common["score_sha256"],
        "internal_base_sha256": common["internal_base_sha256"],
        "candi_history_sha256": array_sha(candi),
        "scaler_sha256": scaler.get("sha256", _sha_bytes(_canonical(dict(scaler)).encode())),
        "architecture": architecture,
    }


@dataclass(frozen=True)
class FeatureRecord:
    detector_seed: int
    architecture: str
    source_seed: int
    scenario: str
    condition: str
    timestamps: np.ndarray
    groups: Mapping[str, np.ndarray]
    scores: np.ndarray
    source_fold: str


def join_evaluator_labels(record: FeatureRecord, stream: Any) -> dict[str, Any]:
    """Join labels only after observation-only feature extraction is complete."""
    truth = build_evaluator_rows(stream, record.timestamps, 64)
    if not np.array_equal(record.timestamps, truth["timestamps"]):
        raise ProtocolViolation("feature/truth timestamps differ")
    keys = make_row_keys(record.detector_seed, record.source_seed, record.scenario, record.condition, record.timestamps, truth["event"])
    return {
        "keys": keys,
        "groups": {name: np.asarray(value) for name, value in record.groups.items()},
        "label": truth["label"],
        "stratum": truth["stratum"],
        "event": truth["event"],
        "event_type": truth["event_type"],
        "duration": truth["duration"],
        "severity": truth["severity"],
        "source_seed": np.full(len(keys), record.source_seed, dtype=np.int64),
        "scenario": np.asarray([record.scenario] * len(keys), dtype=object),
        "condition": np.asarray([record.condition] * len(keys), dtype=object),
        "detector_seed": np.full(len(keys), record.detector_seed, dtype=np.int64),
        "source_fold": record.source_fold,
    }


def select_primary_rows(
    joined: Mapping[str, Any],
    feature_arm: str,
    valid_mask: Sequence[bool] | None = None,
) -> dict[str, Any]:
    """Filter anomaly/drift binary rows; mixed/stationary rows stay separate."""
    mask = primary_binary_mask(joined, allow_empty=True)
    if valid_mask is not None:
        supplied = np.asarray(valid_mask, dtype=bool)
        if supplied.shape != mask.shape:
            raise ProtocolViolation("common primary mask shape mismatch")
        mask &= supplied
    features = np.asarray(joined["groups"][feature_arm], dtype=np.float64)
    if features.ndim != 2 or len(features) != len(mask):
        raise ProtocolViolation("feature/label row mismatch")
    finite = np.isfinite(features).all(axis=1)
    keep = mask & finite
    keys = [dict(key) for key, include in zip(joined["keys"], keep) if include]
    return {
        "X": features[keep],
        "y": np.asarray(joined["label"], dtype=np.int8)[keep],
        "keys": keys,
        "source_seeds": np.asarray(joined["source_seed"], dtype=np.int64)[keep],
        "scenarios": tuple(np.asarray(joined["scenario"], dtype=object)[keep].tolist()),
        "events": tuple(np.asarray(joined["event"], dtype=np.int32)[keep].tolist()),
        "event_types": tuple(np.asarray(joined["event_type"], dtype=object)[keep].tolist()),
        "stratum": np.asarray(joined["stratum"], dtype=object)[keep],
        "duration": np.asarray(joined["duration"], dtype=object)[keep],
        "severity": np.asarray(joined["severity"], dtype=object)[keep],
    }


def probe_split_from_rows(rows: Mapping[str, Any]) -> Any:
    from phase_g1_core import ProbeSplit

    return ProbeSplit(
        X=np.asarray(rows["X"], dtype=np.float64),
        y=np.asarray(rows["y"], dtype=np.int8),
        keys=tuple(rows["keys"]),
        source_seeds=np.asarray(rows["source_seeds"], dtype=np.int64),
        scenarios=tuple(rows["scenarios"]),
        events=tuple(int(x) for x in rows["events"]),
    )


def assert_common_cohort(rows_by_arm: Mapping[str, Mapping[str, Any]]) -> str:
    names = list(rows_by_arm)
    if not names:
        raise ProtocolViolation("empty comparison arm set")
    reference = rows_by_arm[names[0]]["keys"]
    for name in names[1:]:
        assert_same_row_order(reference, rows_by_arm[name]["keys"])
        if not np.array_equal(rows_by_arm[names[0]]["y"], rows_by_arm[name]["y"]):
            raise ProtocolViolation(f"paired labels differ for arm {name}")
    return row_key_hash(reference)


def fit_all_arms(
    train_rows: Mapping[str, Mapping[str, Any]],
    validation_rows: Mapping[str, Mapping[str, Any]],
    test_rows: Mapping[str, Mapping[str, Any]],
    detector_seed: int,
) -> dict[str, dict]:
    """Fit every sealed arm with one pooled C selection per arm."""
    expected = {"history14": 14, "hidden52": 52, "gate130": 130, "memory52": 52, "combined234": 234, "history_plus_combined248": 248, "candi_history14": 14, "candi_history_plus_combined248": 248}
    result = {}
    for arm, dim in expected.items():
        result[arm] = fit_probe_pooled(
            probe_split_from_rows(train_rows[arm]),
            probe_split_from_rows(validation_rows[arm]),
            probe_split_from_rows(test_rows[arm]),
            arm,
            detector_seed,
            dim,
        )
    return result


def _ap(y: np.ndarray, prediction: np.ndarray) -> float:
    from sklearn.metrics import average_precision_score

    return float(average_precision_score(y, prediction))


def compute_arm_ap(fit: Mapping[str, Any], rows: Mapping[str, Any]) -> float:
    y = np.asarray(rows["y"], dtype=np.int8)
    prediction = np.asarray(fit["test_prediction"], dtype=np.float64)
    if len(y) != len(prediction):
        raise ProtocolViolation("prediction/label cardinality mismatch")
    return _ap(y, prediction)


def build_confirmatory_statistics(ap_table: Mapping[str, np.ndarray]) -> dict[str, Any]:
    """Compute the four frozen *primary* source-pooled differences.

    ``ap_table`` values are ``[10 sources, 5 detector seeds]``.  Scenario-wise
    tensors are retained by the launcher as descriptive reproducibility
    diagnostics, but never substituted for the pooled primary estimand.
    """
    required = ("h2", "h3a_a", "h3a_b", "h3a_c")
    if tuple(ap_table) != required:
        raise ProtocolViolation("confirmatory table must contain exactly four members in order")
    raw = {}
    pvalues = []
    for name in required:
        delta = np.asarray(ap_table[name], dtype=np.float64)
        if delta.shape != (10, 5):
            raise ProtocolViolation("primary confirmatory effects must be [10,5] source/seed")
        summary = hierarchical_bootstrap(delta, BOOTSTRAP_DRAWS, BOOTSTRAP_SEED)
        p = source_cluster_sign_flip(delta)
        summary["raw_p"] = p
        raw[name] = summary
        pvalues.append(p)
    from phase_g1_core import holm_adjust

    adjusted = holm_adjust(pvalues, HOLM_FAMILY_SIZE)
    for name, p in zip(required, adjusted):
        raw[name]["holm_adjusted_p"] = p
    return {"family_size": HOLM_FAMILY_SIZE, "alpha": HOLM_ALPHA, "members": list(required), "comparisons": raw}


def expected_feature_arms() -> tuple[str, ...]:
    return ("history14", "hidden52", "gate130", "memory52", "combined234", "history_plus_combined248", "candi_history14", "candi_history_plus_combined248")


def run_labelled(prelabel_commit: str) -> dict:
    """Full Stage-C execution hook; never callable before the seal commit."""
    require_prelabel_seal(prelabel_commit)
    assert_sealed_inputs()
    # Keep the launcher in a separate file so the label-blind core remains
    # importable by Stage-A tests.  The import is lazy and therefore cannot
    # accidentally join truth during pre-label review.
    from phase_g1_run import run

    return run(prelabel_commit, REPORT)


__all__ = [
    "FeatureRecord",
    "assert_common_cohort",
    "assert_sealed_inputs",
    "build_confirmatory_statistics",
    "compute_arm_ap",
    "expected_feature_arms",
    "extract_backbone_rows",
    "extract_candi_history",
    "extract_condition_features",
    "fit_all_arms",
    "join_evaluator_labels",
    "load_backbone_entries",
    "load_candi_controls",
    "probe_split_from_rows",
    "require_prelabel_seal",
    "require_duration_matching_resolution",
    "run_labelled",
    "scientific_file_sha256",
    "select_primary_rows",
]
