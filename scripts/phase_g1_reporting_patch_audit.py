"""Audit the post-label G1 reporting patch without opening cache arrays.

This is an implementation/provenance audit only.  It proves that the
2c79cbf patch is limited to relative output-path handling and that the
historical pre-label review remains byte-identical.  It never loads labels,
features, checkpoints or probe results.
"""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_IMPLEMENTATION = "fe507084b9a1aba0c67a4536c5bb938ea89a4945"
ORIGINAL_SEAL = "5622376087aaa97249ff9a055f201b250efbf1c2"
REPORTING_PATCH = "2c79cbf62574df498f1c9fd39d1bee9aa495e41a"
REVIEW_PATH = "reports/phase_g1/g1_self_review_prelabel_v2.json"
RUNNER_PATH = "scripts/phase_g1_run.py"

EXPECTED_CHANGED_FILES = (
    ("A", "README.md"),
    ("M", "reports/phase_g1/adversarial_tests.json"),
    ("A", "reports/phase_g1/g1_postlabel_amendment_v1.md"),
    ("A", "reports/phase_g1/g1_postlabel_failure_v1.json"),
    ("A", "reports/phase_g1/g1_postlabel_failure_v1.md"),
    ("M", "scripts/phase_g1_run.py"),
    ("M", "tests/test_phase_g1.py"),
)

SCIENTIFIC_FILES = (
    "configs/phase_g1.json",
    "reports/m0_protocol.md",
    "reports/phase_g1/g1_1_duration_severity_amendment.md",
    "configs/synthetic_v1.json",
    "reports/phase_f/preprocessing_manifest.json",
    "reports/phase_e2/source_hashes.json",
    "reports/phase_e2/environment.json",
    "reports/phase_e2/dependency_install.json",
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


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _git_bytes(commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)


def _git_diff_names(old: str, new: str) -> tuple[tuple[str, str], ...]:
    output = subprocess.check_output(
        ["git", "diff", "--name-status", old, new], cwd=ROOT, text=True
    )
    rows = []
    for line in output.splitlines():
        if not line.strip():
            continue
        status, path = line.split("\t", 1)
        rows.append((status, path))
    return tuple(rows)


def _function_hashes(source: bytes) -> dict[str, str]:
    tree = ast.parse(source.decode("utf-8"))
    result: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result[node.name] = _sha(ast.dump(node, include_attributes=False).encode())
    return result


def _top_level_non_functions(source: bytes) -> str:
    tree = ast.parse(source.decode("utf-8"))
    nodes = [
        node
        for node in tree.body
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    return ast.dump(ast.Module(body=nodes, type_ignores=[]), include_attributes=False)


def _diff_added_lines(old: str, new: str) -> list[str]:
    diff = subprocess.check_output(
        ["git", "diff", "--no-ext-diff", "--unified=0", old, new, "--", RUNNER_PATH],
        cwd=ROOT,
        text=True,
    )
    return [
        line[1:]
        for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]


def _run_ast_scope_check() -> dict[str, Any]:
    old = _git_bytes(ORIGINAL_SEAL, RUNNER_PATH)
    new = _git_bytes(REPORTING_PATCH, RUNNER_PATH)
    old_functions = _function_hashes(old)
    new_functions = _function_hashes(new)
    common = sorted(set(old_functions) & set(new_functions))
    unchanged = [name for name in common if old_functions[name] == new_functions[name]]
    changed = [name for name in common if old_functions[name] != new_functions[name]]
    added = sorted(set(new_functions) - set(old_functions))
    removed = sorted(set(old_functions) - set(new_functions))
    added_lines = _diff_added_lines(ORIGINAL_SEAL, REPORTING_PATCH)
    allowed_fragments = (
        "def _canonical_output_dir(output_dir: Path) -> Path:",
        '    """Return an absolute output path for repository-relative artifact links.',
        "    Scientific execution accepts a relative output directory, but artifact",
        "    manifests store paths relative to ROOT.  Canonicalizing once at the",
        "    boundary keeps that serialization operation reporting-only and avoids",
        "    calling Path.relative_to() between relative and absolute paths.",
        '    """',
        "    return Path(output_dir).expanduser().resolve()",
        "    output_dir = _canonical_output_dir(output_dir)",
    )
    unexpected_additions = [
        line for line in added_lines
        if line.strip() and line not in allowed_fragments
    ]
    return {
        "old_runner_sha256": _sha(old),
        "new_runner_sha256": _sha(new),
        "function_hashes_unchanged": unchanged,
        "function_hashes_changed": changed,
        "functions_added": added,
        "functions_removed": removed,
        "top_level_non_functions_identical": _top_level_non_functions(old)
        == _top_level_non_functions(new),
        "added_source_lines": added_lines,
        "unexpected_added_source_lines": unexpected_additions,
        "pass_": (
            changed == ["run"]
            and added == ["_canonical_output_dir"]
            and not removed
            and _top_level_non_functions(old) == _top_level_non_functions(new)
            and not unexpected_additions
            and "    output_dir = _canonical_output_dir(output_dir)" in added_lines
        ),
    }


def _test_scope_check() -> dict[str, Any]:
    old = _git_bytes(ORIGINAL_SEAL, "tests/test_phase_g1.py")
    new = _git_bytes(REPORTING_PATCH, "tests/test_phase_g1.py")
    old_functions = _function_hashes(old)
    new_functions = _function_hashes(new)
    common = sorted(set(old_functions) & set(new_functions))
    changed = [name for name in common if old_functions[name] != new_functions[name]]
    added = sorted(set(new_functions) - set(old_functions))
    removed = sorted(set(old_functions) - set(new_functions))
    return {
        "old_sha256": _sha(old),
        "new_sha256": _sha(new),
        "function_hashes_changed": changed,
        "functions_added": added,
        "functions_removed": removed,
        "pass_": not changed and not removed and added == [
            "test_relative_output_dir_is_canonicalized_before_manifest_paths"
        ],
    }


def _current_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def audit() -> dict[str, Any]:
    checks: dict[str, Any] = {}
    checks["commit_lineage"] = {
        "original_implementation_is_ancestor": subprocess.run(
            ["git", "merge-base", "--is-ancestor", ORIGINAL_IMPLEMENTATION, REPORTING_PATCH],
            cwd=ROOT,
        ).returncode
        == 0,
        "original_seal_is_ancestor_of_patch": subprocess.run(
            ["git", "merge-base", "--is-ancestor", ORIGINAL_SEAL, REPORTING_PATCH],
            cwd=ROOT,
        ).returncode
        == 0,
        "current_head": _current_commit(),
        "reporting_patch_commit": REPORTING_PATCH,
    }
    checks["changed_files"] = {
        "expected": list(EXPECTED_CHANGED_FILES),
        "actual": list(_git_diff_names(ORIGINAL_SEAL, REPORTING_PATCH)),
        "pass_": _git_diff_names(ORIGINAL_SEAL, REPORTING_PATCH) == EXPECTED_CHANGED_FILES,
    }
    checks["runner_ast_scope"] = _run_ast_scope_check()
    checks["test_ast_scope"] = _test_scope_check()
    checks["prelabel_review_immutable"] = {
        "original_sha256": _sha(_git_bytes(ORIGINAL_SEAL, REVIEW_PATH)),
        "patch_sha256": _sha(_git_bytes(REPORTING_PATCH, REVIEW_PATH)),
        "working_tree_sha256": _sha((ROOT / REVIEW_PATH).read_bytes()),
        "pass_": (
            _sha(_git_bytes(ORIGINAL_SEAL, REVIEW_PATH))
            == _sha(_git_bytes(REPORTING_PATCH, REVIEW_PATH))
            == _sha((ROOT / REVIEW_PATH).read_bytes())
        ),
    }
    sealed_diffs = {}
    for relative in SCIENTIFIC_FILES:
        old = _git_bytes(ORIGINAL_SEAL, relative)
        patch = _git_bytes(REPORTING_PATCH, relative)
        current = (ROOT / relative).read_bytes()
        sealed_diffs[relative] = {
            "old_sha256": _sha(old),
            "patch_sha256": _sha(patch),
            "current_sha256": _sha(current),
            "changed_from_seal": old != patch,
            "current_matches_patch": current == patch,
        }
    checks["sealed_scientific_files"] = sealed_diffs
    checks["sealed_scientific_scope"] = {
        "changed_paths": [
            path for path, row in sealed_diffs.items() if row["changed_from_seal"]
        ],
        "only_approved_scientific_executable_changed": (
            [path for path, row in sealed_diffs.items() if row["changed_from_seal"]]
            == [RUNNER_PATH, "tests/test_phase_g1.py"]
            and sealed_diffs[RUNNER_PATH]["changed_from_seal"]
            and sealed_diffs["tests/test_phase_g1.py"]["changed_from_seal"]
        ),
        "test_file_is_label_blind_regression_only": checks["test_ast_scope"]["pass_"],
        "all_current_bytes_match_patch": all(
            row["current_matches_patch"] for row in sealed_diffs.values()
        ),
    }
    checks["authorization_record"] = json.loads(
        (ROOT / "reports/phase_g1/g1_reporting_patch_v1.json").read_text()
    )
    hard_checks = [
        checks["commit_lineage"]["original_implementation_is_ancestor"],
        checks["commit_lineage"]["original_seal_is_ancestor_of_patch"],
        checks["changed_files"]["pass_"],
        checks["runner_ast_scope"]["pass_"],
        checks["prelabel_review_immutable"]["pass_"],
        checks["sealed_scientific_scope"]["only_approved_scientific_executable_changed"],
        checks["sealed_scientific_scope"]["test_file_is_label_blind_regression_only"],
        checks["sealed_scientific_scope"]["all_current_bytes_match_patch"],
    ]
    return {
        "status": "PASS" if all(hard_checks) else "STOP",
        "audit": checks,
        "labels_opened": False,
        "cache_arrays_opened": False,
        "metrics_computed": False,
    }


def main() -> None:
    result = audit()
    report = ROOT / "reports" / "phase_g1"
    report.mkdir(parents=True, exist_ok=True)
    (report / "g1_reporting_patch_audit_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    (report / "g1_reporting_patch_audit_v1.md").write_text(
        "# G1-R1 reporting patch audit\n\n"
        f"Status: **{result['status']}**\n\n"
        "This audit opens no cache arrays, labels or scientific metrics. "
        "The machine-readable report contains the exact commit/file/function "
        "hash checks and the approved diff scope.\n"
    )
    print(json.dumps({"status": result["status"]}, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
