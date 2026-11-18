"""Independent output coverage, original-success preservation and archive checks."""

import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / "data/raw/studychat_final_20261118"
cache = root / "data/raw/colab_merge_20261118"


def rows(path):
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def key(row):
    return row["dataset"], row["source_id"]


all_rows = rows(out / "studychat_all_16851.jsonl")
ok = rows(out / "studychat_ok.jsonl")
failed = rows(out / "studychat_failures.jsonl")
decided = rows(out / "studychat_ok_all_labels_decided.jsonl")
report = json.loads((out / "integration_report.json").read_text(encoding="utf-8"))
assert len(all_rows) == len({key(r) for r in all_rows}) == 16851
assert len(ok) + len(failed) == 16851
assert not ({key(r) for r in ok} & {key(r) for r in failed})
assert all(r["status"] == "ok" for r in ok)
assert all(r["status"] != "ok" for r in failed)
assert dict(Counter(r["status"] for r in all_rows)) == report["statuses"]
assert len(decided) == report["ok_all_three_labels_decided"]
by_key = {key(r): r for r in all_rows}
original_ok = [r for r in rows(cache / "owner_original_annotations.jsonl") if r["status"] == "ok"]
for row in original_ok:
    assert by_key[key(row)] == row, key(row)
for row in ok:
    assert row["human_reviewed"] is False and row["gold_eligible"] is False
hashes = json.loads((out / "SHA256.json").read_text(encoding="utf-8"))
with zipfile.ZipFile(out / "studychat_final_bundle.zip") as archive:
    assert archive.testzip() is None
    for name, metadata in hashes.items():
        raw = (out / name).read_bytes()
        assert len(raw) == metadata["bytes"]
        assert hashlib.sha256(raw).hexdigest() == metadata["sha256"]
        assert archive.read(name) == raw
print(
    json.dumps(
        {
            "verified": True,
            "unique_ids": len(all_rows),
            "ok": len(ok),
            "failed": len(failed),
            "original_successes_preserved_exactly": len(original_ok),
            "zip_crc_and_hashes": "OK",
        }
    )
)
