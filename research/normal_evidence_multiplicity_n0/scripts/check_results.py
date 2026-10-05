"""Independent literal-replication and frozen-output validation; never fits models."""
import json,sys,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
REPO=Path(__file__).resolve().parents[3];ROOT=REPO/'research/normal_evidence_multiplicity_n0'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=json.loads((ROOT/'configs/protocol.json').read_text());rows=pd.read_csv(ROOT/'results/intervention.csv');assert len(rows)==216
 art=json.loads((REPO/'research/exathlon_lifecycle_e1/provenance/score_artifacts.json').read_text());ledger=json.loads((ROOT/'provenance/scores.json').read_text());assert len(ledger)==6
 checked=0
 for b in p['families']:
  groups=[]
  for name in p['fixed_calibration']:
   item=next(x for x in art if x['baseline']==b and x['trace']==name);assert sha(REPO/item['path'])==item['sha256'];x=pd.read_csv(REPO/item['path']).score.to_numpy();groups.append(x[np.isfinite(x)])
  for trace in p['fixed_calibration']:
   i=p['fixed_calibration'].index(trace)
   for dose in p['multiplicity']:
    # A separate literal duplicated-array order statistic verifies compressed weight implementation.
    literal=np.sort(np.concatenate([np.tile(g,dose if k==i else 1) for k,g in enumerate(groups)]))
    expected=float(literal[int(np.ceil(.995*len(literal)))-1])
    relevant=rows[(rows.baseline==b)&rows.arm.eq('row_pooled')&rows.duplicated_trace.eq(trace)&rows.dose.eq(dose)]
    np.testing.assert_allclose(relevant.threshold,expected,rtol=1e-12,atol=1e-12);checked+=1
  for item in [x for x in ledger if x['baseline']==b]:
   assert sha(REPO/item['score_path'])==item['sha256'];scores=np.load(REPO/item['score_path'])['score'];scores=scores[np.isfinite(scores)]
   for row in rows[(rows.baseline==b)&rows.test_trace.eq(item['trace'])].to_dict('records'):
    expected=float(sum(float(s)>row['threshold'] for s in scores)/len(scores));assert abs(expected-row['FPR'])<1e-12
  for arm in ['trace_balanced','identity_deduplicated_pooled']:
   assert all(g.threshold.nunique()==1 and g.FPR.nunique()==1 for _,g in rows[(rows.baseline==b)&rows.arm.eq(arm)].groupby('test_trace'))
 report={'status':'PASS','literal_replication_order_statistics':checked,'row_FPR_checks':len(rows),'frozen_score_artifacts':len(ledger),'unique_information_and_checkpoint_weights_preserved':True,'independent_check':'literal rows plus direct threshold alarm counting; not separate researcher review','novelty_verified':False,'fault_recall_checked':False}
 (ROOT/'provenance/verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
