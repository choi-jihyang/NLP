"""키워드 규칙 기반 임시 분류기. NLP 팀 모델이 들어오기 전까지 사용한다."""

import re

from app.classifier.base import ClassificationResult, Classifier
from app.schemas.chat import ChatTurn

_PLEASE = r"(줘|주세요|주실래요|줄래|주시겠어요|달라)"
"""반말 · 존댓말 요청 어미 (예: 짜줘 · 짜주세요)"""
_ANSWER_REQUEST = re.compile(
    r"정답|답\s*(만|좀|을)?\s*(빨리\s*)?(알려|" + _PLEASE + r")|풀어\s*" + _PLEASE
    + r"|전체\s*풀이|다\s*풀어|그냥\s*알려"
    r"|대신\s*(써|풀어|짜)|써\s*" + _PLEASE + r"|(전체|완성된?)\s*코드|코드\s*(전체|전부|통째로)"
    r"|코드\s*(다\s*)?(짜|작성해)\s*" + _PLEASE
)
_HELP_REQUEST = re.compile(r"힌트|어떻게\s*시작|모르겠|막혔|다음\s*(엔|단계)|뭘\s*해야|뭐야|뭔가요|의미|무슨\s*뜻|왜")
_ATTEMPT = re.compile(
    r"=|±|√"
    r"|\d\s*(이|가|랑|과)?\s*(나왔|나와|구했)"
    r"|했는데|까지\s*했|넣었더니|나눠서|구해\s*보니|풀어\s*봤|해\s*봤|짜\s*봤|작성해\s*봤"
    r"|\bdef\s|\bfor\s|\bwhile\s|\breturn\b|[{};]"
)
_OFF_TOPIC = re.compile(r"날씨|게임|연애|맛집|노래\s*추천|영화\s*추천")


class KeywordStubClassifier(Classifier):
    async def classify(self, message: str, history: list[ChatTurn]) -> ClassificationResult:
        wants_answer = bool(_ANSWER_REQUEST.search(message))
        wants_help = bool(_HELP_REQUEST.search(message))
        # 이전에 학생이 보낸 메시지에 시도 흔적이 있어도 근거로 인정
        student_texts = [message] + [t.content for t in history if t.role == "student"]
        attempted = any(_ATTEMPT.search(t) for t in student_texts)
        off_topic = bool(_OFF_TOPIC.search(message))

        matched = wants_answer or wants_help or attempted or off_topic
        return ClassificationResult(
            is_learning_context=not off_topic,
            requests_complete_answer=wants_answer,
            has_self_attempt_evidence=attempted,
            uncertain=not matched,
            confidence=0.6 if matched else 0.3,
        )
