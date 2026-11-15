"""학생 메시지 분류기 — NLP 팀 구현 위치.

백엔드는 CLASSIFIER=module 일 때 이 파일의 classify()를 직접 import 하고,
CLASSIFIER=http 일 때 nlp/server.py 의 POST /classify 를 호출한다.
입출력 형식은 docs/spec/integration-contract.md 와 반드시 같아야 한다.
"""

from typing import Any


def classify(message: str, history: list[dict[str, str]]) -> dict[str, Any]:
    """학생의 새 메시지와 이전 대화를 받아 분류 결과를 돌려준다.

    Args:
        message: 학생이 방금 보낸 메시지
        history: 이전 대화, 오래된 순. 각 항목은 {"role": "student" | "assistant", "content": str}

    Returns:
        {
            "is_learning_context": bool,
            "requests_complete_answer": bool,
            "has_self_attempt_evidence": bool,
            "uncertain": bool,
            "confidence": float,  # 0.0 ~ 1.0
        }
    """
    # TODO(NLP 팀): 모델 구현으로 교체. 지금은 항상 "모호함"을 돌려준다.
    return {
        "is_learning_context": True,
        "requests_complete_answer": False,
        "has_self_attempt_evidence": False,
        "uncertain": True,
        "confidence": 0.0,
    }
