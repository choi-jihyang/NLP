"""판단 보조 규칙 — 판단 모델 결과에 OR로 더한다 (classify()가 마지막에 apply_rules를 거친다).

한국어평가셋1(설계용)만 보고 만들고 고정했다. 셋2 · 3(검증용 125행) 결과:
시도 P/R 0.67/0.07 → 0.89/0.53, 답요청 R 0.71 → 0.85 (ThinkGuard_model/results/ko_eval).
규칙을 고칠 때는 새 문장으로 다시 검증한다(검증용 셋에 맞춰 고치지 않는다).

원칙
- 학생이 쓴 글(이번 메시지 + history의 학생 턴)만 본다. AI 답변은 근거가 아니다 (불변식 I4).
- "해봤는데 안 돼요" 같은 주장만으로는 시도가 아니다. 코드 · 로그 · 구체적 값이 함께 있어야 한다.
- 규칙은 붙인 코드가 학생이 쓴 것인지 구분하지 못한다. 그래서 NEXT_STEP 지시의 완성 코드 금지와
  누출 검사(leak.py)를 함께 둔다.
"""

import re
from typing import Any

# ---- 시도 근거 ---------------------------------------------------------------
_CODE_LINE = re.compile(
    r"(;\s*$|[{}]\s*$|^\s*(#include|int |void |char |long |double |def |class |public |private |return\b|"
    r"for\s*\(|while\s*\(|if\s*\(|else\b|MOV|ADD|SUB|LDR|STR|CMP|B[A-Z]{0,2}\s|import |from \w+ import))",
    re.M,
)
_LOG = re.compile(
    r"(error\s*:|Error|Exception|Traceback|Segmentation|SIGSEGV|segfault|warning\s*:|"
    r"런타임\s*에러|시간\s*초과|무한\s*루프|입력\s*:|출력\s*:|Epoch\s*\d|loss\s*[:=])",
    re.I,
)
_DID = re.compile(
    r"(했더니|했는데|하니까|하니|해봤는데|해 봤는데|돌렸더니|돌려봤|돌려 봤|바꿨는데|바꾸니|바꿔서|"
    r"넣었더니|넣으니|넣고|넣었는데|까지\s*했|만들었는데|짰는데|구했는데|풀었는데|검사했더니|처리하려고)"
)
"""해 본 행동 표현"""
_CONCRETE = re.compile(r"([A-Za-z_][\w.\[\]]*\s*[%=+\-*/<>!]=?|\w+\(|\w+\[|[A-Za-z]{3,}|\d)")
"""행동 표현 앞에 있으면 구체적 흔적으로 보는 것: 코드 토큰, 영어 기술 용어, 숫자"""
_DID_WINDOW = 40

# ---- 완성 답 요청 -------------------------------------------------------------
_NOT_REQUEST = re.compile(r"(답\s*말고|정답\s*말고|힌트만|답은\s*내가|직접\s*(해|풀)|어디부터\s*틀린)")
_REQUEST = re.compile(
    r"(전체\s*(코드|함수|풀이)|코드\s*전체|전부\s*(수정|작성)|완성본|완성\s*코드|정답\s*코드|답\s*코드|최종\s*답|답만|"
    r"(코드|풀이|답|정답)\s*(을|를|이랑|랑|좀|만)?\s*(줘|주라|주세요|줄래|알려|보여|적어|써\s*줘|짜)|"
    r"(구현|작성|풀어|짜|채워)\s*(줘|주라|주세요|줄래|줄 수|봐|하여라|하시오)|"
    r"그냥\s*\S{0,6}\s*(줘|알려|보여))"
)


def apply_rules(message: str, history: list[dict[str, str]], result: dict[str, Any]) -> dict[str, Any]:
    """판단 결과에 규칙을 OR로 더한 새 dict를 돌려준다.

    학습 맥락일 때만 requests_complete_answer · has_self_attempt_evidence를 false → true로 바꾼다.
    is_learning_context · uncertain · confidence는 그대로 둔다.
    """
    out = dict(result)
    if not out.get("is_learning_context"):
        return out
    if not out.get("requests_complete_answer") and request_rule(message, history):
        out["requests_complete_answer"] = True
    if not out.get("has_self_attempt_evidence") and attempt_rule(message, history):
        out["has_self_attempt_evidence"] = True
    return out


def attempt_rule(message: str, history: list[dict[str, str]]) -> str | None:
    """구체적 시도 흔적이 있으면 이유 문자열, 없으면 None."""
    for i, text in enumerate(_student_texts(message, history)):
        where = "msg" if i == 0 else "hist"
        if len(_CODE_LINE.findall(text)) >= 2 or "```" in text:
            return f"{where}:code"
        if _LOG.search(text):
            return f"{where}:log"
        for m in _DID.finditer(text):
            # 행동 표현 앞 40자 안에 구체적 흔적이 있어야 한다 ("몇번이나 해봤는데"는 제외)
            if _CONCRETE.search(text[max(0, m.start() - _DID_WINDOW):m.start()]):
                return f"{where}:did+concrete"
    return None


def request_rule(message: str, history: list[dict[str, str]]) -> str | None:
    """완성 답 요청 문구가 있으면 걸린 문구, 없으면 None. 이번 메시지만 본다."""
    if _NOT_REQUEST.search(message):
        return None
    m = _REQUEST.search(message)
    return m.group(0) if m else None


def _student_texts(message: str, history: list[dict[str, str]]) -> list[str]:
    return [message] + [t["content"] for t in history if t.get("role") == "student"]
