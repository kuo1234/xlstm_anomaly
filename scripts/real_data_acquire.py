"""Acquire only explicitly selected public raw assets; never run research models.

All outputs live in ignored data/external_real. URLs are pinned to source commits
where possible. A second run validates an existing file instead of overwriting it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.request import urlopen
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "external_real"
SMD_COMMIT = "7fb0e0acf89ea49908896bcc9f9e80fcfff6baf4"
ANDRI_COMMIT = "df27f8eee3244c431c55519ebc84957d46924a44"
TELEMANOM_COMMIT = "2e6c5b6c3558e7835601519b7bdef37c649bdbdc"
HAI_COMMIT = "2a814cebc9a66b06c9e5cd545e2d72e65d383737"
SMD_BASE = f"https://raw.githubusercontent.com/NetManAIOps/OmniAnomaly/{SMD_COMMIT}/ServerMachineDataset"
ANDRI_BASE = f"https://raw.githubusercontent.com/mac-dsl/AnDri/{ANDRI_COMMIT}/data/processed/sensor"
FILES = {
    "smd-1-4": [(f"smd/machine-1-4_{split}.txt", f"{SMD_BASE}/{subdir}/machine-1-4.txt")
                for split, subdir in (("train", "train"), ("test", "test"), ("test_label", "test_label"))],
    "smd-2-1": [(f"smd/machine-2-1_{split}.txt", f"{SMD_BASE}/{subdir}/machine-2-1.txt")
                for split, subdir in (("train", "train"), ("test", "test"), ("test_label", "test_label"))],
    "andri-sensor": [(f"andri_sensor/real iot {i}.csv", f"{ANDRI_BASE}/real%20iot%20{i}.csv") for i in (1, 2)],
    "nasa-labels": [("nasa/labeled_anomalies.csv", f"https://raw.githubusercontent.com/khundman/telemanom/{TELEMANOM_COMMIT}/labeled_anomalies.csv")],
}
# Existing Phase A seal is the independently recorded raw source, not CANDI's transformed pickle.
SEALED_SMD_2_1 = {
    "smd/machine-2-1_train.txt": "d6eb13ff74a537cf33686319fffdd4cdcb394862570a3acd519b4c37af97cd2e",
    "smd/machine-2-1_test.txt": "2d103661799271be958227907950a1c76803356442d60a4070671cc0abbefb20",
    "smd/machine-2-1_test_label.txt": "416dd20a447f38b8d9394382293ed44f509c1c3f99c4aa2fbff179498626dbdc",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fetch(path: Path, url: str, expected: str | None = None) -> None:
    if path.exists():
        digest = sha256(path)
        if expected and digest != expected:
            raise ValueError(f"Existing file mismatch: {path}: {digest} != {expected}; no overwrite")
        print(f"REUSE {path} {digest}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".download-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as out, urlopen(url, timeout=60) as source:
            if source.status != 200:
                raise RuntimeError(f"HTTP {source.status}: {url}")
            shutil.copyfileobj(source, out)
        digest = sha256(Path(temporary))
        if expected and digest != expected:
            raise ValueError(f"Downloaded hash mismatch: {url}: {digest} != {expected}")
        os.replace(temporary, path)
        print(f"FETCH {path} {digest}")
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def nasa() -> None:
    # Official Telemanom distribution. Keep archive intact as an upstream evidence asset.
    archive = DEST / "nasa" / "telemanom-data.zip"
    fetch(archive, "https://s3-us-west-2.amazonaws.com/telemanom/data.zip")
    with zipfile.ZipFile(archive) as source:
        for group, series in (("MSL", "P-15"), ("SMAP", "T-3")):
            for split in ("train", "test"):
                suffix = f"/{split}/{series}.npy"
                matches = [name for name in source.namelist() if name == suffix.lstrip("/") or name.endswith(suffix)]
                if len(matches) != 1:
                    raise ValueError(f"Expected exactly one {suffix} in archive, found {matches}")
                target = DEST / "nasa" / group / split / f"{series}.npy"
                if target.exists():
                    with source.open(matches[0]) as stream:
                        h = hashlib.sha256()
                        for block in iter(lambda: stream.read(1024 * 1024), b""):
                            h.update(block)
                    if sha256(target) != h.hexdigest():
                        raise ValueError(f"Existing extraction differs: {target}; no overwrite")
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.open(matches[0]) as inp, target.open("xb") as out:
                    shutil.copyfileobj(inp, out)
                print(f"EXTRACT {target} {sha256(target)}")
    # Interval labels are separately pinned by --dataset nasa-labels.


def hai() -> None:
    if subprocess.run(["git", "lfs", "version"], capture_output=True).returncode:
        raise RuntimeError("HAI 22.04 requires Git LFS; install it and rerun --dataset hai. No pointers are treated as data.")
    target = DEST / "hai-22.04" / "official"
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--filter=blob:none", "--no-checkout", "https://github.com/icsdataset/hai.git", str(target)], check=True)
        subprocess.run(["git", "-C", str(target), "sparse-checkout", "set", "hai-22.04"], check=True)
    subprocess.run(["git", "-C", str(target), "checkout", HAI_COMMIT], check=True)
    subprocess.run(["git", "-C", str(target), "lfs", "pull", "--include=hai-22.04/*.csv"], check=True)
    for name in [*(f"train{i}.csv" for i in range(1, 7)), *(f"test{i}.csv" for i in range(1, 5))]:
        path = target / "hai-22.04" / name
        if not path.is_file() or path.open("rb").read(40).startswith(b"version https://git-lfs"):
            raise RuntimeError(f"Missing actual LFS contents: {path}")


def inventory() -> None:
    # Explicitly local-only; source URL is associated by relative path below.
    urls = {rel: url for entries in FILES.values() for rel, url in entries}
    urls["nasa/telemanom-data.zip"] = "https://s3-us-west-2.amazonaws.com/telemanom/data.zip"
    entries = []
    for path in sorted(DEST.rglob("*")):
        if not path.is_file() or ".git" in path.parts or path.name == "local_manifest.json":
            continue
        rel = path.relative_to(DEST).as_posix()
        entries.append({"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path),
                        "source_url": urls.get(rel, "derived from retained telemanom archive or pinned HAI Git LFS commit")})
    dest = DEST / "local_manifest.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps({"files": entries, "total_bytes": sum(x["bytes"] for x in entries)}, indent=2) + "\n")
    print(f"Inventory: {dest} ({len(entries)} files)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, choices=(*FILES, "nasa", "hai", "swat", "wadi", "yahoo", "creditcard", "inventory"))
    args = parser.parse_args()
    if args.dataset in ("swat", "wadi", "yahoo", "creditcard"):
        parser.error(f"{args.dataset} requires the original provider's request/terms; see acquisition_status.md. No mirror or credential bypass.")
    try:
        if args.dataset in FILES:
            for rel, url in FILES[args.dataset]:
                fetch(DEST / rel, url, SEALED_SMD_2_1.get(rel))
        elif args.dataset == "nasa":
            nasa()
        elif args.dataset == "hai":
            hai()
        inventory()
        return 0
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as error:
        print(f"Acquisition stopped: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
