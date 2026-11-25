import type { HintMode, ProgrammingLanguage, Question, TestCase } from './assignments'
import { del, get, langToUi, nid, post, put, sid, type BackendLanguage } from './client'
import { logPaste } from './pasteEvents'

/** 학생에게 보내는 문항. 정답·모범 답안·숨김 테스트 입력·확인 문제는 빠진다 */
export type StudentQuestion = Omit<
  Question,
  'answer' | 'accepted_answers' | 'misconceptions' | 'model_answer' | 'tests' | 'variant' | 'rubric'
> & {
  public_tests: TestCase[]
  hidden_test_count: number
  /** 이 문항에서 AI 도움을 쓸 수 있는지 */
  ai_enabled: boolean
}

export type StudentAssignment = {
  id: string
  title: string
  course: string
  language: ProgrammingLanguage
  due_at: string | null
  hint_mode: HintMode
  hint_mode_label: string
  max_hint_steps: number
  external_signal_enabled: boolean
  questions: StudentQuestion[]
}

/** 공개 테스트 실행 결과 한 건. `call` = 표준 입력, `expected` = 기대 출력 */
export type TestResult = {
  call: string
  expected: string
  actual: string
  passed: boolean
  hidden: boolean
  /** 컴파일 오류 · 시간 초과 · 세그폴트 등 */
  error?: string | null
}

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
  question_id: string
  content: string
  status: AnswerStatus
  submitted_at: string | null
  hint_step: number
  concept_check: ConceptCheck | null
}

export type ConceptReply = {
  reply: string
  /** 붙여넣기 여부와 답하는 데 걸린 시간. 붙여 넣은 내용은 따로 저장하지 않는다 */
  pasted: boolean
  elapsed_ms: number
}

export type Submission = {
  assignment_id: string
  answers: Record<string, AnswerState>
  /** 최종 제출하면 답이 잠기고 AI 없이 이해 확인으로 넘어간다 */
  finalized: boolean
  /** 교수자가 결과를 공개했는지. 공개 전에는 점수·정답을 보여주지 않는다 */
  results_released: boolean
}

// ---------- 백엔드 모양 ↔ 화면 모양 ----------

type StudentQuestionOut = Omit<StudentQuestion, 'id' | 'public_tests'> & {
  seq: number
  public_tests: { input: string; expected_output: string }[]
}
type StudentAssignmentOut = Omit<StudentAssignment, 'id' | 'language' | 'questions'> & {
  seq: number
  language: BackendLanguage
  questions: StudentQuestionOut[]
}
type AnswerStateOut = Omit<AnswerState, 'question_id'> & { question_id: number; submit_count: number }
type SubmissionOut = { assignment_id: number; answers: Record<string, AnswerStateOut>; finalized: boolean; results_released: boolean }
type RunOut = {
  ok: boolean
  error: string | null
  results: { input: string; expected_output: string; actual_output: string | null; passed: boolean; error: string | null }[]
}

const toSubmission = (s: SubmissionOut): Submission => ({
  assignment_id: sid(s.assignment_id),
  finalized: s.finalized,
  results_released: s.results_released,
  answers: Object.fromEntries(
    Object.entries(s.answers).map(([qid, a]) => [qid, { ...a, question_id: sid(a.question_id) }]),
  ),
})

const base = (assignmentId: string) => `/assignments/${nid(assignmentId)}`

export const getStudentAssignment = async (assignmentId: string): Promise<StudentAssignment> => {
  const { seq, language, questions, ...a } = await get<StudentAssignmentOut>(`${base(assignmentId)}/solve`)
  return {
    ...a,
    id: sid(seq),
    language: langToUi(language),
    questions: questions.map(({ seq: qseq, public_tests, ...q }) => ({
      ...q,
      id: sid(qseq),
      public_tests: public_tests.map((t) => ({ call: t.input, expected: t.expected_output, hidden: false })),
    })),
  }
}
export const getMySubmission = async (assignmentId: string) =>
  toSubmission(await get<SubmissionOut>(`${base(assignmentId)}/submission`))
/** 제출 전에 공개 테스트만 실행해 본다. 컴파일 오류면 모든 줄의 error에 gcc 메시지가 들어간다 */
export const runPublicTests = async (assignmentId: string, questionId: string, code: string): Promise<TestResult[]> => {
  const r = await post<RunOut>(`${base(assignmentId)}/questions/${nid(questionId)}/run`, { code })
  return r.results.map((t) => ({
    call: t.input,
    expected: t.expected_output,
    actual: t.actual_output ?? t.error ?? r.error ?? '',
    passed: t.passed,
    hidden: false,
    error: t.error ?? r.error,
  }))
}
/** 문항 답 제출. 최종 제출 전까지는 고쳐서 다시 낼 수 있고 마지막 답이 채점된다 */
export const submitAnswer = async (assignmentId: string, questionId: string, content: string) =>
  toSubmission(await put<SubmissionOut>(`${base(assignmentId)}/answers/${nid(questionId)}`, { content }))
/**
 * 힌트 없이 처음 낸 문항은 바로 제출되지 않고 개념 확인(AWAITING_CHECK)을 거친다.
 * 붙여넣기 여부는 본문에 싣지 않고 /paste-events(길이 · 시점만)로 따로 보낸다(불변식 I5).
 */
export const answerConceptCheck = async (assignmentId: string, questionId: string, body: ConceptReply) => {
  if (body.pasted) {
    await logPaste({ question_id: questionId, field: 'CONCEPT_CHECK', length: body.reply.length, pasted_at: new Date().toISOString() })
  }
  return toSubmission(
    await post<SubmissionOut>(`${base(assignmentId)}/answers/${nid(questionId)}/concept-check`, {
      reply: body.reply,
      elapsed_ms: Math.max(0, Math.round(body.elapsed_ms)),
    }),
  )
}
/** 개념 확인을 미루고 답을 고치러 돌아간다. 다시 제출하면 같은 질문이 이어진다 */
export const cancelConceptCheck = async (assignmentId: string, questionId: string) =>
  toSubmission(await del<SubmissionOut>(`${base(assignmentId)}/answers/${nid(questionId)}/concept-check`))
/** 과제 최종 제출. 모든 문항을 낸 뒤에만 할 수 있다 */
export const finalizeSubmission = async (assignmentId: string) =>
  toSubmission(await post<SubmissionOut>(`${base(assignmentId)}/submission/finalize`))
