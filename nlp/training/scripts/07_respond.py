"""7단계: 판단 모델 → 정책 → 힌트 생성 LLM 으로 실제 응답을 만든다.

LLM 은 OpenAI 호환 서버면 무엇이든 된다 (vLLM, Ollama 등). 기본값은 로컬 Ollama.
  Qwen3 : --llm-model qwen3:8b            (생각 모드는 자동으로 끔)
  EXAONE: --llm-model exaone3.5:7.8b

사용 예:
  # 프롬프트만 확인 (모델·LLM 없이, 라벨 직접 지정: learning,request,attempt)
  python scripts/07_respond.py --labels 1,1,0 --message "BFS 코드 전체 짜줘" --dry-run
  # 대화형 데모 (판단 모델 + LLM)
  python scripts/07_respond.py --model-dir results/bge_m3/en_ko_full/best_model --interactive
  # 생성 품질 비교용 일괄 생성 (정답 라벨로 모드를 정해 생성기만 평가) → CSV 로 사람이 검토
  python scripts/07_respond.py --batch data/ko/test.jsonl --use-gold --sample 40 --llm-model qwen3:8b --out results/gen/qwen3.csv
"""
import argparse
import csv
import json
import random
import sys
from pathlib import Path

from common import LABELS, SHORT
from policy import (
    FEEDBACK,
    NUDGE,
    RETRY_REMINDER,
    PolicyConfig,
    build_messages,
    clean_response,
    decide,
    leak_flags,
    strip_long_code,
)


class Responder:
    def __init__(self, args):
        self.args = args
        self.cfg = PolicyConfig(first_hint=not args.no_first_hint, final_answer=args.final_answer)
        self.judge = None
        if args.model_dir:
            from judge import Judge
            th = None
            if args.thresholds_file:
                d = json.loads(Path(args.thresholds_file).read_text(encoding="utf-8"))["thresholds"]
                th = [d[l] for l in LABELS] if isinstance(d, dict) else d
            self.judge = Judge(args.model_dir, thresholds=th)
        self.client = None
        if not args.dry_run:
            from openai import OpenAI
            self.client = OpenAI(base_url=args.base_url, api_key=args.api_key)
        self.qwen3 = "qwen3" in args.llm_model.lower()

    def labels_for(self, message, history, gold=None):
        if gold is not None:
            return dict(gold), None
        if self.args.labels:
            vals = [v.strip() in ("1", "t", "true", "T") for v in self.args.labels.split(",")]
            return dict(zip(LABELS, vals)), None
        if self.judge is None:
            sys.exit("--model-dir 또는 --labels 가 필요하다.")
        out = self.judge.judge(message, history)
        return out["labels"], out["probs"]

    def generate(self, messages):
        if self.args.dry_run:
            return ""
        # Qwen3 생각 모드 끄기: vLLM 은 chat_template_kwargs, Ollama 는 reasoning_effort="none"
        # (생각을 켜 두면 생각에 max_tokens 를 다 써서 빈 응답이 나온다)
        kw = {}
        if self.qwen3:
            kw = ({"extra_body": {"chat_template_kwargs": {"enable_thinking": False}}} if self.args.vllm
                  else {"reasoning_effort": "none"})
        resp = self.client.chat.completions.create(
            model=self.args.llm_model, messages=messages, temperature=self.args.temperature,
            max_tokens=self.args.max_tokens, **kw)
        if resp.choices[0].finish_reason == "length":
            print(f"  (max_tokens {self.args.max_tokens} 에서 잘림)", file=sys.stderr)
        return clean_response(resp.choices[0].message.content)

    def respond(self, message, history=(), hint_level=1, gold=None):
        labels, probs = self.labels_for(message, history, gold)
        mode = decide(labels)
        messages = build_messages(message, history, mode, self.cfg, hint_level,
                                  has_attempt=labels["has_self_attempt_evidence"])
        text = self.generate(messages)
        flags = leak_flags(mode, text, self.cfg)
        guard = ""
        if flags and not self.args.dry_run:  # 1) 규칙을 상기시켜 한 번 다시 생성
            retry = messages[:-1] + [{"role": "user", "content": messages[-1]["content"] + "\n\n" + RETRY_REMINDER}]
            text2 = self.generate(retry)
            flags2 = leak_flags(mode, text2, self.cfg)
            guard = "retried"
            if flags2:  # 2) 그래도 긴 코드가 있으면 코드 블록을 지운다
                text2, guard = strip_long_code(text2), "retried+stripped"
            text = text2
        return dict(mode=mode, labels=labels, probs=probs, hint_level=hint_level, messages=messages,
                    response=text, leak_flags=flags, guard=guard)


def show(out, verbose):
    probs = out["probs"]
    p = f" | 확률 {', '.join(f'{SHORT[l]}={v:.2f}' for l, v in probs.items())}" if probs else ""
    print(f"\n[판단] 모드={out['mode']} 힌트단계={out['hint_level']}{p}")
    if verbose or not out["response"]:
        print("----- system prompt -----\n" + out["messages"][0]["content"] + "\n-------------------------")
    if out["response"]:
        print(f"\nThinkGuard> {out['response']}")
    if out["leak_flags"]:
        print(f"  ⚠ 첫 생성에서 정답 누출 의심: {', '.join(out['leak_flags'])} → 처리: {out['guard'] or '없음'}")


def interactive(r):
    history, nudges = [], 0
    print("대화형 모드. 빈 줄 입력 시 종료, /reset 으로 대화 초기화.")
    while True:
        try:
            msg = input("\n학생> ").strip()
        except EOFError:
            break
        if not msg:
            break
        if msg == "/reset":
            history, nudges = [], 0
            continue
        out = r.respond(msg, history[-r.args.history_msgs:], hint_level=nudges + 1)
        show(out, r.args.verbose)
        # 같은 문제에서 시도 없이 계속 요청하면 힌트를 한 단계씩 구체화, 시도를 보이면 초기화
        nudges = nudges + 1 if out["mode"] == NUDGE else (0 if out["mode"] == FEEDBACK else nudges)
        history += [{"role": "student", "text": msg}, {"role": "assistant", "text": out["response"] or "(생략)"}]


def batch(r, args):
    rows = [json.loads(l) for l in open(args.batch, encoding="utf-8") if l.strip()]
    rows = [x for x in rows if x.get("translation_ok", True)]
    if args.sample:
        rng = random.Random(args.seed)
        # 모드별로 고르게 뽑는다 (nudge/feedback 이 핵심)
        by = {}
        for x in rows:
            by.setdefault(decide(x["labels"]), []).append(x)
        quota = {"nudge": 0.35, "feedback": 0.35, "explain": 0.2, "off_topic": 0.1}
        picked = []
        for m, xs in by.items():
            picked += rng.sample(xs, min(len(xs), max(1, round(args.sample * quota.get(m, 0.1)))))
        rows = picked
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["id", "lang", "gold_mode", "mode", "leak_flags", "guard", "message", "response",
              "정답누출(O/X)", "적절성(1-5)", "메모"]
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i, x in enumerate(rows, 1):
            hist = x.get("history", [])[-args.history_msgs:]
            out = r.respond(x["message"], hist, gold=x["labels"] if args.use_gold else None)
            w.writerow({"id": x["id"], "lang": x.get("lang", "en"), "gold_mode": decide(x["labels"]),
                        "mode": out["mode"], "leak_flags": ";".join(out["leak_flags"]), "guard": out["guard"],
                        "message": x["message"][:2000], "response": out["response"]})
            f.flush()
            print(f"  {i}/{len(rows)} {x['id']} {out['mode']}{' ⚠' + ','.join(out['leak_flags']) + ' → ' + out['guard'] if out['leak_flags'] else ''}")
    print(f"저장: {out_path} — '정답누출', '적절성' 열을 채워서 모델끼리 비교한다.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model-dir", help="판단 모델 best_model 폴더")
    ap.add_argument("--thresholds-file", help="06_tune_policy.py 가 만든 policy_thresholds.json (없으면 thinkguard.json)")
    ap.add_argument("--labels", help="판단 모델 대신 직접 지정: learning,request,attempt (예: 1,1,0)")
    ap.add_argument("--message")
    ap.add_argument("--history-file", help='[{"role": "student"|"assistant", "text": ...}] JSON')
    ap.add_argument("--interactive", action="store_true")
    ap.add_argument("--batch", help="jsonl (data/*/test.jsonl 형식)")
    ap.add_argument("--use-gold", action="store_true", help="batch 에서 정답 라벨로 모드 결정 (생성기만 평가)")
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "results/gen/responses.csv"))
    ap.add_argument("--history-msgs", type=int, default=4)
    ap.add_argument("--no-first-hint", action="store_true", help="nudge 모드에서 첫 힌트 없이 확인 질문만")
    ap.add_argument("--final-answer", default="never", choices=["never", "after_attempt"])
    ap.add_argument("--hint-level", type=int, default=1)
    ap.add_argument("--base-url", default="http://localhost:11434/v1")
    ap.add_argument("--api-key", default="EMPTY")
    ap.add_argument("--llm-model", default="qwen3:8b")
    ap.add_argument("--vllm", action="store_true", help="vLLM 서버일 때 (Qwen3 생각 끄기를 chat_template_kwargs 로)")
    ap.add_argument("--temperature", type=float, default=0.3)
    ap.add_argument("--max-tokens", type=int, default=800)
    ap.add_argument("--dry-run", action="store_true", help="LLM 호출 없이 판단 결과와 프롬프트만 출력")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    r = Responder(args)
    if args.interactive:
        interactive(r)
    elif args.batch:
        batch(r, args)
    elif args.message:
        hist = json.loads(Path(args.history_file).read_text(encoding="utf-8")) if args.history_file else []
        show(r.respond(args.message, hist, hint_level=args.hint_level), args.verbose)
    else:
        ap.error("--message, --interactive, --batch 중 하나가 필요하다.")


if __name__ == "__main__":
    main()
