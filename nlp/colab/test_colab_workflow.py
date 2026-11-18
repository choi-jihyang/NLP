"""GPU 없이 근거 오염·체크포인트 재개·변경된 설정 혼입을 검사한다."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))

from contract import parse_annotation
from inference_vllm import Annotator as VllmAnnotator
from journal import Journal
from runner import run


def candidate(**updates):
    base = {
        "is_learning_context": True,
        "requests_complete_answer": False,
        "has_self_attempt_evidence": False,
        "attempt_current": False,
        "context_missing": False,
        "past_evidence_same_task": None,
        "reasons": {
            k: "test reason"
            for k in ("is_learning_context", "requests_complete_answer", "has_self_attempt_evidence", "attempt_current")
        },
        "evidence": [],
    }
    return {**base, **updates}


class AnnotationContractTests(unittest.TestCase):
    def test_assistant_evidence_is_rejected(self):
        source = {"message": "explain", "history": [{"role": "assistant", "content": "x = 2"}]}
        response = candidate(
            has_self_attempt_evidence=True, past_evidence_same_task=True, evidence=[{"turn": 0, "quote": "x = 2"}]
        )
        with self.assertRaisesRegex(ValueError, "Assistant"):
            parse_annotation(json.dumps(response), source)

    def test_hallucinated_quote_is_rejected(self):
        response = candidate(
            attempt_current=True, has_self_attempt_evidence=True, evidence=[{"turn": -1, "quote": "I solved it"}]
        )
        with self.assertRaisesRegex(ValueError, "exact"):
            parse_annotation(json.dumps(response), {"message": "help", "history": []})

    def test_past_positive_requires_same_question(self):
        response = candidate(has_self_attempt_evidence=True, evidence=[{"turn": 0, "quote": "my draft"}])
        with self.assertRaisesRegex(ValueError, "same-task"):
            parse_annotation(
                json.dumps(response),
                {"message": "next question", "history": [{"role": "student", "content": "my draft"}]},
            )

    def test_exact_current_quote_and_null_consistency(self):
        response = candidate(
            attempt_current=True,
            has_self_attempt_evidence=True,
            requests_complete_answer=None,
            evidence=[{"turn": -1, "quote": "x = 2"}],
        )
        result = parse_annotation(json.dumps(response), {"message": "tried x = 2", "history": []})
        self.assertTrue(result["labels"]["uncertain"])
        self.assertEqual(result["evidence"][0]["start"], 6)

    def test_string_booleans_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "boolean"):
            parse_annotation(json.dumps(candidate(is_learning_context="true")), {"message": "x", "history": []})


class VllmBatchTests(unittest.TestCase):
    def test_filtered_rows_keep_order_and_only_invalid_output_is_retried(self):
        class Tokenizer:
            def apply_chat_template(self, messages, **kwargs):
                ids = [1] * (20 if '"current_student_message": "long"' in messages[-1]["content"] else 2)
                # Transformers 5 defaults to a mapping, unlike Transformers 4.
                return ids if kwargs.get("return_dict") is False else {"input_ids": ids}

        class Engine:
            def __init__(self):
                self.sizes = []

            def generate(self, prompts, params, **kwargs):
                self.sizes.append(len(prompts))
                texts = ["bad JSON", json.dumps(candidate())] if len(self.sizes) == 1 else [json.dumps(candidate())]
                return [
                    SimpleNamespace(outputs=[SimpleNamespace(text=text, token_ids=[1], finish_reason="stop")])
                    for text in texts
                ]

        engine = Engine()
        annotator = VllmAnnotator(engine, Tokenizer(), max_input_tokens=10)
        sources = [
            {"message": text, "history": [], "input_verified": verified}
            for text, verified in [("a", True), ("long", True), ("x", False), ("b", True)]
        ]
        fake_module = SimpleNamespace(SamplingParams=lambda **kwargs: kwargs)
        with patch.dict(sys.modules, {"vllm": fake_module}):
            results = annotator.annotate_batch(sources)
        self.assertEqual(engine.sizes, [2, 1])
        self.assertEqual([r["status"] for r in results], ["ok", "context_overflow", "input_unverified", "ok"])
        self.assertEqual(results[0]["attempts"], 2)
        self.assertEqual(results[3]["attempts"], 1)


class CheckpointTests(unittest.TestCase):
    def test_batches_obey_limit_and_resume_in_order(self):
        class BatchAnnotator:
            batch_size = 2

            def __init__(self):
                self.calls = []

            def annotate_batch(self, sources):
                self.calls.append([s["source_id"] for s in sources])
                return [{"status": "ok", "echo": s["source_id"]} for s in sources]

        samples = [
            {
                "dataset": "test",
                "source_id": str(i),
                "student_id": "s",
                "conversation_id": "c",
                "source_sha256": "hash",
                "input_sha256": str(i),
            }
            for i in range(6)
        ]
        annotator = BatchAnnotator()
        with tempfile.TemporaryDirectory() as directory:
            run(samples, annotator, Path(directory), {"engine": "fake"}, limit=3)
            resumed = run(samples, annotator, Path(directory), {"engine": "fake"})
            self.assertEqual(annotator.calls, [["0", "1"], ["2"], ["3", "4"], ["5"]])
            self.assertEqual(len(resumed.records), 6)
            for result in resumed.records.values():
                self.assertEqual(result["source_id"], result["echo"])

    def test_runner_resumes_only_unprocessed_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            samples = [
                {
                    "dataset": "test",
                    "source_id": str(i),
                    "student_id": "s",
                    "conversation_id": "c",
                    "source_sha256": "hash",
                    "input_sha256": str(i),
                }
                for i in range(3)
            ]
            calls = []

            def fake_annotator(source):
                calls.append(source["source_id"])
                return {"status": "ok"}

            run(samples, fake_annotator, Path(directory), {"model": "test"}, limit=1)
            resumed = run(samples, fake_annotator, Path(directory), {"model": "test"})
            self.assertEqual(calls, ["0", "1", "2"])
            self.assertEqual(len(resumed.records), 3)

    def test_resume_skip_duplicate_and_config_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            journal = Journal(path, {"model": "a"}, checkpoint_every=2)
            record = {"dataset": "test", "source_id": "1", "status": "ok"}
            journal.add(record)
            journal.flush()
            resumed = Journal(path, {"model": "a"})
            self.assertEqual(len(resumed.records), 1)
            with self.assertRaises(ValueError):
                resumed.add(record)
            with self.assertRaisesRegex(ValueError, "config changed"):
                Journal(path, {"model": "b"})

    def test_interrupted_temp_is_ignored_and_corruption_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "part-interrupted.tmp").write_text('{"incomplete":', encoding="utf-8")
            journal = Journal(path, {"model": "a"}, checkpoint_every=1)
            journal.add({"dataset": "test", "source_id": "1", "status": "ok"})
            self.assertEqual(len(Journal(path, {"model": "a"}).records), 1)
            next(path.glob("part-*.jsonl")).write_text("corrupted", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "checksum"):
                Journal(path, {"model": "a"})


if __name__ == "__main__":
    unittest.main()
