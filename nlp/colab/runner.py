"""중단·재개 가능한 주석 실행, 진단 비교 및 결과 내보내기."""

import gzip
import json
import time
from pathlib import Path

from contract import LABELS, PROMPT_VERSION, SYSTEM
from journal import Journal, atomic_json, record_key, stable_hash


def read_inputs(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def run(inputs, annotator, run_dir: Path, config: dict, limit: int | None = None) -> Journal:
    journal = Journal(run_dir, config, checkpoint_every=10)
    new = 0
    started = time.monotonic()
    seen = set()
    pending = []
    batch_size = getattr(annotator, "batch_size", 1)

    def process_batch():
        nonlocal new
        if not pending:
            return
        results = (
            annotator.annotate_batch(pending)
            if hasattr(annotator, "annotate_batch")
            else [annotator(source) for source in pending]
        )
        if len(results) != len(pending):
            raise RuntimeError("Annotation batch result count mismatch")
        for source, result in zip(pending, results, strict=False):
            result.update(
                {
                    k: source[k]
                    for k in ("dataset", "source_id", "student_id", "conversation_id", "source_sha256", "input_sha256")
                }
            )
            result.update(
                {
                    "prompt_version": PROMPT_VERSION,
                    "annotation_method": "qwen_semantic_draft",
                    "human_reviewed": False,
                    "gold_eligible": False,
                    "review_required": True,
                }
            )
            journal.add(result)
            new += 1
            if new % 10 == 0:
                rate = (time.monotonic() - started) / new
                print(f"New: {new}; {rate:.1f} sec/row; total saved/in-memory: {len(journal.records)}", flush=True)
        pending.clear()

    try:
        for source in inputs:
            key = record_key(source)
            if key in seen:
                raise ValueError("Duplicate input ID")
            seen.add(key)
            if key in journal.records:
                continue
            if limit is not None and new + len(pending) >= limit:
                break
            pending.append(source)
            if len(pending) >= batch_size:
                process_batch()
        process_batch()
    finally:
        # Also checkpoint KeyboardInterrupt; hard runtime loss can redo at most 9 pending rows.
        journal.flush()
    journal.export()
    print(json.dumps(journal.summary(), indent=2))
    return journal


def configuration(manifest: dict, model: dict, annotator) -> dict:
    return {
        "bundle_inputs_sha256": manifest["inputs_sha256"],
        "bundle_manifest_sha256": stable_hash(manifest),
        "source_hashes": manifest["source_hashes"],
        "model": {k: v for k, v in model.items() if k not in {"gpu", "vram_gib"}},
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": stable_hash(SYSTEM),
        "max_input_tokens": annotator.max_input_tokens,
        "max_new_tokens": annotator.max_new_tokens,
        "batch_size": getattr(annotator, "batch_size", 1),
        "do_sample": False,
        "enable_thinking": False,
    }


def diagnostic(journal: Journal, references: list[dict]) -> dict:
    results = {}
    for label in LABELS:
        compared = agreed = null_predictions = 0
        for reference in references:
            prediction = journal.records.get(record_key(reference), {})
            if prediction.get("status") != "ok":
                continue
            value, expected = prediction["labels"][label], reference["labels"][label]
            if value is None:
                null_predictions += 1
            elif expected is not None:
                compared += 1
                agreed += value == expected
        results[label] = {"both_decided": compared, "agreed": agreed, "predicted_null": null_predictions}
    report = {
        "warning": "Reference labels are AI drafts, NOT independent ground truth or accuracy",
        "per_label": results,
        "execution": journal.summary(),
    }
    atomic_json(journal.directory / "diagnostic.json", report)
    return report


def export_review(journal: Journal, inputs: list[dict]) -> Path:
    path = journal.directory / "sample_review.md"
    sections = ["# Qwen3.5-9B 표본 검토", "", "AI 생성 초안 / 사람 정답 아님", ""]
    for source in inputs:
        result = journal.records.get(record_key(source))
        if result is None:
            continue
        sections += [f"## {record_key(source)}", ""]
        for i, turn in enumerate(source["history"]):
            sections += [f"### 이전 {i}: {turn['role']}", turn["content"], ""]
        sections += [
            "### 현재 학생",
            source["message"],
            "",
            "### 모델 결과",
            "```json",
            json.dumps(result, ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    path.write_text("\n".join(sections), encoding="utf-8")
    return path
