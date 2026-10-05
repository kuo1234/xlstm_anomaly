"""Fetch immutable public evidence only; never executes benchmark/model code."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
PIN='7078876bbd9398481a65c22b7689702ce9e0d558'
CACHE=REPO/'data/d0_issue24_sources'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fetch():
    ledger=json.loads((ROOT/'provenance/strad_sources.json').read_text())+json.loads((ROOT/'provenance/reference_sources.json').read_text())
    def one(row):
        if row.get('status') not in (None,'retrieved'):return
        path=CACHE/('StrAD' if row.get('commit')==PIN else 'references')/row['path']
        path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists():path.write_bytes(urllib.request.urlopen(row['url'],timeout=45).read())
        assert sha(path)==row['sha256'],str(path)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(one,ledger))
    return CACHE


if __name__=='__main__':print(fetch())
