"""보수적인 전체 데이터 약한 주석 규칙. 의미 검토·사람 정답을 대체하지 않는다."""

import re

VERSION = "0.2"


def match(pattern: str, text: str) -> re.Match | None:
    return re.search(pattern, text, re.I | re.S)


def annotate(message: str, history: list[dict]) -> dict:
    text = message.strip()
    prose = re.sub(r"```.*?```", " ", text, flags=re.S)
    social = bool(
        re.fullmatch(
            r"(?:hi|hello|hey|thanks|thank you|good evening|good morning|bye|안녕(?:하세요)?|감사합니다)[!.?\s]*",
            text,
            re.I,
        )
    )
    technical = bool(
        match(
            r"\b(python|pandas|numpy|torch|sklearn|code|function|dataset|essay|paragraph|sentence|"
            r"grammar|writing|learned|lecture|assignment|homework|model|regression|probability|"
            r"algorithm|tensor|dataframe|git|citation|conclusion|introduction|noun|verb|"
            r"mathematics|equation|derivative|proof|data|training|accuracy|loss|class|def)\b"
            r"|과제|문제|풀이|코드|문단|문법|배웠|학습|수업|방정식",
            text,
        )
    )
    learning = False if social else (True if technical else None)
    reasons = {
        "is_learning_context": "R02: 인사"
        if social
        else ("R02: 학습·기술 표현 감지; 문맥 오탐 가능" if technical else "R10: 규칙만으로 맥락 확정 불가")
    }
    explicit = match(
        r"(?:give|provide|tell|show)\s+(?:me\s+)?(?:the\s+)?(?:final\s+|correct\s+)?answer\b"
        r"|(?:write|generate)\s+(?:a |the |my |this )?(?:complete |full |final )?"
        r"(?:paragraph|essay|report|solution)\b"
        r"|(?:finish|complete|fill in)\s+(?:the |my |this )?(?:missing |entire |full )?"
        r"(?:code|function|implementation|parts)\b"
        r"|정답\s*(?:만\s*)?(?:알려|줘)|대신\s*(?:써|풀어|작성)|완성\s*코드",
        prose,
    )
    negated = bool(match(r"\b(?:do not|don't|never|without)\b|정답.*(?:말고|주지|금지)", prose))
    examples = bool(match(r"\b(example|sample|for instance)\b|예시|예문", prose))
    feedback = bool(
        match(
            r"\b(explain|what is|what are|why|meaning|feedback|verify|check|review|"
            r"grammatical|grammar|hint)\b|설명|힌트|검토|피드백|무슨\s*뜻",
            prose,
        )
    )
    if social:
        complete = False
    elif explicit and not negated and not examples:
        complete = True
    elif explicit:
        complete = None
    elif feedback and not match(r"\b(write|generate|finish|complete|answer)\b", prose):
        complete = False
    else:
        complete = None
    reasons["requests_complete_answer"] = (
        "R03: 명시적 완성 요청 패턴; 인용·과제 경계는 추가 검토"
        if complete is True
        else "R04: 인사 또는 설명·검토 패턴"
        if complete is False
        else "R05/R10: 요청 범위·부정·예시·혼합 의도를 규칙으로 확정 못함"
    )
    observed = match(
        r"Traceback \(most recent call last\)|\b(?:ValueError|TypeError|KeyError|"
        r"AttributeError|RuntimeError|SyntaxError|FileNotFoundError):[^\n]*"
        r"|(?:I (?:get|got|am getting)|this (?:line|code) (?:doesn't|does not))[^\n]{0,180}"
        r"|(?:실행했더니|실행하면|이 줄이)[^\n]{0,100}(?:오류|에러|작동하지)",
        text,
    )
    ai_repeat = observed and any(observed.group() in turn["content"] for turn in history if turn["role"] == "assistant")
    code = bool(match(r"\b(?:def |for |return |import |class )|```|<essay>|<para>|\w+\s*=", text))
    if observed and not ai_repeat:
        current = True
        reason = "R06: 학생 발화에 실행 실패 보고; 예시 인용 여부 사람 확인 필요"
    elif code or observed:
        current = None
        reason = "R07/R08: 코드·글 출처 또는 AI 출력 재제시 여부 확인 필요"
    else:
        current = False
        reason = "R07: 현재 발화에서 규칙이 인식한 수행 근거 없음; 의미 기반 누락 가능"
    evidence = []
    if current is True:
        # Match on stripped text, then convert offsets back to original message.
        offset = len(message) - len(message.lstrip())
        evidence.append(
            {
                "role": "student",
                "location": "message",
                "start": offset + observed.start(),
                "end": offset + observed.end(),
                "text": observed.group(),
            }
        )
    prior_students = [t for t in history if t["role"] == "student"]
    # Never carry evidence across an unverified question boundary as a positive.
    cumulative = current if current is True or not prior_students else None
    reasons["has_self_attempt_evidence"] = (
        reason if cumulative is not None else ("R08: 이전 학생 발화 존재; 같은 문항 경계·근거 누적을 의미 검토해야 함")
    )
    labels = {
        "is_learning_context": learning,
        "requests_complete_answer": complete,
        "has_self_attempt_evidence": cumulative,
    }
    labels["uncertain"] = any(value is None for value in labels.values())
    missing = bool(match(r"\b(?:above|earlier|previous|this|these|it)\b|앞에서|이전|위의", prose)) and not history
    return {
        "labels": labels,
        "attempt_current": current,
        "evidence": evidence,
        "rationale_by_label": reasons,
        "context_missing": missing,
        "history_boundary_verified": not prior_students,
    }
