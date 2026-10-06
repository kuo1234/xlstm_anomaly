"""Read-only replay of the three fixed 3W samples; requires duckdb==1.4.3.

Run from repository root. This does not download, impute, score, or train.
Raw assets are reacquired using the pinned URLs and hashes in 3w_sources.json.
"""
import hashlib
import json
from pathlib import Path
import duckdb

BASE = Path(__file__).resolve().parent
rows = json.loads((BASE / '3w_sources.json').read_text())
expected = json.loads((BASE / '3w_sample_inspection.json').read_text())['samples']
conn = duckdb.connect(':memory:')
results = []
for item in expected:
    source = next(r for r in rows if r['path'] == item['path'])
    path = Path(source['local_path'])
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == item['sha256'] == source['sha256']
    assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == source['git_blob_sha']
    conn.read_parquet(str(path)).create_view('sample', replace=True)
    schema = conn.execute('DESCRIBE sample').fetchall()
    assert [{'name': r[0], 'dtype': r[1]} for r in schema] == item['schema']
    count = conn.execute('SELECT count(*) FROM sample').fetchone()[0]
    assert count == item['rows']
    for name in ('class', 'state'):
        labels = [list(r) for r in conn.execute(f'SELECT "{name}", count(*) FROM sample GROUP BY 1 ORDER BY 1 NULLS LAST').fetchall()]
        assert labels == item['label_counts'][name]
    all_missing, intermittent = [], []
    for name, *_ in schema:
        if name in ('class', 'state', 'timestamp'):
            continue
        ident = '"' + name.replace('"', '""') + '"'
        missing = conn.execute(f'SELECT count(*) FILTER (WHERE {ident} IS NULL OR isnan({ident})) FROM sample').fetchone()[0]
        if missing == count:
            all_missing.append(name)
        elif missing:
            intermittent.append(name)
        for group in item['by_released_class']:
            label = group['released_class']
            condition = '"class" IS NULL' if label is None else '"class" = ' + str(int(label))
            fraction = conn.execute(f'SELECT avg(CASE WHEN {ident} IS NULL OR isnan({ident}) THEN 1.0 ELSE 0.0 END) FROM sample WHERE {condition}').fetchone()[0]
            assert fraction == group['sensor_missing_fraction'][name]
    assert all_missing == item['all_missing_channels']
    assert intermittent == item['intermittently_missing_channels']
    results.append({'path': item['path'], 'rows': count, 'all_missing_channels': len(all_missing), 'intermittently_missing_channels': len(intermittent), 'byte_schema_label_null_parity': True})
print(json.dumps({'duckdb': duckdb.__version__, 'samples': results, 'model_runs': 0}, indent=2))
