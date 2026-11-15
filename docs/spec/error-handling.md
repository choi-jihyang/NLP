# 백엔드 에러 응답 표준

> 상태: **설계 초안. 첫 기능 API(auth) 구현 때 함께 TDD로 구현.**
> 관련: [../conventions/coding-conventions.md](../conventions/coding-conventions.md) · [api-contract.md](api-contract.md)

## 결정 사항
1. **에러만 표준화한다.** 성공 응답은 각 API의 Pydantic 응답 모델 그대로.
2. **에러 바디** = `{ "code": str, "message": str, "trace_id": str }`
   - `code`: `UPPER_SNAKE` 문자열 — 프론트 분기 키.
   - `message`: 화면에 그대로 띄울 수 있는 **한국어** 문장. 내부 스택·SQL·비밀값 노출 금지.
   - `trace_id`: 요청마다 만드는 ID. 응답 헤더 `X-Request-Id`와 같다. 서버 로그와 대조용.
3. 프론트는 `code`로 분기하고, 모르는 `code`면 `message`를 그대로 보여 준다.

## 구성
`backend/app/core/errors.py`
| 이름 | 책임 |
|---|---|
| `ErrorCode` | Enum. 항목마다 HTTP 상태 + 기본 메시지 |
| `AppError(Exception)` | service가 던지는 예외. `AppError(ErrorCode.CLASS_FULL)` |
| 예외 핸들러 | `main.py`에 등록. 예외 → 표준 바디 |
| 요청 ID 미들웨어 | `trace_id` 생성, `X-Request-Id` 헤더 |

- service는 `fastapi.HTTPException`을 쓰지 않고 `AppError`를 던진다(service가 FastAPI에 의존하지 않게).

## ErrorCode 카탈로그
| code | HTTP | 기본 메시지 |
|---|---|---|
| `VALIDATION_FAILED` | 400 | 입력 값이 올바르지 않습니다. |
| `UNAUTHORIZED` | 401 | 로그인이 필요합니다. |
| `FORBIDDEN` | 403 | 접근 권한이 없습니다. |
| `NOT_FOUND` | 404 | 대상을 찾을 수 없습니다. |
| `CONFLICT` | 409 | 요청이 현재 상태와 충돌합니다. |
| `INTERNAL_ERROR` | 500 | 일시적인 오류가 발생했습니다. |
| `EMAIL_TAKEN` | 409 | 이미 가입된 이메일입니다. |
| `INVALID_CREDENTIALS` | 401 | 이메일 또는 비밀번호가 올바르지 않습니다. |
| `INVITE_CODE_INVALID` | 404 | 초대 코드를 찾을 수 없습니다. |
| `CLASS_FULL` | 409 | 클래스 정원이 가득 찼습니다. |
| `CLASS_EXPIRED` | 409 | 이용 기간이 끝난 클래스입니다. |
| `ALREADY_ENROLLED` | 409 | 이미 참여한 클래스입니다. |
| `ALREADY_SUBMITTED` | 409 | 이미 제출한 과제입니다. |
| `CLASSIFIER_UNAVAILABLE` | 503 | AI 도움을 잠시 쓸 수 없습니다. 잠시 후 다시 시도해 주세요. |
| `LLM_UNAVAILABLE` | 503 | AI 도움을 잠시 쓸 수 없습니다. 잠시 후 다시 시도해 주세요. |

> 사용량 상한 도달은 **에러가 아니다.** 채팅 API가 200으로 안내 메시지(`response_mode = "USAGE_LIMIT"`)를 돌려준다.

## 핸들러 매핑
| 예외 | 결과 |
|---|---|
| `AppError` | 그 `ErrorCode`의 상태·code, message(지정 시 덮어씀) |
| `RequestValidationError` (Pydantic) | `VALIDATION_FAILED` 400. message는 위반 필드 요약 |
| 그 외 모든 예외 | `INTERNAL_ERROR` 500. **원본 메시지 숨김**, 원본은 서버 로그에만 |

## 수용 기준
1. `AppError(ErrorCode.CLASS_FULL)` → 409 + `{code:"CLASS_FULL", message, trace_id}`.
2. 필수 필드 빠진 요청 → 400 + `VALIDATION_FAILED`.
3. 처리 안 된 `RuntimeError("db password=...")` → 500 + 고정 메시지, 원본 문자열이 응답에 없음.
4. 모든 에러 바디의 `trace_id` = 응답 헤더 `X-Request-Id`.
5. 정상 요청 응답에는 영향 없음.

## 테스트
- 테스트 전용 라우터(테스트 파일 안에서만 등록)로 각 예외를 일부러 발생시켜 `TestClient`로 확인.
- 수용 기준마다 실패 테스트 먼저 → 구현.
