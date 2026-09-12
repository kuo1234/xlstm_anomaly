"""Recheck immutable evidence, then seal v4 without rewriting earlier audits."""
import hashlib
import json
import zipfile
from pathlib import Path
from phase_a_fetch import ROOT, sha256
from phase_a_v3 import select

OUT = Path('reports/phase_a_v4')


def main():
    for directory in ('phase_a','phase_a_v3'):
        for line in Path(f'reports/{directory}/SHA256SUMS').read_text().splitlines():
            expected,path = line.split('  ',1)
            assert sha256(Path(path))==expected,path
    for machine in json.loads(Path('reports/phase_a/smd_seal.json').read_text()):
        for asset in machine['assets']:
            assert sha256(Path(asset['path']))==asset['sha256'],asset['path']
    rows = json.loads(Path('reports/phase_a_v3/candidate_inventory.json').read_text())
    with zipfile.ZipFile(ROOT/'TSB-AD-M.zip') as archive:
        for r in rows:
            assert hashlib.sha256(archive.read(r['archive_member'])).hexdigest()==r['raw_sha256']
            assert r['eligible_v3']==(not r['exclusions_v3'])
            if r['eligible_v3']:
                assert r['numeric_pass'] and r['source_family'] not in ('GHL','CATSv2')
    relations = json.loads(Path('reports/phase_a/trace_relations.json').read_text())
    try:
        selected,objectives = select(rows,relations,objective_version=4)
        status = 'PASS_A2'
    except RuntimeError as error:
        if str(error)!='STOP: no globally feasible assignment':
            raise
        selected,objectives,status = [],dict(blocker=str(error)),'STOP_A2'
    summary = dict(status=status,A1='seal_verified',**objectives,selected_count=len(selected),
        inventory_count=len(rows),eligible_count=sum(r['eligible_v3'] for r in rows),
        inventory_native_provenance_unresolved=sum(r['native_provenance_unresolved'] for r in rows),
        eligible_inventory_native_provenance_unresolved=sum(r['native_provenance_unresolved'] for r in rows if r['eligible_v3']),
        selected_native_provenance_unresolved=sum(r['native_provenance_unresolved'] for r in selected) if selected else None,
        rule='reports/m0_amendment_v4.md',inference_unit='source_family_first')
    OUT.mkdir(parents=True,exist_ok=True)
    for name,obj in [('candidate_inventory.json',rows),('manifest.json',selected),('selection_summary.json',summary)]:
        (OUT/name).write_text(json.dumps(obj,indent=2)+'\n')
    (OUT/'SHA256SUMS').write_text(''.join(f'{sha256(p)}  {p}\n' for p in sorted(OUT.glob('*.json'))))
    print(json.dumps(summary))
    for r in selected:
        print(r['selection_bucket'],r['file'],r['source_family'],r['native_provenance_unresolved'])


if __name__=='__main__':
    main()
