"""Independent direct event counting; no inherited metric-helper import."""
import json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
REPO=Path(__file__).resolve().parents[3];ROOT=REPO/'research/multiplicity_fault_utility_n1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 events=json.loads((ROOT/'configs/events.json').read_text());ledger=json.loads((ROOT/'provenance/scores.json').read_text());rows=pd.read_csv(ROOT/'results/event_operating_points.csv');availability=json.loads((ROOT/'results/availability.json').read_text());normal=pd.read_csv(REPO/'research/normal_evidence_multiplicity_n0/results/intervention.csv');count=0
 assert len(rows)==288 and len(ledger)==6 and len(availability)==14
 for item in ledger:
  assert sha(REPO/item['score_path'])==item['sha256'];d=np.load(REPO/item['score_path']);t=d['t'];score=d['score'];obs=d['observed'];assert np.isnan(score[~obs]).all()
  for ev in [e for e in events if e['trace_name']==item['trace']]:
   lo=int(ev['root_cause_start']);hi=int(ev['combined_end']);ids=[i for i in range(len(t)) if lo<=int(t[i])<=hi and np.isfinite(score[i])]
   original=next(x for x in availability if x['baseline']==item['baseline'] and x['event_id']==ev['event_id']);assert len(ids)==original['count'];assert original['expected']==hi-lo+1
   assert abs(original['coverage']-len(ids)/(hi-lo+1))<1e-12
   for r in rows[(rows.baseline==item['baseline'])&rows.event_id.eq(ev['event_id'])].to_dict('records'):
    threshold=normal[(normal.baseline==r['baseline'])&normal.arm.eq(r['arm'])&normal.duplicated_trace.eq(r['duplicated_trace'])&normal.dose.eq(r['dose'])].threshold.iloc[0];assert abs(r['threshold']-threshold)<1e-12
    expected=sum(score[i]>threshold for i in ids)/len(ids) if ids else None
    if expected is not None:assert abs(expected-r['alarm_fraction'])<1e-12
    count+=1
 proof=json.loads((ROOT/'provenance/execution_seal.json').read_text())
 for path,digest in proof['files'].items():assert sha(REPO/path)==digest
 old=json.loads((ROOT/'provenance/preflight.json').read_text())
 for path,digest in old['immutable_inputs'].items():assert sha(REPO/path)==digest
 report={'status':'PASS','independent_event_operating_point_checks':count,'event_availability_checks':len(availability),'score_artifact_hashes':len(ledger),'inherited_operating_points_and_frozen_code_unchanged':True,'missing_scores_not_normal':True,'no_retraining':True,'independent_implementation':'direct per-target interval/threshold enumeration; same agent, not scientific peer review'}
 (ROOT/'provenance/verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
