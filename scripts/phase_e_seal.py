"""Final reporting seal after all launch logs have closed."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/phase_e'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
    code={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'scripts').glob('phase_e*.py'))}
    code['tests/test_phase_e_schema.py']=sha(ROOT/'tests/test_phase_e_schema.py')
    (REPORT/'code_hashes.json').write_text(json.dumps(code,indent=2)+'\n')
    artifacts=json.loads((REPORT/'source_hashes.json').read_text())
    artifacts.update(json.loads((REPORT/'reference_pilot.json').read_text())['artifacts'])
    deb=ROOT/'data/phase_e/libpython3.12-dev_3.12.3-1ubuntu0.17_arm64.deb'
    artifacts[str(deb.relative_to(ROOT))]=sha(deb)
    for p,h in artifacts.items():assert sha(ROOT/p)==h
    (REPORT/'local_artifact_SHA256SUMS').write_text(''.join(f'{h}  {p}\n' for p,h in sorted(artifacts.items())))
    files=sorted(p for p in REPORT.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
    (REPORT/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(ROOT)}\n' for p in files))
    print('Phase E sealed',len(files),'reports;',len(artifacts),'local inputs/diagnostic artifacts')
