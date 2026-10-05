import csv,gzip,hashlib,json,math,statistics
from pathlib import Path
r=Path('research/exathlon_lifecycle_e1');repo=Path.cwd()
manifest=json.loads((r/'configs/event_manifest.json').read_text());art=json.loads((r/'provenance/score_artifacts.json').read_text());reported=json.loads((r/'results/event_metrics.json').read_text());thresholds=json.loads((r/'results/thresholds.json').read_text())
checks=0;maxerr=0
for a in art:
    events=[x for x in manifest if x['stratum']=='primary' and x['trace_name']==a['trace']]
    if not events:continue
    values=[]
    with gzip.open(repo/a['path'],'rt') as h:
        for row in csv.DictReader(h):
            if row['score']:
                score=float(row['score']);t=int(row['target_timestamp']);avail=int(row['available_at'])
                assert math.isfinite(score) and avail<=t and row['target_observed']=='True'
                values.append((t,score))
    scale=next(x['IQR'] for x in thresholds if x['baseline']==a['baseline'] and x['app'] is None)
    for e in events:
        others=[(int(x['root_cause_start']),int(x['combined_end'])) for x in manifest if x['trace_name']==e['trace_name'] and x['event_id']!=e['event_id']]
        valid=[(t,s) for t,s in values if not any(lo<=t<=hi for lo,hi in others)]
        rc=[s for t,s in valid if e['root_cause_start']<=t<=e['root_cause_end']]
        ee=[s for t,s in valid if e['root_cause_end']<t<=e['extended_effect_end']]
        pre=[s for t,s in valid if e['root_cause_start']-300<=t<e['root_cause_start']]
        delta=(statistics.median(ee)-statistics.median(rc))/scale
        out=next(x for x in reported if x['baseline']==a['baseline'] and x['event_id']==e['event_id'])
        assert len(rc)==out['rci_count'] and len(ee)==out['eei_count'] and len(pre)==out['pre_count']
        err=abs(delta-out['Delta_effect']);assert math.isclose(delta,out['Delta_effect'],abs_tol=1e-9,rel_tol=1e-9)
        maxerr=max(maxerr,err);checks+=1
for a in art:assert hashlib.sha256((repo/a['path']).read_bytes()).hexdigest()==a['sha256']
unchanged={}
for name in ['amendment01.json','amendment02.json']:
    record=json.loads((r/'provenance'/name).read_text());pairs=record.get('unchanged_output_sha256_before_amendment',record.get('unchanged_scientific_output_sha256_before_amendment'))
    for path,digest in pairs.items():assert hashlib.sha256((r/path).read_bytes()).hexdigest()==digest,path
    unchanged[name]=len(pairs)
proof=json.loads((r/'provenance/execution_authorization.json').read_text())
critical={path:digest for path,digest in proof['sealed_files'].items() if '/configs/' in path or path.endswith(tuple('/scripts/'+x for x in ['prepare.py','models.py','run.py','metrics.py','analyze.py']))}
for path,digest in critical.items():assert hashlib.sha256((repo/path).read_bytes()).hexdigest()==digest,path
result={'status':'PASS','independent_implementation':'stdlib gzip/csv/math/statistics; no imported model/metric helpers','primary_event_family_phase_checks':checks,'max_absolute_Delta_difference_vs_saved_JSON':maxerr,'score_archive_hashes':len(art),'scientific_output_hashes_unchanged_through_amendments':unchanged,'original_seal_critical_config_training_scoring_metric_scripts_unchanged':len(critical),'training_repeats':0,'limitations':'Scientific verification, not independent research review; no native reproduction/extra detector seeds.'}
(r/'provenance/independent_checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
