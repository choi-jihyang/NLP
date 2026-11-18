import ast
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from journal import record_key, stable_hash
from optimized_retry import representative_sample, reuse_successes, schedule_32k, validate_attempt


class OptimizedRetryTests(unittest.TestCase):
    def setUp(self):
        self.sources = [
            {
                "dataset": "studychat",
                "source_id": str(i),
                "student_id": "s",
                "conversation_id": "c",
                "input_sha256": str(i),
                "source_sha256": "source",
            }
            for i in range(4)
        ]
        self.original = {record_key(s): {**s, "status": "context_overflow"} for s in self.sources}

    def test_exact_cutoff_and_unique_representative_sample(self):
        normal, excluded, lengths = schedule_32k(self.sources, [32000, 32001, 10, 50000])
        self.assertEqual({s["source_id"] for s in normal}, {"0", "2"})
        self.assertEqual({s["source_id"] for s in excluded}, {"1", "3"})
        self.assertEqual(len(representative_sample(normal, lengths, 8)), 2)

    def test_success_reuse_preserves_original_profile_and_first_success(self):
        a, b = {"batch_size": 2}, {"batch_size": 8}
        first = {**self.sources[0], "status": "ok", "run_signature": stable_hash(a)}
        later = {**self.sources[0], "status": "invalid_output", "run_signature": stable_hash(b)}
        successful, configs = reuse_successes([([first], a), ([later], b)], self.original)
        self.assertIs(successful["studychat:0"], first)
        self.assertEqual(len(configs), 2)

    def test_duplicate_and_tampered_hash_are_rejected(self):
        config = {"batch": 4}
        record = {**self.sources[0], "status": "ok", "run_signature": stable_hash(config)}
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate_attempt([record, record], config, self.original)
        record["input_sha256"] = "tampered"
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            validate_attempt([record], config, self.original)

    def test_generated_notebook_preserves_limits_and_pins(self):
        path = Path(__file__).parents[2] / "notebooks/thinkguard_studychat_a100_32k_optimized.ipynb"
        notebook = json.loads(path.read_text(encoding="utf-8"))
        sources = ["".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code"]
        for source in sources:
            ast.parse(source)
        prepare, load, benchmark, full, merge = sources[3:]
        self.assertIn("MAX_INPUT = 32000", prepare)
        self.assertIn("MAX_OUTPUT = 2048", prepare)
        self.assertIn("PREVIOUS_ROOT", prepare)
        self.assertIn("range(2)", load)
        self.assertNotIn("range(3)", load)
        self.assertIn("enable_prefix_caching=True", load)
        self.assertIn("for batch in (2, 4, 8)", benchmark)
        self.assertIn("record_key(s) not in reused", benchmark)
        self.assertIn("selected_annotator", full)
        self.assertIn('"duplicate_ids"', merge)


if __name__ == "__main__":
    unittest.main()
