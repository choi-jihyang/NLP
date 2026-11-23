# ④-1 과제 · 문항 모델과 기본 API 설계

> 상태: **설계 승인됨(대화)** — 2026-11-23
> 관련: [schema.md](../../planning/schema.md) assignments · questions · AnswerKey · [api-contract.md](../../spec/api-contract.md) 과제 만들기 · [샘플 과제 md](../../spec/samples/c-binary-assignment.md) · 앞선 설계 [③ 클래스 · 참여](2026-11-22-class-api-design.md)

## 1. 목표와 범위
- **목표**: 교수자가 C 과제를 저장 · 조회 · 수정 · 배포 · 결과 공개하고, 승인된 학생이 배포된 과제를 **정답 없이** 본다. ⑤⑥⑦과 C 실행기가 이 모델을 쓴다.
- **범위 안**
  - `assignments` · `questions` 모델
  - 교수자 API: 목록, 빈 초안, 새로 저장, 조회, 수정, 배포, 결과 공개
  - 학생용 과제 조회 `/solve`
- **범위 밖**
  - md 추출(`/extract`), 샘플 초안(`source: SAMPLE`), C 과제 시드 → ④-2 (샘플 md 파서가 필요)
  - 정책 미리보기 · 지시문 초안 · 졸라보기 → ⑤ 다음
  - 제출 · 채점 · `/me/classes`의 과제 목록 → ⑦

**성공 기준**
1. 교수자가 샘플 md 모양의 C 과제를 저장하고, 정답 · 숨김 테스트까지 그대로 다시 읽는다.
2. 학생은 **승인된 참여 + 배포된 과제**만 본다(I7).
3. 학생 응답 JSON 어디에도 정답 · 인정 답안 · 오개념 · 숨김 테스트 내용 · 채점 기준 · 모범 답안 · 확인 문제가 없다(I8, 새로 추가).
4. 배포한 과제의 문항은 바뀌지 않는다.

## 2. 확정한 결정
| # | 결정 | 이유 |
|---|---|---|
| A1 | **테스트 모양 통일**: 모든 언어 `{input, expected_output}` (표준 입력 → 표준 출력). 교수자 API는 `tests[{input, expected_output, hidden}]` 한 배열로 주고받고, 서버가 `public_tests`와 `answer_key.hidden_tests`로 나눈다 | 시연은 C. 언어마다 채점 방식이 달라지지 않게 한다. Python 실행기(함수 호출)는 C 실행기를 만들 때 같은 모양으로 바꾼다 |
| A2 | **출력 비교**: 각 줄 끝 공백과 마지막 줄바꿈은 무시하고 비교한다 | `printf("\n")` 유무로 틀리지 않게. C 실행기 · ⑦ 채점이 이 규칙을 따른다 |
| A3 | **배포 후 문항 잠금**: 배포 전에는 전부 수정(문항은 통째로 교체). 배포 후에는 제목 · 과목 · 대상 · 설명 · 마감 · AI 정책만. 문항이나 `language`가 달라지면 `CONFLICT`. 결과 공개 후에는 모든 수정이 `CONFLICT` | 학생이 풀고 있는 문항이 바뀌면 답 · 대화가 어긋난다 |
| A4 | 배포 후 "문항이 바뀌었는지"는 서버가 저장된 값과 보낸 값을 비교해 판단한다(같으면 통과) | 프론트가 과제 전체를 다시 보내도 된다 |
| A5 | 샘플 초안 · C 과제 시드는 ④-2로 | 샘플 md 파서를 쓰면 과제를 코드에 복사해 두지 않아도 된다 |
| A6 | `language` 값은 대문자 Enum `PYTHON · JAVA · C · JAVASCRIPT` | Enum 대문자 규칙(schema). 프론트 `'Python'`·`'C'` → 대문자로 바꿔야 함 |
| A7 | 학생용 조회에서 초안 · 없는 과제도 `FORBIDDEN` | 과제가 있는지조차 알리지 않는다 |

## 3. 구성
| 파일 | 책임 |
|---|---|
| `app/core/enums.py` | `QuestionType`, `Language` 추가 |
| `app/models/assignment.py` · `question.py` | 테이블 2개 |
| `app/schemas/assignments.py` | `IOTest`, `TestCase`, `Variant`, `AnswerKey`, `QuestionData`(유형별 검증), `AssignmentData`, `AssignmentSummary`, `DraftBody`, `PublishOut`, `ReleaseOut` |
| `app/schemas/student_assignments.py` | `StudentTest`, `StudentQuestion`, `StudentAssignment` (🔒 필드가 **아예 없음**), `HINT_MODE_LABEL`, `MAX_HINT_STEPS` |
| `app/services/question_codec.py` | 요청 모양 ↔ 테이블 값 변환(테스트 나누기 · 합치기), 배포 후 같은 문항인지 비교 |
| `app/services/assignment_service.py` | 빈 초안, 저장, 조회, 수정(잠금), 배포, 결과 공개, 목록 |
| `app/services/student_assignment_service.py` | 학생용 조회(승인된 참여 + 배포) |
| `app/api/routes/assignments.py` · `solve.py` | 교수자 · 학생 라우터 |

## 4. API
모든 id는 `seq`(숫자).

| 권한 | API | 요청 → 응답 |
|---|---|---|
| T | `GET /classes/{class_id}/assignments` | → `AssignmentSummary[]` `{seq, title, kinds, status, due_at, hint_mode, submitted_count, student_count, todo, results_released}`. `status`는 `published_at` · 마감으로 계산(`DRAFT` · `OPEN` · `CLOSED`). `submitted_count`는 ⑦ 전까지 0, `todo`는 null |
| T | `POST /classes/{class_id}/assignments/drafts` | `{source: "BLANK"}` → `AssignmentData` (저장 안 함, `seq: null`, 정책 = 클래스 AI 기본값, `language: C`, 제목 "새 과제") |
| T | `POST /classes/{class_id}/assignments` | `AssignmentData` → 201 `AssignmentData` |
| T | `GET /assignments/{assignment_id}` | → `AssignmentData` (정답 · 숨김 테스트 · 모범 답안 포함) |
| T | `PUT /assignments/{assignment_id}` | `AssignmentData` → `AssignmentData` (A3 · A4) |
| T | `POST /assignments/{assignment_id}/publish` | → `{invite_code}`. 문항 0개면 `CONFLICT`. 이미 배포됐으면 그대로 |
| T | `POST /assignments/{assignment_id}/release` | → `{results_released: true}`. 배포 전이면 `CONFLICT` |
| S | `GET /assignments/{assignment_id}/solve` | → `StudentAssignment` |

**`AssignmentData`** = `{seq, class_id, title, course, audience, language, description, due_at, published, results_released, policy, questions[]}`
- 요청에서 `seq` · `class_id` · `published` · `results_released`는 무시한다(서버가 정함).

**`QuestionData`** = `{seq, type, points, prompt, code, choices, answer, accepted_answers, misconceptions, starter_code, tests[{input, expected_output, hidden}], rubric, model_answer, ai_help, variant}`
- 프론트 `Question` 타입과 같은 필드.
- `id` → `seq`, `tests` 모양만 다르다.

**`StudentAssignment`** = `{seq, title, course, language, due_at, hint_mode, hint_mode_label, max_hint_steps, external_signal_enabled, questions[]}`

**`StudentQuestion`** = `{seq, type, points, prompt, code, choices, starter_code, ai_help, ai_enabled, public_tests[{input, expected_output}], hidden_test_count}`
- 힌트 라벨: `NONE` 힌트 없음 / `CONCEPT` 개념만 / `STEP` 한 단계씩 / `EARNED` 시도한 만큼 열기. 최대 단계는 0 / 1 / 3 / 3 (프론트 mock과 같음).
- `ai_enabled`: 간단 제작이면 `ai_help`, 그 외 문항은 항상 `true`.

## 5. 검증 (`VALIDATION_FAILED`)
- 과제
  - 제목: 앞뒤 공백 제거 후 1–100자.
  - 과목 · 대상: 100자 이하. 설명: 20,000자 이하.
  - `language`: 필수.
  - `due_at`: 시간대 있는 값 또는 null.
  - `policy`: `AiPolicy`로 검증.
- 문항
  - 50개 이하. 배점 0–1000.
  - 문제: 1자 이상.
  - 코드 · 시작 코드: 20,000자 이하.
  - 선택지: 20개 이하.
  - 테스트: 50개 이하. 입력 · 출력은 각각 10,000자 이하이고, 출력은 비어 있지 않아야 한다.
- 유형별
  - 객관식: 선택지 2개 이상, `answer`는 선택지 번호(`'0'`부터) 중 하나.
  - 출력 예측(`SHORT_ANSWER`): `answer`가 비어 있지 않음.
  - 코드 작성: 테스트 1개 이상.
  - 간단 제작: 비어 있지 않은 채점 기준 1개 이상.
- 순서(`position`)는 보낸 순서대로 0부터 매긴다.

## 6. 동작
- **권한**: 교수자 API는 `TeacherUser` + 과제의 클래스에 `own_class`(남의 것 403, 없는 과제 404). 학생 API는 `StudentUser` + `active_enrollment`.
- **저장**: `answer_key`는 `AnswerKey(answer, accepted_answers, misconceptions, hidden_tests, rubric, model_answer, variant)`를 JSON으로 저장한다. 빈 문자열인 정답 · 모범 답안은 `null`로 저장하고, 읽을 때 `""`로 돌려준다.
- **문항 교체**(배포 전): 그 과제의 문항을 지우고 보낸 목록으로 다시 만든다. 배포 전에는 학생 답이 없으므로 안전하다.
- **배포 후 비교**: 보낸 문항 목록을 저장할 값으로 바꾼 것과 지금 저장된 값이 개수 · 순서 · 내용까지 같아야 한다.
- **학생용 조회**: 🔒 값을 담을 필드가 응답 스키마에 없다. 공개 테스트와 숨김 테스트 개수만 준다.

## 7. 테스트 (모두 실패 먼저)
| 파일 | 확인 |
|---|---|
| `test_assignment_schemas.py` | 유형별 검증 4가지 · 길이 · 개수 상한 · 테스트 나누기와 합치기 · 같은 문항 비교 |
| `test_assignment_service.py` | 빈 초안(클래스 기본 정책) · 저장 · 조회 · 초안 문항 교체<br>**배포 후 문항 변경 → CONFLICT, 같은 문항 재전송은 통과** · 배포 후 마감 · 정책 수정 허용 · `language` 변경 거부<br>결과 공개 후 모든 수정 거부 · 문항 0개 배포 거부 · 배포 전 공개 거부 · 남의 클래스 403 |
| `test_student_assignment.py` | 승인 + 배포만 통과. 대기 · 내보낸 · 다른 클래스 학생, 초안 · 없는 과제 → 403. 힌트 라벨 · 최대 단계 · `ai_enabled` · `hidden_test_count` |
| `test_assignments_api.py` | 샘플 md 문항 모양(객관식 · 출력 예측 · 코드 · 간단 제작) 저장 → 배포 → 학생 조회<br>**학생 응답 문자열 어디에도 정답 · 숨김 테스트 입력/출력 · 모범 답안 · 채점 기준 · 오개념 · 확인 문제가 없음**<br>교수자 조회에는 모두 있음 · 401 · 403 · 목록 상태 |

## 8. 함께 고칠 문서
- `docs/planning/schema.md`
  - `public_tests` · `hidden_tests` 모양을 `{input, expected_output}`으로(A1)
  - 출력 비교 규칙(A2), 배포 후 잠금(A3)
  - 결정 사항 D23 · D24
- `docs/spec/api-contract.md`: 과제 만들기 표 — `tests` 모양, `drafts`는 BLANK만(SAMPLE은 ④-2), 잠금 규칙, `/solve` 응답 모양
- `docs/conventions/ai-code-trust.md`: **I8 추가** — "학생에게 가는 과제 응답에 🔒 값이 없다" (`tests/test_assignments_api.py`, `tests/test_student_assignment.py`)

## 9. 위험과 대응
- **프론트 타입 변경**: `TestCase`, `language` 대문자, `seq`. PR 본문 "프론트 영향"에 적는다.
- **Python 실행기 모양 불일치**: 지금 실행기는 `{call, expected}`. C 실행기를 만들 때 A1 모양으로 맞춘다(웹 B). 그 전까지 ⑦은 실행하지 않는다.
- **배포 후 오타 수정 불가**: 문항 문구도 잠긴다. 필요하면 결과 공개 전까지 문구만 고치는 기능을 나중에 추가한다.
