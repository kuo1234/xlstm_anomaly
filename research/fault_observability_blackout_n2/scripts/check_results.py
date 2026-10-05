"""Independent scalar endpoint enumeration, source/protocol/controls validation."""
import hashlib,json,subprocess,sys
from pathlib import Path
import numpy as np
REPO=Path(__file__).resolve().parents[3];ROOT=REPO/'research/fault_observability_blackout_n2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=json.loads((ROOT/'configs/protocol.json').read_text());sources=json.loads((ROOT/'configs/test_manifest.json').read_text());events=json.loads((ROOT/'configs/events.json').read_text());control_plan=json.loads((ROOT/'configs/controls.json').read_text());primary=json.loads((ROOT/'results/primary_events.json').read_text());controls=json.loads((ROOT/'results/controls.json').read_text());secondary=json.loads((ROOT/'results/secondary_events.json').read_text());ledger=json.loads((ROOT/'provenance/mask_artifacts.json').read_text())
 subprocess.run([sys.executable,'-m','unittest','discover','-s',str(ROOT/'tests'),'-v'],check=True)
 total=0;intervals=0
 for row in sources:
  d=np.load(REPO/row['prepared_path']);t=d['t'];x=d['x'];observed=d['observed'];assert hashlib.sha256(t.tobytes()+x.tobytes()+observed.tobytes()).hexdigest()==row['array_sha256']
  scalar_finite=np.array([all(np.isfinite(float(v)) for v in point) for point in x],dtype=bool)
  record=next(r for r in ledger if r['trace']==row['trace']);assert sha(REPO/record['path'])==record['sha256'];saved=np.load(REPO/record['path'])
  naive={}
  for w in p['availability_contracts']:
   result=np.array([bool(observed[i] and i>=w and all(bool(scalar_finite[j]) for j in range(i-w,i+1))) for i in range(len(t))])
   np.testing.assert_array_equal(result,saved[f'W{w}']);naive[w]=result;total+=len(t)
  for output in [r for r in primary+secondary+controls if r.get('trace_name',r.get('trace'))==row['trace']]:
   lo=int(output.get('root_cause_start',output.get('start')));hi=int(output.get('combined_end',output.get('end')))
   indices=[i for i in range(len(t)) if lo<=int(t[i])<=hi];assert output['expected_targets']==hi-lo+1
   for w in p['availability_contracts']:
    valid=sum(bool(naive[w][i]) for i in indices);blocked=sum(bool(naive[0][i] and not naive[w][i]) for i in indices)
    assert valid==output[f'W{w}_available'] and blocked==output[f'W{w}_additional_blocked'];assert abs(blocked/(hi-lo+1)-output[f'W{w}_additional_fraction'])<1e-12
   intervals+=1
  for c in [r for r in control_plan if r['trace']==row['trace']]:
   overlaps=[ev['event_id'] for ev in events if ev['trace_name']==row['trace'] and ev['root_cause_start']<=c['end'] and ev['combined_end']>=c['start']-32]
   extent=bool(t[0]<=c['start']-32 and t[-1]>=c['end']);assert c['overlap_event_ids']==overlaps;assert c['eligible']==bool(extent and not overlaps)
 for s in json.loads((ROOT/'provenance/raw_sources.json').read_text()):assert sha(REPO/s['local_path'])==s['sha256']
 proof=json.loads((ROOT/'provenance/execution_seal.json').read_text())
 for path,digest in proof['files'].items():assert sha(REPO/path)==digest,path
 for path,digest in json.loads((ROOT/'provenance/preflight.json').read_text())['inherited_sha256'].items():assert sha(REPO/path)==digest
 usable=[r for r in primary if r['grid_extent_complete'] and any(c['event_id']==r['event_id'] for c in controls)];material=[r for r in usable if r['W32_additional_fraction']>=.25];cm=float(np.median([c['W32_additional_fraction'] for c in controls]));gate=json.loads((ROOT/'results/gate.json').read_text())
 assert gate['primary_events']==6 and gate['usable_events']==len(usable) and gate['material_events']==len(material) and gate['material_apps']==len({r['app'] for r in material}) and gate['control_median_history_only_loss_fraction']==cm
 assert all(c['W0_fraction']>=.95 for c in controls)
 expected='FAULT_SELECTIVE_BLACKOUT_REPLICATED' if len(material)>=4 and len({r['app'] for r in material})>=3 and cm<=.01 else 'NO_REPLICATED_FAULT_SELECTIVE_AMPLIFICATION';assert gate['verdict']==expected
 report={'status':'PASS','scalar_full_trace_mask_endpoint_checks':total,'independent_interval_count_checks':intervals,'raw_trace_and_array_hashes':len(sources),'mask_artifact_hashes':len(ledger),'protocol_and_fixed_control_positions_unchanged':True,'independent_gate_recalculation':True,'contract_tests':4,'no_model_training_or_scoring':True,'independent_implementation':'scalar Python history enumeration versus prefix-sum mask implementation; same agent, no external peer review'}
 (ROOT/'provenance/verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
