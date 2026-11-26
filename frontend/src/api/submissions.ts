import type { HintMode, Question } from './assignments'
import { del, get, post, put, type Language } from './client'

/** 학생에게 보내는 공개 테스트 (숨김 테스트는 개수만) */
export type PublicTest = { input: string; expected_output: string }

/** 학생에게 보내는 문항. 정답·모범 답안·숨김 테스트·확인 문제·채점 기준은 빠진다(불변식 I8) */
export type StudentQuestion = Pick<Question, 'type' | 'points' | 'prompt' | 'code' | 'choices' | 'starter_code' | 'ai_help'> & {
  seq: number
  public_tests: PublicTest[]
  hidden_test_count: number
  /** 이 문항에서 AI 도움을 쓸 수 있는지 */
  ai_enabled: boolean
}

export type StudentAssignment = {
  seq: number
  title: string
  course: string
  language: Language
  due_at: string | null
  hint_mode: HintMode
  hint_mode_label: string
  max_hint_steps: number
  external_signal_enabled: boolean
  questions: StudentQuestion[]
}

/** 공개 테스트 실행 결과 한 건 */
export type RunCaseResult = {
  input: string
  expected_output: string
  /** 시간 초과면 null */
  actual_output: string | null
  passed: boolean
  /** 실행 시간 초과 · Segmentation fault · 종료 코드 등 */
  error: string | null
}

/** 공개 테스트 실행. ok=false면 컴파일 오류 등으로 돌리지 못함(error에 gcc 메시지) */
export type RunResult = { ok: boolean; error: string | null; results: RunCaseResult[] }

/**
 * 제출 전 개념 확인. 힌트 없이 처음 낸 문항에서 내 코드에 쓴 개념을 묻는다.
 * 답변에 AI 작성 신호가 높으면 질문이 하나 더 붙는다. 판정 결과는 학생에게 보내지 않는다(교수자 참고용)
 */
export type ConceptCheck = {
  questions: string[]
  /** 답한 질문 수. questions[answered]가 지금 답할 질문 */
  answered: number
}

export type AnswerStatus = 'DRAFT' | 'AWAITING_CHECK' | 'SUBMITTED'

/** 학생이 보는 내 답. 정오·점수·숨김 테스트 결과는 교수자가 결과를 공개하기 전까지 오지 않는다 */
export type AnswerState = {
  question_id: number
  content: string
  status: AnswerStatus
  submitted_at: string | null
  submit_count: number
  hint_step: number
  concept_check: ConceptCheck | null
}

/** 붙여넣기 여부는 여기 싣지 않고 /paste-events(field = CONCEPT_CHECK)로 따로 보낸다(불변식 I5) */
export type ConceptReply = {
  reply: string
  elapsed_ms: number
}

export type Submission = {
  assignment_id: number
  /** 문항 seq → 내 답. 아직 손대지 않은 문항은 없다(화면은 시작 코드로 시작) */
  answers: Record<number, AnswerState>
  /** 최종 제출하면 답이 잠기고 AI 없이 이해 확인으로 넘어간다 */
  finalized: boolean
  /** 교수자가 결과를 공개했는지. 공개 전에는 점수·정답을 보여주지 않는다 */
  results_released: boolean
}

const base = (assignmentId: number) => `/assignments/${assignmentId}`

export const getStudentAssignment = (assignmentId: number) => get<StudentAssignment>(`${base(assignmentId)}/solve`)
export const getMySubmission = (assignmentId: number) => get<Submission>(`${base(assignmentId)}/submission`)
/** 제출 전에 공개 테스트만 실행해 본다 */
export const runPublicTests = (assignmentId: number, questionId: number, code: string) =>
  post<RunResult>(`${base(assignmentId)}/questions/${questionId}/run`, { code })
/** 문항 답 제출. 최종 제출 전까지는 고쳐서 다시 낼 수 있고 마지막 답이 채점된다 */
export const submitAnswer = (assignmentId: number, questionId: number, content: string) =>
  put<Submission>(`${base(assignmentId)}/answers/${questionId}`, { content })
/** 힌트 없이 처음 낸 문항은 바로 제출되지 않고 개념 확인(AWAITING_CHECK)을 거친다 */
export const answerConceptCheck = (assignmentId: number, questionId: number, body: ConceptReply) =>
  post<Submission>(`${base(assignmentId)}/answers/${questionId}/concept-check`, {
    reply: body.reply,
    elapsed_ms: Math.max(0, Math.round(body.elapsed_ms)),
  })
/** 개념 확인을 미루고 답을 고치러 돌아간다. 다시 제출하면 같은 질문이 이어진다 */
export const cancelConceptCheck = (assignmentId: number, questionId: number) =>
  del<Submission>(`${base(assignmentId)}/answers/${questionId}/concept-check`)
/** 과제 최종 제출. 모든 문항을 낸 뒤에만 할 수 있다 */
export const finalizeSubmission = (assignmentId: number) => post<Submission>(`${base(assignmentId)}/submission/finalize`)
