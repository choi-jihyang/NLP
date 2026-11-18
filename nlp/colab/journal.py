"""Drive 체크포인트: 불변 JSONL 조각과 내용 해시로 중단 후 재개한다."""

import hashlib
import json
import os
import uuid
from pathlib import Path


def stable_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def record_key(record: dict) -> str:
    return f"{record['dataset']}:{record['source_id']}"


def atomic_json(path: Path, value: object) -> None:
    temp = path.with_name(path.name + ".tmp")
    with temp.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


class Journal:
    def __init__(self, directory: Path, config: dict, checkpoint_every: int = 10):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.config = config
        self.signature = stable_hash(config)
        self.buffer = []
        self.records = {}
        self.checkpoint_every = checkpoint_every
        metadata = directory / "run_config.json"
        if metadata.exists():
            if json.loads(metadata.read_text(encoding="utf-8")) != config:
                raise ValueError("Run config changed: use a NEW run directory")
        else:
            atomic_json(metadata, config)
        for path in sorted(directory.glob("part-*.jsonl")):
            payload = path.read_bytes()
            digest = path.stem.rsplit("-", 1)[1]
            if hashlib.sha256(payload).hexdigest() != digest:
                raise ValueError(f"Checkpoint checksum failed: {path.name}")
            for line in payload.decode("utf-8").splitlines():
                record = json.loads(line)
                key = record_key(record)
                if record.get("run_signature") != self.signature:
                    raise ValueError("Mixed model/prompt/data checkpoints")
                if key in self.records:
                    raise ValueError("Duplicate checkpoint source ID")
                self.records[key] = record

    def add(self, record: dict) -> None:
        key = record_key(record)
        if key in self.records:
            raise ValueError("Attempted duplicate result")
        record = {**record, "run_signature": self.signature}
        self.records[key] = record
        self.buffer.append(record)
        if len(self.buffer) >= self.checkpoint_every:
            self.flush()

    def flush(self) -> None:
        if not self.buffer:
            return
        payload = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in self.buffer).encode()
        digest = hashlib.sha256(payload).hexdigest()
        destination = self.directory / f"part-{uuid.uuid4().hex}-{digest}.jsonl"
        temp = destination.with_suffix(".tmp")
        with temp.open("wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, destination)
        self.buffer.clear()
        atomic_json(self.directory / "progress.json", self.summary())

    def summary(self) -> dict:
        statuses = {}
        for record in self.records.values():
            status = record["status"]
            statuses[status] = statuses.get(status, 0) + 1
        return {
            "processed": len(self.records),
            "statuses": statuses,
            "unflushed": len(self.buffer),
            "run_signature": self.signature,
        }

    def export(self) -> Path:
        self.flush()
        target = self.directory / "annotations.jsonl"
        temp = target.with_suffix(".tmp")
        with temp.open("w", encoding="utf-8") as stream:
            for key in sorted(self.records):
                stream.write(json.dumps(self.records[key], ensure_ascii=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, target)
        return target
