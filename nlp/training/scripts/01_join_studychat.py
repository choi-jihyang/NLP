"""1단계: ThinkGuard 라벨 CSV와 StudyChat 원본 대화를 조인한다.

라벨 CSV의 source_id = "<chatId>:<interactionCount>" 라고 가정하고,
StudyChat data.jsonl의 각 행(한 번의 학생 요청)과 연결한다.

출력: <out-dir>/{train,valid,test}.jsonl, join_report.json
각 행:
  id, split, student_id, conversation_id, turn, topic, semester, lang="en",
  message  : 현재 학생 발화 (모델이 판단할 대상)
  history  : 현재 발화 이전의 대화 [{role: student|assistant, text}], 오래된 것 → 최신 순
  labels   : {is_learning_context, requests_complete_answer, has_self_attempt_evidence} (bool)

사용 예:
  python scripts/01_join_studychat.py \
      --studychat data/raw/data.jsonl \
      --labels-dir ../ThinkGuard_label \
      --out-dir data/joined
"""
import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

SPLITS = {"train": "train_ok.csv", "valid": "valid_ok.csv", "test": "test_ok.csv"}
LABEL_COLS = ("is_learning_context", "requests_complete_answer", "has_self_attempt_evidence")


def to_bool(v):
    v = str(v).strip().lower()
    if v in ("true", "1", "yes"):
        return True
    if v in ("false", "0", "no"):
        return False
    raise ValueError(f"bool로 해석할 수 없는 값: {v!r}")


def content_text(content):
    """messages[].content 가 문자열 또는 [{type:text,text:...}] 리스트인 경우 모두 처리."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for p in content:
            if isinstance(p, dict):
                if p.get("type") == "text" or "text" in p:
                    parts.append(str(p.get("text", "")))
                else:
                    parts.append(f"[{p.get('type', 'non-text')} 입력 생략]")
            else:
                parts.append(str(p))
        return "\n".join(parts)
    return str(content)


def truncate(text, max_chars):
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    head = int(max_chars * 0.7)
    tail = max_chars - head
    return text[:head] + "\n...[중략]...\n" + text[-tail:]


def build_turn(rec, history_msgs, max_chars):
    """StudyChat 한 행에서 (message, history, 검사 플래그)를 만든다."""
    msgs = [m for m in rec.get("messages") or [] if m.get("role") in ("user", "assistant")]
    prompt = content_text(rec.get("prompt"))
    last_is_prompt = bool(msgs) and msgs[-1]["role"] == "user" and \
        content_text(msgs[-1].get("content")).strip() == prompt.strip()
    if last_is_prompt:
        msgs = msgs[:-1]
    history = [
        {"role": "student" if m["role"] == "user" else "assistant",
         "text": truncate(content_text(m.get("content")), max_chars)}
        for m in msgs
    ]
    if history_msgs > 0:
        history = history[-history_msgs:]
    return prompt, history, last_is_prompt


def read_labels(labels_dir):
    rows = {}
    for split, fname in SPLITS.items():
        with open(Path(labels_dir) / fname, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if r.get("status", "ok") != "ok":
                    continue
                chat_id, turn = r["source_id"].rsplit(":", 1)
                rows[r["source_id"]] = dict(
                    split=split, chat_id=chat_id, turn=int(turn), student_id=r["student_id"],
                    labels={c: to_bool(r[c]) for c in LABEL_COLS},
                )
    return rows


def iter_jsonl(paths):
    for p in paths:
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--studychat", nargs="+", required=True, help="StudyChat data.jsonl (여러 개 가능)")
    ap.add_argument("--labels-dir", required=True, help="train_ok.csv / valid_ok.csv / test_ok.csv 폴더")
    ap.add_argument("--out-dir", default="data/joined")
    ap.add_argument("--history-msgs", type=int, default=4, help="보관할 이전 메시지 수 (0=전부)")
    ap.add_argument("--max-chars", type=int, default=800, help="이전 메시지 1개당 최대 글자 수 (0=무제한)")
    ap.add_argument("--turn-offset", type=int, default=0,
                    help="라벨 turn + offset = StudyChat interactionCount 로 매칭 (기본 0)")
    args = ap.parse_args()

    labels = read_labels(args.labels_dir)
    need_chats = {v["chat_id"] for v in labels.values()}
    print(f"라벨 {len(labels)}행 / 대화 {len(need_chats)}개 로드")

    # 라벨에 등장하는 대화의 모든 interaction을 메모리에 (필요한 필드만)
    by_chat = defaultdict(dict)
    dup = 0
    for rec in iter_jsonl(args.studychat):
        cid = rec.get("chatId")
        if cid not in need_chats:
            continue
        ic = int(rec.get("interactionCount", -1))
        if ic in by_chat[cid]:
            dup += 1
            continue
        message, history, last_ok = build_turn(rec, args.history_msgs, args.max_chars)
        by_chat[cid][ic] = dict(message=message, history=history, last_ok=last_ok,
                                user_id=rec.get("userId"), topic=rec.get("topic"),
                                semester=rec.get("semester"))

    # offset 진단: 어떤 offset이 가장 잘 맞는지
    offset_rate = {}
    for off in (-1, 0, 1):
        hit = sum((v["turn"] + off) in by_chat.get(v["chat_id"], {}) for v in labels.values())
        offset_rate[off] = hit / len(labels)
    print("turn offset별 매칭률:", {k: f"{v:.1%}" for k, v in offset_rate.items()})
    best = max(offset_rate, key=offset_rate.get)
    if best != args.turn_offset and offset_rate[best] > offset_rate[args.turn_offset] + 0.05:
        print(f"[경고] --turn-offset {best} 가 더 잘 맞습니다. 확인 후 다시 실행하세요.")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stats = defaultdict(Counter)
    outputs = defaultdict(list)
    for sid, v in labels.items():
        st = stats[v["split"]]
        st["labels"] += 1
        row = by_chat.get(v["chat_id"], {}).get(v["turn"] + args.turn_offset)
        if row is None:
            st["missing"] += 1
            continue
        st["matched"] += 1
        if row["user_id"] != v["student_id"]:
            st["student_id_mismatch"] += 1
        if not row["last_ok"]:
            st["prompt_not_last_message"] += 1
        if not row["message"].strip():
            st["empty_message"] += 1
        outputs[v["split"]].append(dict(
            id=sid, split=v["split"], student_id=v["student_id"], conversation_id=v["chat_id"],
            turn=v["turn"], topic=row["topic"], semester=row["semester"], lang="en",
            message=row["message"], history=row["history"], labels=v["labels"],
        ))

    for split, rows in outputs.items():
        rows.sort(key=lambda r: (r["conversation_id"], r["turn"]))
        with open(out_dir / f"{split}.jsonl", "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    report = dict(turn_offset=args.turn_offset, offset_match_rate=offset_rate,
                  duplicate_studychat_keys=dup, history_msgs=args.history_msgs,
                  max_chars=args.max_chars, splits={k: dict(v) for k, v in stats.items()})
    (out_dir / "join_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for split in SPLITS:
        s = stats[split]
        print(f"{split:5s}: 라벨 {s['labels']} / 매칭 {s['matched']} / 누락 {s['missing']} / "
              f"학생ID 불일치 {s['student_id_mismatch']} / prompt≠마지막메시지 {s['prompt_not_last_message']}")

    # 눈으로 확인할 샘플
    pool = outputs.get("train", [])
    random.Random(0).shuffle(pool)
    print("\n=== 라벨과 발화가 맞는지 눈으로 확인하세요 (train 무작위 5개) ===")
    for r in pool[:5]:
        print(f"\n[{r['id']}] {r['labels']}")
        if r["history"]:
            print(f"  (직전 {r['history'][-1]['role']}) {r['history'][-1]['text'][:200]!r}")
        print(f"  학생: {r['message'][:400]!r}")
    print(f"\n저장: {out_dir}/")


if __name__ == "__main__":
    main()
