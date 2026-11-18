import ast
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
from contract import chat_messages, parse_annotation
from journal import record_key, stable_hash
from retry_workflow import merge_retry_results, select_retry_sources
from test_colab_workflow import candidate


class RetryTests(unittest.TestCase):
    def setUp(self):
        self.sources = [
            {
                "dataset": "studychat",
                "source_id": str(i),
                "input_sha256": str(i),
                "source_sha256": "source",
                "message": "help",
                "history": [],
            }
            for i in range(3)
        ]
        self.original = {
            record_key(s): {**s, "status": status, "input_tokens": n}
            for s, status, n in zip(
                self.sources, ["ok", "invalid_output", "context_overflow"], [10, 10, 150000], strict=False
            )
        }
        self.config = {"retry": "test"}

    def test_only_existing_failed_studychat_is_selected(self):
        foreign = {**self.sources[0], "dataset": "recipe4u"}
        selected, deferred = select_retry_sources([*self.sources, foreign], self.original, 131072)
        self.assertEqual([s["source_id"] for s in selected], ["1", "2"])
        self.assertEqual(deferred, ["studychat:2"])

    def test_merge_preserves_original_success_and_failed_retry(self):
        retries = {
            k: {
                **v,
                "status": "ok" if v["source_id"] == "1" else "invalid_output",
                "run_signature": stable_hash(self.config),
            }
            for k, v in self.original.items()
            if v["status"] != "ok"
        }
        merged, report = merge_retry_results(self.original, retries, self.config)
        self.assertIs(merged["studychat:0"], self.original["studychat:0"])
        self.assertIs(merged["studychat:2"], self.original["studychat:2"])
        self.assertEqual(report["recovered"], 1)
        self.assertEqual(report["statuses"], {"ok": 2, "context_overflow": 1})

    def test_original_success_cannot_be_overwritten(self):
        result = {**self.original["studychat:0"], "run_signature": stable_hash(self.config)}
        with self.assertRaisesRegex(ValueError, "original success"):
            merge_retry_results(self.original, {"studychat:0": result}, self.config)

    def test_input_hash_mismatch_is_rejected(self):
        self.original["studychat:1"]["input_sha256"] = "wrong"
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            select_retry_sources(self.sources, self.original, 131072)

    def test_embedded_retry_class_repairs_up_to_three_times(self):
        notebook = json.loads(
            (Path(__file__).parents[2] / "notebooks/thinkguard_studychat_a100_retry.ipynb").read_text(encoding="utf-8")
        )
        source = next(
            "".join(c["source"])
            for c in notebook["cells"]
            if c["cell_type"] == "code" and "class Annotator:" in "".join(c["source"])
        )
        tree = ast.parse(source)
        class_node = next(n for n in tree.body if isinstance(n, ast.ClassDef))
        namespace = {"chat_messages": chat_messages, "parse_annotation": parse_annotation, "time": __import__("time")}
        exec(compile(ast.Module(body=[class_node], type_ignores=[]), "embedded_retry", "exec"), namespace)

        class Engine:
            calls = 0

            def generate(self, prompts, *args, **kwargs):
                self.calls += 1
                text = "bad JSON" if self.calls < 3 else json.dumps(candidate())
                return [SimpleNamespace(outputs=[SimpleNamespace(text=text, token_ids=[1], finish_reason="stop")])]

        tokenizer = SimpleNamespace(apply_chat_template=lambda *a, **k: [1, 2])
        engine = Engine()
        annotator = namespace["Annotator"](engine, tokenizer)
        with patch.dict(sys.modules, {"vllm": SimpleNamespace(SamplingParams=lambda **kw: kw)}):
            result = annotator(self.sources[1])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["attempts"], 3)


if __name__ == "__main__":
    unittest.main()
