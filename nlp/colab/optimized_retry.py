"""Validated result reuse and length-aware scheduling for the 32K retry pass."""

from journal import record_key, stable_hash


def validate_attempt(records, config, original):
    checked = {}
    values = records.values() if isinstance(records, dict) else records
    for record in values:
        key = record_key(record)
        if key in checked or key not in original:
            raise ValueError("Duplicate/unexpected retry ID: " + key)
        source = original[key]
        if source["dataset"] != "studychat" or source["status"] == "ok":
            raise ValueError("Retry includes non-target/original success: " + key)
        if record.get("run_signature") != stable_hash(config):
            raise ValueError("Retry config signature mismatch: " + key)
        if any(
            record.get(k) != source.get(k) for k in ("input_sha256", "source_sha256", "student_id", "conversation_id")
        ):
            raise ValueError("Retry source identity mismatch: " + key)
        checked[key] = record
    return checked


def reuse_successes(attempts, original):
    successes, configs = {}, {}
    for records, config in attempts:
        signature = stable_hash(config)
        configs[signature] = config
        for key, record in validate_attempt(records, config, original).items():
            if record["status"] == "ok" and key not in successes:
                successes[key] = record
    return successes, configs


def schedule_32k(sources, counts, cutoff=32000):
    if len(sources) != len(counts) or any(type(n) is not int or n <= 0 for n in counts):
        raise ValueError("Invalid token length cache")
    lengths, eligible, excluded = {}, [], []
    for source, count in zip(sources, counts, strict=False):
        key = record_key(source)
        if key in lengths:
            raise ValueError("Duplicate source ID")
        lengths[key] = count
        (eligible if count <= cutoff else excluded).append(source)
    eligible.sort(
        key=lambda s: (lengths[record_key(s)] // 2048, s["conversation_id"], lengths[record_key(s)], record_key(s))
    )
    return eligible, excluded, lengths


def representative_sample(sources, lengths, count=8):
    ordered = sorted(sources, key=lambda s: (lengths[record_key(s)], record_key(s)))
    count = min(count, len(ordered))
    if count <= 1:
        return ordered[:count]
    return [ordered[(len(ordered) - 1) * i // (count - 1)] for i in range(count)]
