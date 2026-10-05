"""API/invariant gates on random observations, before and after training."""
from copy import deepcopy
import io
import numpy as np
import torch
from common import configure,load_config,model_hash,tensor_tree_hash,state_leaves
from models import build,carry,parameter_count

ATOL,RTOL=1e-5,1e-4


def state_compare(a,b):
    aa,bb=state_leaves(a),state_leaves(b)
    assert aa.keys()==bb.keys()
    assert all(torch.equal(aa[k],bb[k]) for k in aa)


def model_audit(model):
    cfg=load_config();model.eval();g=torch.Generator().manual_seed(99001)
    x=torch.randn(2,53,cfg['dimension'],generator=g)
    before=model_hash(model);checks={}
    with torch.inference_mode():
        full=model(x);step,end=carry(model,x)
        checks['full_step_max_abs']=float((full-step).abs().max())
        assert torch.allclose(full,step,atol=ATOL,rtol=RTOL)
        _,prefix=carry(model,x[:,:19]);snapshot=deepcopy(prefix);snap_hash=tensor_tree_hash(snapshot)
        suffix,tail=carry(model,x[:,19:],deepcopy(snapshot));buffer=io.BytesIO();torch.save(snapshot,buffer);buffer.seek(0)
        recovered=torch.load(buffer,weights_only=True);other,other_state=carry(model,x[:,19:],recovered)
        assert torch.equal(suffix,other);state_compare(tail,other_state)
        model.step(x[:,19:20],prefix);assert tensor_tree_hash(snapshot)==snap_hash
        checks['capture_restore_and_deepcopy']='PASS'
        active=None;chunks=[]
        for low,high in [(0,3),(3,19),(19,20),(20,53)]:
            output,active=carry(model,x[:,low:high],active);chunks.append(output);active=deepcopy(active)
        assert torch.equal(torch.cat(chunks,dim=1),step);state_compare(active,end)
        checks['chunk_delivery_parity']='PASS'
        reset,reset_end=carry(model,x[:,19:],None);fresh=model(x[:,19:])
        assert torch.allclose(reset,fresh,atol=ATOL,rtol=RTOL)
        checks['reset_native_fresh']='PASS'
        modified=x.clone();modified[:,19:]+=100
        assert torch.equal(model(modified)[:,:19],full[:,:19])
        assert torch.equal(carry(model,modified)[0][:,:19],step[:,:19])
        checks['future_prefix_invariance']='PASS'
        assert torch.allclose(carry(model,x.flip(0))[0],step.flip(0),atol=ATOL,rtol=RTOL)
        assert torch.allclose(torch.cat([carry(model,x[i:i+1])[0] for i in range(2)]),step,atol=ATOL,rtol=RTOL)
        checks['batch_partition_permutation']='PASS'
        assert all(torch.isfinite(v).all() for v in state_leaves(end).values())
        assert model_hash(model)==before
        checks['finite_parameters_buffers_frozen']='PASS'
        checks['state_shapes']={k:list(v.shape) for k,v in state_leaves(end).items()}
        if model.backbone=='xlstm':
            partial=deepcopy(snapshot)
            for block in partial.values():
                block.pop('slstm_state',None);block.pop('mlstm_state',None)
            altered,_=carry(model,x[:,19:],partial)
            assert not torch.allclose(altered,reset,atol=ATOL,rtol=RTOL)
            checks['conv_history_negative_control']='PASS'
    return checks


def preflight():
    from generator import process,invariants,process_seed,histories,MECHANISMS,SPLITS
    configure();cfg=load_config();assert cfg['model']['device']=='cpu'
    checks={};addresses=[]
    for mechanism in cfg['mechanisms']:
        for group in cfg['groups']:
            specs=[process(mechanism,group,r) for r in ('A','B')]
            for regime,spec in zip(('A','B'),specs):
                inv=invariants(spec)
                assert inv['spectral_radius']<1 and inv['min_sigma_eigenvalue']>1e-8 and inv['min_q_eigenvalue']>1e-8
                assert inv['lyapunov_max_abs']<=1e-10 and inv['symmetry_max_abs']<=1e-12
                assert inv['diagonal_variance_max_deviation']<=1e-10
                checks[f'{mechanism}_{group}_{regime}']=inv
                for split in SPLITS:
                    for index in range(64):addresses.append(process_seed(mechanism,group,split,regime,index))
            if mechanism=='correlation':
                assert np.array_equal(specs[0]['a'],specs[1]['a']) and np.array_equal(specs[0]['mean'],specs[1]['mean'])
                assert np.max(np.abs(np.diag(specs[0]['sigma'])-np.diag(specs[1]['sigma'])))<=1e-10
                assert abs(specs[0]['sigma']-specs[1]['sigma']).max()>=.2
            if mechanism=='dynamics':assert np.array_equal(specs[0]['sigma'],specs[1]['sigma']) and np.array_equal(specs[0]['mean'],specs[1]['mean'])
            if mechanism=='mean':assert np.array_equal(specs[0]['a'],specs[1]['a']) and np.array_equal(specs[0]['sigma'],specs[1]['sigma'])
            data=histories(mechanism,group)
            assert np.isfinite(data['b_suffix']).all()
            assert not np.array_equal(data['a_prefix'],data['b_prefix'])
    assert len(addresses)==len(set(addresses))
    counts={name:parameter_count(build(name,11)) for name in cfg['backbones']}
    assert abs(counts['xlstm']-counts['lstm'])/counts['xlstm']<=cfg['model']['parameter_count_relative_tolerance']
    checks['parameter_counts']=counts
    for name in cfg['backbones']:
        model=build(name,11)
        # Preflight random fixture exercises nonzero scalar recurrent weights.
        with torch.no_grad():
            for n,p in model.named_parameters():
                if '_recurrent_kernel_' in n:p.normal_(0,.05)
        checks[name]=model_audit(model)
    return checks
