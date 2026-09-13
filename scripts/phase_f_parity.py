"""Random-unlabeled checkpoint validity. No anomaly metrics or scientific features saved."""
import torch
from phase_f_common import model_hash, forbid_native_predict
from phase_e2_observer import Observer as XObserver
from phase_e2_schema import summarize as xsummarize
from phase_f_lstm_observer import Observer as LObserver, summarize as lsummarize

def compare(a,b,exact=False):
    return dict(pass_=bool(torch.equal(a,b) if exact else torch.allclose(a,b,atol=1e-5,rtol=1e-4)),
        bitwise=bool(torch.equal(a,b)),max_abs=float((a-b).abs().max()))

def parity(model, architecture):
    model.eval(); initial=model_hash(model)
    Observer=XObserver if architecture=='xlstm' else LObserver
    summarize=xsummarize if architecture=='xlstm' else lsummarize
    gen=torch.Generator(device='cuda').manual_seed(710)
    x=torch.randn(131,64,8,device='cuda',generator=gen); checks={}
    with torch.no_grad(),forbid_native_predict() as trap:
        output=model(x); scores=(output-x).square().mean((1,2))
        checks['BWD']=dict(pass_=list(output.shape)==[131,64,8])
        perm=torch.randperm(len(x),device='cuda',generator=gen)
        swapped=model(x[perm])
        checks['output_permutation']=compare(swapped,output[perm])
        checks['score_permutation']=compare((swapped-x[perm]).square().mean((1,2)),scores[perm])
        for b in (128,3,1):
            chunks=[model(part) for part in x.split(b)]; combined=torch.cat(chunks)
            checks[f'partition_B{b}_output']=compare(combined,output)
            checks[f'partition_B{b}_score']=compare((combined-x).square().mean((1,2)),scores)
        final1=torch.cat([model(x[:128]),model(x[128:129])])
        checks['B128_final1_output']=compare(final1,output[:129])
        small=x[:4]; off=model(small)
        rng=torch.cuda.get_rng_state().clone()
        with Observer(model) as obs: on=model(small); features=obs.summary()
        checks['observer_output_bitwise']=compare(on,off,True)
        checks['observer_score_bitwise']=compare((on-small).square().mean((1,2)),(off-small).square().mean((1,2)),True)
        checks['observer_rng']=dict(pass_=torch.equal(rng,torch.cuda.get_rng_state()))
        if architecture=='xlstm':
            good=all(c['hidden_close'] and c['state_close'] and c['finite'] and c['all_float32'] for c in obs.checks)
        else:
            good=all(all(v if isinstance(v,bool) else v['pass_'] for v in c['checks'].values()) for c in obs.checks)
        checks['reference']=dict(pass_=good,details=obs.checks)
        checks['finite_common18']=dict(pass_=list(features.shape)==[4,18] and bool(torch.isfinite(features).all()))
        saved=obs.latest
        model(x[4:7])
        with Observer(model) as reset: again=model(small); againfeatures=reset.summary()
        checks['reset_output']=compare(again,off,True)
        checks['reset_features']=compare(againfeatures,features,True)
        p=torch.tensor([2,0,3,1],device='cuda')
        with Observer(model) as permobs: model(small[p]); pf=permobs.summary()
        checks['feature_permutation']=compare(pf,features[p])
        single=[]
        for part in small.split(1):
            with Observer(model) as one: model(part); single.append(one.summary())
        checks['feature_partition']=compare(torch.cat(single),features)
        future=small.clone(); future[:,32:]=torch.randn(4,32,8,device='cuda',generator=gen)
        with Observer(model) as changed: future_out=model(future)
        checks['prefix_output']=compare(future_out[:,:32],off[:,:32])
        checks['prefix_states']=dict(pass_=all(torch.equal(saved[n][k][:,:32],changed.latest[n][k][:,:32]) for n in saved for k in saved[n]))
        prefixes={n:{k:v[:,:32] for k,v in layer.items()} for n,layer in saved.items()}
        with Observer(model) as shorter: short_out=model(small[:,:32]); short_summary=shorter.summary()
        checks['shorter_prefix_output']=compare(short_out,off[:,:32])
        checks['shorter_prefix_schema']=compare(short_summary,summarize(prefixes))
        checks['no_native_predict']=dict(pass_=trap.call_count==0)
        checks['no_parameter_mutation']=dict(pass_=model_hash(model)==initial)
    return dict(status='PASS' if all(c['pass_'] for c in checks.values()) else 'STOP',checks=checks,
        model_hash=initial,atol=1e-5,rtol=1e-4,random_unlabeled_only=True,scientific_features_saved=False)
