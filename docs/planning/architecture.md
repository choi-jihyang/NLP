# 시스템 구조

> 상태: **확정** (2026-11-15 팀 승인). 디렉터리 규칙 세부는 [../conventions/coding-conventions.md](../conventions/coding-conventions.md).

## 기술 스택
| 영역 | 선택 | 이유 |
|---|---|---|
| 프론트 | React + TypeScript, **Vite** | 백엔드가 FastAPI로 따로 있어 Next.js의 서버 기능이 필요 없음. 설정이 적고 빠름 |
| 라우팅 · 서버 상태 | React Router, TanStack Query | |
| 백엔드 | Python **FastAPI** | NLP 팀과 같은 언어 → 분류기를 모듈로 바로 붙일 수 있음 |
| DB | SQLAlchemy 2.0 + **SQLite** | `DATABASE_URL`만 바꾸면 PostgreSQL 전환 |
| 인증 | JWT, 역할 2개(교수자/학생) | |
| LLM | Provider 인터페이스: Mock / Ollama | [../spec/integration-contract.md](../spec/integration-contract.md) |

## 구성도
```
[브라우저: React]  ──/api/*──▶  [FastAPI]
                                  ├─ api/routes      HTTP 입출력
                                  ├─ services        로직 (프롬프트·정책·사용량·채팅)
                                  ├─ models  ──▶ [SQLite / PostgreSQL]
                                  ├─ llm     ──▶ Mock | [Ollama 로컬 서버 :11434]
                                  └─ classifier ─▶ 키워드 스텁 | nlp 모듈 | [NLP 서버 :8001]
```
- 개발 중에는 Vite 개발 서버(5173)가 `/api` 요청을 FastAPI(8000)로 넘긴다(프록시).

## 학생 메시지 한 건의 처리 흐름
```
학생 메시지
 → usage.check()                 상한 도달 → 안내 메시지, LLM 호출 안 함        (미구현)
 → classifier.classify(msg, history)
 → policy.decide(분류 결과)       힌트만 / 되묻기 / 학습 외 / 다음 단계 안내       (구현됨)
 → prompt_builder.compose(AI 설정 프롬프트, 정책 지시)                          (compose 구현, 설정 변환 미구현)
 → llm.generate(system, history + msg)
 → 대화·분류 결과·사용량 저장 → 응답                                              (미구현)
```
세부 정책: [../spec/chat-policy.md](../spec/chat-policy.md)

## 환경변수로 바꾸는 것
| 변수 | 값 | 기본 |
|---|---|---|
| `LLM_PROVIDER` | `mock` · `ollama` | `mock` |
| `CLASSIFIER` | `stub` · `module` · `http` | `stub` |
| `DATABASE_URL` | SQLAlchemy URL | `sqlite:///./thinkguard.db` |

전체 목록: `backend/.env.example`
