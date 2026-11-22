# ③ 클래스 · 참여 API 설계

> 상태: **설계 승인됨(대화)** — 2026-11-22. **11/22 개정: 다시 입장을 대기 티켓 방식으로 변경**(리뷰에서 C1 · C2 · I1 발견, §2 C1 · C2 참고)
> 관련: [schema.md](../../planning/schema.md) · [api-contract.md](../../spec/api-contract.md) · [error-handling.md](../../spec/error-handling.md) · 앞선 설계 [2026-11-21-auth-design.md](2026-11-21-auth-design.md)
> 선행: PR #7 → #8 → #10(② 인증). 이 설계는 셋이 머지된다고 보고 그 위에 만든다.

## 1. 목표와 범위
- **목표**: 시연 1·3단계가 실제 API로 동작한다.
  - 교수자: 결제(목업) → 클래스 개설 → 명단
  - 학생: 수업 코드 + 학번으로 입장 → 대기 → 교수자 수락 → 동의 → 내 클래스
  - 그리고 이후 ④⑥⑦이 쓸 **권한 확인 함수(I7)**를 둔다.
- **범위 안**: 요금제 목록, NEW 결제, 클래스 개설·목록·상세, AI 기본값, 명단·입장 방식, 학생 입장(처음 · 다시 입장), 참여 요청 수락·거절, 학생 목록·내보내기, 참여 상태 확인, 기록 동의, 내 클래스.
- **범위 밖**
  - 연장 결제(`EXTEND`)
  - `/me/classes`의 과제 목록 — ④가 생기기 전까지 빈 배열
  - 과제·채팅에서 참여 상태를 확인하는 일 — ④⑥⑦이 이 설계의 `active_enrollment`를 부른다

**성공 기준**
1. 위 시연 흐름이 API 테스트 한 개로 처음부터 끝까지 통과한다.
2. 교수자가 남의 클래스에 접근하면 403이 나온다.
3. 대기·거절·내보낸 학생이 클래스 데이터에 접근하면 403이 나온다.
4. 수업 코드와 남의 학번만으로는 그 학생 데이터에 접근할 수 없다. 교수자 수락이 필요하다.

## 2. 확정한 결정
| # | 결정 | 이유 |
|---|---|---|
| C1 | **다시 입장 = 대기 티켓.** 이미 있는 참여에 토큰 없이(또는 다른 계정으로) 들어오면 **토큰 대신 무작위 티켓**만 준다. 원래 참여 상태는 바꾸지 않는다. 교수자가 수락하면 그 티켓으로 토큰을 **한 번** 받고, 거절하면 티켓이 사라진다 | 학생은 비밀번호가 없어 코드 + 학번만으로 행세할 수 있다. 처음 설계(새 토큰 + `PENDING`)는 그 계정 토큰을 수락 전에 줘서 ① 거절하면 행세한 토큰이 통과하고 ② 그 학생의 다른 클래스가 바로 노출되고 ③ 자리가 비어 정원을 넘길 수 있었다(리뷰 C1 · C2 · I1) |
| C2 | 다시 입장 요청 구분 = `reentry_ticket_hash`가 있고 `reentry_approved_at`이 없음. `enrollments`에 컬럼 3개(`reentry_ticket_hash`, `reentry_requested_at`, `reentry_approved_at`) 추가. 티켓은 SHA-256 해시만 저장 | 수락 여부까지 저장해야 해서 컬럼 3개. 원문 티켓은 DB에 남기지 않는다 |
| C3 | 명단 저장 시 자동 수락은 **처음 참여 요청만**. 다시 입장 요청은 자동 수락하지 않음 | 명단에 있다는 것만으로 행세를 허락하면 안 됨 |
| C4 | **결제 → 개설 2단계**: `POST /payments`(NEW, 클래스 미연결 이용권) → `POST /classes {name, starts_on, payment_seq}` | 화면 흐름·schema 설명("class_id가 비어 있는 결제 = 아직 열지 않은 이용권") 그대로 |
| C5 | `class_payments.period_start`·`period_end`를 **NULL 허용**으로 변경. 개설할 때 채움 | 결제 시점에는 시작일을 모름 |
| C6 | 역할 분담과 상관없이 ③에서 `GET /plans`·`POST /payments`(NEW)까지 만든다 | 개설이 결제에 의존 |

## 3. 구성
| 파일 | 책임 |
|---|---|
| `app/services/payment_service.py` | `create_new_payment(db, teacher, plan)` |
| `app/services/class_service.py` | `create_class` (한 트랜잭션), `list_classes`, `get_class_info`, `get_ai_defaults`·`save_ai_defaults`, `get_roster`·`save_roster` |
| `app/services/enrollment_service.py` | `join`, `decide_request`, `list_requests`, `list_students`, `remove_student`, `my_enrollment`, `consent`, `my_classes` |
| `app/services/access.py` | **I7 권한 확인**:<br>`own_class(db, teacher, class_id) -> ClassRoom` — 없으면 `NOT_FOUND`, 남의 것이면 `FORBIDDEN`<br>`active_enrollment(db, student, class_id) -> Enrollment` — `APPROVED`가 아니면 `FORBIDDEN` |
| `app/schemas/classes.py` · `app/schemas/enrollments.py` | 요청·응답 모양 |
| `app/api/routes/plans.py` · `payments.py` · `classes.py` · `enrollments.py` · `me.py` | 얇은 라우터 |
| `app/api/deps.py` | `OptionalUser` 추가: 토큰이 없거나 틀리면 `None`(401을 던지지 않음) |
| `app/models/class_payment.py` | `period_start`·`period_end` nullable |

파일은 하나당 200줄 이하. 서비스는 FastAPI를 import하지 않고 `AppError`만 던진다.

## 4. API
모든 id는 `seq`(숫자). 권한: **공개** · **T**(교수자) · **S**(학생).

| 권한 | API | 요청 → 응답 |
|---|---|---|
| 공개 | `GET /plans` | → `[{code, student_limit, price}]` |
| T | `POST /payments` | `{plan, kind: "NEW"}` → 201 `{payment_seq, plan, student_limit, amount}` |
| T | `GET /classes` | → `ClassInfo[]` (내 클래스만) |
| T | `POST /classes` | `{name, starts_on, payment_seq}` → 201 `ClassInfo` |
| T | `GET /classes/{class_id}` | → `ClassInfo` |
| T | `GET`·`PUT /classes/{class_id}/ai-defaults` | `AiPolicy`. PUT은 `prompt_mode = FORM`, `custom_prompt = null`로 저장 |
| T | `GET`·`PUT /classes/{class_id}/roster` | `{join_mode, roster: [{student_no, is_use}]}` |
| T | `GET /classes/{class_id}/join-requests` | → `[{seq, student_no, requested_at, is_reentry}]` (`seq` = 참여) |
| T | `POST /classes/{class_id}/join-requests/{seq}` | `{approve: bool}` → `{status}` |
| T | `GET /classes/{class_id}/students` | → `[{seq, student_no}]` (`seq` = 학생 계정, `APPROVED`만) |
| T | `DELETE /classes/{class_id}/students/{student_id}` | → `{ok: true}` |
| 공개 (토큰 있으면 사용) | `POST /enrollments` | `{invite_code, student_no}` → `{class_id, class_name, status, access_token \| null, reentry_ticket \| null}` |
| 공개 | `POST /enrollments/reentry` | `{ticket}` → `{status, access_token \| null}` (수락 전 `PENDING` · null) |
| S | `GET /enrollments/{class_id}/me` | → `{status}` |
| S | `POST /enrollments/{class_id}/consent` | → `{ok: true}` |
| S | `GET /me/classes` | → `[{class_id, class_name, student_no, enrollment_status, assignments: []}]` |

`ClassInfo` = `{seq, name, invite_code, plan, student_limit, student_count, starts_at, expires_at}`. `student_count`는 `APPROVED` 수다.

## 5. 동작

### 5.1 결제 `POST /payments`
- `kind`가 `"NEW"`가 아니면 `VALIDATION_FAILED`.
- `PLANS[plan]`에서 `student_limit`·`price`를 꺼낸다. 클라이언트 금액은 받지 않는다.
- 행: `teacher_id`, `class_id = NULL`, `plan`, `student_limit`, `kind = NEW`, `amount = price`, `period_start`·`period_end = NULL`.
- 실제 PG 연동 없음. 항상 성공.

### 5.2 개설 `POST /classes` (한 트랜잭션)
1. `name`: 앞뒤 공백 제거 후 1–100자. `starts_on`: 오늘(KST) 이후. 위반은 `VALIDATION_FAILED`.
2. 결제 확인: 없으면 `NOT_FOUND`. 다음 중 하나라도 해당하면 `CONFLICT`.
   - 남의 결제
   - `kind ≠ NEW`
   - 이미 `class_id`가 있음
3. `starts_at = start_of_day_kst(starts_on)`, `expires_at = add_years(starts_at, 1)`.
4. 수업 코드 `TG-` + 4자리 숫자(1000–9999, `secrets` 무작위). 겹치면 다시 만들고, 10번 겹치면 `INTERNAL_ERROR`.
5. 클래스 행: `plan`·`student_limit`는 결제 행에서 복사, `join_mode = APPROVAL`, `ai_defaults` 기본 정책.
6. 결제 행 갱신: `class_id`, `period_start = starts_at`, `period_end = expires_at`. **`class_id IS NULL` 조건부 UPDATE**로, 0행이면 `CONFLICT`(동시 개설 방지).

### 5.3 입장 `POST /enrollments`
입력 정리: 수업 코드는 앞뒤 공백 제거 + 대문자. 학번은 앞뒤 공백 제거, 1–30자, 중간 공백 없음.
1. 수업 코드에 맞는 클래스가 없으면 `INVITE_CODE_INVALID`.
2. `now_kst() < starts_at`이면 `CLASS_NOT_STARTED`, `now_kst() ≥ expires_at`이면 `CLASS_EXPIRED`.
3. 요청자:
   - 유효한 **학생** 토큰이면 그 계정.
   - 교수자 토큰이면 `FORBIDDEN`.
   - 토큰이 없거나 틀리거나 만료됐으면 "토큰 없음"으로 본다.
4. 같은 `(class_id, student_no)` 참여가 **있으면**
   - `REMOVED` → `FORBIDDEN`.
   - 요청자 계정의 참여 → 상태를 그대로 두고 새 토큰을 준다. `REJECTED`였다면 `PENDING`으로 바꾸고 `decided_at = NULL`(새 요청).
   - 토큰 없음 · 다른 계정 → **다시 입장(C1)**:
     - 참여 상태는 바꾸지 않는다(자리도 그대로).
     - 무작위 티켓(`secrets.token_urlsafe(32)`)을 만들어 해시 · 요청 시각을 저장하고, `reentry_approved_at = NULL`. 이미 티켓이 있으면 새 티켓으로 바꾼다.
     - 응답: `status = PENDING`, `access_token = null`, `reentry_ticket = <티켓>`. **그 계정의 토큰은 주지 않는다.**
5. 참여가 **없으면**
   - 요청자 계정이 이 클래스에 다른 학번으로 이미 있으면 `ALREADY_ENROLLED`.
   - 요청자가 없으면 학생 계정을 만든다(`role = STUDENT`, `name = student_no`, 이메일·비밀번호 없음).
   - 사용 중(`is_use = true`) 명단에 학번이 있거나 `join_mode = OPEN`이면 `APPROVED`(`decided_at = now`), 아니면 `PENDING`.
   - `APPROVED`가 될 때 `APPROVED` 수가 `student_limit` 이상이면 `CLASS_FULL`. 참여 행을 만들지 않는다.
6. 토큰: `issue_token(계정, klass.expires_at)`. `login_at = now_kst()`.

### 5.4 참여 요청 수락·거절
- `own_class` 확인. 그 클래스의 `PENDING` 참여가 아니면 `NOT_FOUND`.
- 다시 입장 요청(C2)이면 참여 상태는 건드리지 않는다. 수락하면 `reentry_approved_at = now`, 거절하면 티켓 컬럼 3개를 비운다. 정원도 바뀌지 않는다.
- 처음 요청(`PENDING`): 수락은 `APPROVED` 수가 상한 이상이면 `CLASS_FULL`, 아니면 `APPROVED` · `decided_at = now`. 거절은 `REJECTED` · `decided_at = now`.
- 한 참여에 처음 요청과 다시 입장 요청이 함께 있으면 다시 입장 요청을 먼저 결정한다.

### 5.4.1 티켓으로 토큰 받기 `POST /enrollments/reentry {ticket}`
- 해시가 맞는 참여가 없거나 `REMOVED`면 `NOT_FOUND`.
- 아직 수락 전이면 `{status: PENDING, access_token: null}`.
- 수락됐으면 그 참여의 계정 토큰(클래스 만료까지)을 주고 티켓 컬럼 3개를 비운다(한 번만). 응답 `{status: <참여 상태>, access_token}`.

### 5.5 명단 저장 `PUT …/roster`
- `join_mode`를 저장한다.
- 보낸 학번은 `is_use = true`로 한다. 없으면 새 행을 만들고, 중복 학번은 하나로 친다.
- 보낸 목록에 없는 기존 학번은 `is_use = false`.
- 저장 뒤, 사용 중인 명단에 있는 학번의 **처음 참여 요청**(`PENDING`이고 `decided_at`이 없음)을 오래된 순으로 정원 안에서 자동 수락한다. 다시 입장 요청(티켓)은 명단과 상관없이 교수자만 수락한다.
- 요청에 같은 학번이 여러 번 있으면 하나라도 `is_use = true`면 사용으로 본다.

### 5.6 그 밖
- **내보내기**: 그 클래스의 그 학생 참여가 아니면 `NOT_FOUND`. 맞으면 `REMOVED`, `removed_at = now`. 답·대화는 지우지 않는다.
- **동의**: `active_enrollment`로 확인(`APPROVED`만). `consented_at`이 비어 있을 때만 기록한다.
- **참여 상태**: 내 참여가 없으면 `NOT_FOUND`.
- **내 클래스**: 내 참여 중 `APPROVED`·`PENDING`만, 최근 참여 순.
- **AI 기본값 저장**: `AiPolicy`로 검증하고, `prompt_mode = FORM`, `custom_prompt = None`으로 강제한 새 dict를 대입한다(JSON 안쪽만 바꾸면 저장 안 됨).

## 6. 테스트 (모두 실패 먼저)
| 파일 | 확인 |
|---|---|
| `test_class_service.py` | 결제 → 개설 시 요금제 값 복사 · `starts_at`/`expires_at` · 결제 연결<br>남의 결제 · 이미 쓴 결제 · EXTEND 거부<br>오늘 이전 시작일 거부<br>수업 코드 충돌 시 재생성<br>명단 저장(켜기 · 끄기 · 처음 요청 자동 수락 · **다시 입장 자동 수락 안 함**) |
| `test_join_service.py` · `test_enrollment_service.py` | 명단 · OPEN이면 바로 승인, 아니면 대기<br>시작 전 · 만료 · 없는 코드 · 정원 초과<br>내보낸 학번 거부<br>같은 토큰 재입장은 같은 참여<br>**토큰 없이 같은 학번 → 티켓만, 토큰 없음, 참여 상태 그대로**<br>다른 학번 중복 → `ALREADY_ENROLLED`<br>수락 시 정원 초과<br>**다시 입장 수락 → 티켓으로 토큰 한 번 / 거절 → 티켓 무효, 참여 그대로**<br>동의는 승인된 참여만 |
| `test_access.py` (I7) | 교수자 → 남의 클래스 403, 없는 클래스 404<br>대기 · 거절 · 내보낸 학생의 `active_enrollment` → 403 |
| `test_classes_api.py` · `test_enrollments_api.py` | 시연 흐름 한 줄: 교수자 가입 → 결제 → 개설 → 명단 → 학생 입장 → 대기 → 교수자 수락 → 학생 동의 → 내 클래스<br>응답 모양(`seq`, `student_no`, `is_reentry`)<br>권한 없는 호출 401 · 403 |

- `docs/conventions/ai-code-trust.md` I7 행의 "구현 시 API 테스트 추가"를 위 테스트 이름으로 채운다.
- 시각이 걸린 테스트(시작 전 · 만료)는 클래스의 `starts_at`·`expires_at`을 과거·미래로 직접 넣어 만든다(현재 시각을 바꾸지 않음).

## 7. 함께 고칠 문서
| 위치 | 변경 |
|---|---|
| `docs/planning/schema.md` | `class_payments.period_start`·`period_end` nullable(C5), `enrollments` 티켓 컬럼 3개 · UNIQUE(`class_id`, `student_id`), 결정 사항 D21(다시 입장 C1·C2), D22(결제 → 개설 C4) |
| `docs/spec/api-contract.md` | 클래스·참여 표:<br>`alias` → `student_no`, `{id…}` → `{seq…}`<br>`POST /classes` 요청 `{name, starts_on, payment_seq}`<br>`/payments` NEW만<br>`join-requests`에 `is_reentry`<br>roster 모양 `{student_no, is_use}[]`<br>다시 입장 규칙 |
| `docs/conventions/ai-code-trust.md` | I7 확인 위치에 테스트 파일 이름 |

## 8. 위험과 대응
- **교수자가 행세한 사람의 다시 입장을 수락하면** 그 사람이 토큰을 받는다 → 교수자가 요청자를 확인하고 수락해야 한다. 학생 목록에 "다시 입장 요청"이 따로 보인다.
- **남이 같은 학번으로 다시 요청하면 앞선 티켓이 바뀐다** → 진짜 학생은 다시 요청하면 된다. 원래 참여·기존 기기는 막히지 않는다.
- **다시 입장 수락 뒤 옛 토큰 · 새 토큰이 모두 유효** → 토큰 취소는 범위 밖(② 설계 §7).
- 내보낸 학생이 **다른 학번**으로 새로 들어오는 것은 막지 않는다(새 계정이라 옛 기록은 볼 수 없음). 명단 + `APPROVAL` 방식으로 막는다.
- 수업 코드가 동시 개설에서 겹치면 500이 날 수 있다(시연 규모에서 감수).
- **수업 코드 4자리(9,000개)** → 시연 규모에서 충분. 겹치면 재생성.
- **동시 요청**(같은 결제로 두 번 개설, 정원 마지막 한 자리) → 개설은 조건부 UPDATE로 막는다. 정원은 SQLite에서 트랜잭션이 직렬이라 시연 규모에서 감수. PostgreSQL 전환 때 행 잠금 검토.
