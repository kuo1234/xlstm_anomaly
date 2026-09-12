import json
import unittest
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from phase_a_v3 import select


class ManifestTests(unittest.TestCase):
    def test_no_invalid_manifest_on_global_infeasibility(self):
        manifest = json.loads(Path('reports/phase_a_v3/manifest.json').read_text())
        self.assertEqual(manifest,[])
        summary = json.loads(Path('reports/phase_a_v3/selection_summary.json').read_text())
        self.assertEqual(summary['status'],'STOP_A2')
        rows = json.loads(Path('reports/phase_a_v3/candidate_inventory.json').read_text())
        self.assertTrue(all(not r['eligible_v3'] for r in rows if r['source_family'] in ('GHL','CATSv2')))
        periodic = {r['file'] for r in rows if r['eligible_v3'] and 'periodic' in r['tags']}
        random_smd = {r['file'] for r in rows if r['eligible_v3'] and 'random_walk' in r['tags'] and r['source_family']=='SMD'}
        self.assertEqual(len(periodic),3)
        self.assertEqual(periodic,random_smd)

    def test_solver_lex_ties_and_known_duplicate(self):
        buckets = ('continuous','change_point','periodic','random_walk')
        rows = [dict(file=f'{b}{i}',source_family=f'f{j}{i}',source_group=None,
                     eligible_v3=True,tags=[b]) for j,b in enumerate(buckets) for i in range(3)]
        rows.append(dict(rows[0],file='aaa'))
        result,_ = select(rows,[])
        self.assertIn('aaa',[r['file'] for r in result])
        result,_ = select(rows,[dict(left='aaa',right='continuous0')])
        self.assertIn('aaa',[r['file'] for r in result])
        self.assertNotIn('continuous0',[r['file'] for r in result])
