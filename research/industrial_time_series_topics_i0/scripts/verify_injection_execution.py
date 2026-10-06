"""Artifact/split/metric verification without fitting another model."""
import csv,hashlib,io,json,math,subprocess,zipfile
from pathlib import Path
import numpy as np
ROOT=Path('research/industrial_time_series_topics_i0');CACHE=Path('data/industrial_time_series_topics_i0')
seal_commit='7000cc9eb24bc4e6e7daa88200a641137bebb2e0'
for name in ['scripts/injection_probe.py','provenance/injection_probe_seal.json']:
 p=ROOT/name;assert p.read_bytes()==subprocess.check_output(['git','show',seal_commit+':'+str(p)])
s=json.loads((ROOT/'provenance/injection_probe_seal.json').read_text());r=json.loads((ROOT/'results/injection_probe.json').read_text())
assert r['fit_count']==4 and r['neural_runs']==0
with zipfile.ZipFile(CACHE/'injection_dataset1.zip') as z:
 rows=list(csv.DictReader(io.StringIO(z.read('dataset1/ds1_scalar_and_quality.csv').decode())));labels={x['cycle_counter']:float(x['weight'].replace(',','.')) for x in rows}
for a in r['arms']:
 assert a['train_n']==700 and a['calibration_n']==233 and a['test_n']==234 and a['quantile_order']==211
 ids=a['test_cycle_ids'];assert len(ids)==len(set(ids))==234
 y=np.array([labels[x] for x in ids]);v=float(np.mean((y-y.mean())**2));assert math.isclose(1-a['mse']/v,a['r2'],rel_tol=1e-11)
 assert math.isclose(a['rmse']**2,a['mse'],rel_tol=1e-11)
 assert math.isclose(a['width'],2*a['half_width'],rel_tol=1e-11)
 assert abs(a['coverage90']*234-round(a['coverage90']*234))<1e-9
 if a['protocol']=='future_cycles':assert ids==s['labelled_cycle_ids'][933:]
print(json.dumps({'seal_commit':seal_commit,'immutable_program_and_seal':True,'four_fits_no_neural':True,'split_ids_metric_arithmetic_label_variance_coverage_denominator':'passed','additional_fits':0,'not_a_method_or_deployment_certificate':True},indent=2))
