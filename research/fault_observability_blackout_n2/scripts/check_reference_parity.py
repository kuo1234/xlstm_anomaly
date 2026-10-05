"""Replay actual frozen reference input eligibility, without detector forward calls."""
import ast,hashlib,json
from pathlib import Path
import numpy as np
REPO=Path(__file__).resolve().parents[3];ROOT=REPO/'research/fault_observability_blackout_n2'
def main():
 original=REPO/'research/exathlon_lifecycle_e1/scripts/models.py'
 node=next(n for n in ast.parse(original.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='target_ids')
 space={'np':np};exec(compile(ast.Module(body=[node],type_ignores=[]),str(original),'exec'),space)
 training=json.loads((REPO/'research/exathlon_lifecycle_e1/results/training.json').read_text());scalerpath=REPO/'data/exathlon_lifecycle_e1/scaler.npz'
 assert hashlib.sha256(scalerpath.read_bytes()).hexdigest()==training['scaler_hash'];scaler=np.load(scalerpath)
 manifest=json.loads((ROOT/'configs/test_manifest.json').read_text());ledger=json.loads((ROOT/'provenance/mask_artifacts.json').read_text())
 for row in manifest:
  arr=np.load(REPO/row['prepared_path']);x=arr['x'];obs=arr['observed'];z=((x-scaler['mean'])/scaler['std']).astype(np.float32)
  assert np.array_equal(np.isfinite(z),np.isfinite(x))
  mask=np.load(REPO/next(v['path'] for v in ledger if v['trace']==row['trace']));ids=space['target_ids'](z,obs,32);expected=np.zeros(len(x),bool);expected[ids]=True
  np.testing.assert_array_equal(expected,mask['W32']);np.testing.assert_array_equal(obs&np.isfinite(z).all(axis=1),mask['W0'])
 report={'status':'PASS','traces':len(manifest),'actual_original_LSTM_target_ids_source_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'fixed_fit_only_scaler_sha256':training['scaler_hash'],'post_scaling_finiteness_equals_feature_finiteness':True,'W32_masks_exact_original_LSTM_target_ids':True,'W0_masks_exact_original_PCA_target_eligibility':True,'actual_detector_forward_calls':0,'not_detector_performance':True}
 (ROOT/'provenance/reference_eligibility_parity.json').write_text(json.dumps(report,indent=2)+'\n');print('reference eligibility parity PASS')
if __name__=='__main__':main()
