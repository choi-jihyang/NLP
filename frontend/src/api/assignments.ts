import { api, get, langToApi, langToUi, nid, post, put, sid, type BackendLanguage } from './client'

/** 문항 유형. 퀴즈·출력 예측은 정답 대조, 코드는 테스트 실행, 간단 제작은 교수자 채점 */
export type QuestionType = 'MULTIPLE_CHOICE' | 'SHORT_ANSWER' | 'CODE' | 'PROJECT'

/**
 * 테스트 한 건. 모든 언어 표준 입력 → 표준 출력(schema D23).
 * 화면 필드 이름은 그대로 두고 `call` = 표준 입력, `expected` = 기대 표준 출력으로 쓴다.
 */
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
  /** 학생 1명 · 이 과제 AI 메시지 수 상한(기본 30) */
  usage_limit?: number
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
  /** 결과 공개 여부(서버가 정함) */
  results_released?: boolean
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


// ---------- 백엔드 모양 ↔ 화면 모양 ----------

type TestOut = { input: string; expected_output: string; hidden: boolean }
type QuestionOut = Omit<Question, 'id' | 'tests'> & { seq: number | null; tests: TestOut[] }
type AssignmentOut = Omit<Assignment, 'id' | 'class_id' | 'language' | 'questions'> & {
  seq: number | null
  class_id: number | null
  language: BackendLanguage
  questions: QuestionOut[]
}
type SummaryOut = Omit<AssignmentSummary, 'id'> & { seq: number }

const toQuestion = ({ seq, tests, ...q }: QuestionOut, i: number): Question => ({
  ...q,
  id: seq == null ? `new-${i}` : sid(seq),
  tests: tests.map((t) => ({ call: t.input, expected: t.expected_output, hidden: t.hidden })),
})

const toAssignment = ({ seq, class_id, language, questions, ...a }: AssignmentOut): Assignment => ({
  ...a,
  id: sid(seq),
  class_id: sid(class_id),
  language: langToUi(language),
  questions: questions.map(toQuestion),
})

/** 표준 입력은 줄바꿈으로 끝나게 (scanf가 마지막 줄을 읽도록) */
const stdin = (text: string) => (text && !text.endsWith('\n') ? `${text}\n` : text)

const toApi = (a: Assignment) => ({
  title: a.title,
  course: a.course,
  audience: a.audience,
  language: langToApi(a.language),
  description: a.description,
  due_at: a.due_at,
  policy: a.policy,
  questions: a.questions.map(({ id: _id, tests, ...q }) => ({
    ...q,
    tests: tests.map((t) => ({ input: stdin(t.call), expected_output: t.expected, hidden: t.hidden })),
  })),
})

export const listAssignments = async (classId: string): Promise<AssignmentSummary[]> =>
  (await get<SummaryOut[]>(`/classes/${nid(classId)}/assignments`)).map(({ seq, ...s }) => ({ ...s, id: sid(seq) }))
export const getAssignment = async (assignmentId: string) =>
  toAssignment(await get<AssignmentOut>(`/assignments/${nid(assignmentId)}`))
export const createDraftFromSample = async (classId: string) =>
  toAssignment(await post<AssignmentOut>(`/classes/${nid(classId)}/assignments/drafts`, { source: 'SAMPLE' }))
export const createBlankDraft = async (classId: string) =>
  toAssignment(await post<AssignmentOut>(`/classes/${nid(classId)}/assignments/drafts`, { source: 'BLANK' }))
/** 과제 파일(.md, 정해진 양식 — docs/spec/assignment-md-format.md)에서 문항을 찾는다. 저장은 하지 않는다 */
export const extractFromFile = async (classId: string, file: File) => {
  const form = new FormData()
  form.append('file', file)
  return toAssignment(await api<AssignmentOut>(`/classes/${nid(classId)}/assignments/extract`, { method: 'POST', body: form }))
}
/** id가 'new'면 새로 저장, 아니면 수정 */
export const saveAssignment = async (assignment: Assignment) =>
  toAssignment(
    assignment.id === 'new'
      ? await post<AssignmentOut>(`/classes/${nid(assignment.class_id)}/assignments`, toApi(assignment))
      : await put<AssignmentOut>(`/assignments/${nid(assignment.id)}`, toApi(assignment)),
  )
export const publishAssignment = (assignmentId: string) =>
  post<{ invite_code: string }>(`/assignments/${nid(assignmentId)}/publish`)
/** 점수·정답·내 리포트를 학생에게 한꺼번에 공개한다. 공개 전에는 학생에게 정오도 보이지 않는다 */
export const releaseResults = (assignmentId: string) =>
  post<{ results_released: boolean }>(`/assignments/${nid(assignmentId)}/release`)
/** "학생은 이렇게 경험해요" 요약 (시스템 프롬프트 원문은 아님) */
export const getPolicyPreview = (assignment: Assignment) =>
  post<{ lines: string[]; hint_mode_label: string }>('/assignments/preview', toApi(assignment))
/** 지시문 직접 작성 모드의 시작점 */
export const getPromptDraft = async (assignment: Assignment) =>
  (await post<{ prompt: string }>('/assignments/prompt-draft', toApi(assignment))).prompt
/** 학생처럼 우회 요청을 보내 보고 AI가 설정대로 답하는지 확인한다(실제 분류기 · LLM · 누출 검사) */
export const simulateAttacks = (assignment: Assignment) =>
  post<SimulationCase[]>('/assignments/simulate', toApi(assignment))
