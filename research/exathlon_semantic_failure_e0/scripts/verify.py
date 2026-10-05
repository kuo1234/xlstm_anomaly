"""Recompute/hash E0 evidence twice and verify contracts; never invokes detectors."""
import csv
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys
from sources import ROOT,CACHE,RESULT,REPO,fetch,sha


def fingerprint():
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*'))
            if p.is_file() and (p.suffix=='.md' or p.parent==RESULT and p.suffix in ('.csv','.json'))}


def main():
    final='--final' in sys.argv
    rows=fetch();prior=json.loads((ROOT/'provenance/prior_art_sources.json').read_text())
    prior_count=0
    for row in prior['papers']+prior['code_and_trees']:
        if not row.get('sha256') or not row.get('local_path'):continue
        assert sha(REPO/row['local_path'])==row['sha256'],row['local_path'];prior_count+=1
    commands=[['audit_data.py'],['readout_trace.py'],['reports.py']+(['--final'] if final else [])]
    command_records=[]
    for argv in commands:
        proc=subprocess.run([sys.executable,str(ROOT/'scripts'/argv[0])]+argv[1:],cwd=REPO,text=True,capture_output=True)
        command_records.append({'argv':argv,'exit_code':proc.returncode,'stdout':proc.stdout.strip(),'stderr':proc.stderr.strip()})
        assert proc.returncode==0,command_records[-1]
    first=fingerprint()
    for argv in commands:
        proc=subprocess.run([sys.executable,str(ROOT/'scripts'/argv[0])]+argv[1:],cwd=REPO,text=True,capture_output=True)
        assert proc.returncode==0,proc.stderr
    second=fingerprint();assert first==second,'nondeterministic E0 replay'
    tests=subprocess.run([sys.executable,str(ROOT/'scripts/test_metrics.py'),'-v'],cwd=REPO,text=True,capture_output=True)
    assert tests.returncode==0,tests.stderr
    with (CACHE/'ground_truth.csv').open() as handle:gt=list(csv.DictReader(handle))
    types=Counter(r['anomaly_type'] for r in gt)
    assert types=={'bursty_input':29,'bursty_input_crash':7,'stalled_input':16,'cpu_contention':26,'driver_failure':9,'executor_failure':10,'unknown':12}
    missing=sum(not r['extended_effect_end'] for r in gt)
    points=sum(float(r['root_cause_start'])==float(r['root_cause_end']) for r in gt)
    assert (len(gt),missing,points)==(109,28,19)
    status=json.loads((RESULT/'source_status.json').read_text())
    assert (status['trace_files'],status['undisturbed_runs'],status['disturbed_runs'])==(93,59,34)
    assert status['raw_inspected_traces']==7 and status['raw_inspected_events']==9
    with (RESULT/'type_app_context_coverage.csv').open() as handle:coverage=list(csv.DictReader(handle))
    assert sum(int(r['events']) for r in coverage)==len(gt)
    with (RESULT/'normal_trace_support.csv').open() as handle:normal=list(csv.DictReader(handle))
    assert sum(int(r['undisturbed_runs']) for r in normal)==59
    assert sum(int(r['disturbed_runs']) for r in normal)==34
    assert sum(int(r['disturbed_traces_with_exact_normal_context']) for r in normal)==0
    assert sum(int(r['disturbed_traces_with_unknown_context']) for r in normal)==1
    links=0
    for doc in ROOT.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
            if target.startswith(('https:','http:')):continue
            target=target.split('#')[0]
            assert (doc.parent/target).exists(),(doc,target);links+=1
    for path in list(RESULT.glob('*.json'))+list((ROOT/'provenance').glob('*.json')):
        json.loads(path.read_text(),parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v)))
    if final:
        required=['README','DATA_GROUND_TRUTH_AUDIT','TYPE_APP_CONTEXT_COVERAGE','PRIOR_ART_OVERLAP','SCORE_ARTIFACT_INVENTORY','FAILURE_METRICS','ROOT_CAUSE_EFFECT_ANALYSIS','CALIBRATION_ANALYSIS','FRAGMENTATION_ANALYSIS','FINAL_GATE']
        assert all((ROOT/(r+'.md')).exists() for r in required)
        gate=json.loads((RESULT/'final_gate.json').read_text())
        assert gate['verdict']=='DATA_OR_ARTIFACT_INSUFFICIENT' and not gate['method_design_GO']
        assert gate['detector_models_run']==gate['detector_training_runs']==0
        states=json.loads((RESULT/'failure_decomposition_status.json').read_text())
        assert len(states)==16 and all(r['metric_value'] is None and not r['trained'] for r in states)
    evidence={'date':'2026-10-06','mode':'final' if final else 'freeze','status':'PASS',
              'main_source_sha256_checks':sum(r['status'] in ['retrieved','retrieved_unversioned_wiki'] for r in rows),
              'prior_art_sha256_checks':prior_count,'deterministic_replay':True,'replay_commands':command_records,
              'test_exit_code':tests.returncode,'test_output':tests.stdout+tests.stderr,
              'independent_stdlib_type_counts':dict(types),'independent_missing_EEI':missing,'independent_point_RCI':points,
              'local_links_checked':links,'artifact_sha256':second,'detector_training_runs':0,'detector_inference_runs':0,
              'historical_scope':'no existing P4/P5/M0-S/D0 files changed; tracked scope checked separately',
              'limitations':['109 GT rows and93 archive identities; raw inspection7 traces/9 events only',
                             'No scientific detector performance or baseline parity verified',
                             'No causal training/normal-calibration execution seal',
                             'Bounded public output/literature search; unavailable external/private artifacts remain unknown']}
    (ROOT/'provenance'/('verification.json' if final else 'freeze_verification.json')).write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps({k:evidence[k] for k in ['status','mode','main_source_sha256_checks','prior_art_sha256_checks','deterministic_replay','independent_stdlib_type_counts','local_links_checked','detector_training_runs','detector_inference_runs']},indent=2))


if __name__=='__main__':main()
