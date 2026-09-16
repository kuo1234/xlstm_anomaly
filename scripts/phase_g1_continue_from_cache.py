"""Fail-closed continuation of the interrupted labelled G1 execution.

The original G1 process completed the observation/label extraction boundary
for every stream but failed while serialising its primary-cache manifest.  This
entrypoint is deliberately separate from ``phase_g1_run.py``: it can only be
enabled with the accepted post-label reporting-patch authorization and a
``PASS_CACHE_REUSABLE`` audit.  It reconstructs immutable cache references and
then executes the original probe/statistics path, without re-extracting the
2,625 streams.

This file is not invoked by default.  It must never write to the quarantined
cache directory; all newly created artifacts go below an explicitly empty
continuation output directory.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import itertools
import json
import sys
from pathlib import Path
from typing import Any, Mapping

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import phase_g1_cache_audit as audit  # noqa: E402
import phase_g1_pipeline as pipeline  # noqa: E402
import phase_g1_run as runner  # noqa: E402


REPORT_DIR = ROOT / "reports" / "phase_g1"
CACHE_AUDIT_PATH = REPORT_DIR / "g1_cache_audit_v1.json"
INVENTORY_PATH = REPORT_DIR / "g1_cache_file_inventory_v1.jsonl.gz"
CACHE_AUDIT_SHA256 = "730744b626bff018c6fd7f7ab72385583d8d091b4cd8642639fa56dfcc2a0c7b"
INVENTORY_SHA256 = "f9cbfa1a1915ffdb73b8df348b0329dde5b6edf5a5f3c563f60b49e07f783856"
ORIGINAL_SEAL = audit.ORIGINAL_SEAL
REPORTING_PATCH = audit.REPORTING_PATCH

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
PROTECTED_OUTPUTS = {
    "g1_execution_manifest.json",
    "g1_probe_manifest.json",
    "g1_results.json",
    "g1_statistics.json",
    "g1_decision.json",
    "g1_decision.md",
}


class ContinuationFailure(RuntimeError):
    """Raised when the post-label continuation contract is not satisfied."""


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json(path: Path) -> Any:
    return json.loads(path.read_text())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def _assert_digest(path: Path, expected: str, label: str) -> None:
    if not path.exists() or _sha_file(path) != expected:
        raise ContinuationFailure(f"{label} hash mismatch: {path}")


def _load_verified_inventory() -> dict[str, dict[str, Any]]:
    """Read and rehash every cache artifact from the sealed inventory."""
    _assert_digest(INVENTORY_PATH, INVENTORY_SHA256, "cache inventory")
    records: dict[str, dict[str, Any]] = {}
    with gzip.open(INVENTORY_PATH, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            name = str(record.get("path", ""))
            if not name or "/" in name or "\\" in name or name in records:
                raise ContinuationFailure(f"invalid/duplicate inventory path: {name}")
            if set(record) != {"bytes", "path", "sha256"}:
                raise ContinuationFailure(f"inventory record fields changed: {name}")
            records[name] = record
    expected = audit._expected_cache_files()
    if set(records) != expected:
        raise ContinuationFailure("inventory does not enumerate exactly the sealed cache files")
    for name, record in records.items():
        path = audit.CACHE_DIR / name
        if not path.is_file():
            raise ContinuationFailure(f"cache artifact missing during continuation: {name}")
        if path.stat().st_size != int(record["bytes"]):
            raise ContinuationFailure(f"cache artifact size changed: {name}")
        if _sha_file(path) != str(record["sha256"]):
            raise ContinuationFailure(f"cache artifact hash changed: {name}")
    return records


def _cache_ref(prefix: str, records: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    refs: dict[str, Any] = {}
    for suffix, key in ((".npz", "npz"), (".keys.json", "keys"), (".metadata.json", "metadata")):
        name = f"{prefix}{suffix}"
        if name not in records:
            raise ContinuationFailure(f"missing inventory record: {name}")
        refs[key] = str((audit.CACHE_DIR / name).resolve())
        refs[f"{key}_sha256"] = str(records[name]["sha256"])
    with (audit.CACHE_DIR / f"{prefix}.keys.json").open() as handle:
        refs["n"] = len(json.load(handle))
    return refs


def reconstruct_primary_cache_refs(records: Mapping[str, Mapping[str, Any]]) -> dict[int, dict[str, dict[str, list[dict[str, Any]]]]]:
    """Rebuild the original seed/fold/arm grouping using absolute paths."""
    refs: dict[int, dict[str, dict[str, list[dict[str, Any]]]]] = {
        seed: {fold: {} for fold, _ in audit.FOLDS} for seed in audit.DETECTOR_SEEDS
    }
    expected_prefixes = audit._expected_primary_prefixes()
    for prefix, identity in expected_prefixes.items():
        seed, fold, _source, _scenario, _condition, arm, architecture = identity
        name = f"{arm}_{architecture}"
        refs[int(seed)][str(fold)].setdefault(name, []).append(_cache_ref(prefix, records))
    expected_arms = len(audit.ARMS) * len(audit.ARCHITECTURES)
    for seed in audit.DETECTOR_SEEDS:
        for fold, _sources in audit.FOLDS:
            grouped = refs[seed][fold]
            if sum(len(value) for value in grouped.values()) != expected_arms * len(
                tuple(source for f, sources in audit.FOLDS if f == fold for source in sources)
            ):
                raise ContinuationFailure(f"cache reference cardinality mismatch: {seed}/{fold}")
            if set(grouped) != {f"{arm}_{arch}" for arm in audit.ARMS for arch in audit.ARCHITECTURES}:
                raise ContinuationFailure(f"cache reference arms incomplete: {seed}/{fold}")
    return refs


def _ledger_execution_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with audit.LEDGER_PATH.open() as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("event") != "labelled_stream_complete":
                continue
            fields = record.get("fields", {})
            rows.append({
                "seed": int(fields["detector_seed"]),
                "source": int(fields["source_seed"]),
                "fold": str(fields["fold"]),
                "scenario": str(fields["scenario"]),
                "condition": str(fields["condition"]),
                "row_count": int(fields["row_count"]),
                "labels_joined_after_extraction": True,
                "reconstructed_from_quarantined_ledger": True,
            })
    if len(rows) != 2625:
        raise ContinuationFailure("labelled completion ledger does not contain 2,625 rows")
    return rows


def _reconstruct_descriptive_rows() -> list[dict[str, Any]]:
    """Rebuild the original evaluator-only descriptive stream table."""
    rows: list[dict[str, Any]] = []
    for _detector_seed in audit.DETECTOR_SEEDS:
        for fold, sources in audit.FOLDS:
            for source in sources:
                for scenario in audit.SHIFTED_SCENARIOS:
                    conditions = audit.CONDITIONS
                    for condition in conditions:
                        stream = runner._generate(source, scenario, condition)
                        timestamps = np.arange(runner.FIRST_COMMON_TIMESTAMP, len(stream.observations), dtype=np.int64)
                        truth = runner.build_evaluator_rows(stream, timestamps, 64)
                        strata = np.asarray(truth["stratum"], dtype=object)
                        labels = np.asarray(truth["label"], dtype=np.int8)
                        event_types = np.asarray(truth["event_type"], dtype=object)
                        rows.append({
                            "detector_seed": int(_detector_seed),
                            "source_seed": int(source),
                            "fold": str(fold),
                            "scenario": str(scenario),
                            "condition": str(condition),
                            "strata_counts": {
                                str(name): int(np.sum(strata == name))
                                for name in ("anomaly", "drift", "mixed", "stable_new_normal", "stationary_normal")
                            },
                            "anomaly_prevalence": float(np.mean(labels)),
                            "mixed_count": int(np.sum(strata == "mixed")),
                            "event_type_counts": {
                                str(name): int(np.sum(event_types == name))
                                for name in ("spike", "collective", "dependency", "persistent_fault")
                            },
                        })
                stream = runner._generate(source, "stationary", "none")
                timestamps = np.arange(runner.FIRST_COMMON_TIMESTAMP, len(stream.observations), dtype=np.int64)
                truth = runner.build_evaluator_rows(stream, timestamps, 64)
                strata = np.asarray(truth["stratum"], dtype=object)
                labels = np.asarray(truth["label"], dtype=np.int8)
                event_types = np.asarray(truth["event_type"], dtype=object)
                rows.append({
                    "detector_seed": int(_detector_seed),
                    "source_seed": int(source),
                    "fold": str(fold),
                    "scenario": "stationary",
                    "condition": "none",
                    "strata_counts": {
                        str(name): int(np.sum(strata == name))
                        for name in ("anomaly", "drift", "mixed", "stable_new_normal", "stationary_normal")
                    },
                    "anomaly_prevalence": float(np.mean(labels)),
                    "mixed_count": int(np.sum(strata == "mixed")),
                    "event_type_counts": {
                        str(name): int(np.sum(event_types == name))
                        for name in ("spike", "collective", "dependency", "persistent_fault")
                    },
                })
    if len(rows) != 2625:
        raise ContinuationFailure("descriptive stream reconstruction did not produce 2,625 rows")
    return rows


def _write_reconstructed_outputs(
    output_dir: Path,
    refs: Mapping[int, Mapping[str, Mapping[str, list[dict[str, Any]]]]],
    audit_report: Mapping[str, Any],
) -> dict[str, Any]:
    """Run the original post-extraction fitting/statistics path unchanged."""
    output_dir = Path(output_dir).expanduser().resolve()
    if output_dir == audit.CACHE_DIR or audit.CACHE_DIR in output_dir.parents:
        raise ContinuationFailure("continuation output may not be inside the read-only primary cache")
    output_dir.mkdir(parents=True, exist_ok=False)
    if any((output_dir / name).exists() for name in PROTECTED_OUTPUTS):
        raise ContinuationFailure("continuation output already contains protected artifacts")
    ledger_path = output_dir / "g1_continuation_ledger.jsonl"
    runner._ledger_append(ledger_path, "continuation_start", cache_audit_status=audit_report["status"])

    feature_arms = runner.expected_feature_arms()
    artifact_dir = output_dir / "g1_artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=False)
    probe_manifest: dict[str, Any] = {
        "fits": {},
        "row_key_sha256": {},
        "artifacts": {},
        "primary_cache": {
            "directory": str(audit.CACHE_DIR.resolve()),
            "absolute_paths": True,
            "reconstructed": True,
            "resource_contract": "read-only quarantined stream chunks; one detector seed pooled at a time",
            "chunk_count": int(sum(
                len(arm_refs)
                for seed_refs in refs.values()
                for fold_refs in seed_refs.values()
                for arm_refs in fold_refs.values()
            )),
        },
    }
    shared_control_artifacts: dict[str, Any] = {}
    fits: dict[int, dict[str, dict[str, Any]]] = {}
    comparison_rows: dict[int, dict[str, dict[str, Any]]] = {}
    test_results: dict[str, Any] = {}
    expected_dims = EXPECTED_DIMS
    for seed in audit.DETECTOR_SEEDS:
        pooled_seed: dict[str, dict[str, Any]] = {"train": {}, "validation": {}, "test": {}}
        for fold in ("train", "validation", "test"):
            for arm, arm_refs in refs[int(seed)][fold].items():
                if not arm_refs:
                    raise ContinuationFailure(f"empty cache arm: {seed}/{fold}/{arm}")
                pooled_seed[fold][arm] = runner._concat(
                    [runner._load_primary_chunk(ref) for ref in arm_refs]
                )
        for architecture in runner.ARCHITECTURES:
            runner._assert_paired_arms({
                arm.removesuffix(f"_{architecture}"): pooled_seed["test"][arm]
                for arm in pooled_seed["test"] if arm.endswith(f"_{architecture}")
            })
        for arm in feature_arms:
            runner.assert_common_cohort({
                "xlstm": pooled_seed["test"][f"{arm}_xlstm"],
                "lstm": pooled_seed["test"][f"{arm}_lstm"],
            })
            if arm == "candi_history14":
                left = pooled_seed["test"][f"{arm}_xlstm"]
                right = pooled_seed["test"][f"{arm}_lstm"]
                runner.assert_shared_control(left["X"], right["X"], left["keys"], right["keys"])
                x_path = artifact_dir / f"seed{seed}_candi_history_x.npy"
                l_path = artifact_dir / f"seed{seed}_candi_history_l.npy"
                np.save(x_path, np.asarray(left["X"], dtype=np.float64), allow_pickle=False)
                np.save(l_path, np.asarray(right["X"], dtype=np.float64), allow_pickle=False)
                shared_control_artifacts[str(seed)] = {
                    "x_path": str(x_path.relative_to(ROOT)), "x_sha256": runner._sha(x_path),
                    "l_path": str(l_path.relative_to(ROOT)), "l_sha256": runner._sha(l_path),
                    "row_key_sha256": runner.row_key_hash(left["keys"]), "shape": list(left["X"].shape),
                }
            elif arm == "candi_history_plus_combined248":
                left = pooled_seed["test"][f"{arm}_xlstm"]
                right = pooled_seed["test"][f"{arm}_lstm"]
                runner.assert_shared_control(left["X"][:, :14], right["X"][:, :14], left["keys"], right["keys"])
        seed_fits: dict[str, dict[str, Any]] = {}
        for arm in pooled_seed["train"]:
            suffix = "_xlstm" if arm.endswith("_xlstm") else "_lstm"
            base_arm = arm.removesuffix(suffix)
            seed_fits[arm] = runner.fit_probe_pooled(
                runner.probe_split_from_rows(pooled_seed["train"][arm]),
                runner.probe_split_from_rows(pooled_seed["validation"][arm]),
                runner.probe_split_from_rows(pooled_seed["test"][arm]),
                arm,
                seed,
                expected_dims[base_arm],
            )
        fits[int(seed)] = seed_fits
        comparison_rows[int(seed)] = {
            arm: runner._light_primary_rows(rows) for arm, rows in pooled_seed["test"].items()
        }
        probe_manifest["row_key_sha256"][str(seed)] = {
            arm: runner.row_key_hash(value["keys"])
            for arm, value in comparison_rows[int(seed)].items()
        }
        seed_results, seed_artifacts = runner._write_primary_probe_artifacts(
            int(seed), seed_fits, pooled_seed["train"], pooled_seed["validation"], pooled_seed["test"], artifact_dir
        )
        test_results[str(seed)] = seed_results
        probe_manifest["artifacts"].update(seed_artifacts)
        del pooled_seed, seed_fits
    probe_manifest["shared_control_artifacts"] = shared_control_artifacts
    probe_manifest["fits"] = runner._clean(fits)

    pooled_ap = runner._pooled_source_ap(fits, comparison_rows)
    deltas = runner._difference_table(fits, comparison_rows)
    scenario_deltas = runner._scenario_difference_table(fits, comparison_rows)
    statistics = runner.build_confirmatory_statistics(deltas)
    runner._ledger_append(ledger_path, "probe_statistics_complete", confirmatory_family_size=4)
    for name, delta in deltas.items():
        delta_path = artifact_dir / f"delta_{name}.npy"
        np.save(delta_path, np.asarray(delta, dtype=np.float64), allow_pickle=False)
        probe_manifest.setdefault("delta_artifacts", {})[name] = {
            "path": str(delta_path.relative_to(ROOT)), "sha256": runner._sha(delta_path), "shape": list(delta.shape)
        }

    entries = pipeline.load_backbone_entries()
    candi = pipeline.load_candi_controls()
    frozen_backbones = {
        int(seed): {
            architecture: pipeline._load_backbone(entries[(int(seed), architecture)])
            for architecture in runner.ARCHITECTURES
        }
        for seed in audit.DETECTOR_SEEDS
    }
    secondary = runner._secondary_streaming_pass(
        fits,
        frozen_backbones,
        candi,
        feature_arms,
        output_dir,
        artifact_dir,
    )
    probe_manifest["semantic_control"] = secondary["semantic_report"]
    probe_manifest["semantic_control_checks"] = secondary["semantic_control_checks"]
    probe_manifest["semantic_control_artifacts"] = secondary["semantic_artifacts"]
    probe_manifest["robustness_artifacts"] = secondary["robustness_artifacts"]
    probe_manifest["secondary_cache"] = {
        "directory": secondary["secondary_cache_dir"],
        "file_count": secondary["secondary_cache_file_count"],
        "resource_contract": "one source/scenario/condition feature chunk at a time",
    }

    descriptive_rows = _reconstruct_descriptive_rows()
    execution_rows = _ledger_execution_rows()
    backend_environment = __import__("phase_f_v4_common").configure()
    _write_json(output_dir / "g1_execution_manifest.json", {
        "status": "LABELLED_EXECUTION_RECOVERED_FROM_VERIFIED_CACHE",
        "prelabel_seal_commit": ORIGINAL_SEAL,
        "execution_commit": runner.current_commit(),
        "code_sha256": audit._sha_file(Path(__file__)),
        "scientific_file_sha256": runner.scientific_file_sha256(),
        "backend_environment": backend_environment,
        "rows": execution_rows,
        "feature_arms": feature_arms,
        "folds": pipeline.G1_CONFIG["folds"],
        "shifted_scenarios": list(audit.SHIFTED_SCENARIOS),
        "conditions": list(audit.CONDITIONS),
        "labels_joined_after_observation_extraction": True,
        "optimizer_steps": False,
        "test_result_metrics_computed": True,
        "execution_ledger": str(ledger_path.relative_to(ROOT)),
        "execution_ledger_sha256": _sha_file(ledger_path),
        "primary_cache_audit": str(CACHE_AUDIT_PATH.relative_to(ROOT)),
        "primary_cache_audit_sha256": _sha_file(CACHE_AUDIT_PATH),
        "primary_cache_read_only": True,
    })
    _write_json(output_dir / "g1_probe_manifest.json", probe_manifest)
    _write_json(output_dir / "g1_statistics.json", runner._clean(statistics))
    scenario_statistics = {
        name: {"shape": list(value.shape), "sha256": audit._array_digest(value), "values": value.tolist()}
        for name, value in scenario_deltas.items()
    }
    _write_json(output_dir / "g1_results.json", {
        "test_ap": test_results,
        "specificity": secondary["specificity"],
        "descriptive_strata": descriptive_rows,
        "descriptive_test_strata": secondary["descriptive_test"],
        "natural_prevalence_evaluation": secondary["natural_prevalence"],
        "pooled_source_ap": {arm: values.tolist() for arm, values in pooled_ap.items()},
        "pooled_source_ap_mean": {arm: float(np.mean(values)) for arm, values in pooled_ap.items()},
        "scenario_deltas": scenario_statistics,
        "duration_severity_robustness": secondary["robustness_report"],
        "semantic_nonidentifiability_control": secondary["semantic_report"],
        "semantic_control_checks": secondary["semantic_control_checks"],
        "delta_sha256": {name: audit._array_digest(value) for name, value in deltas.items()},
        "delta_shape": {name: list(value.shape) for name, value in deltas.items()},
        "test_sources": list(pipeline.TEST_SOURCES),
        "scenarios": list(pipeline.SHIFTED_SCENARIOS),
        "conditions": list(runner.CONDITIONS),
        "primary_cohort_prevalence": {
            str(seed): {
                arm: float(test_results[str(seed)][arm]["positives"] / test_results[str(seed)][arm]["n"])
                for arm in test_results[str(seed)]
            }
            for seed in audit.DETECTOR_SEEDS
        },
    })
    from phase_g1_core import h2_go, h3a_go, positive_seed_scenario_counts, positive_seed_source_counts

    h2_raw = statistics["comparisons"]["h2"]
    h2_seed_count = positive_seed_source_counts(deltas["h2"])
    h2_scenario_count = positive_seed_scenario_counts(scenario_deltas["h2"])[1]
    h2_robustness_support = secondary["robustness_report"].get("h2_status") == "PASS"
    h3a_robustness_support = secondary["robustness_report"].get("h3a_status_if_primary_h2_go") == "PASS"
    h2_status = "GO" if h2_go(
        h2_raw["mean"], h2_raw["ci95"][0], h2_raw["holm_adjusted_p"],
        h2_seed_count, h2_scenario_count, h2_robustness_support,
    ) else "STOP"
    h3a_counts = {
        name: {
            "positive_detector_seeds": positive_seed_source_counts(deltas[name]),
            "positive_scenarios": positive_seed_scenario_counts(scenario_deltas[name])[1],
        }
        for name in ("h3a_a", "h3a_b", "h3a_c")
    }
    h3_repro = all(
        row["positive_detector_seeds"] >= 4 and row["positive_scenarios"] >= 3
        for row in h3a_counts.values()
    )
    h3a_status = "NOT_ELIGIBLE"
    if h2_status == "GO":
        a, b, c = (statistics["comparisons"][name] for name in ("h3a_a", "h3a_b", "h3a_c"))
        h3a_status = "GO" if h3a_go(
            True,
            a["mean"], a["ci95"][0], a["holm_adjusted_p"],
            b["mean"], b["ci95"][0], b["holm_adjusted_p"],
            c["mean"], c["ci95"][0], c["holm_adjusted_p"],
            h3_repro, h3a_robustness_support,
        ) else "STOP"
    decision = {
        "H2": h2_status,
        "H3a": h3a_status,
        "H3b": "UNLOCKED" if h3a_status == "GO" else "LOCKED",
        "h1_controlled_harm": "STOP",
        "h1_natural_harm": "NOT_RUN",
        "h1_harm_overall": "UNRESOLVED",
        "duration_severity_robustness": secondary["robustness_report"],
        "semantic_nonidentifiability_control": secondary["semantic_report"],
        "h2_positive_detector_seeds": h2_seed_count,
        "h2_positive_scenarios": h2_scenario_count,
        "h3a_reproducibility": h3a_counts,
        "h3a_reproducibility_pass": h3_repro,
        "h2_robustness_support_used": h2_robustness_support,
        "h3a_robustness_support_used": h3a_robustness_support,
        "recovered_from_cache": True,
    }
    _write_json(output_dir / "g1_decision.json", decision)
    (output_dir / "g1_decision.md").write_text(
        "# Phase G1 decision (cache continuation)\n\n"
        + "\n".join(f"{key} = {value}" for key, value in (("H2", h2_status), ("H3a", h3a_status), ("H3b", decision["H3b"])))
        + "\n\nH1_controlled_harm = STOP\nH1_natural_harm = NOT_RUN\nH1_harm_overall = UNRESOLVED\n"
    )
    runner._ledger_append(ledger_path, "continuation_complete", h2=h2_status, h3a=h3a_status, h3b=decision["H3b"])
    return decision


def continue_from_cache(audit_report_path: Path, output_dir: Path) -> dict[str, Any]:
    """Verify the post-label exception and execute only after the cache gate."""
    _assert_digest(audit_report_path, CACHE_AUDIT_SHA256, "cache audit report")
    audit_report = _json(audit_report_path)
    audit.require_reporting_patch_guard(ORIGINAL_SEAL, REPORTING_PATCH, audit_report)
    if audit_report.get("status") != "PASS_CACHE_REUSABLE":
        raise ContinuationFailure("cache audit is not PASS_CACHE_REUSABLE")
    records = _load_verified_inventory()
    refs = reconstruct_primary_cache_refs(records)
    pipeline.assert_sealed_inputs()
    pipeline.require_duration_matching_resolution()
    return _write_reconstructed_outputs(output_dir, refs, audit_report)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-report", type=Path, default=CACHE_AUDIT_PATH)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports" / "phase_g_recovered")
    parser.add_argument(
        "--allow-cache-continuation",
        action="store_true",
        help="required explicit acknowledgement; still subject to all immutable guards",
    )
    args = parser.parse_args()
    if not args.allow_cache_continuation:
        raise SystemExit("refusing continuation without --allow-cache-continuation")
    try:
        decision = continue_from_cache(args.audit_report.resolve(), args.output_dir)
    except Exception as exc:
        raise SystemExit(f"FAIL_CLOSED: {type(exc).__name__}: {exc}") from exc
    print(json.dumps({"status": "CONTINUATION_COMPLETE", "decision": decision}, sort_keys=True))


if __name__ == "__main__":
    main()
