"""Read-only source/data verification. No forecasting dependencies or model runs.
Run from repository root; exact assets/URLs are in provenance ledgers.
"""
import csv
import datetime
import hashlib
import io
import json
import math
import subprocess
from pathlib import Path

ROOT = Path('research/cross_channel_utility_c0')
BASELINE = '53e00cd460e9b4196fdd2a95f3cacbd224caa876'
checks = []
for name in ('sources.json', 'additional_evidence.json', 'hf_prefix_inspection.json'):
    for row in json.loads((ROOT / 'provenance' / name).read_text()):
        checksum = row.get('sha256', row.get('prefix_sha256'))
        if not checksum:
            continue
        path = row['path']
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == checksum, path
        assert subprocess.run(['git', 'check-ignore', '-q', path]).returncode == 0, path
        checks.append({'path': path, 'hash_verified': True, 'ignored': True})
for row in json.loads((ROOT / 'provenance/code_inventory.json').read_text()):
    if 'readme' in row:
        source = row['readme']
        assert hashlib.sha256(Path(source['path']).read_bytes()).hexdigest() == source['sha256']
        checks.append({'repo': row['repo'], 'commit': row['commit'], 'readme_hash_verified': True})
ledger = json.loads((ROOT / 'provenance/additional_evidence.json').read_text())
source = next(row for row in ledger if row['id'].endswith('ETTh1.csv'))
rows = list(csv.DictReader(io.StringIO(Path(source['path']).read_text())))
expected = source['inspection']
assert len(rows) == expected['rows']
assert list(rows[0])[1:] == expected['channels']
time = [datetime.datetime.fromisoformat(row['date']) for row in rows]
assert sorted(set((b-a).total_seconds() for a,b in zip(time,time[1:]))) == expected['cadence_seconds_unique']
assert sum(value == '' for row in rows for value in row.values()) == expected['empty_fields']
assert sum(not math.isfinite(float(value)) for row in rows for key,value in row.items() if key != 'date') == expected['numeric_nonfinite_fields']
for row in json.loads((ROOT / 'provenance/hf_prefix_inspection.json').read_text()):
    if row['status'] != 'prefix_inspected':
        continue
    lines = Path(row['path']).read_bytes().decode(errors='replace').splitlines()
    header = next(csv.reader([lines[0]]))
    sampled = [r for r in csv.reader(lines[1:257]) if len(r) == len(header)]
    assert header == row['columns']
    assert len(sampled) == row['rows_inspected']
    assert sum(value == '' for r in sampled for value in r) == row['empty_fields_in_inspected_rows']
paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASELINE]).decode().splitlines()
for path in paths:
    assert Path(path).read_bytes() == subprocess.check_output(['git', 'show', BASELINE + ':' + path]), path
subprocess.run(['git', 'diff', '--check'], check=True)
gate = json.loads((ROOT / 'results/gate.json').read_text())
assert gate['primary_verdict'] == 'PRIOR_ART_COLLISION'
assert gate['phase_b'] == 'NOT_RUN_GATED' and gate['model_runs'] == 0
print(json.dumps({'baseline': BASELINE, 'baseline_tracked_files_preserved': len(paths), 'source_checks': checks, 'ETTh1_schema_cadence_empty_parity': True, 'prefix_count_header_empty_parity': True, 'model_runs': 0, 'diff_check': 'passed', 'not_a_forecast_or_novelty_reproduction': True}, indent=2))
