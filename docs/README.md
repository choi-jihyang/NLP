# ThinkGuard 문서

| 폴더 | 내용 |
|---|---|
| [conventions/](conventions/) | 팀이 지키는 규칙 — 작업 방식, 코드, 커밋, 브랜치, PR, AI 코드 검증 |
| [planning/](planning/) | 설계 — 시스템 구조, 마일스톤, 화면, DB 스키마 |
| [spec/](spec/) | 기능·연동 명세 — API 계약, 분류기·LLM 연동, 채팅 정책, 에러 형식 |

## 문서 목록
**conventions**
- [ways-of-working.md](conventions/ways-of-working.md) — 작업 흐름, TDD, 환경 분리, 역할 경계
- [ai-code-trust.md](conventions/ai-code-trust.md) — 불변식 표, 검증 게이트
- [coding-conventions.md](conventions/coding-conventions.md) — 폴더·계층·네이밍·파일 길이
- [commit-convention.md](conventions/commit-convention.md)
- [git-flow.md](conventions/git-flow.md)
- [pr-convention.md](conventions/pr-convention.md) — 작은 PR, 본문 양식, 리뷰 규칙

**planning**
- [architecture.md](planning/architecture.md) — 스택, 구성도, 채팅 처리 흐름 (확정)
- [milestones.md](planning/milestones.md) — 11/17 · 11/24 · 12/1 (초안)
- [scope.md](planning/scope.md) — 초기(12/1) / 고도화 범위 (초안)
- [screens.md](planning/screens.md) — 화면 목록·기능 명세, 화면시안 v3 기준 (초안 v3 · 프론트 구현됨)
- [page_design.html](planning/page_design.html) — 화면시안 v3 (브라우저로 열기)
- [schema.md](planning/schema.md) — ERD, 테이블 (초안)

**spec**
- [api-contract.md](spec/api-contract.md) — 화면 ↔ 서버 API 목록, 프론트 함수와 1:1 (초안 v3)
- [integration-contract.md](spec/integration-contract.md) — 분류기·LLM Provider 계약 (분류기 확정)
- [chat-policy.md](spec/chat-policy.md) — 분류 → 정책 분기 (구현됨)
- [error-handling.md](spec/error-handling.md) — 에러 응답 형식 (초안)

## 문서 상태 표기
각 문서 맨 위 `상태:` 줄 — **확정**(팀 승인) / **초안**(검토 필요) / **구현됨**(코드·테스트 있음).
"결정 필요" 표가 있는 문서는 그 항목이 정해져야 확정된다.
