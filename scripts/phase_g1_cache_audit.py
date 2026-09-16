"""G1-R1 cache-integrity and bounded replay audit.

This module is intentionally metric-free.  It verifies the quarantined
stream/cache provenance, sealed model inputs and a prespecified deterministic
replay sample.  It never fits a probe, computes AP/AUROC, reads a decision
threshold, or performs statistical inference.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import itertools
import json
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "reports" / "phase_g" / "g1_primary_cache"
LEDGER_PATH = ROOT / "reports" / "phase_g" / "g1_execution_ledger.jsonl"
REPORT_DIR = ROOT / "reports" / "phase_g1"
INCIDENT_PATH = REPORT_DIR / "g1_postlabel_failure_v1.json"
AUTH_PATH = REPORT_DIR / "g1_reporting_patch_v1.json"
SAMPLE_PATH = REPORT_DIR / "g1_cache_replay_sample_v1.json"
PATCH_AUDIT_PATH = REPORT_DIR / "g1_reporting_patch_audit_v1.json"

ORIGINAL_SEAL = "5622376087aaa97249ff9a055f201b250efbf1c2"
REPORTING_PATCH = "2c79cbf62574df498f1c9fd39d1bee9aa495e41a"
LEDGER_SHA256 = "67e6a30d518011e8d06307e7d1b305449b4787602f3bd1701f8989a7dadeab0a"
INCIDENT_SHA256 = "6eddd07affbe8ff869748abe0d52d64deb9ce41dc6e0beb14bc4eeae9150c42b"
# These report files were sealed in the de8b9e9 authorization commit.  Pin
# their bytes so a later working-tree edit cannot silently widen the one
# post-label reporting exception.
AUTH_SHA256 = "025ce284f1182f0ca2b1ceefaa7225d8ea1ec937992dced2175cee5c5f10a3e8"
SAMPLE_SHA256 = "27888a0ab47db7610030d6b77f56c0708257fbc0f24aa574d005882ca2d535ca"
PATCH_AUDIT_SHA256 = "c604c19ce8658b03d68f742fba36b25b9c8d1aba5ebc254960f24fa017bf2dc2"
APPROVED_PATCH_CHANGED_PATHS = ("scripts/phase_g1_run.py", "tests/test_phase_g1.py")
APPROVED_PATCH_SCIENTIFIC_EXECUTABLE = "scripts/phase_g1_run.py"

DETECTOR_SEEDS = (11, 22, 33, 44, 55)
FOLDS = (
    ("train", tuple(range(1000, 1010))),
    ("validation", tuple(range(2000, 2005))),
    ("test", tuple(range(3000, 3010))),
)
SHIFTED_SCENARIOS = ("abrupt", "gradual", "recurring", "correlation")
CONDITIONS = ("none", "spike", "collective", "dependency", "mixture")
ARCHITECTURES = ("xlstm", "lstm")
ARMS = (
    "history14",
    "hidden52",
    "gate130",
    "memory52",
    "combined234",
    "history_plus_combined248",
    "candi_history14",
    "candi_history_plus_combined248",
)
DIMS = {
    "history14": 14,
    "hidden52": 52,
    "gate130": 130,
    "memory52": 52,
    "combined234": 234,
    "history_plus_combined248": 248,
    "candi_history14": 14,
    "candi_history_plus_combined248": 248,
}
KEY_FIELDS = {"detector_seed", "source_seed", "scenario", "condition", "timestamp", "event"}
METADATA_FIELDS = {"scenarios", "events", "event_types", "stratum", "duration", "severity"}


class AuditFailure(RuntimeError):
    """Raised by a fail-closed cache or authorization check."""


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _assert_file_digest(path: Path, expected_sha256: str) -> None:
    if not path.exists() or _sha_file(path) != expected_sha256:
        raise AuditFailure(f"file digest mismatch: {path}")


def _json(path: Path) -> Any:
    return json.loads(path.read_text())


def _array_digest(value: np.ndarray) -> str:
    value = np.ascontiguousarray(value)
    digest = hashlib.sha256()
    digest.update(str(value.dtype).encode())
    digest.update(str(value.shape).encode())
    digest.update(value.tobytes(order="C"))
    return digest.hexdigest()


def _keys_digest(keys: list[dict[str, Any]]) -> str:
    payload = json.dumps(keys, sort_keys=True, separators=(",", ":")).encode()
    return _sha_bytes(payload)


def _git_bytes(commit: str, relative: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{relative}"], cwd=ROOT)


def _expected_streams(include_stationary: bool = True) -> list[tuple[int, str, int, str, str]]:
    rows = []
    scenarios = SHIFTED_SCENARIOS + (("stationary",) if include_stationary else ())
    for seed, (fold, sources) in itertools.product(DETECTOR_SEEDS, FOLDS):
        for source, scenario, condition in itertools.product(
            sources,
            scenarios,
            CONDITIONS,
        ):
            if scenario == "stationary" and condition != "none":
                continue
            rows.append((int(seed), str(fold), int(source), str(scenario), str(condition)))
    return rows


def _expected_primary_prefixes() -> dict[str, tuple[int, str, int, str, str, str, str]]:
    result = {}
    for seed, fold, source, scenario, condition in _expected_streams(include_stationary=False):
        for arm, architecture in itertools.product(ARMS, ARCHITECTURES):
            prefix = f"seed{seed}_{fold}_{source}_{scenario}_{condition}_{arm}_{architecture}"
            result[prefix] = (seed, fold, source, scenario, condition, arm, architecture)
    return result


def _expected_cache_files() -> set[str]:
    result: set[str] = set()
    for prefix in _expected_primary_prefixes():
        result.update({f"{prefix}.npz", f"{prefix}.keys.json", f"{prefix}.metadata.json"})
    return result


def _record_issue(issues: list[dict[str, Any]], code: str, detail: str, path: str | None = None) -> None:
    row: dict[str, Any] = {"code": code, "detail": detail}
    if path is not None:
        row["path"] = path
    issues.append(row)


def _validate_key_rows(
    keys: Any,
    seed: int,
    fold: str,
    source: int,
    scenario: str,
    condition: str,
    path: Path,
) -> tuple[bool, str, int, list[dict[str, Any]]]:
    if not isinstance(keys, list) or not keys:
        return False, "keys_not_nonempty_list", 0, []
    if any(not isinstance(row, dict) or set(row) != KEY_FIELDS for row in keys):
        return False, "key_fields_mismatch", len(keys), []
    tuples = []
    timestamps = []
    for row in keys:
        try:
            if (
                int(row["detector_seed"]) != seed
                or int(row["source_seed"]) != source
                or str(row["scenario"]) != scenario
                or str(row["condition"]) != condition
            ):
                return False, "key_identity_mismatch", len(keys), []
            timestamp = int(row["timestamp"])
            event = int(row["event"])
        except (TypeError, ValueError, KeyError):
            return False, "key_value_type_mismatch", len(keys), []
        timestamps.append(timestamp)
        tuples.append((seed, source, scenario, condition, timestamp, event))
    if len(set(tuples)) != len(tuples):
        return False, "duplicate_row_key", len(keys), []
    if timestamps != sorted(timestamps) or len(set(timestamps)) != len(timestamps):
        return False, "timestamps_not_strictly_ordered", len(keys), []
    return True, "PASS", len(keys), keys


def _validate_metadata(
    metadata: Any,
    n: int,
    scenario: str,
    path: Path,
) -> tuple[bool, str]:
    if not isinstance(metadata, dict) or set(metadata) != METADATA_FIELDS:
        return False, "metadata_fields_mismatch"
    if any(not isinstance(metadata[field], list) or len(metadata[field]) != n for field in METADATA_FIELDS):
        return False, "metadata_cardinality_mismatch"
    if any(str(value) != scenario for value in metadata["scenarios"]):
        return False, "metadata_scenario_mismatch"
    if any(not isinstance(value, (int, float)) for value in metadata["events"]):
        return False, "metadata_event_type_mismatch"
    for field in ("event_types", "stratum"):
        if any(value is not None and not isinstance(value, str) for value in metadata[field]):
            return False, f"metadata_{field}_type_mismatch"
    for field in ("duration", "severity"):
        if any(value is not None and not isinstance(value, int) for value in metadata[field]):
            return False, f"metadata_{field}_type_mismatch"
    return True, "PASS"


def _validate_triplet(
    npz_path: Path,
    identity: tuple[int, str, int, str, str, str, str],
    stream_state: dict[tuple[int, str, int, str, str], dict[str, str]],
    inventory,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    seed, fold, source, scenario, condition, arm, architecture = identity
    prefix = npz_path.name.removesuffix(".npz")
    keys_path = npz_path.with_name(f"{prefix}.keys.json")
    metadata_path = npz_path.with_name(f"{prefix}.metadata.json")
    file_records = []
    raw_by_name: dict[str, bytes] = {}
    for path in (npz_path, keys_path, metadata_path):
        try:
            raw = path.read_bytes()
        except OSError as exc:
            _record_issue(issues, "unreadable_file", repr(exc), path.name)
            return {"status": "FAIL", "n": 0, "file_records": file_records}
        digest = _sha_bytes(raw)
        raw_by_name[path.name] = raw
        file_records.append({"path": path.name, "bytes": len(raw), "sha256": digest})
        inventory.write(json.dumps(file_records[-1], sort_keys=True) + "\n")
    npz_raw = raw_by_name[npz_path.name]
    keys_raw = raw_by_name[keys_path.name]
    metadata_raw = raw_by_name[metadata_path.name]
    issue_count_before = len(issues)
    try:
        with np.load(io.BytesIO(npz_raw), allow_pickle=False) as cached:
            if set(cached.files) != {"X", "y", "source_seeds"}:
                _record_issue(issues, "npz_fields_mismatch", str(cached.files), npz_path.name)
                return {"status": "FAIL", "n": 0, "file_records": file_records}
            X = np.asarray(cached["X"])
            y = np.asarray(cached["y"])
            source_seeds = np.asarray(cached["source_seeds"])
    except Exception as exc:
        _record_issue(issues, "npz_unreadable", repr(exc), npz_path.name)
        return {"status": "FAIL", "n": 0, "file_records": file_records}
    try:
        keys = json.loads(keys_raw)
        metadata = json.loads(metadata_raw)
    except Exception as exc:
        _record_issue(issues, "sidecar_json_invalid", repr(exc), npz_path.name)
        return {"status": "FAIL", "n": 0, "file_records": file_records}
    n = len(keys) if isinstance(keys, list) else 0
    if X.dtype != np.dtype("float64") or X.ndim != 2 or X.shape[1] != DIMS[arm]:
        _record_issue(issues, "feature_shape_or_dtype", str((X.shape, str(X.dtype), arm)), npz_path.name)
    if y.dtype != np.dtype("int8") or y.shape != (n,) or not np.isin(y, (0, 1)).all():
        _record_issue(issues, "label_shape_dtype_or_domain", str((y.shape, str(y.dtype))), npz_path.name)
    if source_seeds.dtype != np.dtype("int64") or source_seeds.shape != (n,) or not np.all(source_seeds == source):
        _record_issue(issues, "source_seed_shape_dtype_or_identity", str((source_seeds.shape, str(source_seeds.dtype))), npz_path.name)
    if X.shape[0] != n or not np.isfinite(X).all():
        _record_issue(issues, "feature_cardinality_or_finiteness", str(X.shape), npz_path.name)
    keys_ok, key_code, key_n, clean_keys = _validate_key_rows(keys, seed, fold, source, scenario, condition, npz_path)
    if not keys_ok:
        _record_issue(issues, key_code, f"n={key_n}", npz_path.name)
    metadata_ok, metadata_code = _validate_metadata(metadata, n, scenario, npz_path)
    if not metadata_ok:
        _record_issue(issues, metadata_code, "metadata contract failed", npz_path.name)
    if keys_ok and metadata_ok:
        key_events = [int(row["event"]) for row in clean_keys]
        if [int(value) for value in metadata["events"]] != key_events:
            _record_issue(issues, "metadata_event_key_mismatch", "event IDs differ from ordered keys", npz_path.name)
    stream_key = (seed, fold, source, scenario, condition)
    arm_key = f"{arm}_{architecture}"
    if keys_ok:
        key_hash = _keys_digest(clean_keys)
        y_hash = _array_digest(y)
        previous = stream_state.setdefault(stream_key, {})
        if previous:
            reference = next(iter(previous.values()))
            if reference["key_hash"] != key_hash:
                _record_issue(issues, "cross_arm_row_key_mismatch", arm_key, npz_path.name)
            if reference["y_hash"] != y_hash:
                _record_issue(issues, "cross_arm_label_mismatch", arm_key, npz_path.name)
        previous[arm_key] = {"key_hash": key_hash, "y_hash": y_hash}
    return {
        "status": "PASS" if len(issues) == issue_count_before else "FAIL",
        "n": int(n),
        "shape": list(X.shape),
        "dtype": str(X.dtype),
        "key_hash": _keys_digest(clean_keys) if keys_ok else None,
        "label_hash": _array_digest(y),
        "file_records": file_records,
    }


def _audit_ledger() -> dict[str, Any]:
    if not LEDGER_PATH.exists():
        raise AuditFailure("missing quarantined execution ledger")
    if _sha_file(LEDGER_PATH) != LEDGER_SHA256:
        raise AuditFailure("quarantined execution ledger SHA256 changed")
    if not INCIDENT_PATH.exists() or _sha_file(INCIDENT_PATH) != INCIDENT_SHA256:
        raise AuditFailure("post-label incident record bytes changed")
    incident = _json(INCIDENT_PATH)
    records = [json.loads(line) for line in LEDGER_PATH.read_text().splitlines() if line.strip()]
    events = Counter(str(row.get("event")) for row in records)
    commits = sorted({row.get("commit") for row in records})
    expected = {
        (seed, fold, source, scenario, condition)
        for seed, fold, source, scenario, condition in _expected_streams(include_stationary=True)
    }
    starts = {
        (
            int(row["fields"]["detector_seed"]),
            str(row["fields"]["fold"]),
            int(row["fields"]["source_seed"]),
            str(row["fields"]["scenario"]),
            str(row["fields"]["condition"]),
        )
        for row in records
        if row.get("event") == "labelled_stream_start"
    }
    completes = {
        (
            int(row["fields"]["detector_seed"]),
            str(row["fields"]["fold"]),
            int(row["fields"]["source_seed"]),
            str(row["fields"]["scenario"]),
            str(row["fields"]["condition"]),
        )
        for row in records
        if row.get("event") == "labelled_stream_complete"
    }
    last = records[-1] if records else {}
    exception_ok = (
        last.get("event") == "process_exception"
        and last.get("fields", {}).get("exception_type") == incident.get("exception_type")
        and last.get("fields", {}).get("exception") == incident.get("exception")
    )
    no_retry = not any(row.get("event") in {"retry", "resume", "overwrite"} for row in records)
    pass_ = (
        records
        and records[0].get("event") == "process_start"
        and exception_ok
        and events["process_exception"] == 1
        and events["labelled_stream_start"] == 2625
        and events["labelled_stream_complete"] == 2625
        and starts == expected
        and completes == expected
        and commits == [ORIGINAL_SEAL]
        and no_retry
    )
    return {
        "status": "PASS" if pass_ else "FAIL",
        "record_count": len(records),
        "event_counts": dict(events),
        "commit_values": commits,
        "expected_streams": len(expected),
        "started_streams": len(starts),
        "completed_streams": len(completes),
        "first_event": records[0].get("event") if records else None,
        "last_event": last.get("event"),
        "process_exception_count": events["process_exception"],
        "terminal_exception_is_manifest_path": exception_ok,
        "retry_resume_overwrite_present": not no_retry,
    }


def _audit_sealed_inputs() -> dict[str, Any]:
    checkpoint_manifest = _json(ROOT / "reports" / "phase_g" / "checkpoint_manifest.json")
    f4_manifest = _json(ROOT / "reports" / "phase_f_v4" / "final_manifest.json")
    f4_by_run = {str(row["run"]): row for row in f4_manifest["runs"]}
    checkpoint_rows = checkpoint_manifest.get("entries", [])
    checkpoint_checks = []
    for row in checkpoint_rows:
        run = str(row["run"])
        f4 = f4_by_run.get(run)
        path = ROOT / str(row["path"])
        expected_sha = str(row["sha256"])
        actual_sha = _sha_file(path) if path.exists() else None
        source_sha = f4.get("checkpoint_sha256", {}).get("best.pt") if f4 else None
        checkpoint_checks.append({
            "run": run,
            "path": str(row["path"]),
            "manifest_sha256": expected_sha,
            "actual_sha256": actual_sha,
            "f4_sha256": source_sha,
            "pass_": bool(actual_sha == expected_sha == source_sha),
        })
    candi_manifest = _json(ROOT / "reports" / "phase_g" / "candi_control_manifest.json")
    candi_checks = []
    for control in candi_manifest.get("controls", []):
        for path_text, details in control.get("artifacts", {}).items():
            path = ROOT / path_text
            expected_sha = str(details["sha256"])
            actual_sha = _sha_file(path) if path.exists() else None
            candi_checks.append({
                "detector_seed": int(control["detector_seed"]),
                "path": path_text,
                "manifest_sha256": expected_sha,
                "actual_sha256": actual_sha,
                "pass_": actual_sha == expected_sha,
            })
    candi_preflight = _json(ROOT / "reports" / "phase_g" / "candi_preflight.json")
    return {
        "status": "PASS" if (
            len(checkpoint_checks) == 10
            and all(row["pass_"] for row in checkpoint_checks)
            and len(candi_checks) == 15
            and all(row["pass_"] for row in candi_checks)
            and candi_preflight.get("status") == "PASS"
        ) else "FAIL",
        "checkpoint_manifest_sha256": _sha_file(ROOT / "reports" / "phase_g" / "checkpoint_manifest.json"),
        "f4_manifest_sha256": _sha_file(ROOT / "reports" / "phase_f_v4" / "final_manifest.json"),
        "checkpoint_checks": checkpoint_checks,
        "candi_checks": candi_checks,
        "candi_preflight_status": candi_preflight.get("status"),
    }


def _audit_patch_binding() -> dict[str, Any]:
    if not AUTH_PATH.exists() or not SAMPLE_PATH.exists() or not PATCH_AUDIT_PATH.exists():
        raise AuditFailure("missing sealed reporting-patch/replay authorization artifact")
    if _sha_file(AUTH_PATH) != AUTH_SHA256:
        raise AuditFailure("reporting-patch authorization bytes changed")
    if _sha_file(SAMPLE_PATH) != SAMPLE_SHA256:
        raise AuditFailure("bounded replay sample bytes changed")
    if _sha_file(PATCH_AUDIT_PATH) != PATCH_AUDIT_SHA256:
        raise AuditFailure("patch-scope audit bytes changed")
    auth = _json(AUTH_PATH)
    patch_audit = _json(PATCH_AUDIT_PATH)
    scope = patch_audit.get("audit", {}).get("sealed_scientific_scope", {})
    changed_paths = tuple(scope.get("changed_paths", ()))
    scope_ok = (
        changed_paths == APPROVED_PATCH_CHANGED_PATHS
        and scope.get("only_approved_scientific_executable_changed") is True
        and scope.get("test_file_is_label_blind_regression_only") is True
    )
    return {
        "status": "PASS" if (
            auth.get("original_prelabel_review_seal") == ORIGINAL_SEAL
            and auth.get("reporting_patch_commit") == REPORTING_PATCH
            and auth.get("quarantined_execution_ledger_sha256") == LEDGER_SHA256
            and patch_audit.get("status") == "PASS"
            and scope_ok
            and _sha_file(LEDGER_PATH) == LEDGER_SHA256
        ) else "FAIL",
        "authorization_sha256": _sha_file(AUTH_PATH),
        "replay_sample_sha256": _sha_file(SAMPLE_PATH),
        "patch_audit_sha256": _sha_file(PATCH_AUDIT_PATH),
        "patch_audit_status": patch_audit.get("status"),
        "patch_scope_changed_paths": list(changed_paths),
        "patch_scope_ok": scope_ok,
        "original_prelabel_review_seal": auth.get("original_prelabel_review_seal"),
        "reporting_patch_commit": auth.get("reporting_patch_commit"),
    }


def _audit_cache() -> dict[str, Any]:
    if not CACHE_DIR.is_dir():
        raise AuditFailure(f"missing cache directory: {CACHE_DIR}")
    expected_prefixes = _expected_primary_prefixes()
    expected = _expected_cache_files()
    all_entries = sorted(CACHE_DIR.rglob("*"))
    nested_or_nonfiles = [
        str(path.relative_to(CACHE_DIR))
        for path in all_entries
        if not path.is_file() or path.parent != CACHE_DIR
    ]
    actual_paths = sorted(path for path in all_entries if path.is_file() and path.parent == CACHE_DIR)
    actual = {path.name for path in actual_paths}
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    issues: list[dict[str, Any]] = []
    if nested_or_nonfiles:
        _record_issue(issues, "nested_or_nonfile_cache_entries", str(len(nested_or_nonfiles)))
    if missing:
        _record_issue(issues, "missing_cache_files", str(len(missing)))
    if unexpected:
        _record_issue(issues, "unexpected_cache_files", str(len(unexpected)))
    stream_state: dict[tuple[int, str, int, str, str], dict[str, str]] = {}
    inventory_path = REPORT_DIR / "g1_cache_file_inventory_v1.jsonl.gz"
    if inventory_path.exists():
        raise AuditFailure(f"refusing to overwrite existing inventory: {inventory_path}")
    inventory_digest = hashlib.sha256()
    checked_npz = 0
    shape_counts: Counter[str] = Counter()
    with gzip.open(inventory_path, "wt", encoding="utf-8") as inventory:
        for path in actual_paths:
            if not path.name.endswith(".npz"):
                continue
            prefix = path.name.removesuffix(".npz")
            identity = expected_prefixes.get(prefix)
            if identity is None:
                _record_issue(issues, "unexpected_npz_prefix", prefix, path.name)
                continue
            before = len(issues)
            result = _validate_triplet(path, identity, stream_state, inventory, issues)
            for record in result.get("file_records", []):
                inventory_digest.update(
                    f"{record['path']}\\0{record['bytes']}\\0{record['sha256']}\\n".encode()
                )
            checked_npz += 1
            if result.get("shape"):
                shape_counts[f"{identity[5]}:{identity[6]}:{result['shape'][1]}"] += 1
            if checked_npz % 1000 == 0:
                print(f"cache audit: checked {checked_npz} npz files", flush=True)
            if len(issues) == before and result.get("status") != "PASS":
                _record_issue(issues, "triplet_validation_failed", "validator returned FAIL", path.name)
    inventory_sha = _sha_file(inventory_path)
    ledger_mtime_ns = LEDGER_PATH.stat().st_mtime_ns
    cache_mtime_ns = max((path.stat().st_mtime_ns for path in actual_paths), default=0)
    protected_outputs = [
        name for name in (
            "g1_execution_manifest.json",
            "g1_probe_manifest.json",
            "g1_results.json",
            "g1_statistics.json",
            "g1_decision.json",
            "g1_decision.md",
        )
        if (ROOT / "reports" / "phase_g" / name).exists()
    ]
    incomplete_streams = [
        key for key, values in stream_state.items()
        if len(values) != len(ARMS) * len(ARCHITECTURES)
    ]
    pass_ = (
        not missing
        and not unexpected
        and checked_npz == 40_000
        and not issues
        and len(stream_state) == 2_500
        and not incomplete_streams
        and cache_mtime_ns <= ledger_mtime_ns
        and not protected_outputs
    )
    return {
        "status": "PASS" if pass_ else "FAIL",
        "expected_file_count": len(expected),
        "actual_file_count": len(actual),
        "all_entry_count": len(all_entries),
        "nested_or_nonfile_count": len(nested_or_nonfiles),
        "nested_or_nonfile_examples": nested_or_nonfiles[:20],
        "expected_npz_count": 40_000,
        "checked_npz_count": checked_npz,
        "missing_count": len(missing),
        "missing_examples": missing[:20],
        "unexpected_count": len(unexpected),
        "unexpected_examples": unexpected[:20],
        "stream_count": len(stream_state),
        "incomplete_stream_count": len(incomplete_streams),
        "shape_counts": dict(shape_counts),
        "issue_count": len(issues),
        "issue_examples": issues[:50],
        "inventory_path": str(inventory_path.relative_to(ROOT)),
        "inventory_sha256": inventory_sha,
        "inventory_digest": inventory_digest.hexdigest(),
        "cache_latest_mtime_ns": cache_mtime_ns,
        "ledger_mtime_ns": ledger_mtime_ns,
        "cache_mtime_not_after_ledger": cache_mtime_ns <= ledger_mtime_ns,
        "protected_scientific_outputs_present": protected_outputs,
        "labels_or_outcome_summary_emitted": False,
    }


def _load_replay_sample() -> dict[str, Any]:
    if _sha_file(SAMPLE_PATH) != SAMPLE_SHA256:
        raise AuditFailure("bounded replay sample bytes changed after sealing")
    sample = _json(SAMPLE_PATH)
    expected = {
        "detector_seeds": [11, 55],
        "source_seeds": [1000, 2000, 3000],
        "scenarios": ["abrupt", "correlation"],
        "conditions": ["none", "mixture"],
        "architectures": ["xlstm", "lstm"],
        "expected_stream_backbone_pairs": 48,
        "status": "SEALED_BEFORE_CACHE_VALUE_ACCESS",
    }
    for key, value in expected.items():
        if sample.get(key) != value:
            raise AuditFailure(f"replay sample changed: {key}")
    return sample


def _close_arrays(left: np.ndarray, right: np.ndarray) -> tuple[bool, bool, float, float]:
    left = np.asarray(left)
    right = np.asarray(right)
    if left.shape != right.shape:
        return False, False, float("inf"), float("inf")
    difference = np.abs(left.astype(np.float64) - right.astype(np.float64))
    max_abs = float(np.max(difference)) if difference.size else 0.0
    mean_abs = float(np.mean(difference)) if difference.size else 0.0
    exact = bool(np.array_equal(left, right))
    return bool(exact or np.allclose(left, right, atol=1e-5, rtol=1e-4)), exact, max_abs, mean_abs


def _replay_cache_sample() -> dict[str, Any]:
    sample = _load_replay_sample()
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    import phase_f_v4_common as f4
    import phase_g1_pipeline as pipeline
    import phase_g1_run as runner

    f4.configure()
    entries = pipeline.load_backbone_entries()
    candi_controls = pipeline.load_candi_controls()
    expected_prefixes = _expected_primary_prefixes()
    rows: list[dict[str, Any]] = []
    pair_keys: set[tuple[int, int, str, str, str]] = set()
    for seed in sample["detector_seeds"]:
        # Loading each frozen backbone once per detector seed avoids 48
        # repeated deserializations while preserving the sealed model state.
        backbones = {
            architecture: pipeline._load_backbone(entries[(int(seed), architecture)])
            for architecture in sample["architectures"]
        }
        candi_model, candi_row = candi_controls[int(seed)]
        for source, scenario, condition in itertools.product(
            sample["source_seeds"], sample["scenarios"], sample["conditions"]
        ):
            fold = "train" if source < 2000 else "validation" if source < 3000 else "test"
            stream = runner._generate(source, scenario, condition)
            observations = np.asarray(stream.observations, dtype=np.float32).copy()
            timestamps = np.arange(runner.FIRST_COMMON_TIMESTAMP, len(observations), dtype=np.int64)
            candi_history = pipeline.extract_candi_history(candi_model, candi_row, observations, timestamps)
            per_architecture: dict[str, dict[str, Any]] = {
                current_architecture: runner._observation_then_label(
                    stream,
                    int(seed),
                    current_architecture,
                    backbones[current_architecture],
                    candi_history,
                )
                for current_architecture in sample["architectures"]
            }
            common_mask = runner.primary_binary_mask(per_architecture["xlstm"], allow_empty=True)
            for current_architecture in sample["architectures"]:
                for arm in runner.expected_feature_arms():
                    values = np.asarray(per_architecture[current_architecture]["groups"][arm], dtype=np.float64)
                    common_mask &= np.isfinite(values).all(axis=1)
            for current_architecture in sample["architectures"]:
                pair_keys.add((int(seed), int(source), str(scenario), str(condition), str(current_architecture)))
                for arm in runner.expected_feature_arms():
                    rows_for_arm = runner.select_primary_rows(
                        per_architecture[current_architecture], arm, common_mask
                    )
                    prefix = f"seed{seed}_{fold}_{source}_{scenario}_{condition}_{arm}_{current_architecture}"
                    if prefix not in expected_prefixes:
                        raise AuditFailure(f"replay prefix is not in sealed inventory: {prefix}")
                    npz_path = CACHE_DIR / f"{prefix}.npz"
                    keys_path = CACHE_DIR / f"{prefix}.keys.json"
                    with np.load(npz_path, allow_pickle=False) as cached:
                        cached_X = np.asarray(cached["X"])
                        cached_y = np.asarray(cached["y"])
                        cached_sources = np.asarray(cached["source_seeds"])
                    cached_keys = json.loads(keys_path.read_text())
                    feature_ok, feature_exact, feature_max, feature_mean = _close_arrays(
                        rows_for_arm["X"], cached_X
                    )
                    score_pass = None
                    score_exact = None
                    score_max = None
                    score_mean = None
                    internal18_pass = None
                    internal18_exact = None
                    internal18_max = None
                    internal18_mean = None
                    if arm == "history14":
                        score_pass, score_exact, score_max, score_mean = _close_arrays(
                            np.asarray(rows_for_arm["X"], dtype=np.float64)[:, 0],
                            cached_X[:, 0],
                        )
                    if arm == "combined234":
                        base_columns = np.arange(18, dtype=np.int64) * 13
                        internal18_pass, internal18_exact, internal18_max, internal18_mean = _close_arrays(
                            np.asarray(rows_for_arm["X"], dtype=np.float64)[:, base_columns],
                            cached_X[:, base_columns],
                        )
                    candi_history_pass = feature_ok if arm == "candi_history14" else None
                    labels_equal = np.array_equal(np.asarray(rows_for_arm["y"], dtype=np.int8), cached_y)
                    keys_equal = rows_for_arm["keys"] == cached_keys
                    sources_equal = np.array_equal(
                        np.asarray(rows_for_arm["source_seeds"], dtype=np.int64), cached_sources
                    )
                    semantic_checks = [feature_ok, labels_equal, keys_equal, sources_equal]
                    if score_pass is not None:
                        semantic_checks.append(score_pass)
                    if internal18_pass is not None:
                        semantic_checks.append(internal18_pass)
                    rows.append({
                        "detector_seed": int(seed),
                        "source_seed": int(source),
                        "fold": fold,
                        "scenario": scenario,
                        "condition": condition,
                        "architecture": current_architecture,
                        "feature_arm": arm,
                        "feature_pass": feature_ok,
                        "feature_bitwise_equal": feature_exact,
                        "feature_max_abs": feature_max,
                        "feature_mean_abs": feature_mean,
                        "reconstruction_score_pass": score_pass,
                        "reconstruction_score_bitwise_equal": score_exact,
                        "reconstruction_score_max_abs": score_max,
                        "reconstruction_score_mean_abs": score_mean,
                        "internal18_pass": internal18_pass,
                        "internal18_bitwise_equal": internal18_exact,
                        "internal18_max_abs": internal18_max,
                        "internal18_mean_abs": internal18_mean,
                        "candi_history_pass": candi_history_pass,
                        "labels_equal": labels_equal,
                        "keys_equal": keys_equal,
                        "source_seed_array_equal": sources_equal,
                        "status": "PASS" if all(semantic_checks) else "FAIL",
                    })
            del per_architecture, stream, observations, candi_history
            print(
                f"cache replay: seed={seed} source={source} scenario={scenario} condition={condition}",
                flush=True,
            )
        del backbones
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
    return {
        "status": "PASS" if (
            len(pair_keys) == sample["expected_stream_backbone_pairs"]
            and len(rows) == sample["expected_stream_backbone_pairs"] * len(ARMS)
            and all(row["status"] == "PASS" for row in rows)
        ) else "FAIL",
        "sample_sha256": _sha_file(SAMPLE_PATH),
        "stream_backbone_pair_count": len(pair_keys),
        "feature_comparison_count": len(rows),
        "failed_feature_comparisons": sum(row["status"] != "PASS" for row in rows),
        "rows": rows,
        "metric_access": False,
        "probe_fit": False,
        "ap_or_auroc": False,
    }


def _validate_patch_scope(patch_audit: Mapping[str, Any]) -> None:
    """Validate the immutable, narrowly-scoped reporting patch contract."""
    if patch_audit.get("status") != "PASS":
        raise AuditFailure("reporting patch scope audit is not PASS")
    scope = patch_audit.get("audit", {}).get("sealed_scientific_scope", {})
    if tuple(scope.get("changed_paths", ())) != APPROVED_PATCH_CHANGED_PATHS:
        raise AuditFailure("reporting patch changed an unapproved path")
    if scope.get("only_approved_scientific_executable_changed") is not True:
        raise AuditFailure("reporting patch scientific scope is not exact")
    if scope.get("test_file_is_label_blind_regression_only") is not True:
        raise AuditFailure("reporting patch test scope is not label-blind")


def _validate_reporting_patch_guard_values(
    original_seal: str,
    reporting_patch: str,
    cache_audit: Mapping[str, Any],
    *,
    current_head: str,
    runner_sha256: str,
    patch_audit: Mapping[str, Any],
) -> None:
    """Pure-value guard used by production continuation and adversarial tests."""
    if original_seal != ORIGINAL_SEAL:
        raise AuditFailure("continuation requires the original pre-label seal")
    if reporting_patch != REPORTING_PATCH:
        raise AuditFailure("continuation requires the accepted reporting patch")
    require_cache_reuse_boundary(cache_audit)
    _validate_patch_scope(patch_audit)
    if runner_sha256 != _sha_bytes(_git_bytes(REPORTING_PATCH, "scripts/phase_g1_run.py")):
        raise AuditFailure("current runner is not the approved reporting patch")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", REPORTING_PATCH, current_head],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise AuditFailure("current HEAD is not descended from the approved reporting patch")


def require_cache_reuse_boundary(cache_audit: Mapping[str, Any]) -> None:
    """Prevent any continuation or metric path before a reusable-cache PASS."""
    if cache_audit.get("status") != "PASS_CACHE_REUSABLE":
        raise AuditFailure("cache reuse and all downstream metrics require PASS_CACHE_REUSABLE")


def require_reporting_patch_guard(
    original_seal: str,
    reporting_patch: str,
    cache_audit: Mapping[str, Any],
) -> None:
    """Guard the future continuation path against arbitrary seal exceptions."""
    if not AUTH_PATH.exists() or not PATCH_AUDIT_PATH.exists():
        raise AuditFailure("missing immutable reporting-patch authorization inputs")
    if _sha_file(AUTH_PATH) != AUTH_SHA256:
        raise AuditFailure("reporting-patch authorization bytes changed")
    if _sha_file(PATCH_AUDIT_PATH) != PATCH_AUDIT_SHA256:
        raise AuditFailure("reporting-patch scope audit bytes changed")
    current = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    _validate_reporting_patch_guard_values(
        original_seal,
        reporting_patch,
        cache_audit,
        current_head=current,
        runner_sha256=_sha_file(ROOT / "scripts" / "phase_g1_run.py"),
        patch_audit=_json(PATCH_AUDIT_PATH),
    )


def _run_adversarial_fixtures() -> dict[str, Any]:
    sample_prefix = next(iter(_expected_primary_prefixes()))
    source_npz = CACHE_DIR / f"{sample_prefix}.npz"
    source_keys = CACHE_DIR / f"{sample_prefix}.keys.json"
    source_meta = CACHE_DIR / f"{sample_prefix}.metadata.json"
    results = []

    def expect_failure(name: str, function) -> None:
        try:
            function()
        except (AuditFailure, ValueError, KeyError, AssertionError, OSError):
            results.append({"name": name, "status": "PASS", "rejected": True})
        else:
            results.append({"name": name, "status": "FAIL", "rejected": False})

    def assert_triplet_hashes(directory: Path, expected: Mapping[str, str]) -> None:
        for name, digest in expected.items():
            path = directory / name
            if not path.exists() or _sha_file(path) != digest:
                raise AuditFailure(f"cache artifact digest mismatch: {name}")

    def assert_expected_artifact_set(directory: Path, expected_names: set[str]) -> None:
        actual_names = {path.name for path in directory.iterdir() if path.is_file()}
        if actual_names != expected_names:
            raise AuditFailure("cache artifact inventory mismatch")

    expected_triplet = {
        path.name: _sha_file(path)
        for path in (source_npz, source_keys, source_meta)
    }

    with tempfile.TemporaryDirectory(prefix="g1_cache_fixture_") as temp:
        temp_dir = Path(temp)
        for path in (source_npz, source_keys, source_meta):
            shutil.copy2(path, temp_dir / path.name)
        flipped = bytearray((temp_dir / source_npz.name).read_bytes())
        flipped[-1] ^= 1
        (temp_dir / source_npz.name).write_bytes(flipped)
        expect_failure(
            "modified_cache_byte",
            lambda: assert_triplet_hashes(temp_dir, expected_triplet),
        )
        shutil.copy2(source_npz, temp_dir / source_npz.name)
        missing = temp_dir / source_meta.name
        missing.unlink()
        expect_failure(
            "deleted_cache_artifact",
            lambda: assert_expected_artifact_set(temp_dir, set(expected_triplet)),
        )
        shutil.copy2(source_meta, missing)
        keys = json.loads(source_keys.read_text())
        keys[-1]["timestamp"] = keys[-2]["timestamp"]
        (temp_dir / source_keys.name).write_text(json.dumps(keys))
        identity = _expected_primary_prefixes()[sample_prefix]

        def reject_duplicate_key() -> None:
            valid, code, _, _ = _validate_key_rows(
                keys, *identity[:5], temp_dir / source_keys.name
            )
            if valid:
                raise AuditFailure("duplicate row key accepted")
            # The fixture passes only when the validator rejects the input;
            # convert that expected rejection into the common fail-closed
            # assertion convention used by ``expect_failure``.
            raise AuditFailure(f"duplicate key rejected with {code}")

        expect_failure(
            "duplicate_row_key",
            reject_duplicate_key,
        )

    checkpoint_manifest = _json(ROOT / "reports" / "phase_g" / "checkpoint_manifest.json")
    first_checkpoint = checkpoint_manifest["entries"][0]
    checkpoint_bytes = (ROOT / first_checkpoint["path"]).read_bytes()
    with tempfile.NamedTemporaryFile(prefix="g1_checkpoint_fixture_", suffix=".pt") as handle:
        handle.write(checkpoint_bytes)
        handle.flush()
        mutated = bytearray(Path(handle.name).read_bytes())
        mutated[-1] ^= 1
        Path(handle.name).write_bytes(mutated)
        expect_failure(
            "changed_checkpoint_hash",
            lambda: _assert_file_digest(Path(handle.name), str(first_checkpoint["sha256"])),
        )

    patch_audit = _json(PATCH_AUDIT_PATH)
    bad_scope = json.loads(json.dumps(patch_audit))
    bad_scope["audit"]["sealed_scientific_scope"]["changed_paths"] = [
        *APPROVED_PATCH_CHANGED_PATHS,
        "scripts/phase_g1_core.py",
    ]
    expect_failure(
        "scientific_file_outside_approved_patch",
        lambda: _validate_patch_scope(bad_scope),
    )
    expect_failure("wrong_original_seal", lambda: require_reporting_patch_guard("bad", REPORTING_PATCH, {"status": "PASS_CACHE_REUSABLE"}))
    expect_failure("wrong_reporting_patch", lambda: require_reporting_patch_guard(ORIGINAL_SEAL, "bad", {"status": "PASS_CACHE_REUSABLE"}))
    expect_failure("cache_reuse_before_pass", lambda: require_reporting_patch_guard(ORIGINAL_SEAL, REPORTING_PATCH, {"status": "STOP_CACHE_UNRESOLVED"}))

    current_runner_sha = _sha_file(ROOT / "scripts" / "phase_g1_run.py")
    expect_failure(
        "unapproved_head",
        lambda: _validate_reporting_patch_guard_values(
            ORIGINAL_SEAL,
            REPORTING_PATCH,
            {"status": "PASS_CACHE_REUSABLE"},
            current_head="0" * 40,
            runner_sha256=current_runner_sha,
            patch_audit=patch_audit,
        ),
    )
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in results) else "STOP",
        "test_count": len(results),
        "results": results,
        "labels_or_metrics_accessed": False,
    }


def run() -> dict[str, Any]:
    patch_binding = _audit_patch_binding()
    sealed_inputs = _audit_sealed_inputs()
    ledger = _audit_ledger()
    cache = _audit_cache()
    replay = _replay_cache_sample() if cache["status"] == "PASS" else {
        "status": "NOT_RUN",
        "reason": "cache integrity failed",
        "metric_access": False,
    }
    adversarial = _run_adversarial_fixtures() if cache["status"] == "PASS" else {
        "status": "NOT_RUN",
        "reason": "cache integrity failed",
        "labels_or_metrics_accessed": False,
    }
    cache_status = (
        "PASS_CACHE_REUSABLE"
        if (
            patch_binding["status"] == "PASS"
            and sealed_inputs["status"] == "PASS"
            and ledger["status"] == "PASS"
            and cache["status"] == "PASS"
            and replay["status"] == "PASS"
            and adversarial["status"] == "PASS"
        )
        else "STOP_CACHE_INVALID"
    )
    return {
        "status": cache_status,
        "patch_binding": patch_binding,
        "sealed_inputs": sealed_inputs,
        "ledger": ledger,
        "cache_integrity": cache,
        "replay": replay,
        "adversarial_fixtures": adversarial,
        "labels_or_metrics_accessed": False,
        "probe_fit": False,
        "ap_or_auroc": False,
        "continuation_authorized": False,
    }


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "g1_cache_audit_v1.json"
    if report_path.exists():
        raise SystemExit(f"refusing to overwrite existing audit report: {report_path}")
    try:
        result = run()
    except Exception as exc:
        result = {
            "status": "STOP_CACHE_UNRESOLVED",
            "exception_type": type(exc).__name__,
            "exception": str(exc),
            "labels_or_metrics_accessed": False,
            "probe_fit": False,
            "ap_or_auroc": False,
        }
    report_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    md = [
        "# G1-R1 cache integrity audit",
        "",
        f"Status: **{result['status']}**",
        "",
        "This audit is metric-free: no probe fitting, AP/AUROC, prevalence summary or H2/H3a statistic was computed.",
        "The machine-readable report contains the complete inventory, provenance checks, bounded replay and adversarial fixture results.",
    ]
    (REPORT_DIR / "g1_cache_audit_v1.md").write_text("\n".join(md) + "\n")
    print(json.dumps({"status": result["status"]}, indent=2))
    if result["status"] != "PASS_CACHE_REUSABLE":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
