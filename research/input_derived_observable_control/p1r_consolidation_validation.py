"""Read-only consolidation validation for the P1r line (written before results were read).

Checks chronology and ancestry, sealed-file and preflight immutability, run and
aggregate immutability, historical-artifact identity against the pre-P1r main,
the row-key contract, execution sidecars, sealed re-aggregation, and prohibited
wording in current-facing P1r documents.  Fits nothing and reads no cache.

    PYTHONPATH=.:scripts python research/input_derived_observable_control/p1r_consolidation_validation.py --output /tmp/p1r_validation.json
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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

PRE_P1R_MAIN = "855c34d29920cc9aa85fa26d438784d150ac0d79"
SEAL = "90b2470b45b1f8e52aa95ee8677b855b2e3c4e4d"
PREFLIGHT_COMMIT = "4c22e52c876e5e6345b7553063f2fb2e97da2114"
P1R = "research/input_derived_observable_control"
RUN_NAMES = [f"{a}_{s}" for a in ("xlstm", "lstm") for s in (11, 22, 33)]
PREFLIGHT_FILES = [f"{P1R}/{f}" for f in ("preflight.json", "host_preflight.json", "preflight_local_host_nonadmissible.json", "preflight.md")]
SEALED = ["scripts", "tests", f"{P1R}/protocol.md"]
HISTORICAL = [
    "reports", "m0", "configs", "data",
    "research/strong_observable_control", "research/framing-refresh-2026-09",
    "research/temporally_matched_observable_control", "research/aplus_solver_convergence_audit",
    "research/nonlinear_observable_control", "research/consolidation_review_2026-09",
]
CURRENT_FACING = [f"{P1R}/results.md", f"{P1R}/statistical_assessment.md", f"{P1R}/scientific_assessment.md", "research/CURRENT_STATUS.md"]
PROHIBITED = (
    r"observations lack", r"lack the information", r"observable insufficien", r"information[- ]insufficient",
    r"observables? (?:are|is) insufficient", r"closes all observable", r"exhausts all observable",
    r"rules out every observable", r"beyond observables", r"beyond what is observable",
    r"xlstm (?:is )?superior", r"superiority of xlstm",
)
EXPECTED_SUBJECTS = [
    "Seal input-derived observable control (P1r) protocol",
    "Record label-blind P1r preflight (stage 1 and stage 2 PASS on cache host)",
    "Record P1r xLSTM seed-11 run", "Record P1r xLSTM seed-22 run", "Record P1r xLSTM seed-33 run",
    "Record P1r LSTM seed-11 run", "Record P1r LSTM seed-22 run", "Record P1r LSTM seed-33 run",
    "Aggregate P1r input-derived observable control",
]


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def obj(commit: str, path: str) -> str | None:
    out = subprocess.run(["git", "rev-parse", f"{commit}:{path}"], cwd=ROOT, capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else None


def is_ancestor(a: str, b: str) -> bool:
    return subprocess.run(["git", "merge-base", "--is-ancestor", a, b], cwd=ROOT).returncode == 0


def json_equal(a, b, rtol: float = 1e-12) -> bool:
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(json_equal(a[k], b[k], rtol) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(json_equal(x, y, rtol) for x, y in zip(a, b))
    if isinstance(a, float) and isinstance(b, float):
        return a == b or abs(a - b) <= rtol * max(abs(a), abs(b))
    return a == b


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ref", default="HEAD")
    args = parser.parse_args()
    head = git("rev-parse", args.ref)
    checks: dict = {}

    # Chronology on the P1r line (first-parent history of the P1r commits since pre-P1r main).
    p1r_tip = head
    parents = git("log", "-1", "--format=%P", head).split()
    if len(parents) == 2 and is_ancestor(PRE_P1R_MAIN, parents[0]) and not is_ancestor(parents[1], parents[0]):
        p1r_tip = parents[1]  # head is the consolidation merge; walk the P1r side
    subjects = git("log", "--reverse", "--first-parent", "--format=%H\t%s", f"{PRE_P1R_MAIN}..{p1r_tip}").splitlines()
    ordered = [line.split("\t", 1) for line in subjects]
    titles = [t for _, t in ordered]
    checks["chronology"] = {
        "p1r_tip": p1r_tip, "subjects": titles,
        "expected_prefix_in_order": titles[: len(EXPECTED_SUBJECTS)] == EXPECTED_SUBJECTS,
        "seal_is_first": bool(ordered) and ordered[0][0] == SEAL,
        "preflight_is_second": len(ordered) > 1 and ordered[1][0] == PREFLIGHT_COMMIT,
    }
    commit_of = {t: h for h, t in ordered}
    run_commits = {name: commit_of.get(f"Record P1r {'xLSTM' if name.startswith('x') else 'LSTM'} seed-{name[-2:]} run") for name in RUN_NAMES}
    aggregate_commit = commit_of.get("Aggregate P1r input-derived observable control")
    checks["ancestry"] = {
        "pre_p1r_main": is_ancestor(PRE_P1R_MAIN, head), "seal": is_ancestor(SEAL, head),
        "preflight": is_ancestor(PREFLIGHT_COMMIT, head),
        **{f"run_{k}": bool(v) and is_ancestor(v, head) for k, v in run_commits.items()},
        "aggregate": bool(aggregate_commit) and is_ancestor(aggregate_commit, head),
    }
    checks["commits"] = {"runs": run_commits, "aggregate": aggregate_commit}

    # Immutability after creation.
    checks["sealed_files_unchanged_since_seal"] = {p: obj(head, p) == obj(SEAL, p) for p in SEALED}
    checks["preflight_records_unchanged"] = {p: obj(head, p) is not None and obj(head, p) == obj(PREFLIGHT_COMMIT, p) for p in PREFLIGHT_FILES}
    checks["run_files_unchanged_since_run_commit"] = {
        name: bool(run_commits[name]) and all(
            obj(head, f"{P1R}/runs/{kind}_{name}.json") == obj(run_commits[name], f"{P1R}/runs/{kind}_{name}.json") is not None
            for kind in ("results", "execution")
        ) for name in RUN_NAMES
    }
    checks["results_json_unchanged_since_aggregate"] = bool(aggregate_commit) and obj(head, f"{P1R}/results.json") == obj(aggregate_commit, f"{P1R}/results.json")
    checks["historical_artifacts_identical_to_pre_p1r_main"] = {p: obj(head, p) == obj(PRE_P1R_MAIN, p) for p in HISTORICAL}

    # Row-key contract, execution sidecars, sealed re-aggregation.
    import input_derived_observable_control as p1r

    reference = {fold: meta["key_sha256"] for fold, meta in p1r.aplus_row_meta().items()}
    sides = {n: json.loads((ROOT / P1R / "runs" / f"execution_{n}.json").read_text()) for n in RUN_NAMES}
    runs = {n: json.loads((ROOT / P1R / "runs" / f"results_{n}.json").read_text()) for n in RUN_NAMES}
    checks["row_keys"] = {n: all(runs[n]["arms"][arm]["row_key_sha256"] == reference for arm in p1r.ARMS) for n in RUN_NAMES}
    checks["dimensions"] = {n: {arm: runs[n]["arms"][arm]["dimension"] for arm in p1r.ARMS} == p1r.ARM_DIMS for n in RUN_NAMES}
    checks["run_seals"] = {n: runs[n]["protocol_seal"] == SEAL and sides[n]["protocol_seal"] == SEAL for n in RUN_NAMES}
    checks["sidecars"] = {
        n: {
            "host": sides[n]["execution_host"], "cache_unchanged": sides[n]["cache_unchanged"],
            "result_sha256_matches": sides[n]["result_sha256"] == hashlib.sha256((ROOT / P1R / "runs" / f"results_{n}.json").read_bytes()).hexdigest(),
        } for n in RUN_NAMES
    }
    committed = json.loads((ROOT / P1R / "results.json").read_text())
    with tempfile.TemporaryDirectory() as tmp:
        fresh = p1r.aggregate(ROOT / P1R / "runs", Path(tmp) / "agg.json", SEAL)
    checks["reaggregation_equals_results_json"] = json_equal(json.loads(json.dumps(fresh)), committed)

    # Prohibited wording in current-facing documents.
    wording = {}
    for path in CURRENT_FACING:
        target = ROOT / path
        text = target.read_text() if target.exists() else ""
        wording[path] = {"exists": target.exists(), "hits": [pat for pat in PROHIBITED if re.search(pat, text, flags=re.IGNORECASE)]}
    checks["wording"] = wording

    ok = (
        checks["chronology"]["expected_prefix_in_order"] and checks["chronology"]["seal_is_first"] and checks["chronology"]["preflight_is_second"]
        and all(checks["ancestry"].values())
        and all(checks["sealed_files_unchanged_since_seal"].values())
        and all(checks["preflight_records_unchanged"].values())
        and all(checks["run_files_unchanged_since_run_commit"].values())
        and checks["results_json_unchanged_since_aggregate"]
        and all(checks["historical_artifacts_identical_to_pre_p1r_main"].values())
        and all(checks["row_keys"].values()) and all(checks["dimensions"].values()) and all(checks["run_seals"].values())
        and all(v["cache_unchanged"] and v["result_sha256_matches"] and v["host"] == sides[RUN_NAMES[0]]["execution_host"] for v in checks["sidecars"].values())
        and checks["reaggregation_equals_results_json"]
        and all(v["exists"] and not v["hits"] for v in wording.values())
    )
    report = {"head": head, "status": "PASS" if ok else "FAIL", "checks": checks}
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(report["status"])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
