import { api, get, post, put, type Language } from './client'

export type { Language }

/** 문항 유형. 퀴즈·출력 예측은 정답 대조, 코드는 테스트 실행, 간단 제작은 교수자 채점 */
export type QuestionType = 'MULTIPLE_CHOICE' | 'SHORT_ANSWER' | 'CODE' | 'PROJECT'

/** 테스트 한 건. 모든 언어 표준 입력 → 표준 출력(schema D23). 출력은 줄 끝 공백 · 마지막 줄바꿈 무시 */
export type TestCase = {
  input: string
  expected_output: string
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
  /** 저장 전 문항은 null */
  seq: number | null
  /** 화면에서만 쓰는 목록 키(직접 추가한 저장 전 문항). 서버는 무시한다 */
  key?: string
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
  /** 학생 1명 · 이 과제 AI 메시지 수 상한(기본 30) */
  usage_limit: number
}

export type Assignment = {
  /** 저장 전 초안은 null */
  seq: number | null
  class_id: number | null
  title: string
  course: string
  audience: string
  language: Language
  /** 교수자가 쓴 과제 설명. AI 지시문에 맥락으로 들어간다 */
  description: string
  due_at: string | null
  published: boolean
  /** 결과 공개 여부(서버가 정함) */
  results_released: boolean
  policy: AiPolicy
  questions: Question[]
}

export type AssignmentSummary = {
  seq: number
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
  response_mode: string
  reply: string
}

export const listAssignments = (classId: number) => get<AssignmentSummary[]>(`/classes/${classId}/assignments`)
export const getAssignment = (assignmentId: number) => get<Assignment>(`/assignments/${assignmentId}`)
/** 저장 전 초안. SAMPLE = 샘플 md(C 2진수 과제), BLANK = 빈 과제. AI 정책은 클래스 기본값 */
export const createDraftFromSample = (classId: number) =>
  post<Assignment>(`/classes/${classId}/assignments/drafts`, { source: 'SAMPLE' })
export const createBlankDraft = (classId: number) => post<Assignment>(`/classes/${classId}/assignments/drafts`, { source: 'BLANK' })
/** 과제 파일(.md, 정해진 양식 — docs/spec/assignment-md-format.md)에서 문항을 찾는다. 저장은 하지 않는다 */
export const extractFromFile = (classId: number, file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api<Assignment>(`/classes/${classId}/assignments/extract`, { method: 'POST', body: form })
}
/** seq가 없으면 새로 저장, 있으면 수정 */
export const saveAssignment = (a: Assignment) =>
  a.seq == null ? post<Assignment>(`/classes/${a.class_id}/assignments`, a) : put<Assignment>(`/assignments/${a.seq}`, a)
export const publishAssignment = (assignmentId: number) => post<{ invite_code: string }>(`/assignments/${assignmentId}/publish`)
/** 점수·정답·내 리포트를 학생에게 한꺼번에 공개한다. 공개 전에는 학생에게 정오도 보이지 않는다 */
export const releaseResults = (assignmentId: number) => post<{ results_released: boolean }>(`/assignments/${assignmentId}/release`)
/** "학생은 이렇게 경험해요" 요약 (시스템 프롬프트 원문은 아님) */
export const getPolicyPreview = (a: Assignment) => post<{ lines: string[]; hint_mode_label: string }>('/assignments/preview', a)
/** 지시문 직접 작성 모드의 시작점 */
export const getPromptDraft = async (a: Assignment) => (await post<{ prompt: string }>('/assignments/prompt-draft', a)).prompt
/** 학생처럼 우회 요청을 보내 보고 AI가 설정대로 답하는지 확인한다(실제 분류기 · LLM · 누출 검사) */
export const simulateAttacks = (a: Assignment) => post<SimulationCase[]>('/assignments/simulate', a)
