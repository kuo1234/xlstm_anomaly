"""Dataset-only Phase A audit. No detectors, training, or model results.

Byte hashes seal downloads; canonical float64 hashes detect equal feature traces
despite text formatting. Provenance is fail-closed: a numbered TSB filename alone
does not establish an independent physical/source trace.
"""
import csv
import hashlib
import io
import itertools
import json
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from phase_a_fetch import ROOT, OUT, OMNI, TSBAD, STRAD, CANDI, sha256

BUCKETS = ("continuous", "change_point", "periodic", "random_walk")


def digest_array(x):
    x = np.array(x, dtype="<f8", order="C", copy=True)
    x[x == 0] = 0  # signed zero is numerically equal
    return hashlib.sha256(str(x.shape).encode() + x.tobytes()).hexdigest()


def contained_offset(small, large):
    """Exact contiguous containment, full rows checked (no approximate claims)."""
    if small.shape[1] != large.shape[1] or len(small) > len(large):
        return None
    # Pick most variable feature to reduce first-row candidate matches.
    col = int(np.argmax(np.ptp(small, axis=0)))
    starts = np.flatnonzero(large[:len(large)-len(small)+1, col] == small[0, col])
    for start in starts:
        if np.array_equal(large[start:start+len(small)], small):
            return int(start)
    return None


def assign(rows):
    """First feasible sorted tuple is the frozen lexicographic assignment."""
    pools = {b: sorted([r for r in rows if r["eligible"] and b in r["tags"]], key=lambda r: r["file"]) for b in BUCKETS}
    def visit(depth, used, selected):
        if depth == len(BUCKETS):
            return selected
        bucket = BUCKETS[depth]
        for triple in itertools.combinations(pools[bucket], 3):
            groups = {r["source_group"] for r in triple}
            if len(groups) != 3 or used & groups:
                continue
            result = visit(depth + 1, used | groups, selected + [dict(r, selection_bucket=bucket) for r in triple])
            if result is not None:
                return result
        return None
    if any(len({r["source_group"] for r in pools[b]}) < 3 for b in BUCKETS):
        return None
    return visit(0, set(), [])


def inspect_frame(df, cutoff):
    errors = []
    if "Label" not in df or df.columns[-1] != "Label":
        return {"numeric_exclusions": ["missing_or_nonfinal_Label"], "numeric_pass": False}
    try:
        x = df.iloc[:, :-1].to_numpy(dtype=np.float64)
        y = df.Label.to_numpy(dtype=np.float64)
    except (ValueError, TypeError):
        return {"numeric_exclusions": ["nonnumeric_values"], "numeric_pass": False}
    n, d = x.shape
    if d < 2: errors.append("D_lt_2")
    if not np.isfinite(x).all(): errors.append("nonfinite_observations")
    if not np.isin(y, [0, 1]).all(): errors.append("nonbinary_or_nonfinite_labels")
    if not 0 < cutoff < n: errors.append("invalid_cutoff")
    if cutoff < 320: errors.append("training_prefix_lt_320")
    if n-cutoff < 256: errors.append("test_lt_256")
    count = int(np.count_nonzero(y[:cutoff] != 0))
    if count: errors.append("contaminated_original_training_prefix")
    return dict(D=d, N=n, cutoff=cutoff, fit_interval=[0, (4*cutoff)//5],
                calibration_interval=[(4*cutoff)//5, cutoff], test_interval=[cutoff, n],
                finite_observations=bool(np.isfinite(x).all()), binary_labels=bool(np.isin(y, [0,1]).all()),
                training_anomaly_count=count, first_actual_anomaly=int(np.flatnonzero(y == 1)[0]) if (y == 1).any() else None,
                constant_channels=int(np.count_nonzero(np.ptp(x, axis=0) == 0)),
                numeric_exclusions=errors, numeric_pass=not errors,
                feature_sha256=digest_array(x), labels_sha256=digest_array(y))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    metadata = list(csv.DictReader((ROOT / "CD.csv").open()))
    candidates = sorted([r for r in metadata if int(r["CD"]) == 1], key=lambda r: r["file"])
    catalog = (ROOT / "TSB_source_catalog.html").read_text()
    source_urls = {}
    for block in re.findall(r"<tr>.*?</tr>", catalog, flags=re.S):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", block, flags=re.S)
        if len(cells) >= 3:
            link = re.search(r'href="([^"]+)"', cells[2])
            if link:
                source_urls[re.sub(r"<[^>]+>", "", cells[0]).strip()] = link[1]
    source_urls["OPPORTUNITY"] = source_urls["OPP"]
    arrays, rows = {}, []
    with zipfile.ZipFile(ROOT / "TSB-AD-M.zip") as z:
        members = {Path(name).name: name for name in z.namelist() if name.endswith(".csv") and not name.startswith("__MACOSX/")}
        (OUT / "archive_members.json").write_text(json.dumps(z.namelist(), indent=2) + "\n")
        for candidate in candidates:
            name = candidate["file"]
            row = dict(file=name, tags=candidate["type"].split(), strad_commit=STRAD,
                       metadata_sha256=sha256(ROOT / "CD.csv"), archive_url="https://www.thedatum.org/datasets/TSB-AD-M.zip",
                       source_group=None, provenance_status="unresolved_original_trace_mapping")
            if name not in members:
                row.update(eligible=False, exclusions=["missing_archive_member"])
                rows.append(row)
                continue
            blob = z.read(members[name])
            df = pd.read_csv(io.BytesIO(blob), float_precision="round_trip")
            cutoff = int(re.search(r"_tr_(\d+)_", name)[1])
            row.update(inspect_frame(df, cutoff))
            row.update(archive_member=members[name], raw_sha256=hashlib.sha256(blob).hexdigest(),
                       cutoff_provenance=f"https://github.com/TheDatumOrg/TSB-AD/blob/{TSBAD}/Datasets/README.md",
                       benchmark_trace=name, upstream_dataset=name.split("_id_")[0].split("_",1)[1])
            row.update(original_dataset_catalog_url=source_urls.get(row["upstream_dataset"]),
                       source_catalog_sha256=sha256(ROOT / "TSB_source_catalog.html"),
                       archive_sha256_reference="downloads.json: data/phase_a/TSB-AD-M.zip",
                       cutoff_semantics="Original TSB-released prefix cutoff, not necessarily the native source's training partition.",
                       source_mapping_note="Catalog identifies dataset only, not native trace/channel/crop transformation; unknown identity cannot qualify.")
            if row.get("finite_observations"):
                arrays[name] = df.iloc[:, :-1].to_numpy(dtype=np.float64)
            rows.append(row)
            print("audited", name, flush=True)
    relations = []
    # All candidate pairs: exact full-trace equality and contiguous crop checks.
    for left, right in itertools.combinations(arrays, 2):
        x, y = arrays[left], arrays[right]
        if x.shape[1] != y.shape[1]: continue
        small, large = (left, right) if len(x) <= len(y) else (right, left)
        offset = contained_offset(arrays[small], arrays[large])
        if offset is not None:
            relations.append(dict(left=small, right=large, relation="exact_duplicate" if len(x)==len(y) else "exact_contiguous_crop", offset=offset))
    # Compare every SMD candidate against all 28 original SMD test traces.
    for raw_path in sorted((ROOT / "smd_raw").glob("*_test.txt")):
        original = np.loadtxt(raw_path, delimiter=",")
        for row in rows:
            if row.get("upstream_dataset") != "SMD" or row["file"] not in arrays: continue
            offset = contained_offset(arrays[row["file"]], original)
            if offset is not None:
                machine = raw_path.name.removesuffix("_test.txt")
                row.update(source_group=f"SMD/{machine}", original_trace=f"ServerMachineDataset/test/{machine}.txt",
                           original_trace_sha256=sha256(raw_path), original_offset=offset,
                           original_commit=OMNI, original_url=f"https://raw.githubusercontent.com/NetManAIOps/OmniAnomaly/{OMNI}/ServerMachineDataset/test/{machine}.txt",
                           provenance_status="content_verified_exact_original_crop")
    for row in rows:
        errors = list(row.get("numeric_exclusions", row.get("exclusions", [])))
        if row.get("upstream_dataset") == "CATSv2":
            errors.append("synthetic_source_excluded_by_protocol")
            row["synthetic_provenance"] = "https://zenodo.org/records/8338435"
        if row.get("upstream_dataset") == "CreditCard":
            row["source_mapping_note"] += " Catalog incorrectly links CreditCard finance to CICIDS2017; unresolved contradiction."
        if row["provenance_status"] == "unresolved_original_trace_mapping": errors.append("unresolved_original_trace_mapping")
        if row.get("source_group") in ("SMD/machine-1-8", "SMD/machine-2-1"):
            errors.append("overlap_fixed_SMD")
        row.update(exclusions=errors, eligible=not errors)
    (OUT / "candidate_inventory.json").write_text(json.dumps(rows, indent=2) + "\n")
    (OUT / "trace_relations.json").write_text(json.dumps(relations, indent=2) + "\n")
    result = assign(rows)
    summary = dict(status="PASS" if result else "STOP", candidates=len(rows),
                   numeric_pass=sum(r.get("numeric_pass",False) for r in rows),
                   eligible=sum(r["eligible"] for r in rows),
                   eligible_sources_by_bucket={b: len({r["source_group"] for r in rows if r["eligible"] and b in r["tags"]}) for b in BUCKETS},
                   unresolved=sum(r["provenance_status"]=="unresolved_original_trace_mapping" for r in rows),
                   relations=len(relations), selected=[r["file"] for r in result] if result else [])
    summary["exclusion_counts_nonexclusive"] = {e: sum(e in r["exclusions"] for r in rows)
                                               for e in sorted({e for r in rows for e in r["exclusions"]})}
    summary["periodic_remaining_even_if_unresolved_origins_were_independent"] = [r["file"] for r in rows
        if "periodic" in r["tags"] and not (set(r["exclusions"]) - {"unresolved_original_trace_mapping"})]
    (OUT / "audit_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    if result: (OUT / "sealed_manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
