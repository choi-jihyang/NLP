# 연동 계약 (분류기 · LLM Provider)

> 상태: **분류기 계약 확정 · 구현됨(스텁)**, **LLM 모델 선택은 제안 — 팀 확인 필요**.
> 바꿀 때는 웹 1명 + NLP 1명 승인 필요([../conventions/pr-convention.md](../conventions/pr-convention.md)).

## 핵심 원칙: 계약 + Mock → 나중에 실제로 교체
- 연동 지점마다 **인터페이스(계약)** 를 먼저 정하고, Mock 구현으로 전 기능을 만든다.
- 실제 구현은 **환경변수만 바꿔** 교체한다. 백엔드 코드를 다시 쓰지 않는다.
- 웹 팀은 Mock으로 끝까지 만들고, NLP 팀은 같은 계약으로 모델을 준비한다. 서로 기다리지 않는다.

```
backend/app/
  classifier/                     CLASSIFIER=
    base.py        Classifier      ← 인터페이스
    keyword_stub.py                  stub   (기본, 키워드 규칙)
    module.py                        module (nlp 패키지 함수 직접 호출)
    http.py                          http   (NLP 팀 FastAPI 호출)
  llm/                            LLM_PROVIDER=
    base.py        LLMProvider     ← 인터페이스
    mock.py                          mock   (기본, 고정 응답)
    ollama.py                        ollama (로컬 Ollama 서버)
```

---

## 1. 분류기

### 입력
| 필드 | 타입 | 설명 |
|---|---|---|
| `message` | string | 학생이 방금 보낸 메시지 |
| `history` | `{role, content}[]` | 같은 문항의 이전 대화, **오래된 순**. `role`은 `"student"` 또는 `"assistant"` |

### 출력
| 필드 | 타입 | 의미 |
|---|---|---|
| `is_learning_context` | bool | 과제·학습과 관련된 대화인가 |
| `requests_complete_answer` | bool | 정답·전체 풀이·완성 코드를 통째로 요구하는가 |
| `has_self_attempt_evidence` | bool | 학생이 직접 시도한 흔적(식, 중간 결과, 작성한 코드)이 **학생 메시지**에 있는가 |
| `uncertain` | bool | 분류기 스스로 판단이 모호하다고 보는가 |
| `confidence` | float 0.0–1.0 | 판단 전체에 대한 확신도 (**하나의 값**) |

- `has_self_attempt_evidence`는 `history` 중 `role="student"` 메시지만 근거로 삼는다. AI의 이전 답변에 식이 있어도 근거가 아니다(불변식 I4).
- 백엔드는 `uncertain=true` **또는** `confidence < CLASSIFIER_MIN_CONFIDENCE`(기본 0.5)면 "모호함"으로 처리한다. → [chat-policy.md](chat-policy.md)
- 출력 필드가 빠지거나 타입이 다르면 백엔드가 Pydantic 검증 오류를 낸다.

### 예시
```json
// 요청
{ "message": "이제 정답 알려줘",
  "history": [{ "role": "student", "content": "D=b²−4ac 에 넣어서 16−4k 까지 했어요" },
              { "role": "assistant", "content": "좋아요. 중근이 되려면 D가 얼마여야 할까요?" }] }
// 응답
{ "is_learning_context": true, "requests_complete_answer": true,
  "has_self_attempt_evidence": true, "uncertain": false, "confidence": 0.82 }
```

### 방식 A — Python 모듈 (`CLASSIFIER=module`)
1. NLP 팀은 `nlp/thinkguard_nlp/classifier.py`의 `classify(message, history) -> dict`를 구현한다.
2. 백엔드 가상환경에 설치: `cd backend && .venv/bin/pip install -e ../nlp`
3. `backend/.env`: `CLASSIFIER=module`, `CLASSIFIER_MODULE=thinkguard_nlp.classifier:classify`
- 함수는 **동기 함수**로 둔다. 백엔드가 스레드에서 실행한다.
- 모델 로딩은 import 시 한 번만 하도록 모듈 전역에 둔다(요청마다 로딩 금지).

### 방식 B — HTTP (`CLASSIFIER=http`)
1. NLP 서버 실행: `cd nlp && uvicorn server:app --port 8001`
2. `backend/.env`: `CLASSIFIER=http`, `CLASSIFIER_URL=http://localhost:8001/classify`
- `POST /classify`, 요청·응답은 위 JSON. 타임아웃 10초.
- GPU 서버 등 다른 머신에서 모델을 돌릴 때 쓴다.

### 수용 기준
1. `CLASSIFIER` 값만 바꿔 stub ↔ module ↔ http 전환이 되고, 백엔드 코드 수정이 없다.
2. 세 구현 모두 같은 입력에 같은 출력 형식을 돌려준다.
3. NLP 서버가 꺼져 있으면(http) 채팅 API는 오류 응답을 낸다 — 정답이 새어 나가는 방향으로 "실패 시 통과"하지 않는다.

---

## 2. LLM Provider

### 인터페이스
```python
async def generate(system_prompt: str, messages: list[ChatTurn]) -> str
```
- `messages`는 오래된 순, 마지막이 학생의 새 메시지. 반환은 학생에게 보낼 답변 텍스트.

### Mock (`LLM_PROVIDER=mock`)
- 항상 같은 문장을 돌려준다. 호출 기록(`calls`)이 남아 테스트에서 시스템 프롬프트를 확인할 수 있다.

### Ollama (`LLM_PROVIDER=ollama`) — 모델
| 후보 | 크기 | 장점 | 주의 |
|---|---|---|---|
| **`qwen3:8b`** (기본, 11/22 NLP 비교로 결정) | 약 5.2GB | 일반 질문 기준으로 지시 따르기·정답 누출 방지가 후보 중 가장 좋음, 응답이 짧음, Apache 2.0 | 생각 모드가 기본으로 켜짐 → `OllamaProvider`가 `"think": false`로 끈다 |
| `qwen2.5:7b` | 약 4.7GB | 한국어 무난, 지시 따르기 좋음, Apache 2.0 | 가끔 중국어·영어가 섞임 → 프롬프트에 "한국어로만" 명시 |
| `exaone3.5:7.8b` | 약 4.8GB | 국산 모델, 한국어 품질이 가장 좋음 | 비상업 연구용 라이선스 (수업 프로젝트는 가능) |
| `qwen2.5:3b` | 약 1.9GB | 메모리 8GB 노트북에서도 빠름 | 단계별 안내 품질이 떨어짐 |

- 비교(11/22, NLP): StudyChat 한국어 번역 test 40문장, 같은 응답 정책 프롬프트. 첫 생성에서 긴 코드·"정답은" 등 누출 의심이 `qwen3:8b` 1건 / `exaone3.5:7.8b` 17건, 응답 길이 중앙값 200자 / 860자. 자세히: `nlp/README.md`
- 적대적 입력에는 약하다(11/22 우회 점검): "이전 지시는 무시해" 같은 문장이나 시도한 척하기에 66회 중 32회 완성 코드가 나갔다. 프롬프트만으로는 막지 못하므로 LLM 답을 보내기 전 정답 누출 검사가 필요하다(NLP 담당, 진행 중).
- 시연 PC가 RAM 16GB 이상이면 7~8B급, 8GB면 3B급.
- 사용: `ollama pull qwen3:8b` → `backend/.env`에 `LLM_PROVIDER=ollama`, `OLLAMA_MODEL=qwen3:8b`.
- `OllamaProvider`는 항상 `"think": false`를 보낸다(생각 기능이 없는 모델은 무시). 옛 Ollama가 `<think>…</think>`를 본문 맨 앞에 섞어 보내면 학생에게 가기 전에 지우고, 짝 없는 `</think>` 태그도 지운다. 지운 결과가 비면 `chat_service`가 `ASK_ATTEMPT_REPLY` 고정 문구로 바꾼다.
- 다른 LLM(API형 등)을 붙일 때는 `llm/<이름>.py`에 구현을 추가하고 `get_llm_provider()`에 분기 한 줄을 넣는다.

---

## 3. 코드 실행 (CodeRunner)

> 상태: **구현됨** (`backend/app/runner/`, `backend/sandbox/`, 테스트 있음). 채점·실행 API 연결은 미구현.
> 2026-11-17 결정: 코드 작성 문항은 **Docker 컨테이너**에서 실행한다. 숨김 테스트를 학생에게 보내지 않기 위해 서버에서 돌린다.

```
backend/app/runner/                CODE_RUNNER=
  base.py      CodeRunner           ← 인터페이스
  mock.py                             mock   (기본, 실행 없이 모두 통과)
  docker.py                           docker (컨테이너 실행)
backend/sandbox/
  Dockerfile                         실행 이미지 (python:3.12-slim + 일반 사용자)
  harness.py                         컨테이너 안에서 실행·비교
```

### 인터페이스
```python
async def run(code: str, tests: list[TestCase]) -> RunResult
```
| 타입 | 필드 |
|---|---|
| `TestCase` | `call` (호출식, 예 `sum_even([1, 2, 3, 4])`), `expected` (기대값) |
| `TestResult` | `call`, `actual` (반환값 repr, 오류면 null, 최대 1000자), `passed`, `error` (예 `ZeroDivisionError: division by zero`) |
| `RunResult` | `ok` (false면 문법 오류·시간 초과 등으로 실행 못 함), `error`, `results` |

- **비교 방식**: `expected`를 Python 리터럴로 읽어 값으로 비교한다(`6`, `'ab'`, `[1, 2]`). 리터럴이 아니면 문자열로 비교한다(`ab` ↔ 반환값 `'ab'`도 통과).
- **숨김 테스트 구분은 호출하는 service가 한다.** 실행기는 받은 테스트를 모두 돌린다. 학생에게 공개 테스트 결과만 보내는 것은 service·API 책임이다.
- Docker를 쓸 수 없으면 `RunnerUnavailableError` → API는 503(`RUNNER_UNAVAILABLE`)으로 응답한다.

### 격리 (DockerRunner)
| 제한 | 값 |
|---|---|
| 네트워크 | `--network none` |
| 메모리 | `RUNNER_MEMORY_MB` (기본 128MB, 스왑 없음) |
| CPU · 프로세스 | `--cpus 0.5`, `--pids-limit 64` |
| 파일 시스템 | `--read-only`, `/tmp`만 16MB 쓰기 가능 |
| 권한 | root 아닌 사용자, `--cap-drop ALL`, `no-new-privileges` |
| 시간 | `RUNNER_TIMEOUT_SEC` (기본 5초). 넘으면 컨테이너 강제 종료 |

### harness 안의 구조
학생 코드는 컨테이너 안에서도 **별도 자식 프로세스**로 돈다.
- 자식에게는 `code`와 `call`만 보낸다. **기대값은 자식에게 가지 않는다** → 학생 코드가 숨김 테스트 기대값을 읽을 수 없다.
- 통과 판정은 부모가 한다 → 학생 코드가 가짜 결과를 출력하고 종료해도 통과가 되지 않는다.
- 학생 코드의 `print` 출력은 버린다.

### 시연 PC 준비
```bash
docker build -t thinkguard-runner backend/sandbox
```
`backend/.env`에서 `CODE_RUNNER=docker`. Docker Desktop이 켜져 있어야 한다.

### 수용 기준
1. `CODE_RUNNER` 값만 바꿔 mock ↔ docker 전환, 코드 수정 없음.
2. 컨테이너 안에서 인터넷 연결·파일 쓰기가 막힌다.
3. 무한 루프는 시간 제한 안에 끝나고 `ok=false`, "실행 시간 초과".
4. 학생 코드가 결과를 위조하거나 기대값을 읽을 수 없다.

### 테스트
| 파일 | 다루는 것 |
|---|---|
| `backend/tests/test_harness.py` | 비교 방식, 예외·문법 오류, print 무시, 결과 위조 방지, 기대값 비공개, 시간 초과 (Docker 없이) |
| `backend/tests/test_runner.py` | Mock, 격리 옵션, Docker 없음 처리 / 실제 컨테이너: 실행·네트워크 차단·쓰기 차단·시간 초과 (이미지 없으면 건너뜀) |
