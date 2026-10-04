import hashlib,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/"research/writable_neural_memory_p10/p4a_admission_benchmark"
RAW=ROOT/"data/p4a_admission_benchmark"
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1024**2),b""):h.update(b)
    return h.hexdigest()
def save(p,x):
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+"\n")
def freeze_check():
    s=json.loads((OUT/"provenance/freeze_inputs.json").read_text())
    for p,h in s["hashes"].items():
        if sha(ROOT/p)!=h:raise ValueError("frozen input hash mismatch:"+p)
    commit=subprocess.check_output(["git","log","-1","--format=%H","--",str((OUT/"provenance/freeze_inputs.json").relative_to(ROOT))],cwd=ROOT,text=True).strip()
    remote=subprocess.check_output(["git","ls-remote","origin","refs/heads/research/p7-p10-segment-memory"],cwd=ROOT,text=True).split()[0]
    subprocess.run(["git","merge-base","--is-ancestor",commit,remote],cwd=ROOT,check=True)
    return {"freeze_commit":commit,"remote_before_audit":remote,"utc":utc()}
