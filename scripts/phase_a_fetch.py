"""Fetch only dataset/provenance assets; never detector results or model code.

Run from repository root. Downloads are cached, with an inventory of byte hashes.
"""
import concurrent.futures
import hashlib
import json
import subprocess
from pathlib import Path

STRAD = "7078876bbd9398481a65c22b7689702ce9e0d558"
TSBAD = "6beac72e11d1155ade40870492c00d0d1cfdcaaf"
OMNI = "7fb0e0acf89ea49908896bcc9f9e80fcfff6baf4"
CANDI = "28c9679e503832f59e351208cde63657fcb51cad"
ROOT = Path("data/phase_a")
OUT = Path("reports/phase_a")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def fetch(item):
    name, url, commit = item
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        temporary = path.with_suffix(path.suffix + ".part")
        subprocess.run(["rtk", "curl", "--fail", "-L", "--retry", "2", "--max-time", "600",
                        "-o", str(temporary), url], check=True, capture_output=True)
        temporary.replace(path)
    return dict(path=str(path), url=url, commit=commit,
                bytes=path.stat().st_size, sha256=sha256(path))


def main():
    assets = [
        ("CD.csv", f"https://raw.githubusercontent.com/magaliparrino/StrAD/{STRAD}/results/benchmark_eval_results/CD.csv", STRAD),
        ("TSB-AD-M.zip", "https://www.thedatum.org/datasets/TSB-AD-M.zip", None),
        ("TSB_datasets_README.md", f"https://raw.githubusercontent.com/TheDatumOrg/TSB-AD/{TSBAD}/Datasets/README.md", TSBAD),
        ("TSB-AD-M_file_list.csv", f"https://raw.githubusercontent.com/TheDatumOrg/TSB-AD/{TSBAD}/Datasets/File_List/TSB-AD-M.csv", TSBAD),
        ("OmniAnomaly_README.md", f"https://raw.githubusercontent.com/NetManAIOps/OmniAnomaly/{OMNI}/README.md", OMNI),
        ("TSB_source_catalog.html", f"https://raw.githubusercontent.com/TheDatumOrg/TSB-AD/{TSBAD}/docs/index.html", TSBAD),
        ("CATSv2_zenodo.json", "https://zenodo.org/api/records/8338435", None),
        ("cutoff_author_comment.json", "https://api.github.com/repos/TheDatumOrg/TSB-AD/issues/comments/2550137783", None),
    ]
    for machine in ("machine-1-8", "machine-2-1"):
        for split in ("train", "test", "test_label"):
            assets += [
                (f"smd_raw/{machine}_{split}.txt", f"https://raw.githubusercontent.com/NetManAIOps/OmniAnomaly/{OMNI}/ServerMachineDataset/{split}/{machine}.txt", OMNI),
                (f"smd_candi/{machine}_{split}.pkl", f"https://raw.githubusercontent.com/kimanki/CANDI/{CANDI}/data/ServerMachineDataset/preprocessed/{machine}_{split}.pkl", CANDI),
            ]
    # Needed for content-verified TSB SMD origin/overlap mapping, not detection.
    for group, count in ((1, 8), (2, 9), (3, 11)):
        for index in range(1, count + 1):
            machine = f"machine-{group}-{index}"
            if machine in ("machine-1-8", "machine-2-1"):
                continue
            assets.append((f"smd_raw/{machine}_test.txt", f"https://raw.githubusercontent.com/NetManAIOps/OmniAnomaly/{OMNI}/ServerMachineDataset/test/{machine}.txt", OMNI))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(fetch, assets))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "downloads.json").write_text(json.dumps(records, indent=2) + "\n")
    # Exact copies of small source metadata are committed for offline inspection.
    for name in ("CD.csv", "TSB_datasets_README.md", "TSB-AD-M_file_list.csv"):
        (OUT / name).write_bytes((ROOT / name).read_bytes())
    print(json.dumps({"assets": len(records), "download_inventory": str(OUT / "downloads.json")}))


if __name__ == "__main__":
    main()
