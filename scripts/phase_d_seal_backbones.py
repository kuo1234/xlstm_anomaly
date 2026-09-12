"""Pre-outcome seal of all backbone states and buffer layouts."""
import json
import subprocess
from phase_d_operator import ROOT,REPORT,DATA,OFFICIAL,NOTE
from phase_d_backbone import SEEDS
from phase_c_run import digest


def main():
    assert json.loads((REPORT/'operator_parity.json').read_text())['status']=='PASS'
    assert json.loads((REPORT/'pre_curve_tests.json').read_text())['status']=='PASS'
    rows=[json.loads((REPORT/f'backbone_{s}.json').read_text()) for s in SEEDS]
    for r in rows:
        assert not r['authorized_test_sources_used']
        for p,h in r['artifacts'].items(): assert digest(ROOT/p)==h
    assert len(json.loads((REPORT/'buffer_manifest.json').read_text())['rows'])==160
    assert len({r['initial_model_sha256'] for r in rows})==5
    result=dict(prospective_commit=NOTE,rows=rows,all_frozen_before_test_harm=True,
        buffer_manifest_sha256=digest(REPORT/'buffer_manifest.json'),
        official_commit=subprocess.check_output(['rtk','git','-C',str(OFFICIAL),'rev-parse','HEAD'],text=True).strip(),
        note='seed11 timed alone; remaining four training processes launched concurrently. Per-process timings/memory are not aggregate device peaks.')
    (REPORT/'synthetic_backbone_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print('All five backbones, scaler/threshold/SGD/RNG states and160 layouts sealed before harm')


if __name__=='__main__': main()
