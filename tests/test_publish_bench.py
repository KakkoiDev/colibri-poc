import json, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import publish_bench as pb

ROWS = [
    {'name': 'gemma4-26b-ollama', 'engine': 'Ollama', 'model': 'gemma4:26b'},
    {'name': 'glm-5.3-iq2m', 'engine': 'Colibri', 'model': 'glm-5.3-iq2m'},
    {'name': 'qwen38-27b-ollama', 'engine': 'Ollama', 'model': 'qwen3.8:27b-mlx'},
    {'name': 'v1', 'engine': 'Colibri', 'model': 'GLM-5.3 int4'},
    {'name': 'olmoe-mlx', 'engine': 'MLX server', 'model': 'models/olmoe-1b-7b-4bit'},
    {'name': 'glm-5.3-mtp', 'engine': 'Colibri', 'model': 'glm-5.3-mtp'},
    {'name': 'mystery-ollama', 'engine': 'Ollama', 'model': 'mystery:7b'},
]


class ManifestTests(unittest.TestCase):
    def test_titles_and_groups(self):
        got = {r['name']: (r['title'], r['group']) for r in pb.with_titles(ROWS)}
        self.assertEqual(got['v1'], ('GLM-5.3 int4', 'GLM-5.3 on Colibri'))
        self.assertEqual(got['glm-5.3-mtp'], ('GLM-5.3 int4 + int8 MTP head', 'GLM-5.3 on Colibri'))
        self.assertEqual(got['glm-5.3-iq2m'], ('GLM-5.3 UD-IQ2_M', 'GLM-5.3 on Colibri'))
        self.assertEqual(got['qwen38-27b-ollama'], ('Qwen3.8-27B', 'Ollama, fully in RAM'))
        self.assertEqual(got['gemma4-26b-ollama'], ('Gemma 4 26B', 'Ollama, fully in RAM'))
        self.assertEqual(got['olmoe-mlx'], ('OLMoE 1B-7B (4-bit)', 'MLX, fully in RAM'))
        self.assertEqual(got['mystery-ollama'], ('mystery:7b', 'Ollama, fully in RAM'), 'unknown models fall back to their id')
        subs = {r['name']: r['sub'] for r in pb.with_titles(ROWS)}
        self.assertEqual(subs['glm-5.3-iq2m'], 'GGUF IQ2_M, read in place')
        self.assertEqual(subs['glm-5.3-mtp'], 'Colibri int4 g64 + int8 MTP head')
        self.assertEqual(subs['qwen38-27b-ollama'], 'Ollama qwen3.8:27b-mlx')

    def test_order_is_the_tab_order(self):
        names = [r['name'] for r in pb.with_titles(ROWS)]
        self.assertEqual(names, ['v1', 'glm-5.3-mtp', 'glm-5.3-iq2m',
                                 'gemma4-26b-ollama', 'mystery-ollama', 'qwen38-27b-ollama', 'olmoe-mlx'])

    def test_rewrite_manifest_keeps_other_fields(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, 'benches.json')
            p.write_text(json.dumps({'benches': [dict(r, file=f"bench-{r['name']}.json", answers=1) for r in ROWS]}))
            pb.rewrite_manifest(p)
            out = json.loads(p.read_text())['benches']
            self.assertEqual(out[0]['name'], 'v1')
            self.assertTrue(all({'title', 'group', 'file', 'answers', 'engine', 'model'} <= set(r) for r in out))


if __name__ == '__main__':
    unittest.main()
