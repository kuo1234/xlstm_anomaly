"""CPU-only seal/statistics checks; no quarantined outcome parsing."""
import inspect
import json
import subprocess
import numpy as np
from phase_d_operator import ROOT,update
from phase_c_run import digest
from phase_d_statistics import paired_summary,holm

REPORT=ROOT/'reports/phase_d_v2'


def main():
    unchanged=['scripts/phase_d_operator.py','scripts/phase_d_backbone.py','scripts/phase_d_buffers.py',
        'scripts/phase_d_grid.py','scripts/phase_d_statistics.py','scripts/phase_d_finalize.py',
        'reports/phase_d/prospective.md','reports/m0_protocol.md']
    for p in unchanged:
        assert subprocess.check_output(['rtk','git','show',f'6f20427:{p}'])==(ROOT/p).read_bytes(),p
    seals={}
    for folder in ('phase_c','phase_c_v2','phase_c3','phase_d'):
        lines=(ROOT/'reports'/folder/'SHA256SUMS').read_text().splitlines()
        for line in lines:
            h,p=line.split('  ',1);assert digest(ROOT/p)==h,p
        seals[folder]=len(lines)
    assert list(inspect.signature(update).parameters)==['adapter','buffer']
    zero=paired_summary(np.zeros((10,5,4)))
    positive=paired_summary(np.full((10,5,4),.03))
    negative=paired_summary(np.full((10,5,4),-.03))
    assert zero['p_two_sided']==1 and zero['ci95']==[0,0]
    assert positive['p_two_sided']==negative['p_two_sided']==2/1024
    assert np.allclose(positive['ci95'],[.03,.03])
    assert positive['positive_detector_seeds']==5 and negative['positive_detector_seeds']==0
    assert holm([.01,.02,1])==[.03,.04,1]
    files=unchanged+['scripts/phase_d_v2.py','scripts/phase_d_v2_launch.py',
        'scripts/phase_d_v2_integrity.py','scripts/phase_c_run.py']
    files+=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'m0').glob('*.py'))
    result=dict(status='PASS',original_scientific_code_unchanged=unchanged,
        prior_report_seals_verified=seals,controlled_update_has_no_label_argument=True,
        statistics_tests=['zero p1/CI0','signed constant exact sign-flip 2/1024',
            'constant hierarchical bootstrap','seed sign counts','Holm reference'],
        code_sha256={p:digest(ROOT/p) for p in files},
        quarantined_outcomes_parsed=False,prior_report_files_read_only_for_digest=True)
    (REPORT/'implementation_integrity.json').write_text(json.dumps(result,indent=2)+'\n')
    print('CPU integrity PASS: frozen operator/design/statistics unchanged; prior seals intact')


if __name__=='__main__':main()
