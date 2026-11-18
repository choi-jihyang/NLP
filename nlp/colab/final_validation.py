"""Source identity and raw-response evidence checks for final integration."""

import hashlib
import json

from contract import PROMPT_VERSION, parse_annotation


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_rows(path):
    with path.open(encoding="utf-8-sig") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def source_digest(source):
    value = {"message": source["message"], "history": source["history"]}
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def validate_ok(row, source):
    if row.get("status") != "ok":
        return None
    if not isinstance(row.get("raw_response"), str):
        return "Missing raw response for independent evidence validation"
    try:
        parsed = parse_annotation(row["raw_response"], source)
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        return str(exc)
    for field, value in parsed.items():
        if row.get(field) != value:
            return "Stored fields differ from independently validated raw response: " + field
    if row.get("prompt_version") != PROMPT_VERSION:
        return "Unknown prompt version"
    return None


def choose_candidate(candidates):
    valid = [c for c in candidates if c["row"]["status"] == "ok" and c["validation_error"] is None]
    # Source order is intentional: original success > prior successes > pilot > full retry.
    return valid[0] if valid else candidates[-1], valid
