"""Pinned observation acquisition and fail-closed, pushed-seal label access for Step 2c."""
from __future__ import annotations
import datetime, json, subprocess, urllib.request
from pathlib import Path
import numpy as np
from p10_step2a_data import ProtocolViolation, sha256

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "research/p7-p10-segment-memory"
UPSTREAM = "7fb0e0acf89ea49908896bcc9f9e80fcfff6baf4"
MACHINES = ("machine-1-1", "machine-1-2", "machine-1-3", "machine-2-2", "machine-2-3", "machine-2-4", "machine-3-1", "machine-3-2", "machine-3-3")
URL = "https://raw.githubusercontent.com/NetManAIOps/OmniAnomaly/"+UPSTREAM+"/ServerMachineDataset/{split}/{machine}.txt"

def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

def observation_path(root, machine, split):
    if machine not in MACHINES or split not in ("train", "test"):
        raise ProtocolViolation("observation split/machine outside frozen allow-list")
    p=Path(root)/f"{machine}_{split}.txt"
    if "label" in str(p).lower():
        raise ProtocolViolation("observation path contains label")
    return p

def load_observations(machine, split, root):
    x=np.loadtxt(observation_path(root,machine,split),delimiter=",",dtype=np.float64)
    if x.ndim!=2 or not np.isfinite(x).all():
        raise ProtocolViolation("nonfinite/nonmatrix observations: no imputation authorized")
    return x

def acquire(root, out):
    rows=[]
    for m in MACHINES:
        row=dict(dataset_id="SMD/"+m,machine=m,upstream_commit=UPSTREAM,
                 normal_train="source-designated; no independent train labels",benign_transition_ground_truth=False,
                 claim="frozen exploratory machine-transfer",files={})
        for split in ("train","test"):
            p=observation_path(root,m,split); p.parent.mkdir(parents=True,exist_ok=True)
            url=URL.format(split=split,machine=m)
            if not p.exists(): urllib.request.urlretrieve(url,p)
            x=load_observations(m,split,root)
            row["files"][split]=dict(path=str(p.resolve()),url=url,sha256=sha256(p),shape=list(x.shape),
                                      constant_channels=int((x.std(0)==0).sum()),order="source row order; no timestamps")
        if row["files"]["train"]["shape"][1]!=row["files"]["test"]["shape"][1]:
            raise ProtocolViolation("incompatible dimensions")
        rows.append(row)
    Path(out).write_text(json.dumps(dict(datasets=rows,labels_read=0,utc=utc()),indent=2)+"\n")

def verify_seal(run, expected_sha):
    run=Path(run); p=run/"seal.json"
    if not p.exists() or sha256(p)!=expected_sha: raise ProtocolViolation("seal SHA mismatch")
    seal=json.loads(p.read_text())
    if seal.get("stage")!="step2c_label_blind" or seal.get("labels_read")!=0 or seal.get("posthoc") is not False or seal.get("cv_max")!=0.10:
        raise ProtocolViolation("invalid frozen seal")
    if seal["machines"]!=list(MACHINES): raise ProtocolViolation("machine list changed")
    for rel,h in seal["files"].items():
        if sha256(run/rel)!=h: raise ProtocolViolation("sealed file changed: "+rel)
    for rel,h in seal["code"].items():
        if sha256(ROOT/rel)!=h: raise ProtocolViolation("frozen code changed: "+rel)
    cfg=json.loads((run/"policy_config.json").read_text())
    from p10_step2c_transfer import CONFIG, validate_config
    validate_config(cfg)
    if cfg!=CONFIG: raise ProtocolViolation("hidden config change")
    # Find the commit that introduced this exact seal, then prove it is on the configured remote branch.
    rel=str(p.resolve().relative_to(ROOT))
    commit=git("log","-1","--format=%H","--",rel)
    if not commit: raise ProtocolViolation("seal not committed")
    blob=subprocess.check_output(["git","show",commit+":"+rel],cwd=ROOT)
    import hashlib
    if hashlib.sha256(blob).hexdigest()!=expected_sha: raise ProtocolViolation("uncommitted seal")
    remote=git("ls-remote","origin","refs/heads/"+BRANCH).split()[0]
    try: git("merge-base","--is-ancestor",commit,remote)
    except subprocess.CalledProcessError as e: raise ProtocolViolation("seal commit not pushed") from e
    return dict(seal_commit=commit,remote_commit=remote,verified_utc=utc(),seal_sha256=expected_sha)

def load_test_labels(machine, *, run, expected_sha, root, log_path):
    proof=verify_seal(run,expected_sha)
    if machine not in MACHINES: raise ProtocolViolation("unsealed machine")
    p=Path(root)/f"{machine}_test_label.txt"; p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists(): urllib.request.urlretrieve(URL.format(split="test_label",machine=machine),p)
    # Persist the access attempt before parsing, including provenance and pushed-seal proof.
    log=Path(log_path); entries=json.loads(log.read_text()) if log.exists() else []
    entries.append(dict(machine=machine,purpose="step2c_frozen_transfer",utc=utc(),label_sha256=sha256(p),
                        label_url=URL.format(split="test_label",machine=machine),**proof))
    log.write_text(json.dumps(entries,indent=2)+"\n")
    y=np.loadtxt(p,dtype=np.float64,ndmin=1)
    if not np.isin(y,[0,1]).all(): raise ProtocolViolation("labels nonbinary")
    return y.astype(np.int64)

if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser(); a.add_argument("--root",required=True); a.add_argument("--out",required=True)
    s=a.parse_args(); acquire(s.root,s.out)
