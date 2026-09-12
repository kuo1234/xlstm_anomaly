"""Seal E2 report and local artifacts after launch logs close."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];REPORT=ROOT/'reports/phase_e2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
    code={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'scripts').glob('phase_e2*.py'))}
    code['tests/test_phase_e2_schema.py']=sha(ROOT/'tests/test_phase_e2_schema.py')
    (REPORT/'code_hashes.json').write_text(json.dumps(code,indent=2)+'\n')
    artifacts=json.loads((REPORT/'source_hashes.json').read_text())
    for name in ('validity.json','validity_verified.json'):
        artifacts.update(json.loads((REPORT/name).read_text())['artifacts'])
    for p,h in artifacts.items():assert sha(ROOT/p)==h
    (REPORT/'local_artifact_SHA256SUMS').write_text(''.join(f'{h}  {p}\n' for p,h in sorted(artifacts.items())))
    files=sorted(p for p in REPORT.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
    (REPORT/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(ROOT)}\n' for p in files))
    print('Sealed',len(files),'reports;',len(artifacts),'source/dependency/diagnostic artifacts')
