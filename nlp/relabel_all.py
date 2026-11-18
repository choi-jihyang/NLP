"""전체 원본에 약한 주석 적용. 기존 의미 검토 100건은 별도 상태로 보존한다."""

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from annotation_rules import VERSION, annotate

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
OUTPUT = RAW / "relabel_v0_2"


def read_manual() -> dict:
    path = RAW / "relabel_v0_1/batch_001_annotations.jsonl"
    return {(r["dataset"], r["source_id"]): r for line in path.open(encoding="utf-8") if (r := json.loads(line))}


def source_records():
    with (RAW / "data.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            r = json.loads(line)
            messages = r["messages"]
            verified = bool(messages and messages[-1]["role"] == "user" and messages[-1]["content"] == r["prompt"])
            history = (
                [
                    {"role": "student" if t["role"] == "user" else "assistant", "content": t["content"]}
                    for t in messages[:-1]
                    if t["role"] in {"user", "assistant"}
                ]
                if verified
                else []
            )
            yield {
                "dataset": "studychat",
                "source_id": f"{r['chatId']}:{r['interactionCount']}",
                "student_id": r["userId"],
                "conversation_id": r["chatId"],
                "message": r["prompt"],
                "history": history,
                "source_label": r["llm_label"]["label"],
                "input_verified": verified,
            }
    groups = defaultdict(list)
    with (RAW / "recipe4u/reciep4u_dataset.csv").open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            groups[tuple(row[k] for k in ("student_id", "course", "week", "session"))].append(row)
    for key, rows in sorted(groups.items()):
        history = []
        rows.sort(key=lambda r: int(r["idx"]))
        indices = [int(r["idx"]) for r in rows]
        contiguous = indices == list(range(1, len(rows) + 1))
        for row in rows:
            # Only immediate previous AI and prior student turns; never chatgpt_after or essay.
            allowed = [*history, {"role": "assistant", "content": row["chatgpt_before"]}]
            yield {
                "dataset": "recipe4u",
                "source_id": row["sample_id"],
                "student_id": key[0],
                "conversation_id": ":".join(key),
                "message": row["user"],
                "history": allowed,
                "source_label": row["intent_final"],
                "input_verified": contiguous,
            }
            history.append({"role": "student", "content": row["user"]})


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    manual = read_manual()
    inventory = json.loads((RAW / "dataset_inventory.json").read_text(encoding="utf-8"))
    paths = {"studychat": RAW / "data.jsonl", "recipe4u": RAW / "recipe4u/reciep4u_dataset.csv"}
    for name, path in paths.items():
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != inventory[name]["sha256"]:
            raise ValueError(f"Source hash changed: {name}")
    counts = defaultdict(Counter)
    seen = set()
    with (
        (OUTPUT / "annotations.jsonl").open("w", encoding="utf-8") as out,
        (OUTPUT / "review_queue.jsonl").open("w", encoding="utf-8") as queue,
    ):
        for source in source_records():
            key = (source["dataset"], source["source_id"])
            if key in seen:
                raise ValueError(f"Duplicate ID {key}")
            seen.add(key)
            message = source["message"]
            result = annotate(message, source["history"])
            saved = manual.get(key)
            method = "ai_semantic_draft" if saved else "rule_based_weak"
            if saved:
                result.update({k: saved[k] for k in ("labels", "attempt_current", "evidence", "context_missing")})
                result["rationale"] = saved["rationale"]
                result["rationale_by_label"] = None
            if not source["input_verified"] and not saved:
                result["labels"]["has_self_attempt_evidence"] = None
                result["labels"]["uncertain"] = True
            if source["source_label"] == "misc>error" and not saved:
                result["labels"] = {
                    "is_learning_context": None,
                    "requests_complete_answer": None,
                    "has_self_attempt_evidence": None,
                    "uncertain": True,
                }
                result["rationale"] = "R10: 원본 주석 오류 5건은 의미 재검토 전 격리"
                result["evidence"] = []
            for span in result["evidence"]:
                if message[span["start"] : span["end"]] != span["text"]:
                    raise ValueError("Invalid evidence")
            record = {
                **{k: v for k, v in source.items() if k != "history"},
                **result,
                "rule_version": saved["rule_version"] if saved else VERSION,
                "annotation_method": method,
                "annotation_status": "ai_draft" if saved else "weak_label",
                "human_reviewed": False,
                "gold_eligible": False,
                "review_required": True,
                "split": "unassigned",
                "annotation_date": "2026-11-16",
                "source_sha256": inventory[source["dataset"]]["sha256"],
                "history_turn_count": len(source["history"]),
            }
            encoded = json.dumps(record, ensure_ascii=False) + "\n"
            out.write(encoded)
            c = counts[source["dataset"]]
            c["total"] += 1
            c[method] += 1
            c["uncertain"] += result["labels"]["uncertain"]
            c["context_missing"] += result["context_missing"]
            c["input_unverified"] += not source["input_verified"]
            for label, value in result["labels"].items():
                if label != "uncertain":
                    c[f"{label}:{str(value).lower()}"] += 1
            if result["labels"]["uncertain"] or not source["input_verified"]:
                queue.write(encoded)
    if len(seen) != 18764:
        raise ValueError(f"Unexpected coverage {len(seen)}")
    summary = {
        "date": "2026-11-16",
        "coverage": len(seen),
        "datasets": dict(counts),
        "human_reviewed": 0,
        "review_required": len(seen),
        "method": "100 semantic AI drafts preserved; remaining records rule-based weak labels",
    }
    (OUTPUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
