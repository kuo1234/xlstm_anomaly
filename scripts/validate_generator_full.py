"""Full CPU-only validation: 125 seed/scenario cases, every registered condition.

No detectors, scoring, fitting, probes, or GPU libraries. Every failure is retained.
Temporary serialized samples are discarded after round-trip checks; canonical
array hashes and saved-file hashes are retained for every semantic variant.
"""
import hashlib
import json
import platform
import sys
import tempfile
import time
from pathlib import Path
import numpy as np
import scipy

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from m0.synthetic import CONFIG, generate, save_stream
from m0.correlation import verify

OUT = Path('reports/generator_validation_v4')
FIELDS = ('observations','labels','regime','drift_active','event_ids')


def bytehash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def arrayhash(array):
    a = np.ascontiguousarray(array)
    header = json.dumps(dict(shape=a.shape,dtype=a.dtype.str),sort_keys=True).encode()
    return hashlib.sha256(header+b'\n'+a.tobytes()).hexdigest()


def check_stream(stream,fold,condition,semantic):
    n = CONFIG['fit']+CONFIG['calibration']+CONFIG['test']
    start = CONFIG['fit']+CONFIG['calibration']
    assert stream.fold==fold and stream.test_start==start
    assert stream.observations.shape==(n,8)
    assert all(np.isfinite(getattr(stream,f)).all() for f in FIELDS)
    assert np.isin(stream.labels,[0,1]).all()
    assert not stream.labels[:start].any() and not stream.drift_active[:start].any()
    assert np.all(stream.event_ids[:start]==-1)
    coverage = np.zeros(n,dtype=np.int8)
    reconstructed_ids = np.full(n,-1,dtype=np.int32)
    expected_labels = np.zeros(n,dtype=np.int8)
    for event in stream.events:
        left,right = event['start'],event['end']
        assert start<=left<right<=n and right-left==event['duration']
        assert 0<=event['channel']<8 and event['semantic']==semantic
        coverage[left:right] += 1
        reconstructed_ids[left:right] = event['id']
        expected_labels[left:right] = int(semantic=='anomaly')
        if event['stress_only']:
            assert event['type']=='persistent_fault' and event['id']==27
            assert left==start+CONFIG['persistent_fault_onset']
            assert event['duration']==1024 and event['severity']==2
        else:
            i = event['id']
            kind = ('spike','collective','dependency')[i%3]
            assert event['type']==kind and event['channel']==i%8
            assert left==start+512+512*i
            assert event['severity']==1+(i//3)%3
            assert event['duration']==(1 if kind=='spike' else (16,64,256)[i//9])
    assert coverage.max()<=1, 'Event-event overlap'
    np.testing.assert_array_equal(stream.event_ids,reconstructed_ids)
    np.testing.assert_array_equal(stream.labels,expected_labels)
    kinds = ('spike','collective','dependency') if condition=='mixture' else (() if condition=='none' else (condition,))
    for kind in kinds:
        events = [e for e in stream.events if e['type']==kind]
        assert len(events)==9
        pairs = {(e['severity'],e['duration']) for e in events}
        assert pairs=={(s,d) for s in (1,2,3) for d in ((1,) if kind=='spike' else (16,64,256))}
    assert len(stream.events)==(0 if condition=='none' else 28 if condition=='mixture' else 10)
    return dict(finite=True,clean_prefix=True,event_bounds=True,no_event_overlap=True,
                exact_schedule=True,severity_duration_coverage=True,source_fold=True,
                event_count=len(stream.events))


def serialized_check(stream):
    with tempfile.TemporaryDirectory(prefix='m0_generator_validation_') as temporary:
        target = Path(temporary)/'sample'
        save_stream(stream,target)
        assert {p.name for p in target.iterdir()}=={'observations.npy','evaluator_truth.npz','evaluator_metadata.json'}
        observations = np.load(target/'observations.npy',allow_pickle=False)
        assert observations.dtype.fields is None and observations.shape[1]==8
        np.testing.assert_array_equal(observations,stream.observations)
        with np.load(target/'evaluator_truth.npz',allow_pickle=False) as truth:
            assert set(truth.files)=={'labels','regime','drift_active','event_ids','overlap'}
            for name in FIELDS[1:]:
                np.testing.assert_array_equal(truth[name],getattr(stream,name))
            np.testing.assert_array_equal(truth['overlap'],stream.drift_active & stream.labels.astype(bool))
        metadata = json.loads((target/'evaluator_metadata.json').read_text())
        assert metadata['events']==list(stream.events) and metadata['source_seed']==stream.source_seed
        assert metadata['scenario']==stream.scenario and metadata['condition']==stream.condition
        assert metadata['semantic']==stream.semantic and metadata['fold']==stream.fold
        return {p.name:bytehash(p) for p in sorted(target.iterdir())}


def main():
    started = time.monotonic()
    expected = dict(train=list(range(1000,1010)),validation=list(range(2000,2005)),test=list(range(3000,3010)))
    for fold,seeds in expected.items():
        assert CONFIG[fold+'_seeds']==seeds
    assert len(set(sum(expected.values(),[])))==25
    assert CONFIG['scenarios']==['stationary','abrupt','gradual','recurring','correlation']
    records = []
    for fold,seeds in expected.items():
        for seed in seeds:
            for scenario in CONFIG['scenarios']:
                record = dict(seed=seed,fold=fold,scenario=scenario,conditions=[],passed=False)
                try:
                    record['correlation_invariants'] = verify(seed)
                    for condition in CONFIG['conditions']:
                        a = generate(seed,scenario,condition,'anomaly')
                        repeat = generate(seed,scenario,condition,'anomaly')
                        opposite = generate(seed,scenario,condition,'legitimate')
                        checks = check_stream(a,fold,condition,'anomaly')
                        check_stream(opposite,fold,condition,'legitimate')
                        for field in FIELDS:
                            np.testing.assert_array_equal(getattr(a,field),getattr(repeat,field))
                        assert a.events==repeat.events
                        np.testing.assert_array_equal(a.observations,opposite.observations)
                        np.testing.assert_array_equal(a.event_ids,opposite.event_ids)
                        if condition!='none':
                            assert np.all(a.labels[a.event_ids>=0]==1)
                            assert np.all(opposite.labels[a.event_ids>=0]==0)
                        variants = {}
                        for name,stream in (('anomaly',a),('legitimate',opposite)):
                            variants[name] = dict(array_sha256={f:arrayhash(getattr(stream,f)) for f in FIELDS},
                                metadata_sha256=hashlib.sha256(json.dumps(stream.events,sort_keys=True).encode()).hexdigest(),
                                saved_file_sha256=serialized_check(stream))
                        record['conditions'].append(dict(condition=condition,**checks,deterministic_regeneration=True,
                            observation_truth_separation=True,opposite_semantic_observational_identity=True,
                            opposite_labels_on_events=condition!='none',hashes=variants))
                    record['passed'] = True
                except Exception as error:
                    record['error'] = f'{type(error).__name__}: {error}'
                records.append(record)
                print(f'{len(records)}/125 {fold} {seed} {scenario} {"PASS" if record["passed"] else "FAIL"}',flush=True)
    assert len(records)==125
    summary = dict(base_cases=125,passed=sum(r['passed'] for r in records),
        failed=sum(not r['passed'] for r in records),
        fold_cases={f:sum(r['fold']==f for r in records) for f in expected},
        condition_checks=sum(len(r['conditions']) for r in records),
        source_fold_separation=True,elapsed_seconds=time.monotonic()-started,
        python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
        scope='CPU validation only; no model results, scoring, fitting, or GPU training',
        array_hash_encoding='SHA256(sorted-key JSON shape/dtype + newline + C-order array bytes)',
        artifact_policy='Temporary serialized arrays removed after validation; all hashes retained; regenerate from sealed code/config',
        code_config_sha256={p:bytehash(p) for p in ('m0/synthetic.py','m0/correlation.py','configs/synthetic_v1.json','scripts/validate_generator_full.py')})
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'cases.json').write_text(json.dumps(records,indent=2)+'\n')
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (OUT/'SHA256SUMS').write_text(''.join(f'{bytehash(p)}  {p}\n' for p in sorted(OUT.glob('*.json'))))
    print(json.dumps(summary),flush=True)
    if summary['failed']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
