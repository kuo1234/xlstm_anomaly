"""Seal the pre-training STOP evidence; never overwrites accepted E2 artifacts."""
import json
import subprocess
from phase_f_common import ROOT, REPORT, DATA, sha, write_json

def main():
    checked={}
    for filename in ('SHA256SUMS','local_artifact_SHA256SUMS'):
        lines=(ROOT/'reports/phase_e2'/filename).read_text().splitlines()
        for line in lines:
            digest,path=line.split(maxsplit=1)
            assert sha(ROOT/path)==digest,path
        checked[filename]=len(lines)
    e2_files=subprocess.check_output(['rtk','git','ls-tree','-r','--name-only','4d49f1d','reports/phase_e2'],text=True).splitlines()
    for path in e2_files:
        assert subprocess.check_output(['rtk','git','show',f'4d49f1d:{path}'])==(ROOT/path).read_bytes(),path
    gates=json.loads((REPORT/'mechanical_gates.json').read_text())
    assert gates['status']=='STOP'
    assert not (DATA/'runs').exists()
    write_json(REPORT/'status.json',dict(phase_f='STOP_IMPLEMENTATION_VALIDITY',scientific_optimizer_steps=0,
        trained_checkpoints=0,post_training_parity='NOT_RUN',training_curves='NOT_RUN',
        reason='Frozen cuDNN TF32-enabled LSTM native/manual scalar-state parity fails',
        prospective_commit='4c76e07',E2_immutable_commit='4d49f1d',
        H1_controlled_harm='STOP',H1_natural_harm='NOT_RUN',H1_harm_overall='UNRESOLVED',
        H2_H3='NOT_TESTED',phase_g='LOCKED',scientific_backend_changed=False,
        diagnostic_alternate_backend_only=True,test_sources_used=False,labels_extracted=False,
        probe_fit=False,tolerance_changed=False))
    write_json(REPORT/'integrity.json',dict(E2_sha_lists_verified=checked,E2_tracked_files_unchanged=len(e2_files),
        E2_tests_recomputed=False,scientific_run_directory_absent=True))
    local=sorted(p for p in DATA.rglob('*') if p.is_file())
    (REPORT/'local_artifact_SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(ROOT)}\n' for p in local))
    paths=sorted([*ROOT.glob('scripts/phase_f_*.py'),ROOT/'configs/phase_f.json'])
    write_json(REPORT/'code_hashes.json',{str(p.relative_to(ROOT)):sha(p) for p in paths})
    paths+=sorted(p for p in REPORT.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
    (REPORT/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(ROOT)}\n' for p in sorted(paths)))
    print(json.dumps(dict(status='SEALED_STOP',E2_files_unchanged=len(e2_files),local_artifacts=len(local),sealed_files=len(paths))))

if __name__=='__main__': main()
