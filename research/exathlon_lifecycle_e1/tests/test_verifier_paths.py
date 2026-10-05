"""Regression for Path indexing that survived the first verification repair."""
import ast,unittest
from pathlib import Path
class VerifierPaths(unittest.TestCase):
    def test_path_constants_are_not_subscripted(self):
        scripts=Path(__file__).resolve().parents[1]/'scripts';invalid=[]
        for path in scripts.glob('*.py'):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node,ast.Subscript) and isinstance(node.value,ast.Name) and node.value.id in {'REPO','ROOT','E0','CACHE'}:
                    invalid.append(f'{path.name}:{node.lineno}:{node.value.id}')
        self.assertEqual(invalid,[],'Path constants use / composition, not mapping subscripts')
if __name__=='__main__':unittest.main()
