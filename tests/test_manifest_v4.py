import itertools
import json
import unittest
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from phase_a_v3 import select

BUCKETS = ('continuous','change_point','periodic','random_walk')


class ManifestV4Tests(unittest.TestCase):
    def test_matches_exhaustive_lexicographic_objectives(self):
        rows = []
        for b,families in zip(BUCKETS,('ABCD','ADEE','FFFF','BEGG')):
            for i,f in enumerate(families):
                rows.append(dict(file=f'{b}_{i}',source_family=f,source_group=None,
                                 eligible_v3=True,tags=[b]))
        pools = [[r for r in rows if b in r['tags']] for b in BUCKETS]
        def objective(triples):
            flat = sum((list(t) for t in triples),[])
            counts = Counter(r['source_family'] for r in flat)
            return (-len(counts),-sum(len({r['source_family'] for r in t}) for t in triples),
                    sum(n*n for n in counts.values()),tuple(r['file'] for r in flat))
        all_choices = itertools.product(*(itertools.combinations(pool,3) for pool in pools))
        expected = min(objective(triples) for triples in all_choices)
        selected,summary = select(rows,[],objective_version=4)
        actual = (-summary['distinct_families'],-summary['within_bucket_unique_family_sum'],
                  summary['sum_squared_family_counts'],tuple(r['file'] for r in selected))
        self.assertEqual(actual,expected)
        reversed_selection,_ = select(list(reversed(rows)),[],objective_version=4)
        self.assertEqual(selected,reversed_selection)

    def test_sealed_real_manifest_and_explicit_denominators(self):
        root = Path('reports/phase_a_v4')
        rows = json.loads((root/'manifest.json').read_text())
        inventory = json.loads((root/'candidate_inventory.json').read_text())
        summary = json.loads((root/'selection_summary.json').read_text())
        self.assertEqual(summary['status'],'PASS_A2')
        self.assertEqual(summary['selected_count'],12)
        self.assertEqual(len({r['file'] for r in rows}),12)
        self.assertEqual(summary['inventory_native_provenance_unresolved'],sum(r['native_provenance_unresolved'] for r in inventory))
        self.assertEqual(summary['selected_native_provenance_unresolved'],sum(r['native_provenance_unresolved'] for r in rows))
        self.assertTrue(all(r['numeric_pass'] and r['source_family'] not in ('GHL','CATSv2') for r in rows))
        self.assertEqual(Counter(r['selection_bucket'] for r in rows),dict.fromkeys(BUCKETS,3))
        periodic = [r for r in rows if r['selection_bucket']=='periodic']
        self.assertEqual({r['source_family'] for r in periodic},{'SMD'})

    def test_known_group_exclusion_and_mathematical_stop(self):
        rows = [dict(file=f'{b}_{i}',source_family=f'{b}{i}',source_group=None,
                     eligible_v3=True,tags=[b]) for b in BUCKETS for i in range(3)]
        with self.assertRaisesRegex(RuntimeError,'no globally feasible assignment'):
            select(rows,[dict(left=rows[0]['file'],right=rows[1]['file'])],objective_version=4)
