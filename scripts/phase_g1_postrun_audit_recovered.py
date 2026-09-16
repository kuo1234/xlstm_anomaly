"""Independent post-run audit for recovered-cache Phase-G1 executions.

The ordinary :mod:`phase_g1_postrun_audit` validates a normal Stage-C
pre-label/execution lineage.  A recovered execution has two truthful
identities (the original pre-label seal and a later continuation seal), so this
module implements a separate orchestration rather than calling the ordinary
top-level auditor and suppressing its lineage errors.

The scientific checks intentionally reuse the ordinary auditor's *pure*
recomputation helpers, while every recovered-lineage and cache-provenance
check is explicit here.  This module is fail-closed and never repairs or
overwrites scientific artifacts.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import phase_g1_continue_from_cache as continuation  # noqa: E402
import phase_g1_postrun_audit as ordinary  # noqa: E402
from phase_g1_core import (  # noqa: E402
    BOOTSTRAP_DRAWS,
    BOOTSTRAP_SEED,
    C_GRID,
    DETECTOR_SEEDS,
    DURATION_STRATA,
    HOLM_FAMILY_SIZE,
    HOLM_ALPHA,
    SIGN_FLIP_SEED,
    SEVERITY_STRATA,
    SHIFTED_SCENARIOS,
    TEST_SOURCES,
    ProtocolViolation,
    assert_same_row_order,
    assert_unique_keys,
    object_sha,
    row_key_hash,
)
from phase_g1_pipeline import SCIENTIFIC_PRELABEL_FILES  # noqa: E402


ORIGINAL_PRELABEL_SEAL = "5622376087aaa97249ff9a055f201b250efbf1c2"
REPORTING_PATCH = "2c79cbf62574df498f1c9fd39d1bee9aa495e41a"
REVIEWED_CONTINUATION_IMPLEMENTATION = "25a67addabf2de30c706824e47e8e280c2ab4ff3"
REPORT_DIR = ROOT / "reports" / "phase_g1"
CACHE_DIR = continuation.audit.CACHE_DIR
CONTINUATION_REVIEW_PATH = REPORT_DIR / "g1_continuation_self_review_v2.json"
CONTINUATION_REVIEW_VERDICT = "PASS_CONTINUATION_FOR_EXTERNAL_REVIEW"
CONTINUATION_REVIEWED_EXECUTABLES = (
    "scripts/phase_g1_continue_from_cache.py",
    "scripts/phase_g1_cache_audit.py",
    "scripts/phase_g1_reporting_patch_audit.py",
    "scripts/phase_g1_run.py",
)

CACHE_AUDIT_PATH = REPORT_DIR / "g1_cache_audit_v1.json"
INVENTORY_PATH = REPORT_DIR / "g1_cache_file_inventory_v1.jsonl.gz"
INCIDENT_PATH = REPORT_DIR / "g1_postlabel_failure_v1.json"
AUTH_PATH = REPORT_DIR / "g1_reporting_patch_v1.json"
PATCH_AUDIT_PATH = REPORT_DIR / "g1_reporting_patch_audit_v1.json"
CACHE_AUDIT_SHA256 = "730744b626bff018c6fd7f7ab72385583d8d091b4cd8642639fa56dfcc2a0c7b"
INVENTORY_SHA256 = "f9cbfa1a1915ffdb73b8df348b0329dde5b6edf5a5f3c563f60b49e07f783856"
INCIDENT_SHA256 = "6eddd07affbe8ff869748abe0d52d64deb9ce41dc6e0beb14bc4eeae9150c42b"
AUTH_SHA256 = "025ce284f1182f0ca2b1ceefaa7225d8ea1ec937992dced2175cee5c5f10a3e8"
PATCH_AUDIT_SHA256 = "c604c19ce8658b03d68f742fba36b25b9c8d1aba5ebc254960f24fa017bf2dc2"
LEDGER_SHA256 = "67e6a30d518011e8d06307e7d1b305449b4787602f3bd1701f8989a7dadeab0a"

ARMS = ordinary.ARMS
ARCHITECTURES = ordinary.ARCHITECTURES
EXPECTED_DIMS = {
    "history14": 14,
    "hidden52": 52,
    "gate130": 130,
    "memory52": 52,
    "combined234": 234,
    "history_plus_combined248": 248,
    "candi_history14": 14,
    "candi_history_plus_combined248": 248,
}
REQUIRED_OUTPUTS = (
    "g1_execution_manifest.json",
    "g1_probe_manifest.json",
    "g1_results.json",
    "g1_statistics.json",
    "g1_decision.json",
    "g1_decision.md",
)


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _full_sha(value: Any, length: int = 40) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{%d}" % length, value) is not None


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _git_bytes(commit: str, relative: str) -> bytes:
    try:
        return subprocess.check_output(["git", "show", f"{commit}:{relative}"], cwd=ROOT, stderr=subprocess.STDOUT)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ProtocolViolation(f"cannot read committed file {commit}:{relative}") from exc


def _assert_close_reported(label: str, computed: Any, reported: Any, *, atol: float = 1e-12, rtol: float = 1e-10) -> None:
    """Reject a tampered AP/statistic/decision primitive or summary value."""
    try:
        if not bool(np.isclose(float(computed), float(reported), atol=atol, rtol=rtol)):
            raise ProtocolViolation(f"{label} differs from independent recomputation")
    except (TypeError, ValueError) as exc:
        raise ProtocolViolation(f"{label} is not a finite numeric summary") from exc


def _assert_decision_matches(label: str, expected: str, reported: Any) -> None:
    """Reject a decision summary that differs from the primitive Boolean rule."""
    if reported != expected:
        raise ProtocolViolation(f"{label} differs from independent Boolean recomputation")


def _canonical_array_sha(value: np.ndarray) -> str:
    """Match the sealed canonical array digest used by Phase-G1 artifacts."""
    array = np.asarray(value)
    return _sha_bytes(
        str(array.dtype).encode()
        + str(array.shape).encode()
        + np.ascontiguousarray(array).tobytes(order="C")
    )


def _validate_recovered_lineage_values(
    execution: Mapping[str, Any],
    continuation_seal: Any,
    current_head: str,
    review: Mapping[str, Any],
    current_executable_sha256: Mapping[str, str],
    implementation_executable_sha256: Mapping[str, str],
    seal_executable_sha256: Mapping[str, str] | None = None,
    *,
    implementation_is_ancestor: bool,
    code_sha256: str,
    expected_code_sha256: str,
    runner_sha256: str,
    expected_runner_sha256: str,
    scientific_file_sha256: Mapping[str, str],
    expected_scientific_file_sha256: Mapping[str, str],
    duration_status: Any,
) -> None:
    """Pure recovered-lineage contract used by production and fixtures."""
    if not _full_sha(continuation_seal):
        raise ProtocolViolation("recovered audit requires an explicit full continuation seal")
    if execution.get("status") != "LABELLED_EXECUTION_RECOVERED_FROM_VERIFIED_CACHE":
        raise ProtocolViolation("manifest is not a recovered-cache execution")
    if execution.get("prelabel_seal_commit") != ORIGINAL_PRELABEL_SEAL:
        raise ProtocolViolation("recovered manifest has the wrong original pre-label seal")
    if execution.get("execution_commit") != continuation_seal:
        raise ProtocolViolation("recovered manifest execution_commit differs from continuation seal")
    if current_head != continuation_seal:
        raise ProtocolViolation("current HEAD differs from continuation execution seal")
    if review.get("verdict") != CONTINUATION_REVIEW_VERDICT:
        raise ProtocolViolation("continuation review is not PASS_CONTINUATION_FOR_EXTERNAL_REVIEW")
    reviewed_commit = review.get("reviewed_commit")
    if not _full_sha(reviewed_commit) or reviewed_commit == continuation_seal:
        raise ProtocolViolation("continuation review lacks a distinct full reviewed implementation SHA")
    if reviewed_commit != REVIEWED_CONTINUATION_IMPLEMENTATION:
        raise ProtocolViolation("continuation review is not bound to the accepted reviewed implementation")
    if not implementation_is_ancestor:
        raise ProtocolViolation("reviewed continuation implementation is not an ancestor of execution seal")
    expected_paths = set(CONTINUATION_REVIEWED_EXECUTABLES)
    reviewed_hashes = review.get("reviewed_executable_sha256")
    if not isinstance(reviewed_hashes, Mapping) or set(reviewed_hashes) != expected_paths:
        raise ProtocolViolation("continuation reviewed executable hash set is incomplete")
    if set(current_executable_sha256) != expected_paths or set(implementation_executable_sha256) != expected_paths:
        raise ProtocolViolation("continuation executable hash snapshot has unexpected paths")
    if seal_executable_sha256 is not None and set(seal_executable_sha256) != expected_paths:
        raise ProtocolViolation("continuation execution-seal executable snapshot has unexpected paths")
    for relative in CONTINUATION_REVIEWED_EXECUTABLES:
        expected = reviewed_hashes.get(relative)
        if not _full_sha(expected, 64):
            raise ProtocolViolation(f"invalid continuation reviewed hash: {relative}")
        if current_executable_sha256.get(relative) != expected:
            raise ProtocolViolation(f"current continuation executable changed: {relative}")
        if implementation_executable_sha256.get(relative) != expected:
            raise ProtocolViolation(f"reviewed implementation bytes changed: {relative}")
        if seal_executable_sha256 is not None and seal_executable_sha256.get(relative) != expected:
            raise ProtocolViolation(f"execution-seal executable differs from reviewed bytes: {relative}")
    if code_sha256 != expected_code_sha256:
        raise ProtocolViolation("recovered manifest code hash is not phase_g1_continue_from_cache.py")
    if runner_sha256 != expected_runner_sha256:
        raise ProtocolViolation("sealed phase_g1_run.py reporting-patch hash drifted")
    if set(scientific_file_sha256) != set(expected_scientific_file_sha256):
        raise ProtocolViolation("recovered scientific-file hash set differs from pre-label seal")
    if set(expected_scientific_file_sha256) != set(SCIENTIFIC_PRELABEL_FILES):
        raise ProtocolViolation("accepted scientific-file seal has an unexpected file set")
    for relative, expected in expected_scientific_file_sha256.items():
        if not _full_sha(expected, 64) or not _full_sha(scientific_file_sha256.get(relative), 64):
            raise ProtocolViolation(f"invalid scientific-file hash: {relative}")
        if scientific_file_sha256.get(relative) != expected:
            raise ProtocolViolation(f"recovered scientific-file hash drifted: {relative}")
    if duration_status != "RESOLVED":
        raise ProtocolViolation("duration/severity protocol is not RESOLVED")


def _verify_continuation_review_seal(continuation_seal: str) -> Mapping[str, Any]:
    """Verify the exact continuation seal and all reviewed executable bytes."""
    # Reuse the already accepted production guard, then independently check
    # the values again below.  This never enters the continuation/probe path.
    review = continuation.require_continuation_review_seal(continuation_seal)
    if not CONTINUATION_REVIEW_PATH.is_file():
        raise ProtocolViolation("missing recovered continuation self-review")
    review_bytes = CONTINUATION_REVIEW_PATH.read_bytes()
    committed_review = _git_bytes(continuation_seal, str(CONTINUATION_REVIEW_PATH.relative_to(ROOT)))
    if review_bytes != committed_review:
        raise ProtocolViolation("continuation review bytes differ from execution seal")
    reviewed_commit = review.get("reviewed_commit")
    current_hashes = {relative: _sha(ROOT / relative) for relative in CONTINUATION_REVIEWED_EXECUTABLES}
    implementation_hashes = {relative: _sha_bytes(_git_bytes(str(reviewed_commit), relative)) for relative in CONTINUATION_REVIEWED_EXECUTABLES}
    seal_hashes = {relative: _sha_bytes(_git_bytes(continuation_seal, relative)) for relative in CONTINUATION_REVIEWED_EXECUTABLES}
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", str(reviewed_commit), continuation_seal],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise ProtocolViolation("continuation implementation is not an ancestor of execution seal")
    _validate_recovered_lineage_values(
        {
            "status": "LABELLED_EXECUTION_RECOVERED_FROM_VERIFIED_CACHE",
            "prelabel_seal_commit": ORIGINAL_PRELABEL_SEAL,
            "execution_commit": continuation_seal,
        },
        continuation_seal,
        _git_head(),
        review,
        current_hashes,
        implementation_hashes,
        seal_executable_sha256=seal_hashes,
        implementation_is_ancestor=True,
        code_sha256=current_hashes["scripts/phase_g1_continue_from_cache.py"],
        expected_code_sha256=current_hashes["scripts/phase_g1_continue_from_cache.py"],
        runner_sha256=current_hashes["scripts/phase_g1_run.py"],
        expected_runner_sha256=_sha_bytes(_git_bytes(REPORTING_PATCH, "scripts/phase_g1_run.py")),
        scientific_file_sha256={relative: _sha(ROOT / relative) for relative in SCIENTIFIC_PRELABEL_FILES},
        expected_scientific_file_sha256={relative: _sha(ROOT / relative) for relative in SCIENTIFIC_PRELABEL_FILES},
        duration_status="RESOLVED",
    )
    return review


def _validate_cache_provenance_values(
    file_sha256: Mapping[str, str],
    cache_audit: Mapping[str, Any],
    authorization: Mapping[str, Any],
    patch_audit: Mapping[str, Any],
    *,
    primary_cache_read_only: Any,
) -> None:
    """Validate accepted cache/inventory provenance without mutating cache."""
    expected = {
        str(CACHE_AUDIT_PATH.relative_to(ROOT)): CACHE_AUDIT_SHA256,
        str(INVENTORY_PATH.relative_to(ROOT)): INVENTORY_SHA256,
        str(INCIDENT_PATH.relative_to(ROOT)): INCIDENT_SHA256,
        str(AUTH_PATH.relative_to(ROOT)): AUTH_SHA256,
        str(PATCH_AUDIT_PATH.relative_to(ROOT)): PATCH_AUDIT_SHA256,
    }
    if set(file_sha256) != set(expected):
        raise ProtocolViolation("recovered cache provenance file set differs from seal")
    for relative, digest in expected.items():
        if file_sha256.get(relative) != digest:
            raise ProtocolViolation(f"recovered cache provenance hash mismatch: {relative}")
    if cache_audit.get("status") != "PASS_CACHE_REUSABLE":
        raise ProtocolViolation("cache audit is not PASS_CACHE_REUSABLE")
    if cache_audit.get("labels_or_metrics_accessed") is not False or cache_audit.get("probe_fit") is not False or cache_audit.get("ap_or_auroc") is not False:
        raise ProtocolViolation("accepted cache audit records forbidden metric access")
    if cache_audit.get("cache_integrity", {}).get("status") != "PASS" or cache_audit.get("replay", {}).get("status") != "PASS":
        raise ProtocolViolation("accepted cache audit integrity/replay status is not PASS")
    if cache_audit.get("cache_integrity", {}).get("labels_or_outcome_summary_emitted") is not False:
        raise ProtocolViolation("cache audit emitted an outcome summary")
    if primary_cache_read_only is not True:
        raise ProtocolViolation("recovered manifest does not declare primary cache read-only")
    if authorization.get("authorization_type") != "G1-R1_POST_LABEL_REPORTING_PATCH" or authorization.get("cache_use_authorized") is not False or authorization.get("probe_or_metric_execution_authorized") is not False:
        raise ProtocolViolation("reporting-patch authorization scope permits unapproved metric/cache use")
    if authorization.get("original_prelabel_review_seal") != ORIGINAL_PRELABEL_SEAL:
        raise ProtocolViolation("reporting authorization original seal mismatch")
    if authorization.get("reporting_patch_commit") != REPORTING_PATCH:
        raise ProtocolViolation("reporting authorization patch mismatch")
    if authorization.get("quarantined_execution_ledger_sha256") != LEDGER_SHA256:
        raise ProtocolViolation("reporting authorization ledger hash mismatch")
    if patch_audit.get("status") != "PASS":
        raise ProtocolViolation("reporting-patch scope audit is not PASS")
    if cache_audit.get("patch_binding", {}).get("status") != "PASS" or cache_audit.get("patch_binding", {}).get("patch_audit_status") != "PASS":
        raise ProtocolViolation("cache audit patch binding is not PASS")


def _verify_cache_provenance(execution: Mapping[str, Any]) -> dict[str, Any]:
    paths = (CACHE_AUDIT_PATH, INVENTORY_PATH, INCIDENT_PATH, AUTH_PATH, PATCH_AUDIT_PATH)
    if any(not path.is_file() for path in paths):
        raise ProtocolViolation("recovered cache provenance artifact is missing")
    ledger_path = ROOT / "reports/phase_g/g1_execution_ledger.jsonl"
    if not ledger_path.is_file() or _sha(ledger_path) != LEDGER_SHA256:
        raise ProtocolViolation("quarantined execution ledger hash mismatch")
    file_sha256 = {str(path.relative_to(ROOT)): _sha(path) for path in paths}
    expected_audit_rel = str(CACHE_AUDIT_PATH.relative_to(ROOT))
    if execution.get("primary_cache_audit") != expected_audit_rel or execution.get("primary_cache_audit_sha256") != CACHE_AUDIT_SHA256:
        raise ProtocolViolation("recovered manifest cache-audit binding drifted")
    cache_audit = _json(CACHE_AUDIT_PATH)
    authorization = _json(AUTH_PATH)
    patch_audit = _json(PATCH_AUDIT_PATH)
    _validate_cache_provenance_values(
        file_sha256,
        cache_audit,
        authorization,
        patch_audit,
        primary_cache_read_only=execution.get("primary_cache_read_only"),
    )
    return {
        "status": "PASS_CACHE_REUSABLE",
        "file_sha256": file_sha256,
        "cache_audit_status": cache_audit.get("status"),
        "primary_cache_read_only": execution.get("primary_cache_read_only"),
        "cache_modified": False,
    }


def _verify_scientific_file_seal(expected: Mapping[str, str]) -> dict[str, str]:
    """Rehash every protected scientific file, rather than trusting a manifest."""
    if set(expected) != set(SCIENTIFIC_PRELABEL_FILES):
        raise ProtocolViolation("scientific-file seal does not cover the frozen file set")
    current: dict[str, str] = {}
    for relative in SCIENTIFIC_PRELABEL_FILES:
        path = ROOT / relative
        if not path.is_file():
            raise ProtocolViolation(f"sealed scientific file is missing: {relative}")
        digest = _sha(path)
        current[relative] = digest
        if digest != expected.get(relative):
            raise ProtocolViolation(f"sealed scientific file hash drifted: {relative}")
    return current


def _verify_decision_markdown(path: Path, decision: Mapping[str, Any]) -> None:
    """Ensure the human-readable decision is consistent with its JSON twin."""
    try:
        text = path.read_text()
    except OSError as exc:
        raise ProtocolViolation("recovered decision markdown is unreadable") from exc
    expected_lines = (
        f"H2 = {decision.get('H2')}",
        f"H3a = {decision.get('H3a')}",
        f"H3b = {decision.get('H3b')}",
        f"H1_controlled_harm = {decision.get('h1_controlled_harm')}",
        f"H1_natural_harm = {decision.get('h1_natural_harm')}",
        f"H1_harm_overall = {decision.get('h1_harm_overall')}",
    )
    if any(line not in text for line in expected_lines):
        raise ProtocolViolation("recovered decision markdown disagrees with decision JSON")


def _expected_execution_rows() -> set[tuple[int, int, str, str, str]]:
    rows: set[tuple[int, int, str, str, str]] = set()
    for seed in DETECTOR_SEEDS:
        for fold, sources in (("train", range(1000, 1010)), ("validation", range(2000, 2005)), ("test", range(3000, 3010))):
            for source in sources:
                for scenario in SHIFTED_SCENARIOS:
                    for condition in ("none", "spike", "collective", "dependency", "mixture"):
                        rows.add((seed, source, fold, scenario, condition))
                rows.add((seed, source, fold, "stationary", "none"))
    return rows


def _verify_recovered_execution_manifest(execution: Mapping[str, Any], output_dir: Path) -> dict[str, Any]:
    if tuple(execution.get("feature_arms", ())) != tuple(ARMS):
        raise ProtocolViolation("recovered feature-arm manifest drifted")
    if tuple(execution.get("shifted_scenarios", ())) != tuple(SHIFTED_SCENARIOS):
        raise ProtocolViolation("recovered shifted-scenario manifest drifted")
    if tuple(execution.get("conditions", ())) != ("none", "spike", "collective", "dependency", "mixture"):
        raise ProtocolViolation("recovered condition manifest drifted")
    rows = execution.get("rows", [])
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise ProtocolViolation("recovered execution rows are malformed")
    observed = {
        (int(row["seed"]), int(row["source"]), str(row["fold"]), str(row["scenario"]), str(row["condition"]))
        for row in rows
    }
    expected = _expected_execution_rows()
    if len(rows) != len(observed) or observed != expected:
        raise ProtocolViolation(f"recovered execution row inventory mismatch: {len(observed)} != {len(expected)}")
    if execution.get("labels_joined_after_observation_extraction") is not True:
        raise ProtocolViolation("recovered execution did not declare label isolation")
    if execution.get("optimizer_steps") is not False or execution.get("test_result_metrics_computed") is not True:
        raise ProtocolViolation("recovered execution flags are inconsistent")
    ledger_rel = execution.get("execution_ledger")
    if not isinstance(ledger_rel, str):
        raise ProtocolViolation("recovered execution ledger path is missing")
    ledger_path = ROOT / ledger_rel
    if not ledger_path.is_file() or _sha(ledger_path) != execution.get("execution_ledger_sha256"):
        raise ProtocolViolation("recovered continuation ledger hash mismatch")
    ledger_records = [json.loads(line) for line in ledger_path.read_text().splitlines() if line.strip()]
    events = [str(record.get("event")) for record in ledger_records]
    if not events or events[0] != "continuation_start" or events[-1] != "continuation_complete":
        raise ProtocolViolation("recovered continuation ledger lacks clean start/terminal events")
    if any(event in {"process_exception", "retry", "resume", "overwrite"} for event in events):
        raise ProtocolViolation("recovered continuation ledger contains invalid event")
    expected_backend = {
        "cudnn_deterministic": True,
        "cudnn_benchmark": False,
        "deterministic_algorithms": False,
        "matmul_precision": "highest",
        "matmul_allow_tf32": False,
        "cudnn_allow_tf32": False,
    }
    backend = execution.get("backend_environment", {})
    if any(backend.get(key) != value for key, value in expected_backend.items()):
        raise ProtocolViolation("recovered backend fingerprint differs from F-v4 contract")
    return {
        "status": "PASS",
        "row_count": len(rows),
        "ledger_path": str(ledger_path.relative_to(ROOT)),
        "ledger_sha256": _sha(ledger_path),
        "ledger_event_count": len(events),
        "output_dir": str(output_dir.relative_to(ROOT)),
    }


def _load_hashed_array(relative: str, expected_sha256: str) -> np.ndarray:
    path = ROOT / relative
    if not path.is_file() or _sha(path) != expected_sha256:
        raise ProtocolViolation(f"artifact hash mismatch: {relative}")
    return np.load(path, allow_pickle=False)


def _validate_primary_probe_artifact(
    probes: Mapping[str, Any],
    results: Mapping[str, Any],
    seed: int,
    arm: str,
    architecture: str,
    pooled_ap: dict[str, np.ndarray],
    scenario_ap: dict[str, np.ndarray],
    discrepancies: list[str],
) -> None:
    name = f"{arm}_{architecture}"
    stem = f"seed{seed}_{name}"
    artifact = probes.get("artifacts", {}).get(stem)
    if not isinstance(artifact, Mapping):
        raise ProtocolViolation(f"missing probe artifact {stem}")
    labels = _load_hashed_array(artifact["labels"], artifact["labels_sha256"]).astype(np.int8)
    prediction = _load_hashed_array(artifact["prediction"], artifact["prediction_sha256"]).astype(np.float64)
    test_features_path = ROOT / artifact["test_features"]
    if _sha(test_features_path) != artifact["test_features_sha256"]:
        raise ProtocolViolation(f"test feature hash mismatch: {stem}")
    with np.load(test_features_path, allow_pickle=False) as cached:
        test_x = np.asarray(cached["test_X"], dtype=np.float64)
    keys_path = ROOT / artifact["keys"]
    if _sha(keys_path) != artifact["keys_sha256"]:
        raise ProtocolViolation(f"test key hash mismatch: {stem}")
    keys = json.loads(keys_path.read_text())
    assert_unique_keys(keys)
    expected_dim = EXPECTED_DIMS.get(arm)
    if expected_dim is None or test_x.shape != (len(labels), expected_dim):
        raise ProtocolViolation(f"test feature dimension mismatch: {stem}")
    if len(keys) != len(labels) or prediction.shape != labels.shape or test_x.shape[0] != len(labels):
        raise ProtocolViolation(f"primary artifact cardinality mismatch: {stem}")
    if not np.isfinite(test_x).all() or not np.isfinite(prediction).all() or not np.isin(labels, [0, 1]).all():
        raise ProtocolViolation(f"primary artifact non-finite/nonbinary: {stem}")
    if row_key_hash(keys) != artifact.get("test_row_key_sha256"):
        raise ProtocolViolation(f"primary row-key hash mismatch: {stem}")
    if any(int(key["source_seed"]) not in TEST_SOURCES or str(key["scenario"]) not in SHIFTED_SCENARIOS for key in keys):
        raise ProtocolViolation(f"primary artifact source/scenario mismatch: {stem}")
    if {str(key["scenario"]) for key in keys} != set(SHIFTED_SCENARIOS):
        raise ProtocolViolation(f"primary test cohort is not pooled over all shifted scenarios: {stem}")
    if any(str(key.get("condition")) not in {"none", "spike", "collective", "dependency", "mixture"} for key in keys):
        raise ProtocolViolation(f"primary test cohort contains an unknown condition: {stem}")

    # Numeric probe replay and train-only scaler/C validation.
    replay = ordinary._probe_prediction(artifact, test_x)
    if not np.allclose(replay, prediction, atol=1e-12, rtol=1e-10):
        raise ProtocolViolation(f"saved test prediction differs from probe replay: {stem}")
    coef = np.asarray(artifact.get("coef"), dtype=np.float64)
    intercept = np.asarray(artifact.get("intercept"), dtype=np.float64)
    if _canonical_array_sha(coef) != artifact.get("coef_sha256") or _canonical_array_sha(intercept) != artifact.get("intercept_sha256"):
        raise ProtocolViolation(f"coefficient/intercept hash mismatch: {stem}")
    if object_sha(artifact.get("scaler")) != artifact.get("scaler_sha256"):
        raise ProtocolViolation(f"scaler hash mismatch: {stem}")
    tv_path = ROOT / artifact["train_validation_arrays"]
    if _sha(tv_path) != artifact["train_validation_arrays_sha256"]:
        raise ProtocolViolation(f"train/validation array hash mismatch: {stem}")
    with np.load(tv_path, allow_pickle=False) as tv:
        train_x = np.asarray(tv["train_X"], dtype=np.float64)
        train_y = np.asarray(tv["train_y"], dtype=np.int8)
        validation_x = np.asarray(tv["validation_X"], dtype=np.float64)
        validation_y = np.asarray(tv["validation_y"], dtype=np.int8)
    if train_x.ndim != 2 or train_x.shape[1] != expected_dim or train_y.shape != (train_x.shape[0],) or not np.isfinite(train_x).all() or not np.isin(train_y, [0, 1]).all():
        raise ProtocolViolation(f"training probe arrays malformed: {stem}")
    if validation_x.ndim != 2 or validation_x.shape[1] != expected_dim or validation_y.shape != (validation_x.shape[0],) or not np.isfinite(validation_x).all() or not np.isin(validation_y, [0, 1]).all():
        raise ProtocolViolation(f"validation probe arrays malformed: {stem}")
    train_keys_path = ROOT / artifact["train_keys"]
    validation_keys_path = ROOT / artifact["validation_keys"]
    if _sha(train_keys_path) != artifact["train_keys_sha256"] or _sha(validation_keys_path) != artifact["validation_keys_sha256"]:
        raise ProtocolViolation(f"train/validation key hash mismatch: {stem}")
    train_keys = json.loads(train_keys_path.read_text())
    validation_keys = json.loads(validation_keys_path.read_text())
    assert_unique_keys(train_keys)
    assert_unique_keys(validation_keys)
    if len(train_keys) != len(train_x) or len(validation_keys) != len(validation_x):
        raise ProtocolViolation(f"train/validation key cardinality mismatch: {stem}")
    if row_key_hash(train_keys) != artifact.get("train_row_key_sha256") or row_key_hash(validation_keys) != artifact.get("validation_row_key_sha256"):
        raise ProtocolViolation(f"train/validation row-key hash mismatch: {stem}")
    if any(int(key["source_seed"]) not in range(1000, 1010) for key in train_keys):
        raise ProtocolViolation(f"training fold leakage: {stem}")
    if any(int(key["source_seed"]) not in range(2000, 2005) for key in validation_keys):
        raise ProtocolViolation(f"validation fold leakage: {stem}")
    if {str(key.get("scenario")) for key in train_keys} != set(SHIFTED_SCENARIOS) or {str(key.get("scenario")) for key in validation_keys} != set(SHIFTED_SCENARIOS):
        raise ProtocolViolation(f"train/validation probe is not pooled over all shifted scenarios: {stem}")
    scaler = artifact["scaler"]
    mean = train_x.mean(axis=0)
    scale = train_x.std(axis=0, ddof=0)
    scale[scale == 0] = 1.0
    if scaler.get("fit_fold") != "train" or not np.allclose(mean, scaler["mean"], atol=1e-12, rtol=1e-10) or not np.allclose(scale, scaler["scale"], atol=1e-12, rtol=1e-10):
        raise ProtocolViolation(f"scaler is not train-only: {stem}")
    validation_labels = _load_hashed_array(artifact["validation_labels"], artifact["validation_labels_sha256"]).astype(np.int8)
    if not np.array_equal(validation_labels, validation_y) or validation_x.shape[0] != len(validation_labels):
        raise ProtocolViolation(f"validation labels/rows mismatch: {stem}")
    expected_counts = {
        "train_class_counts": np.bincount(train_y, minlength=2).tolist(),
        "validation_class_counts": np.bincount(validation_labels, minlength=2).tolist(),
        "test_class_counts": np.bincount(labels, minlength=2).tolist(),
    }
    for field, counts in expected_counts.items():
        if field in artifact and artifact.get(field) != counts:
            raise ProtocolViolation(f"{field} differs from primitive labels: {stem}")
    candidates = artifact.get("validation_candidates", [])
    if tuple(float(row["C"]) for row in candidates) != tuple(float(value) for value in C_GRID):
        raise ProtocolViolation(f"C grid mismatch: {stem}")
    candidate_aps: list[tuple[float, float]] = []
    for candidate in candidates:
        c_value = str(float(candidate["C"]))
        prediction_meta = artifact.get("validation_prediction_paths", {}).get(c_value)
        if not prediction_meta:
            raise ProtocolViolation(f"missing validation prediction: {stem}/C={c_value}")
        validation_prediction = _load_hashed_array(prediction_meta["path"], prediction_meta["sha256"]).astype(np.float64)
        if validation_prediction.shape != validation_labels.shape or not np.isfinite(validation_prediction).all():
            raise ProtocolViolation(f"validation prediction shape mismatch: {stem}/C={c_value}")
        ap = ordinary._ap(validation_labels, validation_prediction)
        _assert_close_reported(f"validation AP {stem}/C={c_value}", ap, candidate["ap"])
        candidate_aps.append((ap, float(candidate["C"])))
    best_ap = max(ap for ap, _ in candidate_aps)
    selected = min(c for ap, c in candidate_aps if ap == best_ap)
    if float(artifact["selected_C"]) != selected:
        raise ProtocolViolation(f"selected C is not validation winner: {stem}")

    source_ap = ordinary._source_pooled_ap(labels, prediction, keys)
    scenario_values = ordinary._source_scenario_ap(labels, prediction, keys)
    pooled_ap[name][:, DETECTOR_SEEDS.index(seed)] = source_ap
    scenario_ap[name][:, DETECTOR_SEEDS.index(seed), :] = scenario_values
    reported = results.get("test_ap", {}).get(str(seed), {}).get(name, {})
    _assert_close_reported(f"test AP {stem}", ordinary._ap(labels, prediction), reported.get("ap"))
    if int(reported.get("n", -1)) != len(labels) or int(reported.get("positives", -1)) != int(labels.sum()):
        raise ProtocolViolation(f"reported test class counts differ: {stem}")
    if tuple(np.asarray(reported.get("scenario_ap", []), dtype=np.float64).shape) != scenario_values.shape or not np.array_equal(np.asarray(reported.get("scenario_ap"), dtype=np.float64), scenario_values):
        raise ProtocolViolation(f"reported source/scenario AP differs: {stem}")
    if reported.get("labels_sha256") != artifact.get("labels_sha256") or reported.get("prediction_sha256") != artifact.get("prediction_sha256"):
        raise ProtocolViolation(f"reported primitive hash differs: {stem}")
    if reported.get("row_key_sha256") != artifact.get("test_row_key_sha256"):
        raise ProtocolViolation(f"reported test row-key summary mismatch: {stem}")


def _scientific_audit(
    execution: Mapping[str, Any],
    probes: Mapping[str, Any],
    results: Mapping[str, Any],
    statistics: Mapping[str, Any],
    decision: Mapping[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    """Independently recompute scientific primitives for recovered output."""
    discrepancies: list[str] = []
    artifacts = probes.get("artifacts", {})
    expected_names = {f"seed{seed}_{arm}_{architecture}" for seed in DETECTOR_SEEDS for arm in ARMS for architecture in ARCHITECTURES}
    if set(artifacts) != expected_names:
        discrepancies.append("primary probe artifact set mismatch")
    pooled_ap = {f"{arm}_{architecture}": np.full((len(TEST_SOURCES), len(DETECTOR_SEEDS)), np.nan) for arm in ARMS for architecture in ARCHITECTURES}
    scenario_ap = {f"{arm}_{architecture}": np.full((len(TEST_SOURCES), len(DETECTOR_SEEDS), len(SHIFTED_SCENARIOS)), np.nan) for arm in ARMS for architecture in ARCHITECTURES}
    for seed in DETECTOR_SEEDS:
        for arm in ARMS:
            for architecture in ARCHITECTURES:
                try:
                    _validate_primary_probe_artifact(probes, results, seed, arm, architecture, pooled_ap, scenario_ap, discrepancies)
                except (OSError, KeyError, ValueError, ProtocolViolation) as exc:
                    discrepancies.append(f"{seed}/{arm}/{architecture}: {exc}")

    # Exact paired row identities and labels across architectures/arms.
    for seed in DETECTOR_SEEDS:
        reference_by_arch: dict[str, tuple[list[dict[str, Any]], np.ndarray]] = {}
        for arm in ARMS:
            pairs = []
            for architecture in ARCHITECTURES:
                stem = f"seed{seed}_{arm}_{architecture}"
                artifact = artifacts.get(stem, {})
                try:
                    keys = json.loads((ROOT / artifact["keys"]).read_text())
                    labels = _load_hashed_array(artifact["labels"], artifact["labels_sha256"]).astype(np.int8)
                    pairs.append((architecture, keys, labels))
                except (OSError, KeyError, ValueError, ProtocolViolation) as exc:
                    discrepancies.append(f"paired artifact {stem}: {exc}")
            if len(pairs) == 2:
                try:
                    assert_same_row_order(pairs[0][1], pairs[1][1])
                    if not np.array_equal(pairs[0][2], pairs[1][2]):
                        raise ProtocolViolation("paired labels differ")
                except ProtocolViolation as exc:
                    discrepancies.append(f"cross-backbone cohort {seed}/{arm}: {exc}")
        for architecture in ARCHITECTURES:
            reference = artifacts.get(f"seed{seed}_history14_{architecture}", {})
            if not reference:
                continue
            reference_keys = json.loads((ROOT / reference["keys"]).read_text())
            reference_labels = _load_hashed_array(reference["labels"], reference["labels_sha256"]).astype(np.int8)
            for arm in ARMS[1:]:
                other = artifacts.get(f"seed{seed}_{arm}_{architecture}", {})
                try:
                    other_keys = json.loads((ROOT / other["keys"]).read_text())
                    other_labels = _load_hashed_array(other["labels"], other["labels_sha256"]).astype(np.int8)
                    assert_same_row_order(reference_keys, other_keys)
                    if not np.array_equal(reference_labels, other_labels):
                        raise ProtocolViolation("within-backbone labels differ")
                except (OSError, KeyError, ValueError, ProtocolViolation) as exc:
                    discrepancies.append(f"within-backbone cohort {seed}/{architecture}/{arm}: {exc}")

    # Shared CANDI history is a single immutable tensor reused by both arms.
    for seed in DETECTOR_SEEDS:
        control = probes.get("shared_control_artifacts", {}).get(str(seed), {})
        try:
            x_control = _load_hashed_array(control["x_path"], control["x_sha256"])
            l_control = _load_hashed_array(control["l_path"], control["l_sha256"])
            x_art = artifacts[f"seed{seed}_candi_history14_xlstm"]
            l_art = artifacts[f"seed{seed}_candi_history14_lstm"]
            x_keys = json.loads((ROOT / x_art["keys"]).read_text())
            l_keys = json.loads((ROOT / l_art["keys"]).read_text())
            if x_control.shape != tuple(control["shape"]) or x_control.ndim != 2 or x_control.shape[1] != 14 or not np.array_equal(x_control, l_control, equal_nan=True):
                raise ProtocolViolation("shared CANDI history values differ")
            if len(x_keys) != x_control.shape[0] or len(l_keys) != x_control.shape[0]:
                raise ProtocolViolation("shared CANDI history/key cardinality differs")
            if row_key_hash(x_keys) != control.get("row_key_sha256") or row_key_hash(l_keys) != control.get("row_key_sha256"):
                raise ProtocolViolation("shared CANDI history row-key hash differs")
            assert_same_row_order(x_keys, l_keys)
            if row_key_hash(x_keys) != x_art.get("test_row_key_sha256") or row_key_hash(l_keys) != l_art.get("test_row_key_sha256"):
                raise ProtocolViolation("shared CANDI history is not the primary paired cohort")
            if any(int(key["timestamp"]) < 63 for key in x_keys):
                raise ProtocolViolation("CANDI history contains a pre-common-stream timestamp")
        except (OSError, KeyError, ValueError, ProtocolViolation) as exc:
            discrepancies.append(f"shared CANDI control {seed}: {exc}")

    # Verify the runner's per-source AP primitives and means, not only the
    # downstream delta summaries.
    reported_pooled = results.get("pooled_source_ap", {})
    reported_means = results.get("pooled_source_ap_mean", {})
    for name, values in pooled_ap.items():
        try:
            saved = np.asarray(reported_pooled[name], dtype=np.float64)
            if saved.shape != values.shape or not np.array_equal(saved, values):
                raise ProtocolViolation(f"reported pooled source AP differs: {name}")
            _assert_close_reported(f"pooled source AP mean {name}", float(values.mean()), reported_means.get(name))
        except (KeyError, TypeError, ValueError, ProtocolViolation) as exc:
            discrepancies.append(f"pooled AP {name}: {exc}")

    # Reuse the ordinary pure semantic/robustness checks; duplicate the
    # numeric primary fit under robustness stems because robustness artifacts
    # intentionally store subgroup arrays, not a second probe definition.
    robustness_probe = dict(probes)
    robustness_probe["artifacts"] = dict(probes.get("artifacts", {}))
    for stem in probes.get("robustness_artifacts", {}):
        parts = str(stem).split("_", 2)
        if len(parts) == 3:
            primary_stem = f"{parts[0]}_{parts[2]}"
            if primary_stem in robustness_probe["artifacts"]:
                robustness_probe["artifacts"][stem] = robustness_probe["artifacts"][primary_stem]
    semantic_audit = ordinary._audit_semantic_control(probes, discrepancies)
    robustness_audit = ordinary._audit_robustness(robustness_probe, results, discrepancies)

    reconstructed = {
        "h2": pooled_ap["history_plus_combined248_xlstm"] - pooled_ap["history14_xlstm"],
        "h3a_a": pooled_ap["combined234_xlstm"] - pooled_ap["combined234_lstm"],
        "h3a_b": (pooled_ap["history_plus_combined248_xlstm"] - pooled_ap["history14_xlstm"]) - (pooled_ap["history_plus_combined248_lstm"] - pooled_ap["history14_lstm"]),
        "h3a_c": (pooled_ap["candi_history_plus_combined248_xlstm"] - pooled_ap["candi_history14_xlstm"]) - (pooled_ap["candi_history_plus_combined248_lstm"] - pooled_ap["candi_history14_lstm"]),
    }
    reconstructed_scenario = {
        "h2": scenario_ap["history_plus_combined248_xlstm"] - scenario_ap["history14_xlstm"],
        "h3a_a": scenario_ap["combined234_xlstm"] - scenario_ap["combined234_lstm"],
        "h3a_b": (scenario_ap["history_plus_combined248_xlstm"] - scenario_ap["history14_xlstm"]) - (scenario_ap["history_plus_combined248_lstm"] - scenario_ap["history14_lstm"]),
        "h3a_c": (scenario_ap["candi_history_plus_combined248_xlstm"] - scenario_ap["candi_history14_xlstm"]) - (scenario_ap["candi_history_plus_combined248_lstm"] - scenario_ap["candi_history14_lstm"]),
    }
    delta_arrays: dict[str, np.ndarray] = {}
    for name, expected in reconstructed.items():
        artifact = probes.get("delta_artifacts", {}).get(name, {})
        try:
            saved = _load_hashed_array(artifact["path"], artifact["sha256"])
            if saved.shape != expected.shape or not np.array_equal(saved, expected):
                raise ProtocolViolation(f"saved delta differs from AP recomputation: {name}")
            result_digest = results.get("delta_sha256", {}).get(name)
            result_shape = results.get("delta_shape", {}).get(name)
            if result_digest != _canonical_array_sha(expected) or result_shape != list(expected.shape):
                raise ProtocolViolation(f"reported delta hash/shape differs: {name}")
            delta_arrays[name] = expected
            reported_scenario = np.asarray(results.get("scenario_deltas", {}).get(name, {}).get("values", []), dtype=np.float64)
            if reported_scenario.shape != reconstructed_scenario[name].shape or not np.array_equal(reported_scenario, reconstructed_scenario[name]):
                raise ProtocolViolation(f"reported scenario delta differs: {name}")
            scenario_meta = results.get("scenario_deltas", {}).get(name, {})
            if scenario_meta.get("shape") != list(reconstructed_scenario[name].shape) or scenario_meta.get("sha256") != _canonical_array_sha(reconstructed_scenario[name]):
                raise ProtocolViolation(f"reported scenario delta hash/shape differs: {name}")
        except (OSError, KeyError, ValueError, ProtocolViolation) as exc:
            discrepancies.append(f"delta {name}: {exc}")

    independent_statistics: dict[str, Any] = {}
    if len(delta_arrays) == 4:
        expected_family = ("h2", "h3a_a", "h3a_b", "h3a_c")
        if statistics.get("family_size") != HOLM_FAMILY_SIZE or statistics.get("alpha") != HOLM_ALPHA or tuple(statistics.get("members", ())) != expected_family:
            discrepancies.append("confirmatory family metadata differs from the frozen four-member family")
        if set(statistics.get("comparisons", {})) != set(expected_family):
            discrepancies.append("confirmatory statistics comparison set is not exactly four members")
        p_values = []
        for name, values in delta_arrays.items():
            summary = ordinary._bootstrap_primary(values)
            summary["raw_p"] = ordinary._sign_flip_primary(values)
            independent_statistics[name] = summary
            p_values.append(summary["raw_p"])
        for name, adjusted in zip(("h2", "h3a_a", "h3a_b", "h3a_c"), ordinary._holm(p_values)):
            independent_statistics[name]["holm_adjusted_p"] = adjusted
        for name, summary in independent_statistics.items():
            reported = statistics.get("comparisons", {}).get(name, {})
            if reported.get("draws") != BOOTSTRAP_DRAWS or reported.get("seed") != BOOTSTRAP_SEED:
                discrepancies.append(f"bootstrap metadata mismatch: {name}")
            for field in ("mean", "raw_p", "holm_adjusted_p"):
                _assert_close_reported(f"statistic {name}/{field}", summary[field], reported.get(field))
            for index, bound in enumerate(summary["ci95"]):
                _assert_close_reported(f"bootstrap {name}/ci95[{index}]", bound, reported.get("ci95", [None, None])[index])
        counts = {
            name: {
                "positive_detector_seeds": int((values.mean(axis=0) > 0).sum()),
                "positive_scenarios": int((reconstructed_scenario[name].mean(axis=(0, 1)) > 0).sum()),
            }
            for name, values in delta_arrays.items()
        }
        h2_robustness = robustness_audit.get("h2_status") == "PASS"
        h3_robustness = robustness_audit.get("h3a_status_if_primary_h2_go") == "PASS"
        h2_summary = independent_statistics["h2"]
        h2_expected = "GO" if ordinary._independent_h2(
            h2_summary["mean"], h2_summary["ci95"][0], h2_summary["holm_adjusted_p"],
            counts["h2"]["positive_detector_seeds"], counts["h2"]["positive_scenarios"], h2_robustness,
        ) else "STOP"
        try:
            _assert_decision_matches("H2 Boolean decision", h2_expected, decision.get("H2"))
        except ProtocolViolation as exc:
            discrepancies.append(str(exc))
        if decision.get("h2_positive_detector_seeds") != counts["h2"]["positive_detector_seeds"] or decision.get("h2_positive_scenarios") != counts["h2"]["positive_scenarios"]:
            discrepancies.append("H2 positivity counts differ from independent recomputation")
        if h2_expected == "GO":
            h3_repro = all(counts[name]["positive_detector_seeds"] >= 4 and counts[name]["positive_scenarios"] >= 3 for name in ("h3a_a", "h3a_b", "h3a_c"))
            if decision.get("h3a_reproducibility") != counts or decision.get("h3a_reproducibility_pass") is not h3_repro:
                discrepancies.append("H3a reproducibility counts differ from independent recomputation")
            h3_args = [
                {"mean": independent_statistics[name]["mean"], "ci_lower": independent_statistics[name]["ci95"][0], "p": independent_statistics[name]["holm_adjusted_p"]}
                for name in ("h3a_a", "h3a_b", "h3a_c")
            ]
            h3_expected = "GO" if ordinary._independent_h3(True, h3_args[0], h3_args[1], h3_args[2], h3_repro, h3_robustness) else "STOP"
        else:
            h3_expected = "NOT_ELIGIBLE"
            if decision.get("h3a_reproducibility") not in ({}, None) or decision.get("h3a_reproducibility_pass") not in (False, None):
                discrepancies.append("ineligible H3a decision carries an unexpected reproducibility claim")
        try:
            _assert_decision_matches("H3a Boolean decision", h3_expected, decision.get("H3a"))
            _assert_decision_matches("H3b consequence", "UNLOCKED" if h3_expected == "GO" else "LOCKED", decision.get("H3b"))
        except ProtocolViolation as exc:
            discrepancies.append(str(exc))
    else:
        discrepancies.append("four confirmatory delta primitives were not reconstructed")

    return {
        "verdict": "PASS_SCIENTIFIC_AUDIT" if not discrepancies else "STOP_RESULT_INVALID",
        "discrepancies": discrepancies,
        "output_dir": str(output_dir.relative_to(ROOT)),
        "execution_status": execution.get("status"),
        "recomputed_primary_effects": {name: value.tolist() for name, value in reconstructed.items()},
        "recomputed_scenario_effect_shapes": {name: list(value.shape) for name, value in reconstructed_scenario.items()},
        "independent_statistics": independent_statistics,
        "semantic_nonidentifiability_audit": semantic_audit,
        "duration_severity_robustness_audit": robustness_audit,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_draws": BOOTSTRAP_DRAWS,
        "sign_flip_seed": SIGN_FLIP_SEED,
        "holm_family_size": HOLM_FAMILY_SIZE,
        "outcome_exposure": "recovered scientific labels/results are audited after continuation",
    }


def audit_recovered(output_dir: Path, continuation_seal: str) -> dict[str, Any]:
    """Audit one recovered execution with explicit two-seal provenance."""
    output_dir = Path(output_dir).expanduser().resolve()
    if output_dir == ROOT or ROOT not in output_dir.parents:
        raise ProtocolViolation("recovered audit output must be a strict repository descendant")
    if output_dir == CACHE_DIR or CACHE_DIR in output_dir.parents:
        raise ProtocolViolation("recovered audit output may not be inside the quarantined cache")
    missing = [name for name in REQUIRED_OUTPUTS if not (output_dir / name).is_file()]
    if missing:
        raise ProtocolViolation(f"missing recovered execution artifacts: {missing}")
    execution = _json(output_dir / "g1_execution_manifest.json")
    probes = _json(output_dir / "g1_probe_manifest.json")
    results = _json(output_dir / "g1_results.json")
    statistics = _json(output_dir / "g1_statistics.json")
    decision = _json(output_dir / "g1_decision.json")
    _verify_decision_markdown(output_dir / "g1_decision.md", decision)

    review = _verify_continuation_review_seal(continuation_seal)
    current_hashes = {relative: _sha(ROOT / relative) for relative in CONTINUATION_REVIEWED_EXECUTABLES}
    reviewed_commit = review["reviewed_commit"]
    implementation_hashes = {relative: _sha_bytes(_git_bytes(reviewed_commit, relative)) for relative in CONTINUATION_REVIEWED_EXECUTABLES}
    seal_hashes = {relative: _sha_bytes(_git_bytes(continuation_seal, relative)) for relative in CONTINUATION_REVIEWED_EXECUTABLES}
    patch_audit = _json(PATCH_AUDIT_PATH)
    expected_scientific = {
        relative: str(details["patch_sha256"])
        for relative, details in patch_audit.get("audit", {}).get("sealed_scientific_files", {}).items()
    }
    _verify_scientific_file_seal(expected_scientific)
    execution_scientific = execution.get("scientific_file_sha256", {})
    lineage = {
        "reviewed_commit": reviewed_commit,
        "review_verdict": review.get("verdict"),
        "current_head": _git_head(),
        "continuation_seal": continuation_seal,
        "reviewed_executable_sha256": current_hashes,
    }
    _validate_recovered_lineage_values(
        execution,
        continuation_seal,
        lineage["current_head"],
        review,
        current_hashes,
        implementation_hashes,
        seal_executable_sha256=seal_hashes,
        implementation_is_ancestor=True,
        code_sha256=str(execution.get("code_sha256")),
        expected_code_sha256=current_hashes["scripts/phase_g1_continue_from_cache.py"],
        runner_sha256=current_hashes["scripts/phase_g1_run.py"],
        expected_runner_sha256=_sha_bytes(_git_bytes(REPORTING_PATCH, "scripts/phase_g1_run.py")),
        scientific_file_sha256=execution_scientific,
        expected_scientific_file_sha256=expected_scientific,
        duration_status=_json(ROOT / "configs" / "phase_g1.json").get("duration_severity_matching", {}).get("status"),
    )
    cache = _verify_cache_provenance(execution)
    execution_audit = _verify_recovered_execution_manifest(execution, output_dir)
    scientific = _scientific_audit(execution, probes, results, statistics, decision, output_dir)
    for field, expected_value in (
        ("h1_controlled_harm", "STOP"),
        ("h1_natural_harm", "NOT_RUN"),
        ("h1_harm_overall", "UNRESOLVED"),
    ):
        if decision.get(field) != expected_value:
            scientific.setdefault("discrepancies", []).append(f"{field} changed from frozen H1 status")
    if scientific.get("discrepancies"):
        scientific["verdict"] = "STOP_RESULT_INVALID"
    return {
        **scientific,
        "lineage": lineage,
        "cache_provenance": cache,
        "execution_manifest_audit": execution_audit,
        "G1_PRELABEL_SEAL_COMMIT": ORIGINAL_PRELABEL_SEAL,
        "execution_commit": continuation_seal,
        "reviewed_implementation_commit": reviewed_commit,
        "files_audited": list(REQUIRED_OUTPUTS),
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--continuation-seal", required=True)
    args = parser.parse_args()
    report_dir = REPORT_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    try:
        result = audit_recovered(args.output_dir, args.continuation_seal)
    except (ProtocolViolation, FileNotFoundError, KeyError, ValueError, OSError) as exc:
        result = {
            "verdict": "STOP_RESULT_UNRESOLVED",
            "G1_PRELABEL_SEAL_COMMIT": ORIGINAL_PRELABEL_SEAL,
            "execution_commit": args.continuation_seal,
            "discrepancies": [repr(exc)],
        }
    (report_dir / "g1_self_review_postrun_recovered.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    lines = [
        "# Recovered Phase-G1 post-run scientific self-review",
        "",
        f"Verdict: {result.get('verdict')}",
        "",
        f"G1_PRELABEL_SEAL_COMMIT: {result.get('G1_PRELABEL_SEAL_COMMIT')}",
        f"CONTINUATION_EXECUTION_SEAL: {result.get('execution_commit')}",
        "",
        "Discrepancies:",
    ]
    lines.extend(f"- {item}" for item in result.get("discrepancies", []))
    (report_dir / "g1_self_review_postrun_recovered.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"verdict": result.get("verdict"), "discrepancies": result.get("discrepancies", [])}, sort_keys=True))
    if result.get("verdict") != "PASS_SCIENTIFIC_AUDIT":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
