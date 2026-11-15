# 작업 방식

> ThinkGuard 팀(웹 2 · NLP 2)이 함께 지키는 작업 흐름. Claude Code로 개발한다는 전제.
> 관련: [ai-code-trust.md](ai-code-trust.md) · [pr-convention.md](pr-convention.md) · [../planning/milestones.md](../planning/milestones.md)

## 0. 개발 준비
1. 로컬 실행은 루트 [README.md](../../README.md)를 따른다.
2. Claude Code를 쓴다면 **superpowers 플러그인**(브레인스토밍·계획·TDD·검증 스킬)을 설치한다.
   ```
   /plugin marketplace add obra/Superpowers
   ```
3. 작업 전에 이 `docs/` 폴더를 먼저 읽는다. Claude 세션은 루트 `CLAUDE.md`를 통해 자동으로 이 문서를 참고한다.

## 1. 작업 흐름
브레인스토밍 → **설계** → **계획** → 구현 → **별도 세션 검증** → 작은 PR.
- **한 번에 하나, 작게.** 기능 하나 = 브랜치 하나 = PR 하나.
- **설계 먼저.** 새 화면·API·테이블은 `docs/planning/` 또는 `docs/spec/`에 먼저 적고 팀 확인을 받은 뒤 구현한다.
- **생성자 ≠ 검증자.** 구현한 세션이 자기 코드를 "됐다"고 승인하지 않는다. → [ai-code-trust.md](ai-code-trust.md)
- 기능 하나를 끝내면 PR 본문에 **실행 방법과 확인 방법**을 적는다.

## 2. TDD — 핵심 로직부터
- **실패하는 테스트 먼저 → 최소 구현 → 리팩터.**
- 테스트 우선순위: 백엔드 핵심 로직 > API > 화면.
  - 양식 → 시스템 프롬프트 변환 (`services/prompt_builder.py`)
  - 분류 결과 → 응답 정책 분기 (`services/policy.py`)
  - 학생별 AI 사용량 상한 (`services/usage.py`)
- 발견한 버그·우회 사례(예: 학생이 정답을 받아낸 대화)는 **테스트로 고정한 뒤** 고친다.

## 3. 환경 분리 — Mock으로 먼저 완성
- 설정값은 코드에 두지 않고 **환경변수(`backend/.env`)로 주입**한다. 예시는 `backend/.env.example`.
- `.env`와 실제 키·비밀번호는 커밋하지 않는다(`.gitignore`에 포함).
- **Mock으로 먼저 끝까지 만든다.** LLM은 `LLM_PROVIDER=mock`, 분류기는 `CLASSIFIER=stub`으로 화면·흐름을 완성하고, 실제 모델은 환경변수만 바꿔 교체한다. 코드는 다시 쓰지 않는다. → [../spec/integration-contract.md](../spec/integration-contract.md)

## 4. 역할과 경계
| 담당 | 주 작업 위치 | 함께 리뷰할 곳 |
|---|---|---|
| 웹 (2명) | `frontend/`, `backend/app/api` · `models` · `schemas` | `backend/app/services` |
| NLP (2명) | `nlp/`, `backend/app/classifier/` 실제 구현 | `backend/app/services`, 분류기 계약 문서 |

- **분류기 입출력 계약**([../spec/integration-contract.md](../spec/integration-contract.md))을 바꾸려면 웹·NLP 양쪽 1명 이상이 승인한다.
- `services/`는 두 팀의 경계다. 정책 분기·프롬프트 규칙 변경은 양쪽이 함께 본다.

## 5. 이 도메인에서 특히 지킬 것
ThinkGuard의 핵심 가치는 **"AI가 학생 대신 풀지 않는다"** 이다. 아래는 기능보다 우선한다.
- AI 응답에 정답·완성 풀이·완성 코드가 그대로 나가지 않게 한다.
- AI가 학생이 하지 않은 시도·생각을 지어내서 말하지 않게 한다.
- 붙여넣기 기록은 **길이와 시점만** 저장한다. 내용은 저장하지 않는다.
- 외부 AI 의심 신호는 **참고 신호**로만 보여 준다. 점수를 바꾸거나 재풀이를 요구하지 않는다.
- 결제는 목업만 만든다. 실제 PG(결제대행) 연동 코드를 넣지 않는다.

## 요약
설계 문서 먼저 → TDD로 핵심 로직 → Mock으로 끝까지 → 별도 세션 검증 → 작은 PR(실행·확인 방법 포함).
