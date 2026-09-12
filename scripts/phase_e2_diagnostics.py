"""CPU scalar unit fixture with nonzero recurrent weights; not detector fitting."""
import json
import torch
from phase_e2_common import REPORT
from phase_e2_observer import scalar_reference
from xlstm.blocks.slstm.cell import sLSTMCellConfig,sLSTMCell

if __name__=='__main__':
    torch.manual_seed(710)
    cfg=sLSTMCellConfig(hidden_size=40,num_heads=4,backend='vanilla',dtype='float32',
        dtype_b='float32',dtype_r='float32',dtype_w='float32',dtype_g='float32',dtype_s='float32',dtype_a='float32')
    cell=sLSTMCell(cfg)
    with torch.no_grad():cell._recurrent_kernel.uniform_(-.05,.05)
    x=torch.randn(3,12,160)
    with torch.no_grad():
        actual,final=cell(x);traces,states=scalar_reference(cell,x)
    expected=traces['hidden'].permute(0,2,1,3)
    result=dict(status='PASS' if torch.allclose(actual,expected,atol=1e-5,rtol=1e-4) and torch.allclose(final,states[:,-1],atol=1e-5,rtol=1e-4) else 'BLOCKED',
        max_hidden_abs=float((actual-expected).abs().max()),max_state_abs=float((final-states[:,-1]).abs().max()),
        effective_input_range=[float(traces['input'].min()),float(traces['input'].max())],
        effective_retention_range=[float(traces['retention'].min()),float(traces['retention'].max())],
        note='Nonzero random recurrent matrix is an isolated unit fixture only; detector weights untouched; no optimizer/labels.')
    assert result['status']=='PASS'
    assert traces['input'].max()<=1 and traces['retention'].max()<=1
    (REPORT/'nonzero_recurrence_test.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
