"""원문 의미 검토를 전체 주석에 반영하되 이전 스냅샷은 보존한다."""

import json
from collections import Counter
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data/raw"


def key(record: dict) -> tuple:
    return record["dataset"], record["source_id"]


def main() -> None:
    reviews = {}
    for path in sorted(RAW.glob("semantic_batch_*/annotations.jsonl")):
        for line in path.open(encoding="utf-8"):
            record = json.loads(line)
            if key(record) in reviews:
                raise ValueError("Overlapping semantic batches require explicit adjudication")
            for span in record["evidence"]:
                source = record["message"]
                if span["location"] == "history":
                    turn = record["history"][span["turn_index"]]
                    if turn["role"] != "student":
                        raise ValueError("Non-student evidence")
                    source = turn["content"]
                if source[span["start"] : span["end"]] != span["text"]:
                    raise ValueError("Invalid evidence span")
            reviews[key(record)] = record
    output = RAW / "relabel_v0_3"
    output.mkdir(exist_ok=True)
    counts = Counter()
    found = set()
    seen = set()
    with (
        (RAW / "relabel_v0_2/annotations.jsonl").open(encoding="utf-8") as original,
        (output / "annotations.jsonl").open("w", encoding="utf-8") as stream,
        (output / "review_queue.jsonl").open("w", encoding="utf-8") as queue,
    ):
        for line in original:
            record = json.loads(line)
            identifier = key(record)
            if identifier in seen:
                raise ValueError("Duplicate source ID")
            seen.add(identifier)
            if identifier in reviews:
                updated = reviews[identifier]
                if updated["message"] != record["message"] or updated["source_sha256"] != record["source_sha256"]:
                    raise ValueError("Semantic review does not match original input")
                if record["annotation_method"] != "rule_based_weak":
                    raise ValueError("Unexpected overwrite of previous semantic review")
                record = updated
                found.add(identifier)
            labels = record["labels"]
            unknown = any(
                labels[k] is None
                for k in ("is_learning_context", "requests_complete_answer", "has_self_attempt_evidence")
            )
            if unknown != labels["uncertain"]:
                raise ValueError("Inconsistent uncertainty")
            encoded = json.dumps(record, ensure_ascii=False) + "\n"
            stream.write(encoded)
            priority = unknown or not record.get("input_verified", True)
            if priority:
                queue.write(encoded)
            counts["total"] += 1
            counts[record["annotation_method"]] += 1
            counts["priority_queue"] += priority
            counts["uncertain"] += unknown
            if identifier in reviews:
                counts["new_semantic_reviews"] += 1
                counts["newly_resolved"] += not unknown
            counts[f"{record['dataset']}:total"] += 1
    if found != set(reviews) or len(seen) != 18764:
        raise ValueError("Coverage mismatch")
    summary = {
        **counts,
        "snapshot": "0.3",
        "human_reviewed": 0,
        "note": "Mixed rule versions; all semantic decisions remain AI drafts",
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
