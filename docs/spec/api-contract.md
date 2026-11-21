# API 계약

> 상태: **초안 v3** — 프론트 화면시안 v3(프로그래밍 과제)와 `frontend/src/api/` 예시 데이터 기준. 팀 확인 전.
> 공통: 모든 경로는 `/api` 아래. 요청·응답은 JSON, 필드는 snake_case, Enum 값은 대문자 문자열([../planning/schema.md](../planning/schema.md)).
> 에러 형식은 [error-handling.md](error-handling.md). 실제 스펙은 서버를 띄운 뒤 `http://localhost:8000/docs`(Swagger)에서 확인하고, 이 문서와 다르면 이 문서를 고친다.
> 응답 타입의 필드 목록은 `frontend/src/api/<도메인>.ts`의 타입과 같다. 백엔드 Pydantic 스키마는 그 이름을 그대로 쓴다.

## v2 초안에서 바뀐 점
| 항목 | v2 | v3 |
|---|---|---|
| 과목 | 수학 · 프로그래밍 · 글쓰기 · 개념 | **프로그래밍만**. 과목 이름·대상은 자유 입력, 언어 선택 |
| 문항 유형 | 객관식 · 단답형 · 서술형 | 객관식 퀴즈 · 출력 예측 · **코드 작성(테스트 실행)** · **간단 제작(교수자 채점)** |
| AI 도움 설정 | 클래스당 1개 (`/ai-settings`) | **과제마다** (`assignment.policy`). 클래스에는 새 과제에 채울 **기본값**만 (`/ai-defaults`) |
| 제출 | 한 번 제출하면 끝, 결과 바로 표시 | 마감·최종 제출 전까지 **다시 제출** 가능. 정오·점수는 **교수자가 결과 공개**할 때까지 숨김 |
| AI 도움 잠금 | 제출한 문항은 잠김 | **최종 제출 전까지 열림**. 개념 확인 중·최종 제출 후에만 잠김 |
| 개념 확인 | 질문 1개 | 질문 1개 + 답변에 **AI 작성 신호가 높으면 1개 더** |
| 학생 입장 | 회원가입 후 초대 코드 | **가입 없이** 수업 코드 + 학번(`student_no`) (결정 A) |
| 새 기능 | — | 명단 미리 넣기 · 참여 요청 수락 · 학생 내보내기, 클래스별 AI 기본값, 도움 방식 고르기, 공개 테스트 실행, 최종 제출, 이해 확인, 결과 공개, 학생별 기록, 우회 요청 시뮬레이션 |

## 결정 필요
| # | 내용 | 제안 |
|---|---|---|
| A | 학생 입장 방식과 인증 | **결정됨(11/17)**: 학번(`student_no`)으로 입장. `POST /enrollments`가 학생 계정(이메일 없음)을 만들고 `access_token`을 준다. 같은 기기에서 다시 들어오면 토큰으로 이어서 |
| B | `ResponseMode` 값 표기 | schema.md처럼 **대문자**로 통일. 현재 `backend/app/services/policy.py`는 소문자라 맞춰야 함. `OFFER_CHOICES` 추가 |
| C | 마감 뒤 다시 제출 | 마감이 지나면 다시 제출·최종 제출 불가(`CONFLICT`). 마감 때 최종 제출하지 않은 학생은 마지막 제출본으로 자동 최종 처리 |
| D | 결과 공개 뒤 수정 | 공개 뒤에는 문항·정답 수정 불가. 채점(간단 제작)은 공개 뒤에도 가능 |
| E | NLP 계약 추가 | ① AI 답변 **누출 검사**(경서) ② 개념 확인 답변 **AI 작성 점수**(수빈). [integration-contract.md](integration-contract.md)에 입출력 추가 — 웹·NLP 양쪽 승인 |
| F | 판별 과정(`trace`) 노출 | 학생 응답에는 `null`. 시연용 환경변수 `DEMO_TRACE=true`일 때만 채운다 |

## 인증
- 로그인·입장 응답의 `access_token`을 `Authorization: Bearer <token>` 헤더로 보낸다.
- 토큰 클레임: `sub`(user id), `role`(`TEACHER`/`STUDENT`), `exp`.
- 권한 열: **공개** = 토큰 불필요 / **T** = 교수자 / **S** = 학생.
- 교수자는 **자기 클래스만**, 학생은 **참여한 클래스의 배포된 과제와 자기 답·대화만** 본다. 아니면 `FORBIDDEN`(불변식 I7).

---

## 목록
"프론트 함수" 열은 `frontend/src/api/`의 함수다. 백엔드가 생기면 그 함수 안의 `mock…` 호출만 `client.ts` 호출로 바꾼다.

### 상태 · 인증
| 메서드 | 경로 | 권한 | 요청 → 응답 | 프론트 함수 |
|---|---|---|---|---|
| GET | `/health` | 공개 | → `{status, llm_provider, classifier}` ✅ 구현됨 | `getHealth` |
| POST | `/auth/signup` | 공개 | `{name, email, password}` → `{access_token, user}` 교수자만 가입. 비밀번호 8자 이상. 오류: `EMAIL_TAKEN` | `signup` |
| POST | `/auth/login` | 공개 | `{email, password}` → `{access_token, user}` | `login` |

### 클래스 · 참여
| 메서드 | 경로 | 권한 | 요청 → 응답 | 프론트 함수 |
|---|---|---|---|---|
| GET | `/classes` | T | → `ClassInfo[]` | `listClasses` |
| POST | `/classes` | T | `{name, plan, starts_on}` → `ClassInfo` (수업 코드 발급, 학생 수 상한 = 요금제 상한). `starts_on`은 오늘 이후 날짜(`YYYY-MM-DD`), 시작 = 그날 00:00 KST, 만료 = 시작 + 1년. `ClassInfo`에 `starts_at`·`expires_at` 포함 | `createClass` |
| GET | `/classes/{class_id}/ai-defaults` | T | → `AiPolicy` 새 과제에 미리 채울 정책 | `getAiDefaults` |
| PUT | `/classes/{class_id}/ai-defaults` | T | `AiPolicy` → `AiPolicy` (`prompt_mode`는 항상 `FORM`, 이미 만든 과제에는 적용 안 함) | `saveAiDefaults` |
| GET | `/classes/{class_id}` | T | → `ClassInfo` (`invite_code` 포함) | `getClass` |
| GET | `/classes/{class_id}/students` | T | → `{id, student_no}[]` 참여 중인 학생 | `listStudents` |
| GET | `/me/classes` | S | → `MyClass[]` (참여 클래스 + 과제별 상태 `IN_PROGRESS`·`FINALIZED`·`RELEASED`) | `listMyClasses` |
| POST | `/enrollments` | 공개 | `{invite_code, student_no}` → `{class_id, class_name, status: APPROVED\|PENDING, access_token}` (결정 A). 명단에서 사용 중(`is_use`)이거나 입장 방식이 `OPEN`이면 바로 `APPROVED`, 아니면 참여 요청(`PENDING`). 오류: `INVITE_CODE_INVALID`, `CLASS_NOT_STARTED`, `CLASS_FULL`, `CLASS_EXPIRED`, 내보낸 학번이면 `FORBIDDEN` | `joinClass` |
| GET | `/enrollments/{class_id}/me` | S | → `{status: PENDING\|APPROVED\|REJECTED\|REMOVED}` 참여 요청이 수락됐는지 확인 | `getMyEnrollment` |
| POST | `/enrollments/{class_id}/consent` | S | → `{ok}` 기록 열람·붙여넣기 기록 안내 동의 | `acceptConsent` |
| GET | `/classes/{class_id}/join-requests` | T | → `{id, student_no, requested_at}[]` 기다리는 참여 요청 | `listJoinRequests` |
| POST | `/classes/{class_id}/join-requests/{request_id}` | T | `{approve: bool}` → `{ok}`. 수락할 때 정원이 차 있으면 `CLASS_FULL` | `decideJoinRequest` |
| DELETE | `/classes/{class_id}/students/{student_id}` | T | → `{ok}` 학생 내보내기. **제출·대화 기록은 남기고** 학생의 과제·AI 접근만 막는다. 같은 학번으로 다시 입장 불가 | `removeStudent` |
| GET | `/classes/{class_id}/roster` | T | → `{join_mode: APPROVAL\|OPEN, roster: {student_no, is_use}[]}` 입장 방식과 미리 넣어 둔 학번 명단 | `getRosterSettings` |
| PUT | `/classes/{class_id}/roster` | T | 같은 모양 → 같은 모양. 명단에서 빼면 지우지 않고 `is_use = false`(이미 수락된 학생은 그대로). 이미 요청한 학생이 사용 중인 명단에 있으면 저장할 때 바로 수락 | `saveRosterSettings` |

- 시작 전(`starts_at` 이전) 클래스는 교수자 준비(과제 만들기·명단)만 되고, 학생 입장은 `CLASS_NOT_STARTED`.

### 과제 만들기 (교수자)
| 메서드 | 경로 | 권한 | 요청 → 응답 | 프론트 함수 |
|---|---|---|---|---|
| GET | `/classes/{class_id}/assignments` | T | → `AssignmentSummary[]` | `listAssignments` |
| POST | `/classes/{class_id}/assignments/drafts` | T | `{source: "SAMPLE" \| "BLANK"}` → `Assignment` (저장 전 초안, `id: "new"`) | `createDraftFromSample`, `createBlankDraft` |
| POST | `/classes/{class_id}/assignments/extract` | T | multipart `file` → `Assignment` 초안. 문항·코드·정답·테스트·배점 추출 | `extractFromFile` |
| POST | `/classes/{class_id}/assignments` | T | `Assignment` → `Assignment` (새로 저장) | `saveAssignment` (id가 `new`) |
| GET | `/assignments/{assignment_id}` | T | → `Assignment` (정답·숨김 테스트·모범 답안 포함) | `getAssignment` |
| PUT | `/assignments/{assignment_id}` | T | `Assignment` → `Assignment` (결정 D) | `saveAssignment` |
| POST | `/assignments/{assignment_id}/publish` | T | → `{invite_code}` | `publishAssignment` |
| POST | `/assignments/{assignment_id}/release` | T | → `{results_released: true}` 점수·정답·내 리포트를 학생에게 공개 | `releaseResults` |
| POST | `/assignments/preview` | T | `Assignment` → `{lines[], hint_mode_label}` "학생은 이렇게 경험해요" (프롬프트 원문 아님) | `getPolicyPreview` |
| POST | `/assignments/prompt-draft` | T | `Assignment` → `{prompt}` 지시문 직접 작성의 시작 문안 | `getPromptDraft` (응답에서 `prompt`를 꺼냄) |
| POST | `/assignments/simulate` | T | `Assignment` → `SimulationCase[]` 우회 요청을 보내 본 결과 | `simulateAttacks` |

- preview · prompt-draft · simulate는 **저장 전 초안**을 받으므로 과제 id 없는 경로를 쓴다.
- `Assignment.policy`(`AiPolicy`)에 `usage_limit`(학생 1명 · 이 과제 AI 메시지 수, 기본 30)를 둔다.
- 코드 작성 문항 테스트는 지금처럼 `tests[{call, expected, hidden}]` 한 배열로 주고받는다. 서버가 저장할 때 공개(`public_tests`)와 숨김(`answer_key.hidden_tests`)으로 나누고, 교수자 조회 때 다시 합쳐 돌려준다([schema.md](../planning/schema.md) D17).
- `custom_prompt`를 써도 고정 규칙(정답·완성 코드 금지, 시도 지어내기 금지, 누출 검사)은 항상 붙는다(불변식 I3).

### 풀이 · 제출 (학생)
| 메서드 | 경로 | 권한 | 요청 → 응답 | 프론트 함수 |
|---|---|---|---|---|
| GET | `/assignments/{assignment_id}/solve` | S | → `StudentAssignment` | `getStudentAssignment` |
| GET | `/assignments/{assignment_id}/submission` | S | → `Submission` (없으면 만든다) | `getMySubmission` |
| POST | `/assignments/{assignment_id}/questions/{question_id}/run` | S | `{code}` → `TestResult[]` **공개 테스트만** | `runPublicTests` |
| PUT | `/assignments/{assignment_id}/answers/{question_id}` | S | `{content}` → `Submission`. 처음 내는 문항이고 힌트 0단계면 `AWAITING_CHECK`, 아니면 `SUBMITTED` | `submitAnswer` |
| POST | `/assignments/{assignment_id}/answers/{question_id}/concept-check` | S | `{reply, elapsed_ms}` → `Submission`. 붙여넣기는 `/paste-events`(`field = CONCEPT_CHECK`)로만 보낸다 | `answerConceptCheck` |
| DELETE | `/assignments/{assignment_id}/answers/{question_id}/concept-check` | S | → `Submission` 답 고치러 돌아가기(`DRAFT`). 추가 질문 단계에서는 `CONFLICT` | `cancelConceptCheck` |
| POST | `/assignments/{assignment_id}/submission/finalize` | S | → `Submission` 최종 제출. 안 낸 문항이 있으면 `CONFLICT` | `finalizeSubmission` |

- 최종 제출 뒤 답 제출·개념 확인·채팅은 `ALREADY_SUBMITTED`.
- **결과 공개 전 학생 응답에는 정오·점수·숨김 테스트 결과를 넣지 않는다.** `AnswerState`에 해당 필드 자체가 없다.

### 학습 AI 채팅 (학생)
| 메서드 | 경로 | 권한 | 요청 → 응답 | 프론트 함수 |
|---|---|---|---|---|
| GET | `/assignments/{assignment_id}/questions/{question_id}/chat` | S | → `ChatState` | `getChat` |
| POST | `/assignments/{assignment_id}/questions/{question_id}/chat` | S | `{message, choice?}` → `ChatState`. 붙여넣기는 `/paste-events`(`field = CHAT`)로만 보낸다 | `sendChat` |

- 잠김(`FORBIDDEN`): 교수자가 AI를 끈 간단 제작 문항, 개념 확인 중인 문항, 최종 제출한 과제.
- 완성 답안 요청 + 시도 근거 없음이면 LLM을 부르지 않고 `OFFER_CHOICES` 응답을 준다. 학생이 `choice`(`FIRST_HINT`·`FEEDBACK`·`ORIGINAL`)를 골라 다시 보낸다. `ORIGINAL`이어도 정책은 `HINT_ONLY` 그대로(불변식 I1).
- 사용량 상한이면 LLM을 부르지 않고 `USAGE_LIMIT`(불변식 I6).

### 붙여넣기 기록
| 메서드 | 경로 | 권한 | 요청 → 응답 | 프론트 함수 |
|---|---|---|---|---|
| POST | `/paste-events` | S | `{question_id, field, length, pasted_at}` → `{ok}`. **내용 필드 없음**, 알 수 없는 필드는 거부(불변식 I5). 서버는 이 학생의 그 문항 답(`answers`)에 묶어 저장하고, 답이 없으면 만든다 | `logPaste` |

### 이해 확인 · 내 리포트 (학생)
| 메서드 | 경로 | 권한 | 요청 → 응답 | 프론트 함수 |
|---|---|---|---|---|
| GET | `/assignments/{assignment_id}/understanding-check` | S | → `UnderstandingCheck` (최종 제출 후에만) | `getUnderstandingCheck` |
| POST | `/assignments/{assignment_id}/understanding-check` | S | `{explanation, answers[{question_id, value, confidence}]}` → `{submitted_at}`. 정오는 돌려주지 않음 | `submitUnderstandingCheck` |
| GET | `/assignments/{assignment_id}/my-report` | S | → `{released: false, assignment_title}` 또는 `{released: true, …MyReport}` | `getMyReport` |

### 리포트 · 채점 (교수자)
| 메서드 | 경로 | 권한 | 요청 → 응답 | 프론트 함수 |
|---|---|---|---|---|
| GET | `/assignments/{assignment_id}/report` | T | → `AssignmentReport` | `getAssignmentReport` |
| GET | `/assignments/{assignment_id}/grading` | T | → `GradingItem[]` 간단 제작 답안 | `getGradingList` |
| PUT | `/answers/{answer_id}/grade` | T | `{score, feedback}` → `GradingItem`. `0 ≤ score ≤ points` | `gradeAnswer` |
| GET | `/assignments/{assignment_id}/students/{student_id}/record` | T | → `StudentRecord` | `getStudentRecord` |

- 외부 AI 참고 신호·개념 확인 AI 작성 신호는 **교수자 응답에만** 있고, 점수를 바꾸지 않는다.

### 요금제 · 결제 (목업)
| 메서드 | 경로 | 권한 | 요청 → 응답 | 프론트 함수 |
|---|---|---|---|---|
| GET | `/plans` | 공개 | → `Plan[]` `{code, name, student_limit, price}` | `listPlans` |
| POST | `/payments` | T | `{plan, kind: NEW\|EXTEND, class_id}` → `{payment_id, amount, period_end}` | `payMock` |

- **실제 결제 대행(PG) 연동 코드는 넣지 않는다.** 항상 성공으로 처리한다.
- 요금제(수익화 기획 기준, 클래스 하나 · 1년): `SMALL` 학생 50명 이하 90,000원 / `MEDIUM` 100명 이하 150,000원 / `LARGE` 200명 이하 250,000원. 기능은 같고 학생 수 상한만 다르다. 학생은 무료.
- 지금 학생 수보다 작은 요금제로는 연장할 수 없다(`CONFLICT`).
- `EXTEND`는 해당 클래스의 `expires_at`을 1년 늘린다. 교수자 본인 클래스만.

---

## 상태 흐름
```
문항 답(AnswerState.status)
  DRAFT ──제출──▶ AWAITING_CHECK ──개념 확인 답변(필요하면 1개 더)──▶ SUBMITTED
    ▲   (힌트 0단계 + 처음 낼 때만)  │                                  │
    └──────── 답 고치러 돌아가기 ◀──┘     다시 제출 ◀──────────────────┘

과제 제출(Submission)
  finalized=false ──최종 제출──▶ finalized=true ──(교수자) 결과 공개──▶ results_released=true
  (답 수정·AI 도움 가능)        (답·AI 잠김, 이해 확인)              (점수·정답·내 리포트 공개)
```

## 학생에게 보내지 않는 것
| 대상 | 이유 |
|---|---|
| 정답, `accepted_answers`, `model_answer`, `rubric`, 숨김 테스트 입력·기대값 | 답 누출 |
| 결과 공개 전 정오·점수·숨김 테스트 결과·이해 확인 정오 | 제출 시간이 달라 친구에게 퍼질 수 있음 |
| 분류 원본(`confidence` 등), `trace`, 외부 AI 신호, 개념 확인 판정 | 우회 학습 방지, 참고 신호는 교수자용 (결정 F) |

## 채팅 예시
```json
// POST /api/assignments/a1/questions/q3/chat
{ "message": "sum_even 코드 전체 짜주세요" }

// 200 — 완성 답안 요청 + 시도 근거 없음
{ "question_id": "q3", "hint_step": 0, "max_hint_steps": 3, "usage_remaining": 29,
  "turns": [
    { "role": "STUDENT", "text": "sum_even 코드 전체 짜주세요", "response_mode": null, "trace": null },
    { "role": "ASSISTANT", "text": "완성된 답을 바로 받기보다, 아래에서 골라 볼래요?", "response_mode": "OFFER_CHOICES", "trace": null }
  ] }

// 이어서 { "message": "", "choice": "FIRST_HINT" } → HINT_ONLY 응답, hint_step 1
```

## 개념 확인 예시
```json
// PUT /api/assignments/a1/answers/q1  { "content": "1" }
// → answers.q1 = { "status": "AWAITING_CHECK",
//                  "concept_check": { "questions": ["append가 리스트를 어떻게 바꾸는지 …"], "answered": 0 }, … }

// POST /api/assignments/a1/answers/q1/concept-check
{ "reply": "물론입니다. append 메서드는 …", "elapsed_ms": 4200 }
// (붙여넣었다면 그 전에 POST /api/paste-events { "question_id": "q1", "field": "CONCEPT_CHECK", … })
// AI 작성 신호가 높으면 → concept_check.questions에 질문 1개 추가, 여전히 AWAITING_CHECK
// 아니면 → status "SUBMITTED"
```
