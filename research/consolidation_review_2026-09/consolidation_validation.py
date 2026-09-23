"""Consolidation validation for consolidation/observable-control-line.

Read-only.  Performs git ancestry and object-identity checks, re-aggregates the
committed A+, A+S and nonlinear results into a temporary directory and compares
them with the committed files, verifies every reports/*/SHA256SUMS, checks the
row-key contract across all runs, and scans current-facing documents for
prohibited wording.  No model is fitted and no cache is read.

Run from the repository root of a git checkout:

    PYTHONPATH=.:scripts python research/consolidation_review_2026-09/consolidation_validation.py \
        --output /tmp/consolidation_validation.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

ANCESTORS = {
    "main_base": "2810c346d40ceb3e011625f6fbf63db8833d9572",
    "A+": "04e0abbd7a9a6a8c8d00052cd1b20c51e0a71d28",
    "A+_review": "f1967b6a9d3801bf1a3c962def32fc3a08b30732",
    "A+S": "ccb9a3d7e8fc1ced5707b5691de6b09a90f3736f",
    "nonlinear": "0b00d6f97635f991c8f12c2e34be9b1073d7f33d",
    "consolidation_review": "aa0860cbbc67e6d58baf73f3c7fd9c9d6a484bd4",
    "A+_seal": "de76db7",
    "nonlinear_seal": "61e57ef7894c8db7faaeb5efc2fd63fb5f58956e",
}
REVIEW_FILES = (
    "research/temporally_matched_observable_control/independent_review.md",
    "research/temporally_matched_observable_control/independent_review_numbers.csv",
    "research/temporally_matched_observable_control/independent_review_recompute.py",
)
# path -> commit whose object must be identical at HEAD
FROZEN = {
    "reports": ANCESTORS["main_base"],
    "m0": ANCESTORS["main_base"],
    "data": ANCESTORS["main_base"],
    "configs": ANCESTORS["nonlinear"],
    "scripts": ANCESTORS["nonlinear"],
    "tests": ANCESTORS["nonlinear"],
    "research/strong_observable_control": ANCESTORS["main_base"],
    "research/framing-refresh-2026-09": ANCESTORS["main_base"],
    "research/temporally_matched_observable_control/protocol.md": ANCESTORS["A+"],
    "research/temporally_matched_observable_control/results.json": ANCESTORS["A+"],
    "research/temporally_matched_observable_control/results.md": ANCESTORS["A+"],
    "research/temporally_matched_observable_control/results": ANCESTORS["A+"],
    "research/temporally_matched_observable_control/execution.md": ANCESTORS["A+"],
    "research/temporally_matched_observable_control/red_team.md": ANCESTORS["A+"],
    "research/temporally_matched_observable_control/scientific_assessment.md": ANCESTORS["A+"],
    "research/aplus_solver_convergence_audit": ANCESTORS["A+S"],
    "research/nonlinear_observable_control/protocol.md": ANCESTORS["nonlinear"],
    "research/nonlinear_observable_control/preflight.json": ANCESTORS["nonlinear"],
    "research/nonlinear_observable_control/preflight.md": ANCESTORS["nonlinear"],
    "research/nonlinear_observable_control/runs": ANCESTORS["nonlinear"],
    "research/nonlinear_observable_control/results.json": ANCESTORS["nonlinear"],
    "research/nonlinear_observable_control/results.md": ANCESTORS["nonlinear"],
    "research/nonlinear_observable_control/source_seed_effects.csv": ANCESTORS["nonlinear"],
    "research/nonlinear_observable_control/statistical_assessment.md": ANCESTORS["nonlinear"],
    "research/nonlinear_observable_control/scientific_assessment.md": ANCESTORS["nonlinear"],
    "research/nonlinear_observable_control/red_team.md": ANCESTORS["nonlinear"],
}
ALLOWED_DOC_CHANGES = {
    "research/CURRENT_STATUS.md",
    "research/consolidation_review_2026-09/consolidation_review.md",
    "research/consolidation_review_2026-09/reviewer_recompute.py",
    "research/consolidation_review_2026-09/reviewer_numbers.csv",
    "research/consolidation_review_2026-09/consolidation_validation.py",
    "research/consolidation_review_2026-09/consolidation_validation.json",
    "research/consolidation_review_2026-09/final_consolidation_report.md",
    "research/nonlinear_observable_control/post_review_addendum.md",
    "research/temporally_matched_observable_control/post_review_addendum.md",
    *REVIEW_FILES,
}
CURRENT_FACING = (
    "research/CURRENT_STATUS.md",
    "research/consolidation_review_2026-09/consolidation_review.md",
    "research/nonlinear_observable_control/post_review_addendum.md",
    "research/temporally_matched_observable_control/post_review_addendum.md",
)
PROHIBITED = (
    r"observations lack", r"lack the information", r"observable insufficien",
    r"information[- ]insufficient", r"observables? (?:are|is) insufficient",
    r"residuals? (?:are|is) insufficient", r"closes all observable", r"beyond observables",
    r"beyond what is observable",
)
WORDING_RULE_HEADER = "## 8. Wording rule"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def object_id(commit: str, path: str) -> str | None:
    out = subprocess.run(["git", "rev-parse", f"{commit}:{path}"], cwd=ROOT, capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


FLOAT_RTOL = 1e-12  # admits last-ulp reduction differences across NumPy builds only


def json_equal(a, b, ignore: tuple[str, ...] = (), stats: dict | None = None) -> bool:
    """Structural equality; floats may differ by at most FLOAT_RTOL (relative)."""
    stats = stats if stats is not None else {}
    if isinstance(a, dict) and isinstance(b, dict):
        keys = (set(a) | set(b)) - set(ignore)
        return all(k in a and k in b and json_equal(a[k], b[k], ignore, stats) for k in keys)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(json_equal(x, y, ignore, stats) for x, y in zip(a, b))
    if isinstance(a, float) and isinstance(b, float) and not isinstance(a, bool):
        if a == b:
            return True
        rel = abs(a - b) / max(abs(a), abs(b))
        stats["max_rel_float_diff"] = max(stats.get("max_rel_float_diff", 0.0), rel)
        stats["inexact_floats"] = stats.get("inexact_floats", 0) + 1
        return rel <= FLOAT_RTOL
    return a == b


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    head = git("rev-parse", "HEAD")
    report: dict = {"head": head, "checks": {}}
    checks = report["checks"]

    # 1. Ancestry.
    checks["ancestry"] = {
        name: subprocess.run(["git", "merge-base", "--is-ancestor", sha, head], cwd=ROOT).returncode == 0
        for name, sha in ANCESTORS.items()
    }

    # 2. Independent review files present and byte-identical to f1967b6.
    checks["independent_review_files"] = {
        path: (ROOT / path).exists() and object_id(head, path) == object_id(ANCESTORS["A+_review"], path)
        for path in REVIEW_FILES
    }

    # 3. Frozen experimental artifacts: git object identity.
    frozen = {}
    for path, commit in FROZEN.items():
        at_head, at_source = object_id(head, path), object_id(commit, path)
        frozen[path] = {"source_commit": commit[:7], "object": at_head, "identical": at_head is not None and at_head == at_source}
    checks["frozen_artifacts"] = frozen

    # 4. Only allowed documents changed relative to the nonlinear head.
    changed = sorted(set(git("diff", "--name-only", ANCESTORS["nonlinear"], head).splitlines()))
    checks["changed_files_vs_0b00d6f"] = {"files": changed, "only_allowed": set(changed) <= ALLOWED_DOC_CHANGES}

    # 5. reports/*/SHA256SUMS (M0/G1 and phase seals).
    tracked = set(git("ls-files").splitlines())
    sums = {}
    for sums_file in sorted((ROOT / "reports").glob("*/SHA256SUMS")):
        bad, untracked_absent, verified = [], [], 0
        for line in sums_file.read_text().splitlines():
            if not line.strip():
                continue
            digest, name = line.split(maxsplit=1)
            name = name.lstrip("*")
            rel = name if (ROOT / name).exists() or name in tracked else str((sums_file.parent / name).relative_to(ROOT))
            target = ROOT / rel
            if not target.exists():
                # git-ignored artifacts (e.g. model checkpoints) that live only on the
                # training host; they are not part of the repository and cannot drift here.
                (untracked_absent if rel not in tracked else bad).append(rel)
                continue
            verified += 1
            if sha256(target) != digest:
                bad.append(rel)
        sums[str(sums_file.relative_to(ROOT))] = {
            "verified": verified, "mismatches": bad, "untracked_absent": len(untracked_absent),
        }
    checks["sha256sums"] = sums

    # 6. Re-aggregation of committed results (no fitting, no cache).
    import aplus_solver_convergence_audit as aps
    import nonlinear_observable_control as nl
    import temporally_matched_observable_control as ap

    reagg = {}
    float_stats: dict = {}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        committed = json.loads((ROOT / "research/temporally_matched_observable_control/results.json").read_text())
        fresh = ap.aggregate(ROOT / "research/temporally_matched_observable_control/results", tmp / "aplus.json")
        reagg["A+_results.json"] = json_equal(json.loads(json.dumps(fresh)), committed, stats=float_stats)
        committed = json.loads((ROOT / "research/aplus_solver_convergence_audit/s0_results.json").read_text())
        fresh = aps.run_s0(tmp / "s0.json")
        reagg["A+S_s0_results.json"] = json_equal(json.loads(json.dumps(fresh)), committed, stats=float_stats)
        for stage in ("s1", "s2"):
            committed = json.loads((ROOT / f"research/aplus_solver_convergence_audit/{stage}_summary.json").read_text())
            fresh = aps.summarize_stage(ROOT / f"research/aplus_solver_convergence_audit/{stage}", stage, tmp / f"{stage}.json")
            reagg[f"A+S_{stage}_summary.json"] = json_equal(json.loads(json.dumps(fresh)), committed, stats=float_stats)
        committed = json.loads((ROOT / "research/nonlinear_observable_control/results.json").read_text())
        fresh = nl.aggregate(ROOT / "research/nonlinear_observable_control/runs", tmp / "nl.json", ANCESTORS["nonlinear_seal"])
        reagg["nonlinear_results.json"] = json_equal(json.loads(json.dumps(fresh)), committed, ignore=("sklearn_version",), stats=float_stats)
        reagg["nonlinear_sklearn_version_committed_vs_local"] = [committed.get("sklearn_version"), fresh.get("sklearn_version")]
    reagg["float_comparison"] = {"rtol": FLOAT_RTOL, **float_stats}
    checks["reaggregation_matches_committed"] = reagg

    # 7. Headline numbers read from the committed aggregates.
    ap_res = json.loads((ROOT / "research/temporally_matched_observable_control/results.json").read_text())
    s0 = json.loads((ROOT / "research/aplus_solver_convergence_audit/s0_results.json").read_text())
    nl_res = json.loads((ROOT / "research/nonlinear_observable_control/results.json").read_text())
    report["headline_numbers"] = {
        arch: {
            "A+_source_level_mean": ap_res["architectures"][arch]["mean"],
            "A+S_S0": s0.get("architectures", s0).get(arch, None) if isinstance(s0, dict) else None,
            "nonlinear_source_level_mean": nl_res["architectures"][arch]["source_level_mean_effect"],
            "nonlinear_crossed_ci95": nl_res["architectures"][arch]["bootstrap_crossed"]["ci95"],
            "nonlinear_source_only_ci95": nl_res["architectures"][arch]["bootstrap_source_only"]["ci95"],
        }
        for arch in ("xlstm", "lstm")
    }

    # 8. Row-key contract identical across A+, A+S S1/S2 and nonlinear runs.
    rows = {}
    reference = None
    for arch in ("xlstm", "lstm"):
        for seed in (11, 22, 33):
            ap_meta = json.loads((ROOT / f"research/temporally_matched_observable_control/results/results_{arch}_{seed}.json").read_text())["row_meta"]
            nl_meta = json.loads((ROOT / f"research/nonlinear_observable_control/runs/results_{arch}_{seed}.json").read_text())["row_meta"]
            s1 = json.loads((ROOT / f"research/aplus_solver_convergence_audit/s1/s1_{arch}_{seed}.json").read_text())["row_key_sha256"]
            s2 = json.loads((ROOT / f"research/aplus_solver_convergence_audit/s2/s2_{arch}_{seed}.json").read_text())["row_key_sha256"]
            keys = {fold: ap_meta[fold]["key_sha256"] for fold in ("train", "validation", "test")}
            reference = reference or ap_meta
            rows[f"{arch}_{seed}"] = {
                "nonlinear_row_meta_equals_A+": nl_meta == ap_meta,
                "s1_keys_equal_A+": s1 == keys,
                "s2_keys_equal_A+": s2 == keys,
                "equal_to_first_run": ap_meta == reference,
            }
    checks["row_key_contract"] = {"runs": rows, "reference_row_meta": reference}

    # 9. Seals recorded in run files.
    checks["seals"] = {
        "nonlinear_runs_protocol_seal": sorted({json.loads(p.read_text())["protocol_seal"] for p in (ROOT / "research/nonlinear_observable_control/runs").glob("results_*.json")}),
        "nonlinear_preflight_seal": json.loads((ROOT / "research/nonlinear_observable_control/preflight.json").read_text())["protocol_seal"],
    }

    # 10. Prohibited wording in current-facing documents (outside the wording-rule section).
    wording = {}
    for path in CURRENT_FACING:
        text = (ROOT / path).read_text()
        if WORDING_RULE_HEADER in text:
            text = text.split(WORDING_RULE_HEADER)[0]
        hits = [pattern for pattern in PROHIBITED if re.search(pattern, text, flags=re.IGNORECASE)]
        wording[path] = hits
    checks["prohibited_wording_hits"] = wording

    # Verdict.
    ok = (
        all(checks["ancestry"].values())
        and all(checks["independent_review_files"].values())
        and all(v["identical"] for v in frozen.values())
        and checks["changed_files_vs_0b00d6f"]["only_allowed"]
        and all(not v["mismatches"] for v in sums.values())
        and all(v is True for k, v in reagg.items() if k.endswith(".json"))
        and all(all(v.values()) for v in rows.values())
        and checks["seals"]["nonlinear_runs_protocol_seal"] == [ANCESTORS["nonlinear_seal"]]
        and checks["seals"]["nonlinear_preflight_seal"] == ANCESTORS["nonlinear_seal"]
        and all(not hits for hits in wording.values())
    )
    report["status"] = "PASS" if ok else "FAIL"
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(report["status"])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
