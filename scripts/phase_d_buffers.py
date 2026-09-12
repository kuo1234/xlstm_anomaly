"""Score-free paired buffer composition; truth never enters the update operator."""
from collections import Counter
import hashlib
import json
import numpy as np
from phase_d_backbone import windows
from phase_d_operator import ROOT,REPORT,DATA,tensor_hash
from m0.synthetic import generate

SCENARIOS=['abrupt','gradual','recurring','correlation']
TYPES=['spike','collective','dependency','mixture']
CS=[0,5,10,20,30]
S=5120+4096
U=S+3000


def layout():
    starts=[S+32+300*j for j in range(9)]
    priority=[starts[j]+offset for offset in range(4) for j in range(9)][:30]
    eligible=[t for t in range(S+9,U) if not any(t>=left and t-9<left+256 for left in starts)]
    extra=[eligible[i] for i in np.floor(np.linspace(0,len(eligible)-1,70)).astype(int)]
    endpoints=sorted(priority+extra)
    assert len(endpoints)==len(set(endpoints))==100
    slots=[endpoints.index(t) for t in priority]
    return starts,endpoints,slots


def compose(source,scenario,condition):
    assert source in range(3000,3010) and scenario in SCENARIOS and condition in TYPES
    clean=generate(source,scenario,'none')
    starts,endpoints,priority=layout()
    corrupted=clean.observations.copy(); labels=np.zeros(len(corrupted),dtype=np.int8)
    events=[]
    for j,left in enumerate(starts):
        kind=TYPES[j%3] if condition=='mixture' else condition
        severity=1+j//3; duration=1 if kind=='spike' else [16,64,256][(j+j//3)%3]
        right=left+duration; channel=j%8
        if kind=='dependency':
            noise=np.random.default_rng(np.random.SeedSequence([source,j,812,4])).standard_normal(duration)
            corrupted[left:right,channel]+=severity*(noise-clean.observations[left:right,channel])/np.sqrt(2)
        else: corrupted[left:right,channel]+=severity
        labels[left:right]=1
        events.append(dict(id=j,type=kind,start=left,end=right,severity=severity,duration=duration,channel=channel))
    normal=np.stack([clean.observations[t-9:t+1] for t in endpoints])
    altered=np.stack([corrupted[t-9:t+1] for t in endpoints])
    y=np.array([labels[t-9:t+1].any() for t in endpoints])
    assert set(np.flatnonzero(y))==set(priority)
    arms={}; meta={}
    for c in CS:
        x=normal.copy(); selected=priority[:c]; x[selected]=altered[selected]
        assert np.sum(np.any(x!=normal,axis=(1,2)))==c
        unselected=sorted(set(range(100))-set(selected))
        assert np.array_equal(x[unselected],normal[unselected])
        arm_events=[next(e for e in events if endpoints[i]>=e['start'] and endpoints[i]-9<e['end']) for i in selected]
        counts=Counter(e['type'] for e in arm_events)
        if condition=='mixture': assert max([counts[k] for k in TYPES[:3]])-min([counts[k] for k in TYPES[:3]])<=1
        arms[c]=x
        meta[str(c)]=dict(selected_slots=selected,anomaly_window_count=c,buffer_sha256=tensor_hash(x),
            type_counts=dict(counts),unique_events=len({e['id'] for e in arm_events}),
            event_ids=[e['id'] for e in arm_events],severity=[e['severity'] for e in arm_events],duration=[e['duration'] for e in arm_events])
    eval_stream=generate(source,scenario,condition)
    eval_start=U+10
    eval_x=windows(eval_stream.observations[eval_start:])
    eval_y=np.lib.stride_tricks.sliding_window_view(eval_stream.labels[eval_start:],10).any(axis=1).astype(np.int8)
    times=np.arange(eval_start+9,len(eval_stream.labels))
    primary=np.ones(len(times),dtype=bool)
    for e in eval_stream.events:
        if e['stress_only']: primary &= ~((times>=e['start']) & (times-9<e['end']))
    assert eval_y[primary].any() and (~eval_y[primary].astype(bool)).any()
    assert max(endpoints)<U<eval_start
    manifest=dict(source=source,scenario=scenario,condition=condition,window=10,dimension=8,
        cutoff=U,evaluation_raw_start=eval_start,ordered_endpoints=endpoints,replacement_priority_slots=priority,
        events=events,arms=meta,clean_source_sha256=tensor_hash(clean.observations),
        evaluation_observations_sha256=tensor_hash(eval_x),evaluation_labels_sha256=tensor_hash(eval_y),
        primary_mask_sha256=tensor_hash(primary),eval_count=int(primary.sum()),anomalies=int(eval_y[primary].sum()))
    return arms,eval_x,eval_y,primary,manifest


def main():
    import time
    start=time.perf_counter()
    manifests=[]
    for source in range(3000,3010):
        for scenario in SCENARIOS:
            for condition in TYPES:
                *_,m=compose(source,scenario,condition); manifests.append(m)
    (REPORT/'buffer_manifest.json').write_text(json.dumps(dict(selection='prospective.md deterministic layout',rows=manifests,
        outcomes_inspected=False,composition_seconds=time.perf_counter()-start),indent=2)+'\n')
    print('Sealed',len(manifests),'paired buffer layouts; no model outcomes')


if __name__=='__main__': main()
