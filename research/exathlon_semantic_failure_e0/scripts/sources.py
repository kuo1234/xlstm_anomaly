"""Fetch/hash saved public source and bounded raw samples, never run models."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
CACHE=REPO/'data/exathlon_e0_sources'
RESULT=ROOT/'results'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fetch():
    rows=[]
    for name in ['source_inventory.json','raw_sample_sources.json','wiki_sources.json']:
        rows+=json.loads((ROOT/'provenance'/name).read_text())
    def one(row):
        if row['status'] not in ['retrieved','retrieved_unversioned_wiki']:return
        path=CACHE/row.get('cache_path',row['path']);path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists():path.write_bytes(urllib.request.urlopen(row['url'],timeout=60).read())
        assert sha(path)==row['sha256'],path
        if 'git_blob_sha' in row:
            data=path.read_bytes()
            assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==row['git_blob_sha'],path
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(one,rows))
    with zipfile.ZipFile(CACHE/'exathlon/data/raw/ground_truth.zip') as archive:
        (CACHE/'ground_truth.csv').write_bytes(archive.read('data/raw/ground_truth.csv'))
    return rows


if __name__=='__main__':print('verified',len(fetch()),'source ledger rows')
