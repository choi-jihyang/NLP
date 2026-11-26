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

> 상태: **구현됨 — C · Python** (`backend/app/runner/`, `backend/sandbox/`, 테스트 있음). 채점·실행 API 연결은 ⑦에서.
> 2026-11-17 결정: 코드 작성 문항은 **Docker 컨테이너**에서 실행한다. 숨김 테스트를 학생에게 보내지 않기 위해 서버에서 돌린다.
> 11/25: 테스트 모양을 모든 언어 `{input, expected_output}`(표준 입력 → 표준 출력, schema D23)으로 바꾸고 C(gcc)를 추가했다.

```
backend/app/runner/                CODE_RUNNER=
  base.py      CodeRunner           ← 인터페이스
  mock.py                             mock   (기본, 실행 없이 모두 통과)
  docker.py                           docker (컨테이너 실행)
backend/sandbox/
  Dockerfile                         실행 이미지 (python:3.12-slim + gcc + 일반 사용자)
  harness.py                         컨테이너 안에서 컴파일·실행·비교
```

### 인터페이스
```python
async def run(language: Language, code: str, tests: list[IOCase]) -> RunResult
```
| 타입 | 필드 |
|---|---|
| `IOCase` | `input` (표준 입력), `expected_output` (기대 표준 출력) |
| `RunCaseResult` | `input`, `actual_output` (실제 표준 출력, 최대 1000자, 시간 초과면 null), `passed`, `error` (예 `실행 시간 초과 (5초)`, `Segmentation fault (잘못된 메모리 접근)`, `프로그램이 종료 코드 1로 끝났어요`) |
| `RunResult` | `ok` (false면 컴파일 오류 · 지원하지 않는 언어로 실행 못 함), `error` (컴파일 오류면 `컴파일 오류:\n<gcc 메시지>`), `results` |

- **언어**: `C`(gcc, `-std=c11 -O1 -lm`), `PYTHON`. `JAVA` · `JAVASCRIPT`는 아직 없음 → `ok=false`, Docker를 부르지 않는다.
- **비교**: 각 줄 끝 공백과 마지막 줄바꿈은 무시하고 비교한다(D23). `\r\n`은 `\n`으로 본다. 줄 안의 공백은 비교한다.
- **종료 코드**: 0이 아니어도 출력이 맞으면 통과, `error`에 종료 코드를 적는다. 신호로 죽으면(세그폴트 · 메모리) 실패.
- **시간 제한**: 테스트마다 `RUNNER_TIMEOUT_SEC`. 한 테스트가 시간을 넘어도 나머지 테스트는 돈다. 컨테이너 전체는 컴파일 15초 + 테스트 수 × 제한 + 여유 10초.
- **숨김 테스트 구분은 호출하는 service가 한다.** 실행기는 받은 테스트를 모두 돌린다. 학생에게 공개 테스트 결과만 보내는 것은 service·API 책임이다.
- Docker를 쓸 수 없거나 **이미지가 없으면** `RunnerUnavailableError` → API는 503(`RUNNER_UNAVAILABLE`). `--pull never`라서 이미지가 없을 때 Docker Hub에서 받으려 하지 않는다.

### 격리 (DockerRunner)
| 제한 | 값 |
|---|---|
| 네트워크 | `--network none` |
| 메모리 | `RUNNER_MEMORY_MB` (기본 128MB, 스왑 없음) |
| CPU · 프로세스 | `--cpus 0.5`, `--pids-limit 64` |
| 파일 시스템 | `--read-only`, `/tmp`만 32MB 쓰기 가능(`exec` 허용 — 컴파일 결과 실행, `nosuid` · `nodev`, `mode=1777`) |
| 권한 | root 아닌 사용자, `--cap-drop ALL`, `no-new-privileges` |
| 이미지 | `--pull never` (없으면 503) |
| 시간 | 위 "시간 제한". 넘으면 컨테이너 강제 종료 |

### harness 안의 구조
학생 프로그램은 컨테이너 안에서도 **테스트마다 별도 자식 프로세스**로 돈다.
- 자식에게는 **그 테스트의 `input`만** 표준 입력으로 준다. 기대 출력은 부모만 가진다.
- 부모는 시작하자마자 `prctl(PR_SET_DUMPABLE, 0)`을 호출한다. 같은 사용자인 자식이 `/proc/<부모>/mem`에서 기대값을 읽거나 `/proc/<부모>/fd/1`로 가짜 결과를 쓰는 우회를 막는다(11/18 리뷰에서 실제로 뚫리는 것을 확인).
- 통과 판정은 부모가 한다 → 학생 프로그램이 가짜 결과 JSON을 출력해도 그 테스트의 "실제 출력"일 뿐이다.
- 자식 출력은 `/tmp` 파일로 받아 앞 64KB만 읽는다 → 출력 폭탄이 부모 메모리를 채우지 못한다. 자식은 새 세션으로 띄워 손자 프로세스까지 한 번에 끝낸다.

### 시연 PC 준비
```bash
docker build -t thinkguard-runner backend/sandbox
```
`backend/.env`에서 `CODE_RUNNER=docker`. Docker Desktop이 켜져 있어야 한다. `harness.py`를 고치면 다시 빌드한다.

### 수용 기준
1. `CODE_RUNNER` 값만 바꿔 mock ↔ docker 전환, 코드 수정 없음.
2. 컨테이너 안에서 인터넷 연결·`/tmp` 밖 파일 쓰기가 막힌다.
3. 무한 루프는 테스트별 시간 제한 안에 끝나고 "실행 시간 초과".
4. 학생 코드가 결과를 위조하거나 기대값을 읽을 수 없다(부모 메모리 · 부모 출력 통로 포함).
5. C 컴파일 오류는 `ok=false`와 gcc 메시지(서버 경로 없이)로 알려 준다.
6. 이미지가 없으면 받지 않고 `RUNNER_UNAVAILABLE`.

### 테스트
| 파일 | 다루는 것 |
|---|---|
| `backend/tests/test_harness.py` | C · Python 입출력 비교, 줄 끝 공백 규칙, 컴파일 오류, 세그폴트 · 종료 코드, 시간 초과, 출력 폭탄, 결과 위조, **부모 메모리 · 출력 통로 차단**(리눅스 일반 사용자에서만) — Docker 없이, C는 gcc 필요 |
| `backend/tests/test_runner.py` | Mock, 격리 옵션, Docker 없음 · 이미지 없음 → `RunnerUnavailableError`, 미지원 언어 / 실제 컨테이너: C 실행 · 네트워크 차단 · 쓰기 차단 · 시간 초과 · 부모 메모리 차단 (이미지 없으면 건너뜀) |

---

## 4. 누출 검사 (LeakGuard)

> 상태: **계약 제안 · 규칙 기반 1차 구현됨** (`nlp/thinkguard_nlp/leak.py`, `backend/app/leak_guard/`, 테스트 `backend/tests/test_leak_guard.py`).
> [chat-policy.md](chat-policy.md) "마지막 필터". LLM 답변을 학생에게 보내기 전에 항상 거친다(끄는 설정 없음).

```
backend/app/leak_guard/          LEAK_GUARD_MODULE=
  base.py      LeakGuard          ← 인터페이스
  module.py                         thinkguard_nlp.leak:check_leak (기본)
```

### 입력
| 필드 | 타입 | 설명 |
|---|---|---|
| `reply` | string | 학생에게 보내기 전의 LLM 답변 초안 |
| `history` | `{role, content}[]` | 분류기와 같은 형식, 오래된 순. 이번 학생 메시지는 들어가지 않는다 |

### 출력
| 필드 | 타입 | 의미 |
|---|---|---|
| `leaked` | bool | 정답·완성 코드가 들어 있어 학생에게 보내면 안 되는가 |
| `reasons` | string[] | 걸린 규칙. `complete_function` · `filled_blank` · `code_chunk` · `answer_expression` · `accumulated` |

### 1차 규칙 (`check_leak`)
| 규칙 | 막는 것 |
|---|---|
| `complete_function` | 빈칸 없는 `def` + 본문(return 또는 문장 3개 이상). 코드블록 유무와 상관없음 |
| `filled_blank` | `____` 빈칸 줄과 같은 모양에 빈칸만 채운 줄이 함께 있음 ("정답 채운 버전") |
| `code_chunk` | 빈칸 없는 코드 문장 3개 이상 + return, 또는 5개 이상 (def 없이 "나머지 전부") |
| `answer_expression` | `sum(x for x in … if …)`, `sorted(…)[1]` 같은 한 줄 정답 표현식 |
| `accumulated` | 최근 AI 답변 4개 + 이번 답변의 코드를 합치면 위 `complete_function` · `filled_blank` |

- 빈칸(`____`)이 남은 코드, 말로 된 힌트, 한두 줄짜리 예시는 통과시킨다(명세가 허용한 빈칸 채우기 형태).
- 차단되면 백엔드는 답변을 `LEAK_BLOCKED_REPLY`로 바꾸고 `leak_blocked=true`, 원문은 `blocked_draft`에 둔다(학생에게 보내지 않음). 응답 모드 기록은 그대로다.
- 검사기가 오류를 내거나 출력 형식이 다르면 답변을 내보내지 않고 오류가 난다 — "실패 시 통과" 없음.
- 설치: `cd backend && .venv/bin/pip install -r requirements.txt` (`-e ../nlp` 포함).
- 모델 기반 판별로 바꿀 때는 같은 함수 이름·입출력으로 교체한다. HTTP 방식이 필요하면 분류기처럼 `http.py`를 추가한다.

### 수용 기준
1. 우회 시도 검증(PR #12)의 누출 사례가 `test_leak_guard.py`에 고정되어 있고 모두 차단된다.
2. HINT_ONLY · NEXT_STEP 등 LLM을 부르는 모든 모드에 적용된다.
3. 대조군 힌트 · 빈칸 템플릿 · 짧은 예시는 통과한다.

### 알려진 빈틈
- 학생이 보낸 빈칸 코드의 빈칸만 채워 주는 답(PR #12 #15)은 학생 메시지를 보지 않아 놓친다.
- 코드 조각을 문장 속에 흩어 주는 답(`x = list(set(nums))`로 …, `x[-2]`로 …), 기대 출력값(숫자)은 놓친다. 정답(`answer_key`) 비교는 문항 모델이 생기면 입력에 추가한다.
