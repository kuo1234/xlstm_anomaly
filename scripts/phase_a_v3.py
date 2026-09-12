"""Frozen A2 assignment: exact integer objectives, then feasibility-based lex ties."""
import hashlib
import json
import math
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from phase_a_fetch import ROOT, sha256
from phase_a_audit import BUCKETS

OLD = Path('reports/phase_a')
OUT = Path('reports/phase_a_v3')


def select(rows, relations):
    rows = sorted([r for r in rows if r['eligible_v3']], key=lambda r: r['file'])
    parent = {r['file']: r['file'] for r in rows}
    def root(x):
        while parent[x] != x:
            x = parent[x]
        return x
    for pair in relations:
        if pair['left'] in parent and pair['right'] in parent:
            parent[root(pair['right'])] = root(pair['left'])
    # Also merge documented native identity when present.
    native = {}
    for r in rows:
        if r.get('source_group'):
            group = r['source_group']
            if group in native:
                parent[root(r['file'])] = root(native[group])
            native[group] = r['file']
    families = sorted({r['source_family'] for r in rows})
    keys = [('x', b, r['file']) for b in BUCKETS for r in rows if b in r['tags']]
    keys += [('y', b, f) for b in BUCKETS for f in families]
    keys += [('z', f, k) for f in families for k in range(1, 13)]
    index = {key: i for i, key in enumerate(keys)}
    n = len(keys)
    constraints = []
    def vector(entries):
        v = np.zeros(n)
        for key, value in entries:
            v[index[key]] += value
        return v
    def add(entries, lo, hi):
        constraints.append((vector(entries), lo, hi))
    for group in sorted({root(r['file']) for r in rows}):
        add([(key, 1) for key in keys if key[0]=='x' and root(key[2])==group], 0, 1)
    for b in BUCKETS:
        pool = [r for r in rows if b in r['tags']]
        fcount = len({r['source_family'] for r in pool})
        if not fcount:
            raise RuntimeError(f'No eligible family in {b}')
        diversity = min(3, fcount)
        cap = math.ceil(3/diversity)
        add([(('x', b, r['file']), 1) for r in pool], 3, 3)
        add([(('y', b, f), 1) for f in families], diversity, diversity)
        for f in families:
            members = [(('x', b, r['file']), 1) for r in pool if r['source_family']==f]
            add(members+[(('y', b, f), -cap)], -np.inf, 0)
            add(members+[(('y', b, f), -1)], 0, np.inf)
    for f in families:
        members = [(('x', b, r['file']), 1) for b in BUCKETS for r in rows
                   if b in r['tags'] and r['source_family']==f]
        add(members+[(('z', f, k), -1) for k in range(1, 13)], 0, 0)
        for k in range(1, 12):
            add([(('z', f, k), 1), (('z', f, k+1), -1)], 0, np.inf)
    def solve(objective):
        matrix = np.array([c[0] for c in constraints])
        result = milp(objective, integrality=np.ones(n), bounds=Bounds(0, 1),
                      constraints=LinearConstraint(matrix, [c[1] for c in constraints], [c[2] for c in constraints]),
                      options={'mip_rel_gap': 0.0})
        if result.status == 2:
            return None
        if not result.success:
            raise RuntimeError(result.message)
        x = np.rint(result.x)
        if np.max(np.abs(result.x-x)) > 1e-6:
            raise RuntimeError('Nonintegral solver result')
        values = matrix @ x
        if any(v < lo-1e-7 or v > hi+1e-7 for v, (_,lo,hi) in zip(values, constraints)):
            raise RuntimeError('Integer constraint verification failed')
        return x
    diversity = vector([(('z', f, 1), 1) for f in families])
    x = solve(-diversity)
    if x is None:
        raise RuntimeError('STOP: no globally feasible assignment')
    optimum = int(diversity @ x)
    constraints.append((diversity, optimum, optimum))
    squares = vector([(('z', f, k), 2*k-1) for f in families for k in range(1,13)])
    x = solve(squares)
    square_optimum = int(squares @ x)
    constraints.append((squares, square_optimum, square_optimum))
    for key in [k for k in keys if k[0]=='x']:
        v = vector([(key, 1)])
        constraints.append((v, 1, 1))
        trial = solve(np.zeros(n))
        if trial is None:
            constraints[-1] = (v, 0, 0)
        else:
            x = trial
    x = solve(np.zeros(n))
    selected = [dict(r, selection_bucket=b) for b in BUCKETS for r in rows
                if ('x', b, r['file']) in index and x[index['x', b, r['file']]]]
    counts = Counter(r['source_family'] for r in selected)
    assert len(selected)==12 and len({r['file'] for r in selected})==12
    assert len({root(r['file']) for r in selected})==12
    assert len(counts)==optimum and sum(v*v for v in counts.values())==square_optimum
    for b in BUCKETS:
        count = Counter(r['source_family'] for r in selected if r['selection_bucket']==b)
        available = {r['source_family'] for r in rows if b in r['tags']}
        assert sum(count.values())==3 and len(count)==min(3,len(available))
        assert max(count.values())<=math.ceil(3/min(3,len(available)))
    return selected, dict(distinct_families=optimum, sum_squared_family_counts=square_optimum,
                          family_counts=dict(counts), repeated_families={k:v for k,v in counts.items() if v>1})


def main():
    # Check immutable A1 and strict evidence before interpreting anything.
    for line in (OLD/'SHA256SUMS').read_text().splitlines():
        expected, name = line.split('  ', 1)
        assert sha256(Path(name))==expected, name
    for machine in json.loads((OLD/'smd_seal.json').read_text()):
        for asset in machine['assets']:
            assert sha256(Path(asset['path']))==asset['sha256'], asset['path']
    rows = json.loads((OLD/'candidate_inventory.json').read_text())
    with zipfile.ZipFile(ROOT/'TSB-AD-M.zip') as archive:
        for row in rows:
            assert hashlib.sha256(archive.read(row['archive_member'])).hexdigest()==row['raw_sha256']
            row['source_family'] = row['upstream_dataset']
            row['native_provenance_unresolved'] = row['provenance_status'].startswith('unresolved')
            row['exclusions_v3'] = [e for e in row['exclusions'] if e!='unresolved_original_trace_mapping']
            # Newly verified source fact; same frozen no-synthetic criterion.
            if row['source_family']=='GHL':
                row['exclusions_v3'].append('synthetic_source_excluded_by_protocol')
                row['synthetic_provenance'] = 'https://arxiv.org/abs/1612.06676'
            row['eligible_v3'] = not row['exclusions_v3']
    try:
        selected, objectives = select(rows, json.loads((OLD/'trace_relations.json').read_text()))
        status = 'PASS_A2'
    except RuntimeError as error:
        if str(error)!='STOP: no globally feasible assignment':
            raise
        selected, objectives = [], dict(blocker=str(error))
        status = 'STOP_A2'
    OUT.mkdir(parents=True, exist_ok=True)
    for name, obj in [('candidate_inventory.json', rows), ('manifest.json', selected),
                      ('selection_summary.json', dict(status=status, A1='seal_verified', **objectives,
                          eligible=sum(r['eligible_v3'] for r in rows),
                          native_provenance_unresolved=sum(r['native_provenance_unresolved'] for r in selected),
                          rule='reports/m0_amendment_v3.md', inference_unit='source_family_first'))]:
        (OUT/name).write_text(json.dumps(obj, indent=2)+'\n')
    (OUT/'SHA256SUMS').write_text(''.join(f'{sha256(p)}  {p}\n' for p in sorted(OUT.glob('*.json'))))
    print(json.dumps(objectives))
    for r in selected:
        print(r['selection_bucket'], r['file'], r['source_family'], r['native_provenance_unresolved'])


if __name__=='__main__':
    main()
