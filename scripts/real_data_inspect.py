"""Read-only, no-imputation schema and label inspection of local raw datasets.

Prints JSON. Interval indices are zero-based half-open [start, end); timestamp
absence is reported as unknown. No resampling, normalization, or model calls.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import csv
from datetime import datetime
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "external_real"


def intervals(flags: list[bool]) -> list[list[int]]:
    result = []
    start = None
    for i, on in enumerate(flags + [False]):
        if on and start is None:
            start = i
        if not on and start is not None:
            result.append([start, i])
            start = None
    return result


def timestamp(text: str):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(text.strip(), fmt)
        except ValueError:
            pass
    return None


def read_delimited(path: Path, *, header: bool = True, delimiter: str = ",",
                   timestamp_column: str | None = None, value_columns: list[str] | None = None,
                   anomaly_column: str | None = None, drift_column: str | None = None):
    if not path.is_file():
        return {"path": str(path), "status": "unavailable"}
    n = missing = total = 0
    times = []
    anomalies = []
    drifts = []
    counts = Counter()
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = csv.reader(stream, delimiter=delimiter)
        first = next(rows)
        columns = first if header else [f"channel_{i}" for i in range(len(first))]
        if not header:
            rows = iter([first] + list(rows))  # SMD fits memory; no modification.
        indices = {name: i for i, name in enumerate(columns)}
        features = value_columns or [name for name in columns if name not in
                                      (timestamp_column, anomaly_column, drift_column)]
        for row in rows:
            if len(row) != len(columns):
                raise ValueError(f"Column-count mismatch in {path} at row {n}")
            n += 1
            for col in features:
                total += 1
                if row[indices[col]].strip().lower() in ("", "nan", "null", "na", "none"):
                    missing += 1
            if timestamp_column:
                times.append(timestamp(row[indices[timestamp_column]]))
            if anomaly_column:
                value = row[indices[anomaly_column]].strip()
                counts[value] += 1
                anomalies.append(value.lower() in ("1", "1.0", "attack", "true", "a1", "anomaly"))
            if drift_column:
                drifts.append(row[indices[drift_column]].strip() in ("1", "1.0", "True"))
    valid_times = [t for t in times if t is not None]
    deltas = [(b - a).total_seconds() for a, b in zip(times, times[1:]) if a and b]
    return {"path": str(path), "status": "available", "shape": [n, len(columns)], "columns": columns,
            "n_channels": len(features), "value_columns": features,
            "timestamp_range": [valid_times[0].isoformat(), valid_times[-1].isoformat()] if valid_times else "unknown",
            "timestamp_parse_failures": len(times) - len(valid_times),
            "sampling_interval_seconds_mode": Counter(deltas).most_common(1)[0][0] if deltas else "unknown",
            "sampling_irregular_deltas": sum(d != Counter(deltas).most_common(1)[0][0] for d in deltas) if deltas else "unknown",
            "missing_value_rate": missing / total if total else "unknown",
            "label_distribution": dict(counts) if anomaly_column else "unknown",
            "anomaly_intervals": intervals(anomalies) if anomaly_column else "unknown",
            "drift_intervals": "unknown",  # A change-point column marks instants, not drift duration.
            "drift_point_indices": [i for i, value in enumerate(drifts) if value] if drift_column else "unknown"}


def smd(machine: str):
    base = DATA / "smd"
    train = read_delimited(base / f"{machine}_train.txt", header=False)
    test = read_delimited(base / f"{machine}_test.txt", header=False)
    labels = read_delimited(base / f"{machine}_test_label.txt", header=False, anomaly_column="channel_0", value_columns=[])
    if all(x["status"] == "available" for x in (train, test, labels)) and test["shape"][0] != labels["shape"][0]:
        raise ValueError(f"SMD {machine} test/label length mismatch")
    return {"dataset_id": f"smd-{machine}", "train": train, "test": test,
            "test_labels": labels, "train_test_boundary": train.get("shape", ["unknown"])[0],
            "timestamp_semantics": "No source timestamps; sample cadence not encoded"}


def sensor():
    result = []
    for i in (1, 2):
        path = DATA / "andri_sensor" / f"real iot {i}.csv"
        record = read_delimited(path, timestamp_column="timestamp", value_columns=["value"],
                                anomaly_column="anomaly_point", drift_column="change_point")
        if record["status"] == "available":
            # Pattern anomalies are a separate upstream column; union is the paper loader's rule.
            with path.open(newline="") as stream:
                rows = csv.DictReader(stream)
                union = [r["anomaly_pattern"] == "1" or r["anomaly_point"] == "1" for r in rows]
            record["anomaly_pattern_or_point_intervals"] = intervals(union)
            record["anomaly_pattern_or_point_distribution"] = {"1": sum(union), "0": len(union) - sum(union)}
            record["train_test_boundary"] = "unknown; AnDri's training prefix is a run parameter"
        result.append(record)
    return result


def nasa(series: str, group: str):
    try:
        import numpy as np
    except ImportError:
        return {"dataset_id": f"{group}-{series}", "status": "numpy required to inspect .npy (never unpickle)"}
    base = DATA / "nasa" / group
    result = {"dataset_id": f"{group}-{series}", "timestamp_semantics": "none in released arrays"}
    for split in ("train", "test"):
        path = base / split / f"{series}.npy"
        if not path.is_file():
            result[split] = {"status": "unavailable", "path": str(path)}
            continue
        arr = np.load(path, mmap_mode="r", allow_pickle=False)
        result[split] = {"status": "available", "path": str(path), "shape": list(arr.shape),
                         "columns": [f"channel_{i}" for i in range(arr.shape[1])],
                         "n_channels": arr.shape[1], "timestamp_range": "unknown", "sampling_interval": "unknown",
                         "missing_value_rate": float(np.isnan(arr).sum() / arr.size)}
    labels = DATA / "nasa" / "labeled_anomalies.csv"
    if labels.exists():
        with labels.open(newline="") as stream:
            matches = [r for r in csv.DictReader(stream) if r["chan_id"] == series and r["spacecraft"] == group]
        result["official_test_anomaly_intervals"] = [ast.literal_eval(r["anomaly_sequences"]) for r in matches]
        result["label_granularity"] = "test intervals; verify inclusive endpoint convention before point expansion"
    result["train_test_boundary"] = result.get("train", {}).get("shape", ["unknown"])[0]
    return result


def hai():
    base = DATA / "hai-22.04" / "official" / "hai-22.04"
    return [{"split": "train" if i <= 6 else "test", **read_delimited(
        base / f"{'train' if i <= 6 else 'test'}{i if i <= 6 else i-6}.csv",
        timestamp_column="timestamp", anomaly_column="Attack")} for i in range(1, 11)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", choices=("all", "smd-1-4", "smd-2-1", "andri-sensor", "msl-p15", "smap-t3", "hai-22.04"))
    args = parser.parse_args()
    fn = {"smd-1-4": lambda: smd("machine-1-4"), "smd-2-1": lambda: smd("machine-2-1"),
          "andri-sensor": sensor, "msl-p15": lambda: nasa("P-15", "MSL"),
          "smap-t3": lambda: nasa("T-3", "SMAP"), "hai-22.04": hai}
    selected = fn if args.dataset == "all" else {args.dataset: fn[args.dataset]}
    print(json.dumps({key: action() for key, action in selected.items()}, indent=2))


if __name__ == "__main__":
    main()
