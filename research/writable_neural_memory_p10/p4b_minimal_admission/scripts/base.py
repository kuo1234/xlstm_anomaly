import json,hashlib,subprocess
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/"research/writable_neural_memory_p10/p4b_minimal_admission"
RAW=ROOT/"data/p4b_minimal_admission"
A=OUT.parent/"p4a_admission_benchmark"
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(1024**2),b""):h.update(b)
 return h.hexdigest()
def ah(x):return hashlib.sha256(x.tobytes()).hexdigest()
def save(p,x):
 Path(p).parent.mkdir(parents=True,exist_ok=True)
 Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+"\n")
def freeze():
 f=json.loads((OUT/"provenance/freeze.json").read_text())
 for path,h in f["hashes"].items():
  if sha(ROOT/path)!=h:raise ValueError("frozen input changed:"+path)
 commit=subprocess.check_output(["git","log","-1","--format=%H","--",str((OUT/"provenance/freeze.json").relative_to(ROOT))],text=True,cwd=ROOT).strip()
 remote=subprocess.check_output(["git","ls-remote","origin","refs/heads/research/p7-p10-segment-memory"],text=True,cwd=ROOT).split()[0]
 subprocess.run(["git","merge-base","--is-ancestor",commit,remote],cwd=ROOT,check=True)
 return {"freeze_commit":commit,"verified_remote_SHA":remote,"check_utc":utc()}
