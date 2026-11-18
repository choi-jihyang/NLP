"""Select failed StudyChat rows and preserve original successes during retry merge."""

from collections import Counter

from journal import record_key, stable_hash


def select_retry_sources(inputs, original, max_tokens):
    selected, seen = [], set()
    for source in inputs:
        key = record_key(source)
        previous = original.get(key)
        if previous is None or source["dataset"] != "studychat" or previous["status"] == "ok":
            continue
        if key in seen:
            raise ValueError("Duplicate retry source")
        seen.add(key)
        if any(previous.get(k) != source[k] for k in ("input_sha256", "source_sha256")):
            raise ValueError("Original result/input hash mismatch: " + key)
        if previous["status"] not in {"context_overflow", "invalid_output", "oom"}:
            continue
        selected.append(source)
    # Original counts are estimates for ordering only. Tokenizer checks the actual
    # current prompt (including repairs) before every engine call.
    selected.sort(key=lambda s: (original[record_key(s)].get("input_tokens", 0), record_key(s)))
    deferred = [record_key(s) for s in selected if original[record_key(s)].get("input_tokens", 0) > max_tokens]
    return selected, deferred


def merge_retry_results(original, retries, retry_config):
    merged = dict(original)
    recovered = 0
    for key, result in retries.items():
        previous = original.get(key)
        if key != record_key(result) or previous is None or previous["dataset"] != "studychat":
            raise ValueError("Unexpected retry result: " + key)
        if previous["status"] == "ok":
            raise ValueError("Retry attempted to replace original success: " + key)
        if result.get("run_signature") != stable_hash(retry_config):
            raise ValueError("Retry signature mismatch")
        if any(previous.get(k) != result.get(k) for k in ("input_sha256", "source_sha256")):
            raise ValueError("Retry input mismatch")
        if result["status"] == "ok":
            merged[key] = result
            recovered += 1
    report = {
        "processed": len(merged),
        "original_ok_preserved": sum(r["status"] == "ok" for r in original.values()),
        "recovered": recovered,
        "statuses": dict(Counter(r["status"] for r in merged.values())),
        "remaining_failed_ids": [k for k, r in merged.items() if r["status"] != "ok"],
        "note": "Mixed inference profiles; consult provenance.json. ok is validation, not human gold.",
    }
    return merged, report
