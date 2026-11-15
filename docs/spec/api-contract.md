# API 계약

> 상태: **초안** — [../planning/schema.md](../planning/schema.md)의 결정 필요 항목(D1–D5)에 따라 바뀔 수 있다.
> 공통: 모든 경로는 `/api` 아래. 요청·응답은 JSON, 필드는 snake_case. 에러 형식은 [error-handling.md](error-handling.md).
> 실제 스펙은 서버를 띄운 뒤 `http://localhost:8000/docs`(Swagger)에서 확인한다. 이 문서와 다르면 이 문서를 고친다.

## 인증
- 로그인 응답의 `access_token`을 `Authorization: Bearer <token>` 헤더로 보낸다.
- 토큰 클레임: `sub`(user id), `role`(`TEACHER`/`STUDENT`), `exp`.
- 권한 열: **공개** = 토큰 불필요 / **T** = 교수자 / **S** = 학생 / **T·S** = 둘 다.
- 교수자는 **자기 클래스만**, 학생은 **참여한 클래스만** 접근한다. 아니면 `FORBIDDEN`(불변식 I7).

## 목록

### 상태
| 메서드 | 경로 | 권한 | 설명 | 구현 |
|---|---|---|---|---|
| GET | `/health` | 공개 | 서버 상태, 현재 LLM·분류기 종류 | ✅ |

### 인증 · 계정
| 메서드 | 경로 | 권한 | 설명 |
|---|---|---|---|
| POST | `/auth/signup` | 공개 | `{email, password, name, role}` → 사용자 |
| POST | `/auth/login` | 공개 | `{email, password}` → `{access_token, user}` |
| GET | `/me` | T·S | 내 정보 |

### 요금제 · 결제 (목업)
| 메서드 | 경로 | 권한 | 설명 |
|---|---|---|---|
| GET | `/plans` | 공개 | Starter/Pro/Master 정보(이름, 학생 수 상한, 단가) |
| POST | `/classes/{class_id}/payments` | T | 결제 목업 `{plan, student_count, kind: NEW\|EXTEND}` → 이용 기간 갱신 |

### 클래스
| 메서드 | 경로 | 권한 | 설명 |
|---|---|---|---|
| GET | `/classes` | T·S | 교수자: 내가 개설한 클래스 / 학생: 참여한 클래스 |
| POST | `/classes` | T | `{name, student_limit, plan}` → 클래스 + `invite_code` |
| GET | `/classes/{class_id}` | T·S | 상세 (교수자에게만 `invite_code` 포함) |
| GET | `/classes/{class_id}/students` | T | 참여 학생 목록 |
| POST | `/enrollments` | S | `{invite_code}` → 참여. 오류: `INVITE_CODE_INVALID`, `CLASS_FULL`, `CLASS_EXPIRED`, `ALREADY_ENROLLED` |

### 학습 AI 설정
| 메서드 | 경로 | 권한 | 설명 |
|---|---|---|---|
| GET | `/classes/{class_id}/ai-settings` | T | 현재 설정 |
| PUT | `/classes/{class_id}/ai-settings` | T | `{subject_type, hints_enabled, max_hint_steps, concept_check_enabled, usage_limit}` |
| GET | `/classes/{class_id}/ai-settings/preview` | T | "학생은 이렇게 경험해요" 요약 문장 목록 (시스템 프롬프트 원문은 보여 주지 않음) |

### 과제 · 문항
| 메서드 | 경로 | 권한 | 설명 |
|---|---|---|---|
| GET | `/classes/{class_id}/assignments` | T·S | 과제 목록 (학생에겐 공개된 것만 + 내 제출 상태) |
| POST | `/classes/{class_id}/assignments` | T | `{title, due_at, questions[]}` 생성 |
| GET | `/assignments/{assignment_id}` | T·S | 과제 + 문항. **학생 응답에는 정답·모범 답안 제외** |
| PUT | `/assignments/{assignment_id}` | T | 수정 (제출이 생긴 뒤에는 배점·정답 수정 제한 — 정책 미정) |
| POST | `/assignments/{assignment_id}/publish` | T | 학생에게 공개 |

### 풀이 · 제출
| 메서드 | 경로 | 권한 | 설명 |
|---|---|---|---|
| GET | `/assignments/{assignment_id}/submission` | S | 내 제출(없으면 `IN_PROGRESS`로 생성) + 문항별 답·힌트 단계 |
| PUT | `/submissions/{submission_id}/answers/{question_id}` | S | 답 임시 저장 `{content}` |
| POST | `/submissions/{submission_id}/answers/{question_id}/concept-check` | S | 혼자 푼 문항: 개념 확인 질문 받기 → `{question_text}` |
| PUT | `/submissions/{submission_id}/answers/{question_id}/concept-check` | S | 개념 확인 답변 `{reply}` |
| POST | `/submissions/{submission_id}/submit` | S | 제출 → 객관식·단답형 자동 채점. 개념 확인이 필요한 문항이 남았으면 `CONFLICT` |

### 학습 AI 채팅
| 메서드 | 경로 | 권한 | 설명 |
|---|---|---|---|
| GET | `/questions/{question_id}/chat` | S | 이 문항의 내 대화 + `hint_step`, `max_hint_steps`, 남은 사용량 |
| POST | `/questions/{question_id}/chat` | S | `{message}` → `{reply, response_mode, hint_step, usage_remaining}` |

- 제출한 문항·서술형 문항은 `FORBIDDEN`(AI 도움 잠김).
- 학생 응답에는 분류 결과 원본(`confidence` 등)을 넣지 않는다. 교수자 대시보드와 로그에서만 쓴다.

### 붙여넣기 기록
| 메서드 | 경로 | 권한 | 설명 |
|---|---|---|---|
| POST | `/paste-events` | S | `{question_id, field, length, pasted_at}` — **내용 필드 없음**. 서버는 알 수 없는 필드를 거부한다 |

### 채점 · 분석 (교수자)
| 메서드 | 경로 | 권한 | 설명 |
|---|---|---|---|
| GET | `/assignments/{assignment_id}/grading` | T | 서술형 답안 목록(학생, 답, 붙여넣기 신호, 채점 상태) |
| PUT | `/answers/{answer_id}/grade` | T | `{score, feedback}` 확정. `0 ≤ score ≤ points` |
| GET | `/assignments/{assignment_id}/analytics` | T | 문항별 오답률, 평균 힌트 단계, 오답 분포, 개념 확인 결과, 붙여넣기 신호 요약 |

## 채팅 예시
```json
// POST /api/questions/12/chat
{ "message": "정답만 빨리 알려주세요" }

// 200
{ "reply": "완성된 답 대신 힌트를 드릴게요. 두 근의 합은 계수만으로 구할 수 있어요. …",
  "response_mode": "HINT_ONLY",
  "hint_step": 1,
  "usage_remaining": 27 }
```
