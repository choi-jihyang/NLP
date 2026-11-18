"""사람/AI 의미 검토 결정을 원문·근거 위치와 결합한다. 새 판단을 추론하지 않는다."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

VALUES = {"y": True, "n": False, "u": None}
NAMES = ("is_learning_context", "requests_complete_answer", "has_self_attempt_evidence")


def build(directory: Path) -> None:
    samples = json.loads((directory / "input.json").read_text(encoding="utf-8"))
    decisions = json.loads((directory / "decisions.json").read_text(encoding="utf-8"))
    mapping = {r[0]: r for r in decisions}
    if len(mapping) != len(decisions) or set(mapping) != set(range(len(samples))):
        raise ValueError("Decision coverage mismatch")
    inventory = json.loads((directory.parent / "dataset_inventory.json").read_text(encoding="utf-8"))
    reviewed = []
    past_evidence = json.loads((directory / "past_evidence.json").read_text(encoding="utf-8"))
    batch_name = directory.name
    for i, source in enumerate(samples):
        _, learning, complete, current, cumulative, missing, intent, reason = mapping[i]
        labels = dict(zip(NAMES, (VALUES[learning], VALUES[complete], VALUES[cumulative]), strict=True))
        labels["uncertain"] = any(value is None for value in labels.values())
        spans = []
        if current == "y":
            text = source["message"]
            spans.append({"role": "student", "location": "message", "start": 0, "end": len(text), "text": text})
        elif cumulative == "y":
            turn = past_evidence[str(i)]
            text = source["history"][turn]["content"]
            if source["history"][turn]["role"] != "student":
                raise ValueError("AI message used as evidence")
            spans.append(
                {
                    "role": "student",
                    "location": "history",
                    "turn_index": turn,
                    "start": 0,
                    "end": len(text),
                    "text": text,
                }
            )
        record = {
            **source,
            "labels": labels,
            "attempt_current": VALUES[current],
            "annotation_id": f"{batch_name}-{i + 1:03}",
            "rule_version": "0.3",
            "annotation_method": "ai_semantic_draft",
            "annotation_status": "ai_draft",
            "human_reviewed": False,
            "gold_eligible": False,
            "review_required": True,
            "context_missing": missing,
            "rationale": reason,
            "intent_note": intent,
            "rule_ids": ["R01", "R02", "R03-R10", "S01-S09"],
            "evidence": spans,
            "source_sha256": inventory[source["dataset"]]["sha256"],
            "message_sha256": hashlib.sha256(source["message"].encode()).hexdigest(),
            "supersedes": "relabel_v0_2:rule_based_weak",
            "annotation_date": "2026-11-16",
            "split": "unassigned",
        }
        reviewed.append(record)
    with (directory / "annotations.jsonl").open("w", encoding="utf-8") as stream:
        for record in reviewed:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    summary = {
        "total": len(reviewed),
        "datasets": dict(Counter(r["dataset"] for r in reviewed)),
        "resolved": sum(not r["labels"]["uncertain"] for r in reviewed),
        "still_uncertain": sum(r["labels"]["uncertain"] for r in reviewed),
        "context_missing": sum(r["context_missing"] for r in reviewed),
        "human_reviewed": 0,
        "rule_version": "0.3",
    }
    (directory / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    markdown = [f"# 원문 의미 검토 {batch_name}", "", "AI 초안 / 규칙 v0.3 / 사람 미검토", ""]
    for r in reviewed:
        markdown += [f"## {r['annotation_id']} · {r['dataset']}", "", f"원본: `{r['source_id']}`", ""]
        for index, turn in enumerate(r["history"]):
            markdown += [f"### 이전 {index}: {turn['role']}", "", turn["content"], ""]
        markdown += [
            "### 현재 학생 발화",
            "",
            r["message"],
            "",
            "### 의미 검토",
            "",
            str(r["labels"]),
            "",
            f"현재 시도: {r['attempt_current']}",
            "",
            r["rationale"],
            "",
            f"문맥 결손: {r['context_missing']}",
            "",
        ]
    (directory / "review.md").write_text("\n".join(markdown), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    build(parser.parse_args().directory)
