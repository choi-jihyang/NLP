# ④-1 과제 · 문항 API Implementation Plan

> **For agentic workers:** executing-plans(Native)로 이 세션에서 실행. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 교수자 과제 저장 · 조회 · 수정(배포 후 문항 잠금) · 배포 · 결과 공개와, 정답이 없는 학생용 과제 조회.

**Architecture:** `QuestionData`(교수자 요청 모양)를 `question_codec`이 테이블 값(`public_tests` · `answer_key`)으로 바꾸고, 같은 변환으로 배포 후 "같은 문항인지"를 비교한다. 학생 응답은 🔒 필드가 없는 별도 스키마로만 만든다.

**Spec:** [docs/superpowers/specs/2026-11-23-assignment-api-design.md](../specs/2026-11-23-assignment-api-design.md)

> 사용자 요청("진행. 후 개발까지")에 따라 계획은 짧게 적고 바로 실행한다. 코드는 각 Task의 테스트를 먼저 쓰고 실패를 확인한 뒤 작성한다.

## Global Constraints
- 테스트 모양 `{input, expected_output}`, 교수자 API는 `tests[{…, hidden}]`(A1).
- 배포 후 문항 · `language` 변경은 `CONFLICT`, 결과 공개 후 모든 수정 `CONFLICT`(A3 · A4).
- 학생 응답 스키마에 🔒 필드가 없다(I8). 학생 조회는 승인된 참여 + 배포된 과제만(I7).
- service는 FastAPI를 import하지 않는다. 파일 200줄 이하. 커밋 `[assignment-api] …` + Co-Authored-By. **푸시하지 않는다.**

## Review Focus
1. 객관식 정답 번호가 선택지 범위를 벗어남(`"5"`, `"-1"`, `"a"`) → 400. → Task 1
2. 배포 후 문항 순서만 바꿔 보냄 → 바뀐 것으로 보고 `CONFLICT`. → Task 2
3. 배포 후 `hidden` 표시만 바꿈(숨김 테스트를 공개로) → `CONFLICT`. → Task 2
4. 다른 클래스의 승인 학생이 이 과제 `/solve` → 403. → Task 3
5. 학생 응답에 확인 문제(`variant`)의 정답이 새지 않음. → Task 4

## Tasks
- [ ] **Task 1: Enum · 모델 · 스키마 · 변환** — `QuestionType`, `Language`, `Assignment`, `Question`, `schemas/assignments.py`, `services/question_codec.py`. 테스트 `test_assignment_schemas.py`.
- [ ] **Task 2: 교수자 과제 서비스** — `services/assignment_service.py`. 테스트 `test_assignment_service.py`.
- [ ] **Task 3: 학생용 조회** — `schemas/student_assignments.py`, `services/student_assignment_service.py`. 테스트 `test_student_assignment.py`.
- [ ] **Task 4: 라우터 · API 테스트 · 문서** — `routes/assignments.py`, `routes/solve.py`, `router.py`, schema.md · api-contract.md · ai-code-trust.md(I8). 테스트 `test_assignments_api.py`.
