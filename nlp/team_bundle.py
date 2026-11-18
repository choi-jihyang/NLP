"""Build the private tail assignment package without copying its data to Git."""

import gzip
import hashlib
import json
import zipfile
from collections import Counter


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def create_team_bundle(base, out, modules, bundle_name):
    from journal import record_key
    from runner import read_inputs
    from team_split import input_digest

    out.mkdir(exist_ok=True)
    parent = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
    assert digest(base / "inputs.jsonl.gz") == parent["inputs_sha256"]
    total = parent["total"]
    assert total == 18764
    owner_count = total - 3000
    tail = []
    count = 0
    for index, source in enumerate(read_inputs(base / "inputs.jsonl.gz")):
        count += 1
        if index >= owner_count:
            assert input_digest(source) == source["input_sha256"]
            tail.append(source)
    assert count == total and len(tail) == 3000
    assert len({record_key(r) for r in tail}) == 3000
    with gzip.open(out / "inputs.jsonl.gz", "wt", encoding="utf-8") as stream:
        for source in tail:
            stream.write(json.dumps(source, ensure_ascii=False) + "\n")
    assignment = {
        "total": total,
        "owner_count": owner_count,
        "team_count": len(tail),
        "parent_inputs_sha256": parent["inputs_sha256"],
        "team_inputs_sha256": digest(out / "inputs.jsonl.gz"),
        "team_keys": [record_key(r) for r in tail],
        "team_counts": dict(Counter(r["dataset"] for r in tail)),
    }
    (out / "assignment.json").write_text(json.dumps(assignment, ensure_ascii=False, indent=2), encoding="utf-8")
    modules = [p for p in modules.glob("*.py") if not p.name.startswith("test_")]
    paths = [out / "inputs.jsonl.gz", out / "assignment.json", *modules]
    manifest = {
        "total": len(tail),
        "counts": assignment["team_counts"],
        "source_hashes": parent["source_hashes"],
        "inputs_sha256": assignment["team_inputs_sha256"],
        "files": {p.name: digest(p) for p in paths},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    archive_path = out / bundle_name
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in [out / "manifest.json", *paths]:
            archive.write(path, path.name)

    return assignment, owner_count, archive_path


def print_bundle_summary(archive_path, owner_count, assignment):
    summary = {
        "team_zip": str(archive_path),
        "bytes": archive_path.stat().st_size,
        "owner_count": owner_count,
        "team_counts": assignment["team_counts"],
    }
    print(json.dumps(summary, ensure_ascii=True))
