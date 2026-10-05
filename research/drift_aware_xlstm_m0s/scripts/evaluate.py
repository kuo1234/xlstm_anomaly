"""Frozen observation-only inference with separate evaluator state and metadata."""
from copy import deepcopy
import numpy as np
import torch
from common import load_config,model_hash,tensor_tree_hash,array_hash
from models import carry
from metrics import duration_summary,detection_metrics


def standardize(x,scaler):
    return (np.asarray(x)-scaler['mean'])/scaler['std']


def replay_predictions(model,history,prefix_length,suffix_length,l):
    # Each prediction receives only L observations strictly before its target.
    blocks=torch.stack([history[:,prefix_length+k-l:prefix_length+k] for k in range(suffix_length)],dim=1)
    shape=blocks.shape; blocks=blocks.reshape(-1,l,shape[-1]); values=[]
    for chunk in blocks.split(256):values.append(model(chunk)[:,-1])
    return torch.cat(values).reshape(shape[0],shape[1],shape[-1])


def predict_arms(model,prefix,suffix,scaler):
    """Returns forecasts; no label, regime ID, truth boundary or threshold argument.

    The named RESET arm is a predetermined counterfactual at suffix index0.
    Its x_0 prediction was issued before the boundary; reset changes ingestion
    of x_0 and prediction of x_1 onward. It never revises an emitted forecast.
    """
    prefix=torch.from_numpy(standardize(prefix,scaler)).float()
    suffix=torch.from_numpy(standardize(suffix,scaler)).float()
    prefix_outputs,state=carry(model,prefix)
    initial=prefix_outputs[:,-1:]
    output={}
    for name in ('KEEP','ORACLE_BOUNDARY_RESET'):
        current=initial.clone(); active=deepcopy(state) if name=='KEEP' else None
        predictions=[]
        for k in range(suffix.shape[1]):
            predictions.append(current)
            current,active=model.step(suffix[:,k:k+1],active)
        output[name]=torch.cat(predictions,dim=1).cpu().numpy()
    combined=torch.cat([prefix,suffix],dim=1)
    for l in load_config()['inference']['fixed_l']:
        output['FIXED_'+str(l)]=replay_predictions(model,combined,prefix.shape[1],suffix.shape[1],l).cpu().numpy()
    assert np.array_equal(output['KEEP'][:,0],output['ORACLE_BOUNDARY_RESET'][:,0])
    return output


def losses(predictions,suffix,scaler):
    targets=standardize(suffix,scaler)
    return {name:np.mean((value-targets)**2,axis=-1) for name,value in predictions.items()}


def linear_ar_fit(data,ridge):
    features=data[:,:-1].reshape(-1,data.shape[-1]); targets=data[:,1:].reshape(-1,data.shape[-1])
    design=np.column_stack([features,np.ones(len(features))]).astype(np.float64)
    penalty=np.eye(design.shape[1])*ridge;penalty[-1,-1]=0
    return np.linalg.solve(design.T@design+penalty,design.T@targets)


def baseline_losses(prefix,suffix,scaler,ar):
    cfg=load_config(); x=standardize(np.concatenate([prefix,suffix],axis=1),scaler); p=prefix.shape[1];s=suffix.shape[1]
    last=x[:,p-1:p+s-1];l=cfg['baselines']['moving_mean_l']
    moving=np.stack([x[:,p+k-l:p+k].mean(axis=1) for k in range(s)],axis=1)
    predicted=np.concatenate([last,np.ones((*last.shape[:2],1))],axis=-1)@ar
    target=x[:,p:]
    return {n:np.mean((v-target)**2,axis=-1) for n,v in [('last_value',last),('moving_mean',moving),('b_trained_linear_ar',predicted)]}


def b_support(model,data,scaler,ar):
    pred=predict_arms(model,data['b_prefix'],data['b_suffix'],scaler)
    loss=losses(pred,data['b_suffix'],scaler);base=baseline_losses(data['b_prefix'],data['b_suffix'],scaler,ar)
    mse=float(loss['KEEP'].mean());simple=min(float(base['last_value'].mean()),float(base['moving_mean'].mean()));linear=float(base['b_trained_linear_ar'].mean())
    cfg=load_config()['gates']; a=mse/simple;b=mse/linear
    return {'forecast_mse':mse,'baseline_mse':{k:float(v.mean()) for k,v in base.items()},'vs_best_simple_ratio':a,'vs_b_ar_ratio':b,'pass':a<=cfg['support_vs_best_simple_max_ratio'] and b<=cfg['support_vs_b_ar_max_ratio']},pred,loss


def paired_mechanism(model,data,scaler,compatible_predictions,compatible_loss):
    a_pred=predict_arms(model,data['a_prefix'],data['b_suffix'],scaler);a_loss=losses(a_pred,data['b_suffix'],scaler)
    cfg=load_config();lo,hi=cfg['inference']['primary_offsets'];den=float(compatible_loss['KEEP'][:,lo:hi].mean())
    assert den>0
    harm=a_loss['KEEP']-compatible_loss['KEEP']; recovery=a_loss['KEEP']-a_loss['ORACLE_BOUNDARY_RESET']
    h=float(harm[:,lo:hi].mean()/den);r=float(recovery[:,lo:hi].mean()/den)
    stationary={}
    for regime in ('a','b'):
        physical=data['physical_'+regime];p=cfg['data']['prefix_length'];pred=predict_arms(model,physical[:,:p],physical[:,p:],scaler);err=losses(pred,physical[:,p:],scaler)
        stationary[regime.upper()]=float((err['KEEP'][:,lo:hi]-err['ORACLE_BOUNDARY_RESET'][:,lo:hi]).mean()/err['KEEP'][:,lo:hi].mean())
    a_stationary_pred=predict_arms(model,data['a_prefix'],data['a_suffix'],scaler)
    a_stationary_loss=losses(a_stationary_pred,data['a_suffix'],scaler)
    early,late=cfg['inference']['primary_offsets']; later=slice(32,None)
    long_context={str(l):float((compatible_loss['FIXED_'+str(l)][:,later]-compatible_loss['KEEP'][:,later]).mean()/compatible_loss['KEEP'][:,later].mean()) for l in cfg['inference']['fixed_l']}
    replay_reset={str(l):float((a_loss['FIXED_'+str(l)][:,lo:hi]-a_loss['ORACLE_BOUNDARY_RESET'][:,lo:hi]).mean()/den) for l in cfg['inference']['fixed_l']}
    # Identical recent L tokens MUST produce identical replay forecasts past L.
    for l in cfg['inference']['fixed_l']:
        assert np.array_equal(a_pred['FIXED_'+str(l)][:,l:],compatible_predictions['FIXED_'+str(l)][:,l:])
    bins=[]
    for low,high in cfg['inference']['reported_bins']:
        bins.append({'offsets':[low,high],'history_harm_normalized':float(harm[:,low:high].mean()/den),'reset_recovery_normalized':float(recovery[:,low:high].mean()/den)})
    result={'history_harm_normalized':h,'reset_recovery_normalized':r,'reset_recovery_fraction':r/h if h>0 else None,'normalization_mse':den,'primary_offsets':[lo,hi],
            'long_context_benefit_normalized':long_context,'replay_vs_reset_normalized':replay_reset,
            'stationary_deterioration_normalized':stationary,'stationary_a_splice_mse':float(a_stationary_loss['KEEP'].mean()),'bins':bins,
            'duration':duration_summary(harm,den),'same_suffix_hash':array_hash(data['b_suffix']),
            'suffix_trace':{'history_harm_normalized':(harm.mean(axis=0)/den).tolist(),'reset_recovery_normalized':(recovery.mean(axis=0)/den).tolist(),'compatible_loss':compatible_loss['KEEP'].mean(axis=0).tolist()},
            'arm_mse':{'incompatible_'+k:float(v.mean()) for k,v in a_loss.items()}|{'compatible_'+k:float(v.mean()) for k,v in compatible_loss.items()}}
    return result


def calibration_threshold(model,calibration,scaler):
    x=torch.from_numpy(standardize(calibration,scaler)).float(); y,_=carry(model,x)
    errors=((y[:,:-1]-x[:,1:])**2).mean(-1).numpy()
    warm=load_config()['training']['warmup_tokens'];q=load_config()['anomalies']['false_alarm_quantile']
    return float(np.quantile(errors[:,warm-1:],q,method='linear'))


def anomaly_extension(model,data,scaler,mechanism,group,threshold):
    from generator import contaminated_suffix
    rows=[]; cfg=load_config()
    for target_regime in ('A','B'):
        clean=data['a_suffix'] if target_regime=='A' else data['b_suffix']
        compatible=data['a_prefix'] if target_regime=='A' else data['b_prefix']
        incompatible=data['b_prefix'] if target_regime=='A' else data['a_prefix']
        for kind in cfg['anomalies']['types']:
            for onset in cfg['anomalies']['onsets']:
                modified,labels,events=contaminated_suffix(clean,mechanism,group,kind['name'],onset,scaler['std'])
                pred=predict_arms(model,incompatible,modified,scaler);loss=losses(pred,modified,scaler)
                compat=predict_arms(model,compatible,modified,scaler);loss['COMPATIBLE_'+target_regime+'_HISTORY']=losses(compat,modified,scaler)['KEEP']
                metrics={name:detection_metrics(labels,score,threshold,events) for name,score in loss.items()}
                keep=metrics['KEEP'];reset=metrics['ORACLE_BOUNDARY_RESET']
                rows.append({'target_regime':target_regime,'type':kind['name'],'onset':onset,'events':events,'common_contaminated_suffix_hash':array_hash(modified),'metrics':metrics,
                             'reset_minus_keep':{'point_ap':reset['point_average_precision']-keep['point_average_precision'],'event_recall':reset['event_recall']-keep['event_recall'],'missed_point_rate':reset['post_reset_missed_anomaly_point_rate']-keep['post_reset_missed_anomaly_point_rate'],'anomaly_score_ratio':reset['mean_anomaly_score']/keep['mean_anomaly_score']}})
    return rows
