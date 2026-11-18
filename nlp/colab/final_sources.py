"""Load integration snapshots and interrupted-run checkpoints with provenance checks."""

import json
from collections import Counter, defaultdict

from final_validation import read_rows, sha
from journal import record_key, stable_hash


def load_sources(cache, team):
    configurations = {}
    for path in cache.glob("*_config.json"):
        config = json.loads(path.read_text(encoding="utf-8"))
        configurations[stable_hash(config)] = config
    downloaded = json.loads((cache / "source_downloads.json").read_text(encoding="utf-8-sig"))
    checkpoints_manifest = cache / "checkpoint_download_manifest_private.json"
    if checkpoints_manifest.exists():
        downloaded += json.loads(checkpoints_manifest.read_text(encoding="utf-8-sig"))
    observed_downloads = {}
    for file in downloaded:
        path = cache / file["name"]
        if path.stat().st_size != file["size"]:
            raise ValueError("Downloaded byte count mismatch: " + file["name"])
        # Persist only the safe Drive URL, never temporary signed download URLs.
        observed_downloads[file["name"]] = {k: file[k] for k in ("id", "drive_url", "modified", "size")}
    source_sets = [
        ("owner_original", [cache / "owner_original_annotations.jsonl"], "owner"),
        (
            "owner_prior_full",
            sorted(cache.glob("prior_full_part-*.jsonl")) or [cache / "prior_full_annotations.jsonl"],
            "owner",
        ),
        ("owner_prior_32k", sorted(cache.glob("prior_short_part-*.jsonl")), "owner"),
        ("owner_benchmark_b2", [cache / "benchmark_b2_annotations.jsonl"], "owner"),
        ("owner_benchmark_b4", [cache / "benchmark_b4_annotations.jsonl"], "owner"),
        ("owner_benchmark_b8", [cache / "benchmark_b8_annotations.jsonl"], "owner"),
        ("owner_optimized", [cache / "optimized_annotations.jsonl"], "owner"),
        ("team_studychat1087", [team], "team"),
    ]
    by_key, source_info = defaultdict(list), []
    for name, paths, scope in source_sets:
        seen = set()
        statuses, signatures = Counter(), Counter()
        for path in paths:
            if "_part-" in path.name:
                expected_sha = path.stem.rsplit("-", 1)[1]
                if sha(path) != expected_sha:
                    raise ValueError("Checkpoint SHA mismatch: " + path.name)
            for line, row in enumerate(read_rows(path), 1):
                key = record_key(row)
                if key in seen:
                    raise ValueError("Duplicate ID inside source set: " + name + ":" + key)
                seen.add(key)
                if row.get("dataset") != "studychat":
                    raise ValueError("Non-StudyChat row in supplied result: " + name)
                if row.get("run_signature") in configurations:
                    config = configurations[row["run_signature"]]
                    if config["prompt_version"] != row.get("prompt_version"):
                        raise ValueError("Config/record prompt mismatch")
                statuses[row["status"]] += 1
                signatures[row.get("run_signature")] += 1
                by_key[key].append(
                    {
                        "row": row,
                        "source_name": name,
                        "scope": scope,
                        "file": str(path),
                        "line": line,
                        "validation_error": None,
                    }
                )
        source_info.append(
            {
                "name": name,
                "rows": len(seen),
                "statuses": dict(statuses),
                "run_signatures": dict(signatures),
                "files": [
                    {
                        "path": str(p),
                        "sha256": sha(p),
                        "bytes": p.stat().st_size,
                        "drive": observed_downloads.get(p.name),
                    }
                    for p in paths
                ],
            }
        )

    return configurations, by_key, source_info
