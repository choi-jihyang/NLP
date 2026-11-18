"""Integrate owner retries and a supplied team shard; verify identity and evidence."""

import argparse
import gzip
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "nlp/colab"))
from final_report import export_results  # noqa: E402
from final_sources import load_sources  # noqa: E402
from final_validation import choose_candidate, source_digest, validate_ok  # noqa: E402
from journal import record_key, stable_hash  # noqa: E402

CACHE = ROOT / "data/raw/colab_merge_20261118"
OUT = ROOT / "data/raw/studychat_final_20261118"
TEAM = None


def main():
    OUT.mkdir(exist_ok=True)
    configurations, by_key, source_info = load_sources(CACHE, TEAM)
    all_rows, failures, lineage, conflicts, quarantine = [], [], [], [], []
    expected_keys, owner_expected, team_expected = set(), set(), set()
    chosen_sources = Counter()
    verified_rows = 0
    full_inputs = ROOT / "data/raw/colab_bundle/inputs.jsonl.gz"
    with gzip.open(full_inputs, "rt", encoding="utf-8") as stream:
        for source in map(json.loads, stream):
            if source["dataset"] != "studychat":
                continue
            index = len(expected_keys)
            key = record_key(source)
            if key in expected_keys:
                raise ValueError("Duplicate ID in original source")
            expected_keys.add(key)
            scope = "owner" if index < 15764 else "team"
            (owner_expected if scope == "owner" else team_expected).add(key)
            if source_digest(source) != source["input_sha256"]:
                raise ValueError("Original input digest mismatch: " + key)
            candidates = by_key.get(key, [])
            for candidate in candidates:
                row = candidate["row"]
                if candidate["scope"] != scope:
                    raise ValueError("Shard scope mismatch: " + key)
                for field in ("source_sha256", "input_sha256", "student_id", "conversation_id"):
                    if row.get(field) != source.get(field):
                        raise ValueError("Result/source identity mismatch: " + key + ":" + field)
                candidate["validation_error"] = validate_ok(row, source)
                if candidate["validation_error"]:
                    quarantine.append(
                        {"id": key, "source": candidate["source_name"], "error": candidate["validation_error"]}
                    )
                verified_rows += 1
            if not candidates:
                row = {
                    k: source[k]
                    for k in ("dataset", "source_id", "student_id", "conversation_id", "source_sha256", "input_sha256")
                }
                row.update(
                    status="missing_result",
                    error="No supplied result for expected source ID",
                    human_reviewed=False,
                    gold_eligible=False,
                    review_required=True,
                )
                all_rows.append(row)
                failures.append(row)
                lineage.append({"id": key, "selected_source": None, "candidate_count": 0})
                continue
            chosen, valid = choose_candidate(candidates)
            selected = dict(chosen["row"])
            if selected["status"] == "ok" and chosen["validation_error"]:
                selected.update(status="integration_validation_failed", error=chosen["validation_error"])
            selected.update(human_reviewed=False, gold_eligible=False, review_required=True)
            all_rows.append(selected)
            chosen_sources[chosen["source_name"]] += 1
            if selected["status"] != "ok":
                failures.append(selected)
            if (
                len(
                    {
                        stable_hash({"labels": c["row"]["labels"], "attempt_current": c["row"].get("attempt_current")})
                        for c in valid
                    }
                )
                > 1
            ):
                conflicts.append(
                    {
                        "id": key,
                        "selected_source": chosen["source_name"],
                        "variants": [
                            {
                                "source": c["source_name"],
                                "labels": c["row"]["labels"],
                                "attempt_current": c["row"].get("attempt_current"),
                                "run_signature": c["row"].get("run_signature"),
                            }
                            for c in valid
                        ],
                    }
                )
            lineage.append(
                {
                    "id": key,
                    "selected_source": chosen["source_name"],
                    "file": chosen["file"],
                    "line": chosen["line"],
                    "status": selected["status"],
                    "run_signature": selected.get("run_signature"),
                    "candidate_count": len(candidates),
                }
            )
    if len(expected_keys) != 16851 or len(owner_expected) != 15764 or len(team_expected) != 1087:
        raise ValueError("Unexpected source coverage")
    unexpected = sorted(set(by_key) - expected_keys)
    if unexpected:
        raise ValueError("Unexpected result IDs: " + repr(unexpected[:5]))
    if {
        record_key(c["row"]) for key in by_key for c in by_key[key] if c["source_name"] == "owner_original"
    } != owner_expected:
        raise ValueError("Original owner result does not cover its exact shard")
    if {record_key(c["row"]) for key in by_key for c in by_key[key] if c["scope"] == "team"} != team_expected:
        raise ValueError("Team result does not cover the expected 1,087 IDs")
    if len(all_rows) != len({record_key(r) for r in all_rows}):
        raise ValueError("Duplicate final ID")
    export_results(
        OUT,
        all_rows,
        failures,
        lineage,
        conflicts,
        quarantine,
        owner_expected,
        team_expected,
        unexpected,
        by_key,
        verified_rows,
        chosen_sources,
        source_info,
        configurations,
        full_inputs,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--team-annotations", type=Path, required=True)
    args = parser.parse_args()
    TEAM = args.team_annotations
    main()
