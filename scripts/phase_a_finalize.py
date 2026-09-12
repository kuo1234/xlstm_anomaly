"""Materialize evidence groups and integrity seal after the eligibility audit."""
import json
import platform
from collections import Counter
import numpy as np
import pandas as pd
from phase_a_fetch import ROOT, OUT, sha256


def main():
    rows = json.loads((OUT / 'candidate_inventory.json').read_text())
    relations = json.loads((OUT / 'trace_relations.json').read_text())
    parent = {r['file']: r['file'] for r in rows}
    def root(x):
        while parent[x] != x:
            x = parent[x]
        return x
    for pair in relations:
        a, b = sorted((root(pair['left']), root(pair['right'])))
        parent[b] = a
    groups = {}
    for row in rows:
        groups.setdefault(root(row['file']), []).append(row['file'])
    output = dict(exact_feature_groups=[v for v in groups.values() if len(v)>1],
                  verified_native_sources={r['file']: r['source_group'] for r in rows if r['source_group']},
                  unresolved_by_dataset=dict(Counter(r['upstream_dataset'] for r in rows if r['provenance_status'].startswith('unresolved'))),
                  limitation='Exact equality/contiguous containment tested across all 75 candidates. Nonidentical crops, transformed traces, and common physical origins are NOT ruled out without source mappings. Unresolved rows are ineligible, not independent singleton sources.')
    (OUT / 'source_groups.json').write_text(json.dumps(output, indent=2)+'\n')
    for name in ('CATSv2_zenodo.json', 'cutoff_author_comment.json', 'TSB_source_catalog.html'):
        (OUT / name).write_bytes((ROOT / name).read_bytes())
    environment = dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
                       protocol_commit='5acc64aee055d3c223efc89510c53a92ec319bbc',
                       kind='Phase A dataset audit only; not a successful selection manifest',
                       model_result_files_inspected=False, detector_training=False, phase_b='NOT RUN: Phase A STOP')
    (OUT / 'environment.json').write_text(json.dumps(environment, indent=2)+'\n')
    paths = sorted(p for p in OUT.iterdir() if p.is_file() and p.name != 'SHA256SUMS')
    (OUT / 'SHA256SUMS').write_text(''.join(f'{sha256(p)}  {p}\n' for p in paths))
    print('Sealed audit evidence; no successful 12-series manifest fabricated.')


if __name__ == '__main__':
    main()
