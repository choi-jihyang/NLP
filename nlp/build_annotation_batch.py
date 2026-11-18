"""검토자가 작성한 배치 결정을 원문과 결합한다. 라벨을 자동 추론하지 않는다."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

RULE_VERSION = "0.1"
LABEL_NAMES = (
    "is_learning_context",
    "requests_complete_answer",
    "has_self_attempt_evidence",
)
VALUES = {"y": True, "n": False, "u": None}
CONTEXT_MISSING = {6, 24, 39, 49, 54, 55, 58, 59, 63, 65, 69, 74, 77, 78, 79, 83, 87, 88, 93}


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def build(batch_dir: Path, inventory_path: Path) -> None:
    samples = read_json(batch_dir / "batch_001_input.json")
    decisions = read_json(batch_dir / "batch_001_decisions.json")
    inventory = read_json(inventory_path)
    if not isinstance(samples, list) or not isinstance(decisions, list):
        raise ValueError("Expected sample and decision arrays")
    if len(samples) != 100 or len(decisions) != 100:
        raise ValueError("This builder expects exactly 100 decisions")
    by_index = {row[0]: row for row in decisions}
    if set(by_index) != set(range(100)) or len(by_index) != len(decisions):
        raise ValueError("Missing or duplicated decision index")
    records = []
    for index, sample in enumerate(samples):
        _, learning, complete, attempt, intent, rule, reason = by_index[index]
        codes = (learning, complete, attempt)
        labels = {name: VALUES[code] for name, code in zip(LABEL_NAMES, codes, strict=True)}
        uncertain = "u" in codes
        message = sample["message"]
        # Full student message is the exact source span; no AI output is evidence.
        evidence = []
        if attempt == "y":
            evidence = [{"role": "student", "location": "message", "start": 0, "end": len(message), "text": message}]
        records.append(
            {
                **sample,
                "annotation_id": f"batch001-{index + 1:03}",
                "rule_version": RULE_VERSION,
                "annotation_status": "ai_draft",
                "human_reviewed": False,
                "annotator": "Codex",
                "annotation_date": "2026-11-16",
                "source_sha256": inventory[sample["dataset"]]["sha256"],
                "message_sha256": hashlib.sha256(message.encode("utf-8")).hexdigest(),
                "labels": {**labels, "uncertain": uncertain},
                "attempt_current": labels["has_self_attempt_evidence"],
                "intent_note": intent,
                "rule_ids": ["R01", rule, "R09"],
                "rationale": reason,
                "evidence": evidence,
                "context_missing": index in CONTEXT_MISSING,
                "review_required": True,
                "hold_reason": reason if uncertain else None,
                "split": "unassigned",
                "gold_eligible": False,
            }
        )
    ids = {(r["dataset"], r["source_id"]) for r in records}
    if len(ids) != len(records):
        raise ValueError("Duplicate source IDs")
    for record in records:
        for span in record["evidence"]:
            if record["message"][span["start"] : span["end"]] != span["text"]:
                raise ValueError("Evidence span does not match student message")
    output = batch_dir / "batch_001_annotations.jsonl"
    with output.open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    summary = {
        "rule_version": RULE_VERSION,
        "annotation_status": "ai_draft",
        "total": len(records),
        "datasets": dict(Counter(r["dataset"] for r in records)),
        "label_counts": {name: dict(Counter(str(r["labels"][name]).lower() for r in records)) for name in LABEL_NAMES},
        "uncertain": sum(r["labels"]["uncertain"] for r in records),
        "context_missing": sum(r["context_missing"] for r in records),
        "human_reviewed": 0,
        "sampling": "seed=20261116; label-round-robin; initial turn; <=400 chars",
        "limitations": [
            "not representative",
            "not a gold test set",
            "single AI annotator",
            "no multi-turn validation",
            "translations not included",
        ],
    }
    (batch_dir / "batch_001_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    sections = [
        "# 재라벨링 배치 001",
        "",
        "규칙 v0.1 / AI 초안 / 사람 검토 0건",
        "원문 기준 주석이며 번역 완료 데이터가 아닙니다.",
        "",
    ]
    for record in records:
        sections += [
            f"## {record['annotation_id']} · {record['dataset']}",
            "",
            f"원본 ID: `{record['source_id']}`",
            "",
            "### 허용된 이전 대화",
            "",
        ]
        for turn in record["history"]:
            sections += [f"{turn['role']}: {turn['content']}", ""]
        sections += [
            "### 학생 원문",
            "",
            record["message"],
            "",
            "### 판단",
            "",
            f"- 라벨: {json.dumps(record['labels'], ensure_ascii=False)}",
            f"- 의도: {record['intent_note']}",
            f"- 근거: {record['rationale']}",
            f"- 규칙: {', '.join(record['rule_ids'])}",
            f"- 문맥 결손: {record['context_missing']}",
            "- 사람 최종 판단: 미검토",
            "",
        ]
    (batch_dir / "batch_001_review.md").write_text("\n".join(sections), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch_dir", type=Path)
    parser.add_argument("inventory", type=Path)
    args = parser.parse_args()
    build(args.batch_dir, args.inventory)
