"""Validate compatible inference settings and merge disjoint work by source ID."""

import hashlib
import json
from collections import Counter

from journal import record_key, stable_hash

SEMANTIC_KEYS = (
    "source_hashes",
    "model",
    "prompt_version",
    "prompt_sha256",
    "max_input_tokens",
    "max_new_tokens",
    "batch_size",
    "do_sample",
    "enable_thinking",
)


def assert_compatible(owner, team):
    if team.get("inference_profile") == "team_long32k_v1":
        # Explicitly declared long-context variant: same full prompt, weights,
        # quantization and packages, but a larger input budget and one sequence.
        keys = [k for k in SEMANTIC_KEYS if k not in {"model", "max_input_tokens", "batch_size"}]
        for key in keys:
            if key not in owner or owner[key] != team.get(key):
                raise ValueError(f"Owner/team inference settings differ: {key}")
        a, b = dict(owner["model"]), dict(team["model"])
        original = a.pop("engine_settings")
        expected = {**original, "max_model_len": 32768, "max_num_seqs": 1}
        if b.pop("engine_settings") != expected or a != b:
            raise ValueError("Unexpected long-context model/engine settings")
        if team.get("max_input_tokens") != 32000 or team.get("batch_size") != 1:
            raise ValueError("Unexpected long-context input/batch limits")
        if team["max_input_tokens"] + team["max_new_tokens"] > 32768:
            raise ValueError("Long-context input plus output exceeds engine limit")
        return
    for key in SEMANTIC_KEYS:
        if key not in owner or owner[key] != team.get(key):
            raise ValueError(f"Owner/team inference settings differ: {key}")


def input_digest(record):
    payload = {"message": record["message"], "history": record["history"]}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def merge_records(inputs, owner_records, team_records, owner_config, team_config, assignment):
    assert_compatible(owner_config, team_config)
    if owner_config["bundle_inputs_sha256"] != assignment["parent_inputs_sha256"]:
        raise ValueError("Assignment belongs to a different full input file")
    if team_config["bundle_inputs_sha256"] != assignment["team_inputs_sha256"]:
        raise ValueError("Team config belongs to a different shard")
    expected = {}
    tail = []
    for index, source in enumerate(inputs):
        key = record_key(source)
        if key in expected:
            raise ValueError("Duplicate source ID in full inputs")
        expected[key] = source
        if index >= assignment["owner_count"]:
            tail.append(key)
    if len(expected) != assignment["total"] or tail != assignment["team_keys"]:
        raise ValueError("Assignment boundaries/IDs do not match full inputs")
    merged, overlap = {}, []
    team_keys = set(tail)
    for records, config, is_team in ((owner_records, owner_config, False), (team_records, team_config, True)):
        seen = set()
        for record in records:
            key = record_key(record)
            if key in seen:
                raise ValueError("Duplicate ID inside a result file: " + key)
            seen.add(key)
            source = expected.get(key)
            if source is None or (is_team and key not in team_keys):
                raise ValueError("Unexpected result ID: " + key)
            if record.get("run_signature") != stable_hash(config):
                raise ValueError("Result/config signature mismatch: " + key)
            if (
                record.get("input_sha256") != source["input_sha256"]
                or record.get("source_sha256") != source["source_sha256"]
            ):
                raise ValueError("Result/input hash mismatch: " + key)
            if key in merged:
                overlap.append(key)  # Keep owner's result; never silently overwrite it.
            else:
                merged[key] = record
    missing = sorted(set(expected) - set(merged))
    report = {
        "expected": len(expected),
        "processed": len(merged),
        "missing_ids": missing,
        "team_profile": team_config.get("inference_profile", "same_as_owner"),
        "owner_input_limit": owner_config["max_input_tokens"],
        "team_input_limit": team_config["max_input_tokens"],
        "overlap_kept_owner": overlap,
        "statuses": dict(Counter(r["status"] for r in merged.values())),
        "all_rows_semantically_processed": not missing and all(r["status"] == "ok" for r in merged.values()),
    }
    return [merged[key] for key in expected if key in merged], report
