import { mockAssignments } from './mock/assignmentStore'

/** 문항 유형. 퀴즈·출력 예측은 정답 대조, 코드는 테스트 실행, 간단 제작은 교수자 채점 */
export type QuestionType = 'MULTIPLE_CHOICE' | 'SHORT_ANSWER' | 'CODE' | 'PROJECT'

export type TestCase = {
  call: string
  expected: string
  hidden: boolean
}

/** AI 없이 푸는 확인 문제 (값을 바꾼 문제 또는 내 함수의 출력 예측) */
export type Variant = {
  type: 'MULTIPLE_CHOICE' | 'SHORT_ANSWER'
  prompt: string
  code: string
  choices: string[]
  answer: string
  accepted_answers: string[]
}

/** 교수자가 보는 문항 (정답·숨김 테스트 포함) */
export type Question = {
  id: string
  type: QuestionType
  points: number
  prompt: string
  /** 문제 코드 또는 요구사항. 없으면 빈 문자열 */
  code: string
  choices: string[]
  /** 객관식은 정답 선택지 번호('0'부터), 단답형은 정답 값 */
  answer: string
  accepted_answers: string[]
  /** 객관식 오답 선택지 번호 → 예상 오개념 */
  misconceptions: Record<string, string>
  starter_code: string
  tests: TestCase[]
  rubric: string[]
  model_answer: string
  /** 간단 제작 문항에서 AI 도움을 열지 여부 */
  ai_help: boolean
  variant: Variant | null
}

export type HintMode = 'NONE' | 'CONCEPT' | 'STEP' | 'EARNED'
export type HintPenalty = 'NONE' | 'PER_STEP' | 'PRACTICE'

export type AiPolicy = {
  hint_mode: HintMode
  /** 힌트에 보여줄 코드 최대 줄 수. 0이면 설명만 */
  code_line_limit: number
  hint_penalty: HintPenalty
  variant_enabled: boolean
  variant_graded: boolean
  concept_check_enabled: boolean
  external_signal_enabled: boolean
  report_misconceptions: boolean
  report_dependency: boolean
  prompt_mode: 'FORM' | 'CUSTOM'
  custom_prompt: string | null
}

export type ProgrammingLanguage = 'Python' | 'Java' | 'C' | 'JavaScript'

export type Assignment = {
  id: string
  class_id: string
  title: string
  course: string
  audience: string
  language: ProgrammingLanguage
  /** 교수자가 쓴 과제 설명. AI 지시문에 맥락으로 들어간다 */
  description: string
  due_at: string | null
  published: boolean
  policy: AiPolicy
  questions: Question[]
}

export type AssignmentSummary = {
  id: string
  title: string
  kinds: string
  status: 'DRAFT' | 'OPEN' | 'CLOSED'
  due_at: string | null
  hint_mode: HintMode | null
  submitted_count: number
  student_count: number
  todo: string | null
  /** 점수·정답·리포트를 학생에게 공개했는지 */
  results_released: boolean
}

export type SimulationCase = {
  question_index: number
  message: string
  classification: string
  attempt: boolean
  leak_blocked: boolean
  external_signals: string[]
  reply: string
}

export const listAssignments = (classId: string) => mockAssignments.list(classId)
export const getAssignment = (assignmentId: string) => mockAssignments.get(assignmentId)
export const createDraftFromSample = (classId: string) => mockAssignments.sampleDraft(classId)
export const createBlankDraft = (classId: string) => mockAssignments.blankDraft(classId)
/** 과제 파일에서 문항을 찾는다. 지금은 어떤 파일이든 샘플 과제를 돌려준다 */
export const extractFromFile = (classId: string, fileName: string) => mockAssignments.extract(classId, fileName)
export const saveAssignment = (assignment: Assignment) => mockAssignments.save(assignment)
export const publishAssignment = (assignmentId: string) => mockAssignments.publish(assignmentId)
/** 점수·정답·내 리포트를 학생에게 한꺼번에 공개한다. 공개 전에는 학생에게 정오도 보이지 않는다 */
export const releaseResults = (assignmentId: string) => mockAssignments.release(assignmentId)
/** "학생은 이렇게 경험해요" 요약 (시스템 프롬프트 원문은 아님) */
export const getPolicyPreview = (assignment: Assignment) => mockAssignments.preview(assignment)
/** 지시문 직접 작성 모드의 시작점 */
export const getPromptDraft = (assignment: Assignment) => mockAssignments.promptDraft(assignment)
/** 학생처럼 우회 요청을 보내 보고 AI가 설정대로 답하는지 확인한다 */
export const simulateAttacks = (assignment: Assignment) => mockAssignments.simulate(assignment)
