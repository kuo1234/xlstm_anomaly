"""Acquire three prospectively selected unscored process-failure runs; no detector execution."""
import csv,hashlib,io,json,subprocess,sys,urllib.request,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
REPO=Path(__file__).resolve().parents[3];ROOT=REPO/'research/fault_observability_blackout_n2';CACHE=REPO/'data/fault_observability_blackout_n2'
sys.path.insert(0,str(REPO/'research/exathlon_lifecycle_e1/scripts'))
from prepare import features,normalize,INPUTS
PIN='4101f6087f902fa150e392b65c957976faa84e40'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
def main():
    tree=json.loads((REPO/'research/exathlon_semantic_failure_e0/provenance/exathlon_tree.json').read_text())['tree']
    chosen=['2_5_1000000_87','3_5_1000000_89','5_5_1000000_91','5_5_1000000_92','8_5_1000000_83'];rows=[];sources=[]
    old=json.loads((REPO/'research/exathlon_lifecycle_e1/configs/data_manifest.json').read_text());assert not set(chosen)&{r['trace'] for r in old}
    for name in chosen:
        parts=[r for r in tree if r['type']=='blob' and (r['path'].endswith('/'+name+'.zip') or r['path'].endswith('/'+name+'.z01'))]
        folder=CACHE/'raw'/name;folder.mkdir(parents=True,exist_ok=True)
        for r in parts:
            dst=folder/Path(r['path']).name;url=f'https://raw.githubusercontent.com/exathlonbenchmark/exathlon/{PIN}/{r["path"]}'
            if not dst.exists():
                with urllib.request.urlopen(url,timeout=180) as src,dst.open('wb') as target:
                    while chunk:=src.read(1024*1024):target.write(chunk)
            data=dst.read_bytes();assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==r['sha']
            sources.append({'trace':name,'path':r['path'],'url':url,'git_blob_sha':r['sha'],'sha256':sha(dst),'bytes':len(data),'local_path':str(dst.relative_to(REPO))})
        archive=folder/(name+'.zip')
        if len(parts)>1:
            merged=folder/'merged.zip'
            if not merged.exists():subprocess.run(['zip','-s','0',str(archive), '--out',str(merged)],check=True,capture_output=True)
            archive=merged
        with zipfile.ZipFile(archive) as z:
            member=next(n for n in z.namelist() if n.endswith('.csv'))
            digest=hashlib.sha256()
            with z.open(member) as h:
                while chunk:=h.read(1024*1024):digest.update(chunk)
            with z.open(member) as h:cols=next(csv.reader(io.TextIOWrapper(h)))
            with z.open(member) as h:raw=pd.read_csv(h,usecols=[c for c in cols if c=='t' or normalize(c) in INPUTS])
        t,x,obs=features(raw);dest=CACHE/(name+'.npz');np.savez_compressed(dest,t=t,x=x,observed=obs)
        rows.append({'trace':name,'app':int(name.split('_')[0]),'role':'unseen_fault_test','csv_sha256':digest.hexdigest(),'assembled_zip_sha256':sha(archive),'array_sha256':hashlib.sha256(t.tobytes()+x.tobytes()+obs.tobytes()).hexdigest(),'prepared_path':str(dest.relative_to(REPO)),'rows':len(raw),'grid_rows':len(t),'missing_timestamps':int((~obs).sum()),'duplicate_rows':len(raw)-raw.t.nunique()})
        print('acquired',name,len(t),flush=True)
    save(ROOT/'provenance/raw_sources.json',sources);save(ROOT/'configs/test_manifest.json',rows)
if __name__=='__main__':main()
