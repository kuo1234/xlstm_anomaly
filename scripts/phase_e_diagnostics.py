"""Small CPU fixtures to localize failures without changing any detector."""
import json,sys
import torch
from phase_e_common import REPORT,native
from phase_e_observer import scalar_reference
from xlstm.blocks.slstm.cell import sLSTMCellConfig,sLSTMCell
from models.reconstruct_dataset import ReconstructNormalizedDataset
import numpy as np

if __name__=='__main__':
    cfg=sLSTMCellConfig(hidden_size=40,num_heads=4,backend='vanilla',dtype='float32',
        dtype_b='float32',dtype_r='float32',dtype_w='float32',dtype_g='float32',dtype_s='float32',dtype_a='float32')
    torch.manual_seed(710)
    cell=sLSTMCell(cfg)
    # Unit fixture deliberately exercises nonzero recurrent weights, unlike the
    # native untrained zero-R initialization; never used in detector or probe.
    with torch.no_grad():cell._recurrent_kernel.uniform_(-.05,.05)
    x=torch.randn(3,8,160)
    with torch.no_grad():
        actual,final=cell(x);traces,states=scalar_reference(cell,x)
    error=float((actual-traces['hidden'].permute(0,2,1,3)).abs().max())
    assert torch.allclose(actual,traces['hidden'].permute(0,2,1,3),atol=1e-5,rtol=1e-4)
    assert torch.allclose(final,states[:,-1],atol=1e-5,rtol=1e-4)
    # Model-free native layout fixture: rows of a batch cease to be independent.
    output=torch.arange(4.).view(1,4,1).expand(64,4,8).contiguous()
    target=torch.zeros(4,64,8)
    def scores(o):return (o.view(4,512)-target.view(4,512)).square().mean(1)
    before=scores(output);changed=output.clone();changed[:,3]=100;after=scores(changed)
    assert before[0]!=after[0]  # window0 output/target unchanged; window3 contaminates its score
    data=np.arange(80*8,dtype=float).reshape(80,8)
    ds=ReconstructNormalizedDataset(data,64,normalize=False)
    assert len(ds)==80 and torch.equal(ds[16][0],ds[79][0])
    result=dict(status='PASS_DIAGNOSTIC_FAILURE_LOCALIZED',nonzero_recurrent_reference_max_abs=error,
        nonzero_R_is_unit_fixture_only=True,native_layout_other_window_changes_score=True,
        marker_score_before=before.tolist(),marker_score_after=after.tolist(),
        native_dataset_count=80,causally_distinct_windows=17,tail_repeats_last_window=True,
        tail_indices_inclusive=[16,79],detector_or_dataset_fixes_applied=False)
    (REPORT/'independent_diagnostics.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
