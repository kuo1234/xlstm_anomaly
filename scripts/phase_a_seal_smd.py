"""Seal original SMD and immutable CANDI preprocessing without loading pickles."""
import json
import numpy as np
from phase_a_fetch import ROOT, OUT, OMNI, CANDI, sha256


def main():
    downloads = {r["path"]: r for r in json.loads((OUT / "downloads.json").read_text())}
    rows = []
    for machine in ("machine-1-8", "machine-2-1"):
        train = np.loadtxt(ROOT / f"smd_raw/{machine}_train.txt", delimiter=",")
        test = np.loadtxt(ROOT / f"smd_raw/{machine}_test.txt", delimiter=",")
        labels = np.loadtxt(ROOT / f"smd_raw/{machine}_test_label.txt", delimiter=",")
        assert train.ndim == test.ndim == 2 and train.shape[1] == test.shape[1] >= 2
        assert np.isfinite(train).all() and np.isfinite(test).all()
        assert labels.shape == (len(test),) and np.isin(labels, [0, 1]).all()
        assets = [downloads[str(ROOT / f"{folder}/{machine}_{split}.{ext}")]
                  for folder, ext in (("smd_raw", "txt"), ("smd_candi", "pkl"))
                  for split in ("train", "test", "test_label")]
        cutoff = len(train)
        rows.append(dict(machine=machine, source_group=f"SMD/{machine}", D=train.shape[1],
                         N=len(train)+len(test), train_N=len(train), test_N=len(test), cutoff=cutoff,
                         audit_fit_interval=[0, 4*cutoff//5],
                         audit_calibration_interval=[4*cutoff//5, cutoff],
                         concatenated_test_interval=[cutoff, cutoff+len(test)],
                         official_reproduction="Keep original separate train/test and CANDI preprocessing; audit splits do not modify reproduction.",
                         finite_observations=True, binary_test_labels=True,
                         train_normality="Documented normal training split; upstream has no train-label file. Not independently label-verified.",
                         provenance_url=f"https://github.com/NetManAIOps/OmniAnomaly/blob/{OMNI}/README.md",
                         candi_commit=CANDI, assets=assets,
                         preprocessing_audit="Byte seal only; no pickle execution, normalization audit, or model run."))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "smd_seal.json").write_text(json.dumps(rows, indent=2) + "\n")
    print("Sealed 2 SMD machines, 12 raw/preprocessed assets; numerical checks passed.")


if __name__ == "__main__":
    main()
