# ThinkGuard — Claude 작업 가이드

작업 전에 아래 문서를 따른다. 문서와 코드가 다르면 멈추고 사람에게 묻는다.

- 작업 흐름·역할: @docs/conventions/ways-of-working.md
- 코드 구조·네이밍: @docs/conventions/coding-conventions.md
- 불변식·검증 게이트: @docs/conventions/ai-code-trust.md
- 커밋·브랜치·PR: docs/conventions/commit-convention.md, git-flow.md, pr-convention.md

## 꼭 지킬 것
- 설계 문서(`docs/planning`, `docs/spec`)에 없는 화면·API·테이블을 새로 만들지 않는다. 먼저 문서를 제안한다.
- service는 `LLMProvider`·`Classifier` 인터페이스에만 의존한다.
- 붙여넣기 내용은 저장하지 않는다(길이·시점만). 실제 결제 연동 코드를 넣지 않는다.
- 요구사항이 모호하면 추측하지 말고 질문한다.

## 검사 명령
- backend: `cd backend && .venv/bin/pytest && .venv/bin/ruff check .`
- frontend: `cd frontend && npm run build && npm run lint`
