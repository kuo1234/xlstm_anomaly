"""Isolated SOURCE-only method process for P5-0B3.

The CLI accepts only the value-free SOURCE projection and the canonical
SOURCE label artifact. It never receives the restricted firewall audit or a
full role/manifest table.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import random
import sys
import zipfile

import numpy as np

from research.p5_0b3.scripts.source_access_gate import execute_projected_source_access_gate
from research.p5_0b3.scripts.source_ingestion import SourceCsvError, project_source_csv
from research.p5_0b3.scripts.source_pipeline import (
    CanonicalSourceInterval, SourceEntityRows, SourcePipelineError, build_fold_plan,
    capped_clean_indices, run_source_stratum,
)

SEED = 17
EFD_COMMIT = "ced470e1386066931bad32f3cb6e24bac9c5bb89"
RUNTIME_LOCK_SHA256 = "5cc46d5a1b2dc63dd4ec1f879babd337a97481f1af8595603ea9ed97ecfad9a5"
ROLE_SEAL_SHA256 = "00e0cec62d238c78f2d0b3c79910c0ffaf1122d1582c28c8848022fb3e10e33f"
FEATURE_PROJECTION_SHA256 = "4bfe14f2650dbd3397f1840fa9a8ddea59e8aec961e808d3819e2dea88e375ec"
EXPECTED_STRATA = {
    ("manufacturer 1", "SH + DHW"): 8,
    ("manufacturer 1", "SH + DHW with sub-circuits"): 11,
    ("manufacturer 2", "SH"): 8,
    ("manufacturer 2", "SH + DHW"): 12,
    ("manufacturer 2", "SH with buffer tank"): 8,
}


class MethodFailure(RuntimeError):
    pass


class PhaseWideFailure(MethodFailure):
    """A model repeat/replay failure invalidates the entire backbone stage."""


def runtime_preflight_is_pinned(record: dict) -> bool:
    code = record.get("code", {})
    runtime = record.get("runtime", {})
    return (
        record.get("status") == "PASS"
        and code.get("efd_commit") == EFD_COMMIT
        and code.get("runtime_lock_sha256") == RUNTIME_LOCK_SHA256
        and code.get("python") == "3.12.3"
        and runtime.get("tensorflow") == "2.18.1"
        and runtime.get("keras") == "3.15.1"
        and runtime.get("numpy") == "1.26.4"
        and runtime.get("device") == "CPU"
        and runtime.get("deterministic_ops") is True
        and runtime.get("intra_threads") == 1
        and runtime.get("inter_threads") == 1
    )


def _fail():
    raise MethodFailure("SOURCE_METHOD_BLOCKED") from None


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _load_projection(path: Path, expected_sha: str) -> dict:
    try:
        payload = path.read_bytes()
        if _sha(payload) != expected_sha:
            _fail()
        value = json.loads(payload)
        if (value.get("schema_version") != "p5-0b3-source-method-input-v1"
                or value.get("source_entity_count") != 74
                or len(value.get("source_entities", [])) != 74
                or value.get("pinned_inputs", {}).get("role_seal_sha256") != ROLE_SEAL_SHA256
                or value.get("pinned_inputs", {}).get("feature_projection_sha256") != FEATURE_PROJECTION_SHA256):
            _fail()
        allowed = {"manufacturer", "configuration_type", "role", "role_digest", "raw_path", "raw_sha256"}
        if any(set(row) != allowed or row["role"] != "SOURCE" for row in value["source_entities"]):
            _fail()
        digests = [row["role_digest"] for row in value["source_entities"]]
        membership = ("P5-0B3-SOURCE-MEMBERSHIP-v1\n" + "\n".join(sorted(digests)) + "\n").encode("ascii")
        if (len(set(digests)) != 74
                or _sha(membership) != value.get("source_membership_sha256")
                or len(value.get("strata", [])) != 5):
            _fail()
        strata_seen = set()
        observed_strata = {}
        for row in value["strata"]:
            if set(row) != {"manufacturer", "configuration_type", "ordered_features",
                            "feature_count", "feature_schema_sha256"}:
                _fail()
            key = (row["manufacturer"], row["configuration_type"])
            features = row["ordered_features"]
            if (key in strata_seen or key not in EXPECTED_STRATA
                    or not isinstance(features, list)
                    or len(features) != EXPECTED_STRATA[key]
                    or row["feature_count"] != EXPECTED_STRATA[key]
                    or any(not isinstance(name, str) or not name for name in features)
                    or features != sorted(set(features))):
                _fail()
            schema_bytes = (json.dumps(features, sort_keys=True, separators=(",", ":"),
                                      ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")
            if _sha(schema_bytes) != row["feature_schema_sha256"]:
                _fail()
            strata_seen.add(key)
            observed_strata[key] = row["feature_count"]
        if strata_seen != set(EXPECTED_STRATA):
            _fail()
        if {(row["manufacturer"], row["configuration_type"]) for row in value["source_entities"]} != strata_seen:
            _fail()
        return value
    except MethodFailure:
        raise
    except Exception:
        _fail()


def _load_labels(path: Path, expected_sha: str, source_digests: set[str]):
    try:
        payload = path.read_bytes()
        if _sha(payload) != expected_sha:
            _fail()
        intervals = {digest: [] for digest in source_digests}
        required = {"role_digest", "annotation_source", "annotation_kind", "interval_start", "interval_end"}
        from datetime import datetime
        for line in payload.splitlines():
            row = json.loads(line)
            if set(row) != required or row["role_digest"] not in source_digests:
                _fail()
            start = datetime.fromisoformat(row["interval_start"])
            end = datetime.fromisoformat(row["interval_end"])
            item = CanonicalSourceInterval(
                row["annotation_source"], row["annotation_kind"], start, end, row["role_digest"]
            )
            item._validate(expected_role_digest=row["role_digest"])
            intervals[row["role_digest"]].append(item)
        return intervals
    except MethodFailure:
        raise
    except Exception:
        _fail()


def _runtime(efd_source: Path):
    try:
        if os.environ.get("CUDA_VISIBLE_DEVICES") != "-1" or os.environ.get("PYTHONHASHSEED") != str(SEED):
            _fail()
        lock = Path(__file__).resolve().parents[1] / "runtime.lock"
        if _sha(lock.read_bytes()) != RUNTIME_LOCK_SHA256:
            _fail()
        from research.p5_0b3.scripts.runtime_preflight import _verify_installed_lock
        _verify_installed_lock(lock)
        preflight_path = Path(__file__).resolve().parents[1] / "runtime_preflight_result.json"
        preflight_bytes = preflight_path.read_bytes()
        if _sha(preflight_bytes) != "e5ea82ab60d69e1578d4cef835e815c83e1d0fdb63eaa17a645557cbac9cb939":
            _fail()
        preflight = json.loads(preflight_bytes)
        if (not runtime_preflight_is_pinned(preflight)
                or preflight.get("code", {}).get("python") != platform.python_version()
                or preflight.get("runtime", {}).get("numpy") != np.__version__):
            _fail()
        commit = __import__("subprocess").run(
            ["git", "-C", str(efd_source), "rev-parse", "HEAD"], check=True,
            capture_output=True, text=True,
        ).stdout.strip()
        if commit != EFD_COMMIT:
            _fail()
        efd_tree = __import__("subprocess").run(
            ["git", "-C", str(efd_source), "rev-parse", "HEAD^{tree}"], check=True,
            capture_output=True, text=True,
        ).stdout.strip()
        efd_status = __import__("subprocess").run(
            ["git", "-C", str(efd_source), "status", "--porcelain", "--untracked-files=all"],
            check=True, capture_output=True, text=True,
        ).stdout
        if efd_tree != preflight.get("code", {}).get("efd_git_tree") or efd_status.strip():
            _fail()
        sys.path.insert(0, str(efd_source))
        import tensorflow as tf
        tf.config.threading.set_intra_op_parallelism_threads(1)
        tf.config.threading.set_inter_op_parallelism_threads(1)
        tf.config.experimental.enable_op_determinism()
        from energy_fault_detector.autoencoders.multilayer_autoencoder import MultilayerAutoencoder
        from energy_fault_detector.autoencoders import multilayer_autoencoder
        from energy_fault_detector.core import autoencoder as core_autoencoder
        if (tf.config.list_physical_devices("GPU") or np.__version__ != "1.26.4"
                or tf.__version__ != "2.18.1" or platform.python_version() != "3.12.3"):
            _fail()
        package_root = Path(efd_source).resolve() / "energy_fault_detector"
        model_module_path = Path(multilayer_autoencoder.__file__).resolve()
        core_module_path = Path(core_autoencoder.__file__).resolve()
        if (model_module_path != (package_root / "autoencoders/multilayer_autoencoder.py").resolve()
                or core_module_path != (package_root / "core/autoencoder.py").resolve()
                or _sha(model_module_path.read_bytes()) != preflight.get("code", {}).get("multilayer_autoencoder_sha256")
                or _sha(core_module_path.read_bytes()) != preflight.get("code", {}).get("core_autoencoder_sha256")):
            _fail()
        def seed_fn(seed):
            random.seed(seed); np.random.seed(seed); tf.keras.utils.set_random_seed(seed)
        return MultilayerAutoencoder, seed_fn
    except MethodFailure:
        raise
    except Exception:
        _fail()


def _check_replay(fitted, restored, model_input: np.ndarray,
                  expected_scores: np.ndarray | None = None) -> dict[str, float]:
    """Require save/load replay to preserve float32 reconstructions."""
    try:
        first = np.asarray(fitted.predict(model_input, verbose=0), dtype=np.float64)
        second = np.asarray(restored.predict(model_input, verbose=0), dtype=np.float64)
        if (first.shape != second.shape or not np.isfinite(first).all()
                or not np.isfinite(second).all()
                or not np.allclose(first, second, atol=1e-7, rtol=1e-7)):
            raise PhaseWideFailure("BACKBONE_NOT_ADMISSIBLE")
        first_scores = np.sqrt(np.mean((np.asarray(model_input, dtype=np.float32).astype(np.float64) - first) ** 2, axis=1))
        second_scores = np.sqrt(np.mean((np.asarray(model_input, dtype=np.float32).astype(np.float64) - second) ** 2, axis=1))
        if (not np.allclose(first_scores, second_scores, atol=1e-7, rtol=1e-7)
                or (expected_scores is not None and
                    (not np.isfinite(expected_scores).all()
                     or not np.allclose(second_scores, expected_scores, atol=1e-7, rtol=1e-7)))):
            raise PhaseWideFailure("BACKBONE_NOT_ADMISSIBLE")
        return {
            "model_max_absolute_delta": float(np.max(np.abs(first - second), initial=0.0)),
            "score_max_absolute_delta": float(np.max(np.abs(first_scores - second_scores), initial=0.0)),
        }
    except PhaseWideFailure:
        raise
    except Exception:
        raise PhaseWideFailure("BACKBONE_NOT_ADMISSIBLE") from None


def _parse_projected_entity(item, payload, features_by_key, intervals):
    """Project one already-hash-verified SOURCE payload into selected values."""
    key = (item["manufacturer"], item["configuration_type"])
    text = payload.decode("utf-8-sig")
    parsed = project_source_csv(text, timestamp_column=None, feature_columns=features_by_key[key])
    return SourceEntityRows(
        role_digest=item["role_digest"], features=parsed.features,
        timestamps=parsed.timestamps, timestamp_valid=parsed.timestamp_valid,
        measurement_valid=parsed.measurement_valid, raw_row_indices=parsed.raw_row_indices,
        intervals=tuple(intervals[item["role_digest"]]),
    )


def _parse_projected_entities(checked, by_digest, staged, features_by_key, intervals):
    """Synthetic helper for stratum-local CSV failure behavior."""
    entities = {key: [] for key in features_by_key}
    parse_failures: set[tuple[str, str]] = set()
    for row in checked:
        item = by_digest[row["role_digest"]]
        key = (item["manufacturer"], item["configuration_type"])
        try:
            entities[key].append(_parse_projected_entity(
                item, staged[item["role_digest"]], features_by_key, intervals
            ))
        except (SourceCsvError, SourcePipelineError, UnicodeError):
            parse_failures.add(key)
    for key in parse_failures:
        entities[key] = []
    return entities, parse_failures


def execute_method(projection: dict, archive_path: Path, labels_path: Path,
                   labels_sha: str, output_root: Path, efd_source: Path) -> dict:
    """Run each exact SOURCE stratum using only projected files and labels."""
    try:
        source_rows = projection["source_entities"]
        digests = {row["role_digest"] for row in source_rows}
        if len(digests) != 74:
            _fail()
        model_factory, seed_fn = _runtime(efd_source)
        intervals = _load_labels(labels_path, labels_sha, digests)
        by_digest = {row["role_digest"]: row for row in source_rows}
        strata = projection["strata"]
        features_by_key = {(s["manufacturer"], s["configuration_type"]): s["ordered_features"] for s in strata}
        entities = {key: [] for key in features_by_key}
        parse_failures: set[tuple[str, str]] = set()
        with zipfile.ZipFile(archive_path, "r") as zipped:
            # Central-directory membership is inspected only in memory. Only
            # exact projected paths are opened; names are never logged.
            infos = zipped.infolist()
            counts = {row["raw_path"]: 0 for row in source_rows}
            for info in infos:
                if info.filename in counts:
                    counts[info.filename] += 1
            if any(count != 1 for count in counts.values()):
                _fail()
            def opener(path):
                return zipped.read(path)
            def stager(entry, payload):
                key = (entry["manufacturer"], entry["configuration_type"])
                if key in parse_failures:
                    return
                try:
                    item = by_digest[entry["role_digest"]]
                    entities[key].append(
                        _parse_projected_entity(item, payload, features_by_key, intervals)
                    )
                except (SourceCsvError, SourcePipelineError, UnicodeError):
                    parse_failures.add(key)
            checked, audit = execute_projected_source_access_gate(
                source_rows, opener=opener, stager=stager
            )
        for key in parse_failures:
            entities[key] = []
        summary = {"schema_version": "p5-0b3-source-method-result-v1", "strata": [], "access_audit": audit}
        output_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        private = output_root / "source_artifacts"
        private.mkdir(parents=True, exist_ok=False, mode=0o700)
        for index, (key, group) in enumerate(sorted(entities.items())):
            audit_path = private / f"stratum_{index:02d}_audit.json"
            if key in parse_failures:
                parse_audit = {
                    "schema_version": "p5-0b3-private-source-stratum-artifacts-v1",
                    "status": "SOURCE_MODEL_NOT_EVALUABLE",
                    "failure_stage": "source_csv_projection",
                    "support_gate": "NOT_REACHED",
                }
                audit_path.write_text(
                    json.dumps(parse_audit, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n",
                    encoding="utf-8",
                )
                summary["strata"].append({"manufacturer": key[0], "configuration_type": key[1],
                                          "status": "SOURCE_MODEL_NOT_EVALUABLE"})
                continue
            pipeline_diagnostics: dict[str, object] = {}
            try:
                result = run_source_stratum(
                    group, model_factory=model_factory, seed_fn=seed_fn,
                    diagnostic_sink=pipeline_diagnostics,
                )
            except PhaseWideFailure:
                raise
            except SourcePipelineError as exc:
                if getattr(exc, "code", None) == "BACKBONE_NOT_ADMISSIBLE":
                    raise PhaseWideFailure("BACKBONE_NOT_ADMISSIBLE") from None
                pipeline_diagnostics["status"] = "SOURCE_MODEL_NOT_EVALUABLE"
                pipeline_diagnostics.setdefault(
                    "failure_stage", pipeline_diagnostics.get("stage", "unknown")
                )
                failure_audit = {
                    "schema_version": "p5-0b3-private-source-stratum-artifacts-v1",
                    "pipeline_diagnostics": pipeline_diagnostics,
                }
                audit_path.write_text(
                    json.dumps(failure_audit, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n",
                    encoding="utf-8",
                )
                summary["strata"].append({"manufacturer": key[0], "configuration_type": key[1],
                                          "status": "SOURCE_MODEL_NOT_EVALUABLE"})
                continue

            # Row score vectors are restricted SOURCE artifacts. A stratum is
            # reported READY only after all score, model, replay, and audit
            # artifacts have been written successfully.
            source_order = sorted(result.artifacts.final_scores)
            final_arrays = {f"source_{n:03d}": result.artifacts.final_scores[d]
                            for n, d in enumerate(source_order)}
            np.savez_compressed(private / f"stratum_{index:02d}_final_scores.npz", **final_arrays)
            oof_arrays = {}
            oof_index = {}
            for ci, candidate_id in enumerate(sorted(result.artifacts.oof_scores_by_candidate)):
                for ei, digest in enumerate(source_order):
                    array_name = f"candidate_{ci:03d}_source_{ei:03d}"
                    oof_arrays[array_name] = result.artifacts.oof_scores_by_candidate[candidate_id][digest]
                    oof_index[array_name] = {"candidate_id": candidate_id, "role_digest": digest}
            np.savez_compressed(private / f"stratum_{index:02d}_oof_scores.npz", **oof_arrays)
            fold_plan = build_fold_plan(group)
            audit_doc = {
                "schema_version": "p5-0b3-private-source-stratum-artifacts-v1",
                "pipeline_diagnostics": pipeline_diagnostics,
                "candidate_arrays": oof_index,
                "source_order": source_order,
                "fold_assignments": fold_plan.assignments,
                "invalid_rows": {},
            }
            for digest in source_order:
                entity = next(item for item in group if item.role_digest == digest)
                final = result.artifacts.final_scores[digest]
                timestamp_bad = ~np.asarray(entity.timestamp_valid, dtype=bool)
                measurement_bad = ~np.asarray(entity.measurement_valid, dtype=bool)
                nonfinite = ~np.isfinite(final)
                reason = np.full(len(final), "none", dtype=object)
                reason[timestamp_bad] = "invalid_timestamp"
                reason[~timestamp_bad & measurement_bad] = "invalid_measurement"
                reason[~timestamp_bad & ~measurement_bad & nonfinite] = "invalid_score"
                audit_doc["invalid_rows"][digest] = {
                    "invalid_score_count": int(np.count_nonzero(nonfinite)),
                    "invalid_score_rows": [
                        {"raw_row_index": int(entity.raw_row_indices[row_index]),
                         "reason": str(reason[row_index])}
                        for row_index in np.flatnonzero(nonfinite)
                    ],
                    "invalid_score_reason_counts": {
                        label: int(np.count_nonzero(reason == label))
                        for label in ("invalid_timestamp", "invalid_measurement", "invalid_score")
                    },
                }
            # A compact replay sample is drawn from clean capped SOURCE rows.
            entity = next(item for item in group if len(capped_clean_indices(item)))
            sample_rows = capped_clean_indices(entity)[:min(32, len(capped_clean_indices(entity)))]
            model_input = result.final_preprocessor.transform(entity.features[sample_rows])
            fitted_model = getattr(result.final_model, "model", None)
            if fitted_model is None:
                raise PhaseWideFailure("BACKBONE_NOT_ADMISSIBLE")
            model_path = private / f"stratum_{index:02d}_model.keras"
            try:
                fitted_model.save(model_path)
                import tensorflow as tf
                restored_model = tf.keras.models.load_model(model_path)
                audit_doc["save_load_replay"] = _check_replay(
                    fitted_model, restored_model, np.asarray(model_input, dtype=np.float32),
                    result.artifacts.final_scores[entity.role_digest][sample_rows],
                )
            except PhaseWideFailure:
                raise
            except Exception as exc:
                raise PhaseWideFailure("BACKBONE_NOT_ADMISSIBLE") from exc
            np.savez_compressed(
                private / f"stratum_{index:02d}_preprocessor.npz",
                medians=result.final_preprocessor.medians_,
                means=result.final_preprocessor.means_,
                scales=result.final_preprocessor.scales_,
            )
            audit_path.write_text(
                json.dumps(audit_doc, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n",
                encoding="utf-8",
            )
            summary["strata"].append({"manufacturer": key[0], "configuration_type": key[1],
                                      **result.safe_summary})
        target = output_root / "source_summary.json"
        target.write_text(json.dumps(summary, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n", encoding="utf-8")
        return {"stratum_count": len(summary["strata"]), "opened_source_files": audit["opened_source_files"]}
    except MethodFailure:
        raise
    except Exception:
        _fail()


def main(argv=None):
    try:
        args = list(sys.argv[1:] if argv is None else argv)
        required = {"--projection", "--projection-sha256", "--archive", "--labels", "--labels-sha256", "--output", "--efd-source"}
        if len(args) != 14 or set(args[::2]) != required:
            _fail()
        values = dict(zip(args[::2], args[1::2]))
        if any(not values[key] for key in required):
            _fail()
        projection = _load_projection(Path(values["--projection"]), values["--projection-sha256"])
        result = execute_method(projection, Path(values["--archive"]), Path(values["--labels"]),
                                values["--labels-sha256"], Path(values["--output"]), Path(values["--efd-source"]))
        print(f"P5_0B3_METHOD_OK {result['opened_source_files']} {result['stratum_count']}")
        return 0
    except PhaseWideFailure:
        print("P5_0B3_BACKBONE_NOT_ADMISSIBLE")
        return 2
    except Exception:
        print("P5_0B3_METHOD_BLOCKED")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
