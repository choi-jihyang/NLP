"""Colab 업로드용 데이터·실행 모듈 패키지. 원본은 수정하거나 외부 전송하지 않는다."""

import argparse
import csv
import gzip
import hashlib
import json
import zipfile
from collections import defaultdict
from pathlib import Path

from relabel_all import source_records

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
OUT = RAW / "colab_bundle"


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def record_digest(record: dict) -> str:
    payload = {"message": record["message"], "history": record["history"]}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def recipe_records():
    groups = defaultdict(list)
    with (RAW / "recipe4u/reciep4u_dataset.csv").open(encoding="utf-8-sig", newline="") as stream:
        for r in csv.DictReader(stream):
            groups[tuple(r[k] for k in ("student_id", "course", "week", "session"))].append(r)
    for group, rows in sorted(groups.items()):
        rows.sort(key=lambda r: int(r["idx"]))
        verified = [int(r["idx"]) for r in rows] == list(range(1, len(rows) + 1))
        history = []
        for r in rows:
            before = {"role": "assistant", "content": r["chatgpt_before"]}
            yield {
                "dataset": "recipe4u",
                "source_id": r["sample_id"],
                "student_id": group[0],
                "conversation_id": ":".join(group),
                "message": r["user"],
                "history": [*history, before],
                "input_verified": verified,
            }
            # The next row's chatgpt_before is the next allowed AI response.
            # Never use the CURRENT row's chatgpt_after or essay as classifier input.
            history.extend([before, {"role": "student", "content": r["user"]}])


def main(refresh_code: bool = False) -> None:
    OUT.mkdir(exist_ok=True)
    if refresh_code:
        manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
        for name in ("inputs.jsonl.gz", "pilot_inputs.jsonl.gz", "references.jsonl"):
            if digest(OUT / name) != manifest["files"][name]:
                raise ValueError("Existing data package changed")
        write_archive(manifest)
        return
    inventory = json.loads((RAW / "dataset_inventory.json").read_text(encoding="utf-8"))
    for name, relative in (("studychat", "data.jsonl"), ("recipe4u", "recipe4u/reciep4u_dataset.csv")):
        if digest(RAW / relative) != inventory[name]["sha256"]:
            raise ValueError(f"Source hash changed: {name}")
    counts = defaultdict(int)
    seen = set()

    # Chain streams to avoid keeping 600+ MB of full StudyChat history in RAM.
    def records():
        for r in source_records():
            if r["dataset"] == "studychat":
                yield {k: v for k, v in r.items() if k != "source_label"}
        yield from recipe_records()

    with gzip.open(OUT / "inputs.jsonl.gz", "wt", encoding="utf-8", compresslevel=6) as stream:
        for record in records():
            key = (record["dataset"], record["source_id"])
            if key in seen:
                raise ValueError("Duplicate source ID")
            seen.add(key)
            record["source_sha256"] = inventory[record["dataset"]]["sha256"]
            record["input_sha256"] = record_digest(record)
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            counts[record["dataset"]] += 1
    references = []
    for path in [
        RAW / "relabel_v0_1/batch_001_annotations.jsonl",
        *sorted(RAW.glob("semantic_batch_*/annotations.jsonl")),
    ]:
        references.extend(json.loads(line) for line in path.open(encoding="utf-8"))
    if len({(r["dataset"], r["source_id"]) for r in references}) != len(references):
        raise ValueError("Duplicate diagnostic references")
    with (
        gzip.open(OUT / "pilot_inputs.jsonl.gz", "wt", encoding="utf-8") as pilot,
        (OUT / "references.jsonl").open("w", encoding="utf-8") as ref,
    ):
        for r in references:
            sample = {k: r[k] for k in ("dataset", "source_id", "student_id", "message", "history")}
            sample["conversation_id"] = r.get("conversation_id", r["source_id"])
            sample["input_verified"] = True
            sample["source_sha256"] = inventory[r["dataset"]]["sha256"]
            sample["input_sha256"] = record_digest(sample)
            pilot.write(json.dumps(sample, ensure_ascii=False) + "\n")
            ref.write(
                json.dumps(
                    {
                        "dataset": r["dataset"],
                        "source_id": r["source_id"],
                        "labels": r["labels"],
                        "reference_status": "AI draft, not gold",
                    }
                )
                + "\n"
            )
    if dict(counts) != {"studychat": 16851, "recipe4u": 1913}:
        raise ValueError("Unexpected full coverage")
    modules = [p for p in (ROOT / "nlp/colab").glob("*.py") if not p.name.startswith("test_")]
    files = [OUT / "inputs.jsonl.gz", OUT / "pilot_inputs.jsonl.gz", OUT / "references.jsonl", *modules]
    manifest = {
        "created": "2026-11-16",
        "total": sum(counts.values()),
        "counts": dict(counts),
        "references": len(references),
        "inputs_sha256": digest(OUT / "inputs.jsonl.gz"),
        "source_hashes": {name: inventory[name]["sha256"] for name in counts},
        "files": {p.name: digest(p) for p in files},
        "recipe_history": "all prior student and chatgpt_before turns; no current future AI or essay",
        "pilot_history": "original context of existing AI drafts, not necessarily full current history",
    }
    write_archive(manifest)


def write_archive(manifest: dict) -> None:
    modules = [p for p in (ROOT / "nlp/colab").glob("*.py") if not p.name.startswith("test_")]
    files = [OUT / "inputs.jsonl.gz", OUT / "pilot_inputs.jsonl.gz", OUT / "references.jsonl", *modules]
    manifest["files"] = {p.name: digest(p) for p in files}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    archive = OUT / "thinkguard_colab_vllm_bundle.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in [OUT / "manifest.json", *files]:
            bundle.write(path, path.name)
    print(
        json.dumps(
            {
                "path": str(archive),
                "bytes": archive.stat().st_size,
                "counts": manifest["counts"],
                "reference_rows": manifest["references"],
                "sha256": digest(archive),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-code", action="store_true")
    main(parser.parse_args().refresh_code)
