"""Independent checks of D0 source buffers, statistical code and label boundary."""
import copy
import inspect
import json
import sys
import numpy as np
import torch
from phase_d_operator import ROOT,REPORT,DATA,OFFICIAL,update,object_hash,tensor_hash
from phase_c_run import digest,state_hash
from phase_d_grid import load,reset,score
from phase_d_buffers import compose
from phase_d_statistics import paired_summary,holm
from config import get_cfg_defaults
from datasets.build import build_dataset


def main():
    capture=torch.load(DATA/'real_operator_capture.pth',map_location='cpu',weights_only=False)
    cfg=get_cfg_defaults();cfg.merge_from_other_cfg(type(cfg).load_cfg(capture['config']))
    cfg.DATA.BASE_DIR=str(OFFICIAL/'data')
    dataset=build_dataset(cfg,'test')
    expected=torch.from_numpy(np.stack([dataset[i][0] for i in capture['event']['ids']]))
    assert torch.equal(expected,capture['buffer'])
    segment=torch.from_numpy(np.stack([dataset[i][0] for i in range(256,512)]))
    assert torch.equal(segment,capture['segment'])
    assert list(inspect.signature(update).parameters)==['adapter','buffer']
    # Actual D8 label permutation closure: same prestate, x and buffer, shuffled
    # evaluator truth stays outside operator; score/update state must not change.
    arms,x,y,mask,m=compose(3000,'abrupt','spike')
    adapter,state=load(11)
    mean=np.array(state['scaler']['scaler_mean']); scale=np.array(state['scaler']['scaler_scale'])
    buffer=torch.from_numpy(np.ascontiguousarray((arms[10]-mean)/scale,dtype=np.float32)).cuda()
    test=torch.from_numpy(np.ascontiguousarray((x-mean)/scale,dtype=np.float32))
    outcomes=[]
    for permute in (False,True):
        labels=np.random.default_rng(902).permutation(y) if permute else y.copy()
        reset(adapter,state)
        losses=update(adapter,buffer)
        scores=score(adapter.model,test)
        outcomes.append(dict(model=state_hash(adapter.model),scores=tensor_hash(scores),optimizer=object_hash(adapter.optimizer.state_dict()),losses=losses))
        assert len(labels)==len(scores)  # labels are used only outside adaptation
    assert outcomes[0]==outcomes[1]
    dry=json.loads((REPORT/'rows/3000_abrupt_spike_11.json').read_text())['rows']
    target=next(r for r in dry if r['c']==10)
    assert outcomes[0]['model']==target['final_model_sha256']
    assert outcomes[0]['scores']==tensor_hash(np.load(ROOT/target['score_path']))
    zero=paired_summary(np.zeros((10,5,4)))
    positive=paired_summary(np.full((10,5,4),.03))
    negative=paired_summary(np.full((10,5,4),-.03))
    assert zero['p_two_sided']==1 and zero['ci95']==[0,0]
    assert positive['p_two_sided']==2/1024 and negative['p_two_sided']==2/1024
    assert np.allclose(positive['ci95'],[.03,.03])
    assert positive['positive_detector_seeds']==5 and negative['positive_detector_seeds']==0
    assert holm([.01,.02,1])==[.03,.04,1]
    tests=dict(status='PASS',native_buffer_reconstructed_from_official_dataset_exact=True,
        native_next_segment_reconstructed_exact=True,ordered_examples_hash=tensor_hash(expected),
        controlled_operator_has_no_label_argument=True,synthetic_label_permutation_exact=True,
        synthetic_repeat_vs_dry_exact=True,synthetic_repeat_hashes=outcomes,
        statistics_tests=['zero differences p1/CI0','constant signed differences exact two-sided2/1024',
            'paired bootstrap constant preservation','seed sign counts','Holm reference vector'],
        no_new_harm_condition=True)
    (REPORT/'independent_integrity.json').write_text(json.dumps(tests,indent=2)+'\n')
    print('Independent native buffer/order, D8 label-isolation/repeat, statistics PASS')


if __name__=='__main__': main()
