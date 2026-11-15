# 학습 AI 채팅 정책

> 상태: **분류 → 정책 → 프롬프트 합성 구현됨**(`services/policy.py`, `services/chat_service.py`, 테스트 있음).
> 채팅 API·대화 저장·사용량 상한·AI 설정 → 프롬프트 변환은 **미구현**.
> 관련: [integration-contract.md](integration-contract.md) · 불변식 [../conventions/ai-code-trust.md](../conventions/ai-code-trust.md)

## 처리 순서
```
1. 사용량 확인        상한 도달 → USAGE_LIMIT 안내, LLM 호출 안 함     (미구현)
2. 분류              classifier.classify(message, history)
3. 정책 결정          policy.decide(결과, min_confidence)
4. 고정 응답이면 바로 반환 (LLM 호출 안 함)
5. 시스템 프롬프트 = AI 설정 프롬프트 + 고정 규칙 + 이번 응답 정책 지시
6. llm.generate(시스템 프롬프트, history + message)
7. 저장 후 응답                                                      (미구현)
```

## 정책 분기 (우선순위 위에서부터)
| 순서 | 조건 | 모드 | 동작 |
|---|---|---|---|
| 1 | `uncertain` 또는 `confidence < 0.5` | `ASK_ATTEMPT` | LLM 없이 "이미 시도한 부분이 있나요? …" |
| 2 | `is_learning_context = false` | `OFF_TOPIC` | LLM 없이 "과제와 관련된 질문에만 도움을 줄 수 있어요 …" |
| 3 | `requests_complete_answer` 이고 `has_self_attempt_evidence = false` | `HINT_ONLY` | LLM 호출 + "정답·완성 코드 금지, 힌트 하나만" 지시 |
| 4 | 그 외 | `NEXT_STEP` | LLM 호출 + "학생이 보여 준 풀이까지만 근거로 다음 한 단계" 지시 |

- 완성 답안을 요청했더라도 시도 근거가 있으면 4번(다음 단계)으로 간다. 정답을 주는 것은 아니다.
- `0.5`는 `CLASSIFIER_MIN_CONFIDENCE`로 바꿀 수 있다.

## 고정 규칙 (모든 LLM 호출에 포함)
`services/prompt_builder.py`의 `FIXED_RULES`:
- 학생이 스스로 풀도록 돕는 학습 도우미다.
- 정답·최종 값·완성 풀이·완성 코드를 직접 주지 않는다.
- **학생이 하지 않은 시도나 생각을 지어내지 않는다.** "앞에서 ~까지 했으니"는 학생이 실제로 쓴 내용일 때만.
- 존댓말, 3문장 이내.

## AI 설정 → 프롬프트 (미구현, M2)
| 설정 | 프롬프트에 들어갈 내용 |
|---|---|
| 과목 유형 = 수학 | 한 단계씩만 안내하고, 다음 단계는 학생이 먼저 예측해 말하게 유도 |
| 과목 유형 = 프로그래밍 | 전체 코드 금지. 흐름(의사코드·단계) 설명과 빈칸 채우기(`____`) 형태로만 코드 제시 |
| 과목 유형 = 글쓰기 · 개념 학습 | 정책 문구 정의 필요 |
| 힌트 제공 = 끔 | 힌트·풀이 단계를 주지 않고 교재·개념 복습을 권유 |
| 최대 힌트 단계 = n | n단계까지만 공개, 마지막 계산·작성은 학생 몫 |

## 수용 기준
1. 분류 결과가 같으면 정책 결과도 항상 같다(LLM 결과와 무관).
2. `ASK_ATTEMPT`·`OFF_TOPIC`·`USAGE_LIMIT`에서는 LLM이 호출되지 않는다.
3. LLM에 가는 시스템 프롬프트에 고정 규칙이 항상 들어간다.
4. LLM에 가는 메시지 순서는 `history`(오래된 순) 다음 새 메시지.

## 테스트
| 파일 | 다루는 것 |
|---|---|
| `backend/tests/test_policy.py` | 분기 4종, 우선순위, confidence 경계값 |
| `backend/tests/test_chat_service.py` | LLM 호출 여부, 시스템 프롬프트 구성, 메시지 순서 |
| `backend/tests/test_classifier_stub.py` | 키워드 스텁 분류 결과, 시도 근거는 학생 메시지에서만 |
