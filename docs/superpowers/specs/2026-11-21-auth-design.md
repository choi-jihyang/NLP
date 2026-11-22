# ② 인증 설계 (에러 형식 · JWT · 교수자 가입·로그인 · 권한 의존성)

> 상태: **설계 승인됨(대화), 문서 검토 대기** — 2026-11-21
> 관련: [schema.md](../../planning/schema.md) · [api-contract.md](../../spec/api-contract.md) · [error-handling.md](../../spec/error-handling.md) · 앞선 계획 [2026-11-21-db-models.md](../plans/2026-11-21-db-models.md)
> 선행: PR #7(`feature/db-foundation`), PR #8(`feature/db-models`) — 이 설계는 두 PR이 머지된다고 보고 그 위에 만든다.

## 1. 목표와 범위
- **목표**: 교수자가 가입·로그인해 토큰을 받고, 이후 모든 API가 같은 방식으로 "누가 요청했는지 · 어떤 역할인지"를 확인하며, 에러는 하나의 형식으로 응답한다.
- **범위 안**
  - 에러 형식 (`error-handling.md` 그대로 구현)
  - JWT 발급·검증
  - `POST /api/auth/signup`, `POST /api/auth/login`
  - 권한 의존성 `get_current_user` · `require_teacher` · `require_student`
- **범위 밖**
  - 학생 입장(`POST /enrollments`: 수업 코드 + 학번 → 학생 계정 · 토큰) → **③ 클래스 API**. ③은 ②의 `issue_token()`을 부른다.
  - 내보낸 학생(`REMOVED`) 차단, 남의 클래스 접근 차단(I7) → ③에서 요청마다 참여 상태로 확인
  - 프론트에서 토큰 저장 · `Authorization` 헤더 붙이기(`frontend/src/api/client.ts`) → 화면 담당

**성공 기준**
1. 교수자가 가입·로그인하면 `{access_token, user}`를 받는다.
2. 토큰이 없거나 틀리거나 만료되면 401, 역할이 다르면 403이 `{code, message, trace_id}` 형식으로 나온다.
3. 처리 안 된 예외는 원문을 숨긴 500으로 나온다.

## 2. 확정한 결정
| # | 결정 | 이유 |
|---|---|---|
| A1 | 학생 입장은 ③으로 | 명단·입장 방식·정원·시작 전 같은 클래스 규칙을 대부분 써서 |
| A2 | 토큰: PyJWT(HS256) + FastAPI 의존성. 새 테이블 없음 | 의존성 1개, 스키마 변경 없음. 즉시 취소가 필요한 경우(내보낸 학생)는 ③에서 참여 상태로 막음 |
| A3 | 토큰 유효 기간: 교수자 12시간(`TEACHER_TOKEN_HOURS`), 학생 = 그 클래스 `expires_at`까지 | 학생은 비밀번호가 없어 토큰이 계정을 잇는 유일한 수단 |
| A4 | **모든 테이블 PK 이름은 `seq`**, 값은 숫자. API 응답 필드도 `seq`(숫자). FK 이름(`teacher_id`, `class_id`, `student_id`)은 그대로 두고 각 테이블의 `seq`를 가리킨다 | `users.id`가 사람이 입력하는 로그인 ID처럼 보이는 혼동을 없앰. DB와 API 이름을 같게(코딩 규칙) |
| A5 | 로그인 ID는 `users.email`, 학번은 `enrollments.student_no`(로그인 ID와 별개) | 지금 스키마 그대로. 나중에 학생 단독 가입도 이메일로 |
| A6 | 가입은 누구나 교수자로 가능 | 시연용 프로토타입 |

## 3. 구성
| 파일 | 책임 |
|---|---|
| `app/core/errors.py` | `ErrorCode` Enum(HTTP 상태 + 한국어 기본 메시지), `AppError(Exception)`. service는 이것만 던진다(FastAPI에 의존하지 않음) |
| `app/api/errors.py` | 예외 핸들러 3개(`AppError` · `RequestValidationError` · 그 외), 요청 ID 미들웨어. `main.py`에서 등록 |
| `app/core/tokens.py` | `issue_token(user, expires_at) -> str`, `decode_token(token) -> TokenClaims` |
| `app/services/auth_service.py` | `signup(db, name, email, password) -> AuthResult`, `login(db, email, password) -> AuthResult` |
| `app/api/deps.py` | `get_current_user`, `require_teacher`, `require_student` |
| `app/schemas/auth.py` | `SignupRequest`, `LoginRequest`, `UserOut{seq, name, email, role}`, `AuthResponse{access_token, user}` |
| `app/api/routes/auth.py` | 두 엔드포인트. 요청 검증 → service 호출 → 응답 변환만 |
| `app/core/config.py` · `backend/.env.example` | `jwt_secret`(필수, 32자 이상), `teacher_token_hours: int = 12` |
| `backend/requirements.txt` | `PyJWT` 추가 |

## 4. 동작

### 4.1 가입 `POST /api/auth/signup`
요청 `{name, email, password}` → **201** `{access_token, user}`
- `name`: 앞뒤 공백 제거 후 1–100자.
- `email`: 앞뒤 공백 제거 + 소문자로 저장. `@`가 있는 간단한 형식 검사(의존성 추가 없음), 255자 이하. 이미 있으면 `EMAIL_TAKEN`(409).
- `password`: 8–128자. UTF-8로 인코딩할 수 없는 문자(짝 없는 surrogate)는 거부. 위반은 `VALIDATION_FAILED`(400).
- 만들어지는 계정: `role = TEACHER`, `password_hash = hash_password(password)`, `login_at = now_kst()`. 교수자 토큰 발급.

### 4.2 로그인 `POST /api/auth/login`
요청 `{email, password}` → **200** `{access_token, user}`
- 이메일을 가입과 같은 방식으로 정리해서 찾는다.
- 다음 경우는 모두 같은 `INVALID_CREDENTIALS`(401, "이메일 또는 비밀번호가 올바르지 않습니다."):
  - 계정 없음
  - `password_hash`가 없는 계정(수업 코드로 입장한 학생)
  - 비밀번호 틀림
- 계정이 없을 때도 미리 만든 가짜 해시로 `verify_password`를 한 번 돌린다(응답 시간으로 가입 여부를 알 수 없게).
- 성공하면 `login_at = now_kst()`로 갱신하고 교수자 토큰을 준다.
- 학생 계정으로는 로그인할 수 없다. 이메일이 없으므로 찾을 수 없다.

### 4.3 토큰
- PyJWT HS256. 클레임은 아래 넷.
  - `sub`: `str(user.seq)`. JWT 표준상 문자열이며 토큰 안에서만 그렇다.
  - `role`
  - `iat`
  - `exp`
- `issue_token(user, expires_at)` — 교수자는 `now_kst() + teacher_token_hours`, 학생은 ③이 클래스 `expires_at`을 넘긴다.
- `decode_token`은 서명 오류·만료·형식 오류를 모두 `AppError(UNAUTHORIZED)`로 바꾼다.
- `jwt_secret`이 비었거나 32자 미만이면 설정 로드 단계에서 실패해 앱이 시작되지 않는다. `.env.example`에는 "바꿔서 쓰세요" 자리 표시 값만 둔다.

### 4.4 권한 의존성
- `get_current_user`
  - `Authorization: Bearer <token>`이 없거나 형식이 틀리면 `UNAUTHORIZED`(401).
  - 토큰 검증에 실패하면 401.
  - `sub`의 사용자를 DB에서 찾고, 없으면 401.
  - **역할은 토큰 값이 아니라 DB의 `role`** 기준.
- `require_teacher`: 교수자가 아니면 `FORBIDDEN`(403). `require_student`: 학생이 아니면 403.
- 경로의 id(`/classes/{class_id}` 등)는 숫자(`int`)로만 받는다. 숫자가 아니면 `VALIDATION_FAILED`(400).

### 4.5 에러 형식 (`error-handling.md` 구현)
- 모든 에러 바디: `{code, message, trace_id}`. `trace_id` = 응답 헤더 `X-Request-Id`. 정상 응답에도 `X-Request-Id`를 붙인다.
- `AppError` → 그 코드의 HTTP 상태 · code · message(지정하면 덮어씀).
- `RequestValidationError` → 400 `VALIDATION_FAILED`, message = "입력 값이 올바르지 않습니다: <필드 이름들>".
- 그 외 예외 → 500 `INTERNAL_ERROR`, 고정 메시지. 원문은 서버 로그에만 남긴다.
- 비밀번호 원문은 로그·에러 메시지 어디에도 남기지 않는다.
- `ErrorCode`에는 `error-handling.md` 카탈로그 전체를 정의한다. 이번 PR이 실제로 쓰는 것은 아래 여섯이다.
  - `VALIDATION_FAILED`
  - `UNAUTHORIZED`
  - `FORBIDDEN`
  - `EMAIL_TAKEN`
  - `INVALID_CREDENTIALS`
  - `INTERNAL_ERROR`

## 5. 테스트 (모두 실패 먼저)
| 파일 | 확인 |
|---|---|
| `test_errors.py` | `error-handling.md` 수용 기준 5개(테스트 전용 라우터):<br>① `AppError(CLASS_FULL)` → 409 + 형식<br>② 필수 필드 누락 → 400<br>③ `RuntimeError("db password=...")` → 500, 원문 없음<br>④ `trace_id` = `X-Request-Id`<br>⑤ 정상 응답 영향 없음 |
| `test_tokens.py` | 발급 → 해석 시 `sub`·`role` 일치<br>만료 · 다른 키 서명 · 깨진 문자열은 거부<br>32자 미만 키는 설정 단계에서 거부 |
| `test_auth_service.py` | 가입 → 교수자 계정 + `login_at`<br>이메일 대소문자·공백 정리<br>중복 이메일 → `EMAIL_TAKEN`<br>로그인 → `login_at` 갱신<br>없는 계정 · 틀린 비밀번호 · 비밀번호 없는 학생 계정 → 모두 같은 `INVALID_CREDENTIALS` |
| `test_auth_api.py` | 가입 201 + `{access_token, user{seq, name, email, role}}`<br>비밀번호 7자 · 129자 · surrogate → 400<br>로그인 200 / 실패 401 |
| `test_deps.py` | 헤더 없음 · `Bearer` 아님 · 만료 · 지워진 계정 → 401<br>교수자 전용 경로에 학생 토큰 → 403<br>토큰 `role`과 DB `role`이 다르면 DB를 따름 |

- 테스트 DB는 메모리 SQLite 픽스처(`tests/conftest.py`). API 테스트는 `app.dependency_overrides[get_db]`로 그 세션을 끼워 실제 `thinkguard.db`를 건드리지 않는다.
- 테스트용 `JWT_SECRET`은 픽스처에서 설정한다(실제 키 아님).

## 6. 이 설계로 함께 고칠 곳 (A4 `seq`)
| 위치 | 변경 |
|---|---|
| `docs/planning/schema.md` | 공통 규칙 "`id` (INTEGER PK)" → "`seq`", 모든 테이블 표의 `id` 행 → `seq`, 결정 사항에 추가 |
| PR #8 모델 5개 · 테스트 · 시드 | `id` → `seq` (FK 대상 `users.seq` 등) |
| `docs/spec/api-contract.md` | 공통 규칙에 "id 필드는 `seq`, 숫자" · 응답 예시의 id |
| `frontend/src/api/*.ts` 타입 | `id: string` → `seq: number` (화면 담당) |

## 7. 위험과 대응
- **비밀키 유출·약한 키** → 32자 미만이면 시작 거부. `.env`는 커밋하지 않는다(`.gitignore`).
- **가입 여부 노출** → 로그인 실패 응답을 하나로, 응답 시간도 가짜 해시로 맞춤.
- **토큰 탈취 시 12시간 · 클래스 만료까지 유효** → 프로토타입 범위에서 감수. 학생 내보내기는 ③에서 참여 상태로 즉시 막는다.
