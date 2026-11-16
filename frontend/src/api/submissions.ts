import type { HintMode, ProgrammingLanguage, Question, TestCase } from './assignments'
import { mockStudent } from './mock/studentStore'

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

export type TestResult = {
  call: string
  expected: string
  actual: string
  passed: boolean
  hidden: boolean
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

export const getStudentAssignment = (assignmentId: string) => mockStudent.assignment(assignmentId)
export const getMySubmission = (assignmentId: string) => mockStudent.submission(assignmentId)
/** 제출 전에 공개 테스트만 실행해 본다 */
export const runPublicTests = (assignmentId: string, questionId: string, code: string) =>
  mockStudent.runPublicTests(assignmentId, questionId, code)
/** 문항 답 제출. 최종 제출 전까지는 고쳐서 다시 낼 수 있고 마지막 답이 채점된다 */
export const submitAnswer = (assignmentId: string, questionId: string, content: string) =>
  mockStudent.submitAnswer(assignmentId, questionId, content)
/** 힌트 없이 처음 낸 문항은 바로 제출되지 않고 개념 확인(AWAITING_CHECK)을 거친다 */
export const answerConceptCheck = (assignmentId: string, questionId: string, body: ConceptReply) =>
  mockStudent.answerConceptCheck(assignmentId, questionId, body)
/** 개념 확인을 미루고 답을 고치러 돌아간다. 다시 제출하면 같은 질문이 이어진다 */
export const cancelConceptCheck = (assignmentId: string, questionId: string) =>
  mockStudent.cancelConceptCheck(assignmentId, questionId)
/** 과제 최종 제출. 모든 문항을 낸 뒤에만 할 수 있다 */
export const finalizeSubmission = (assignmentId: string) => mockStudent.finalize(assignmentId)
