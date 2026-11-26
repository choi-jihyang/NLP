"""Frozen CSV IDs, provenance and group leakage checks; labels never enter text."""

import csv
import gzip
import hashlib
import json
from pathlib import Path

LABELS = ('requests_complete_answer','has_self_attempt_evidence')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def stable(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def load_sources(directory):
    directory = Path(directory)
    labels, splits, students, chats = {}, {}, {}, {}
    for split in ('train','valid','test'):
        with (directory/f'{split}_ok.csv').open(encoding='utf-8-sig',newline='') as stream:
            rows = list(csv.DictReader(stream))
        splits[split] = []
        for row in rows:
            uid = row['dataset']+':'+row['source_id']
            if row['dataset'] != 'studychat' or uid in labels or row['status'] != 'ok':
                raise ValueError('Duplicate ID or non-ok StudyChat row')
            if any(row[k] not in ('true','false') for k in (*LABELS,'is_learning_context')):
                raise ValueError('Null or malformed label in _ok CSV')
            for key, owners in (('student_id',students),('conversation_id',chats)):
                if not row[key] or owners.setdefault(row[key],split) != split:
                    raise ValueError('Student/conversation overlaps splits')
            labels[uid] = row
            splits[split].append(uid)
    sources = {}
    with gzip.open(directory/'inputs.jsonl.gz','rt',encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            uid = row['dataset']+':'+row['source_id']
            if uid not in labels:
                continue
            if uid in sources or row.get('input_verified') is not True:
                raise ValueError('Duplicate or unverified original')
            if stable({k:row[k] for k in ('message','history')}) != row['input_sha256']:
                raise ValueError('Original text hash mismatch')
            if any(row[k] != labels[uid][k] for k in ('student_id','conversation_id')):
                raise ValueError('CSV/source identity mismatch')
            sources[uid] = row
    if set(sources) != set(labels):
        raise ValueError('CSV ID missing from original source')
    # Fixed label-independent policy. Never move IDs or inspect test predictions.
    seen, excluded, kept = {}, [], {}
    for split in ('test','valid','train'):
        kept[split] = []
        for uid in splits[split]:
            digest = sources[uid]['input_sha256']
            if digest in seen:
                excluded.append({'id':uid,'split':split,'duplicate_of':seen[digest], 'reason':'exact_input_duplicate'})
            else:
                seen[digest] = uid
                kept[split].append(uid)
    if any(not kept[split] for split in ('train','valid','test')):
        raise ValueError('A split is empty after duplicate removal')
    return sources, labels, kept, excluded


def load_cache(config):
    import torch
    for name,digest in config['inputs'].items():
        if sha(Path(config['data_dir'])/name) != digest:
            raise ValueError('Frozen source snapshot changed')
    manifest = json.loads((Path(config['run_dir'])/'token_cache_manifest.json').read_text(encoding='utf-8'))
    path = Path(config['run_dir'])/'tokenized.pt'
    if manifest['identity'] != config['identity'] or sha(path) != manifest['sha256']:
        raise ValueError('Token cache identity/content changed')
    return torch.load(path,map_location='cpu',weights_only=True)
