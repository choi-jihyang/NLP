"""학생 메시지 분류기 — bge-m3 판단 모델.

백엔드는 CLASSIFIER=module 일 때 이 파일의 classify()를 직접 import 하고,
CLASSIFIER=http 일 때 nlp/server.py 의 POST /classify 를 호출한다.
입출력 형식은 docs/spec/integration-contract.md 와 반드시 같아야 한다.

모델 위치: 환경변수 THINKGUARD_MODEL_DIR, 없으면 nlp/models/bge_m3_en_ko/
모델은 import 할 때 한 번만 불러온다(요청마다 로딩하지 않음). 모델이 없으면 import 가 실패한다.
"""

import os
from pathlib import Path
from typing import Any

from thinkguard_nlp.model import Judge

DEFAULT_MODEL_DIR = Path(__file__).resolve().parent.parent / "models" / "bge_m3_en_ko"

_judge = Judge(os.environ.get("THINKGUARD_MODEL_DIR", DEFAULT_MODEL_DIR))


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
    return _judge.classify(message, history)
