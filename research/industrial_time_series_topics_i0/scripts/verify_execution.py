"""Verify immutable seal, execution artifact and prefix future-invariance; no fits."""
import importlib.util
import hashlib
import json
import math
import subprocess
from pathlib import Path
import numpy as np

ROOT=Path('research/industrial_time_series_topics_i0')
commit='e95ba3657e16bda8d3cc060fef714425cdb472ab'
for suffix in ['scripts/linear_feasibility.py','provenance/linear_probe_seal.json']:
    path=ROOT/suffix
    assert path.read_bytes()==subprocess.check_output(['git','show',commit+':'+str(path)])
record=json.loads((ROOT/'provenance/linear_probe_execution.json').read_text())
assert hashlib.sha256(Path(record['results_path']).read_bytes()).hexdigest()==record['results_sha256']
result=json.loads(Path(record['results_path']).read_text())
seal=json.loads((ROOT/'provenance/linear_probe_seal.json').read_text())
assert result['fit_count']==20 and result['neural_runs']==0
assert result['ordered_batch_ids']==seal['ordered_batch_ids']
assert result['split_batches']==[66,9,20]
material=result['variants']['materials_recipe']['test']['mse_original_scale']
for name,item in result['variants'].items():
    assert item['test']['n_batches']==20
    assert math.isclose(item['test']['rmse_original_scale']**2,item['test']['mse_original_scale'],rel_tol=1e-12)
    if 'relative_mse_gain_vs_materials_percent' in item:
        expected=100*(material-item['test']['mse_original_scale'])/material
        assert math.isclose(expected,item['relative_mse_gain_vs_materials_percent'],rel_tol=1e-12)
    if 'chosen_alpha' in item:
        trials=item['validation_trials']
        chosen=min(trials,key=lambda r:(r['mse'],-r['alpha']))['alpha']
        assert chosen==item['chosen_alpha']

spec=importlib.util.spec_from_file_location('probe',ROOT/'scripts/linear_feasibility.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
rows=[{'timestamp':'2020-01-01 00:00:00',**{c:'1' for c in module.CHANNELS}}, {'timestamp':'2020-01-01 00:10:00',**{c:'2' for c in module.CHANNELS}}]
future={'timestamp':'2020-01-01 02:00:00',**{c:'999999' for c in module.CHANNELS}}
for cutoff in [15,60]:
    assert np.array_equal(module.summaries(rows,cutoff),module.summaries(rows+[future],cutoff),equal_nan=True)
print(json.dumps({'seal_commit':commit,'program_and_manifest_unchanged':True,'result_hash_verified':True,'fixed_splits_counts_metric_arithmetic_and_validation_selection':'passed','prefix_future_invariance_15_60':'passed','additional_fits':0,'no_method_or_generalization_go':True},indent=2))
