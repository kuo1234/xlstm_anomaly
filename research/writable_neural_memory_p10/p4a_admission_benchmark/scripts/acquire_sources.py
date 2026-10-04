"""Reacquire only pinned public source/docs; never datasets, models or mirrors."""
import json
from pathlib import Path
import requests
from common import ROOT,OUT,sha
def main():
    for r in json.loads((OUT/"provenance/source_files.json").read_text()):
        url=r["url"]
        if not url.startswith("https://raw.githubusercontent.com/"+r["repo"]+"/"+r["commit"]+"/"):
            raise ValueError("source URL not pinned")
        p=ROOT/r["path"]
        if p.exists() and sha(p)==r["sha256"]:continue
        resp=requests.get(url,timeout=30);resp.raise_for_status()
        if len(resp.content)>4*1024**2:raise ValueError("source cap")
        p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(resp.content)
        if sha(p)!=r["sha256"]:raise ValueError("source hash mismatch; no fallback")
    print("pinned source hashes verified")
if __name__=="__main__":main()
