import { get, nid, put, sid } from './client'

export type QuestionStat = {
  question_index: number
  type_label: string
  /** AI 도움을 받을 수 있는 원문제 정답률(%) */
  correct_rate: number
  /** AI 없이 푼 확인 문제 정답률(%) */
  variant_rate: number
  avg_hint_steps: number
}

export type MistakeRow = { label: string; rate: number; note: string | null; correct: boolean }
export type QuestionMistakes = { question_index: number; kind: 'CHOICE' | 'ANSWER' | 'TEST'; rows: MistakeRow[] }

export type DependencyRow = { student_id: string; student_name: string; question_index: number; hint_steps: number; variant_answer: string; cause: string }
export type SignalRow = { student_id: string; student_name: string; question_index: number; signals: string[] }

export type AssignmentReport = {
  assignment_id: string
  title: string
  submitted_count: number
  student_count: number
  assisted_correct_rate: number
  alone_variant_rate: number
  concept_check_ok_rate: number
  question_stats: QuestionStat[]
  mistakes: QuestionMistakes[]
  supplement: { question_index: number; rate: number; summary: string; items: string[] } | null
  dependency: DependencyRow[]
  signals: SignalRow[]
}

export type GradingItem = {
  answer_id: string
  student_name: string
  question_index: number
  points: number
  rubric: string[]
  content: string
  signals: string[]
  score: number | null
  feedback: string
}

export type RecordRow = { question_index: number; hint_steps: number; result: string; variant: string; concept_check: string; signal: string | null }
export type RecordTurn = { message: string; classification: string; attempt: boolean; leak_blocked: boolean }

export type StudentRecord = {
  student_id: string
  student_name: string
  assignment_title: string
  score: number
  max_score: number
  pending_points: number
  variant_passed: number
  variant_total: number
  variant_note: string
  hint_steps: number
  class_avg_hint_steps: number
  rows: RecordRow[]
  conversation: { question_index: number; turns: RecordTurn[]; note: string }
}

export type ConceptStatus = 'CONFIRMED' | 'NEEDS_WORK' | 'UNCLEAR'

/** 결과 공개 뒤 문항별 내 결과와 정답 */
export type MyQuestionResult = { question_index: number; type_label: string; result: string; correct_answer: string }

export type MyReport = {
  assignment_title: string
  score: number
  max_score: number
  pending_points: number
  hint_steps: number
  concepts: { name: string; status: ConceptStatus; reason: string }[]
  misconceptions: string[]
  overconfident: string[]
  next_steps: string[]
  questions: MyQuestionResult[]
}

/** 교수자가 결과를 공개하기 전에는 내용 없이 released: false만 온다 */
export type MyReportResponse = { released: false; assignment_title: string } | ({ released: true } & MyReport)

// ---------- 백엔드 모양(숫자 id) ↔ 화면 모양(문자열 id) ----------

type Num<T, K extends keyof T> = Omit<T, K> & { [P in K]: number }
type ReportOut = Omit<AssignmentReport, 'assignment_id' | 'dependency' | 'signals'> & {
  assignment_id: number
  dependency: Num<DependencyRow, 'student_id'>[]
  signals: Num<SignalRow, 'student_id'>[]
}
type GradingOut = Num<GradingItem, 'answer_id'>
type RecordOut = Omit<StudentRecord, 'student_id' | 'conversation'> & {
  student_id: number
  conversation: StudentRecord['conversation'] | null
}

const toGrading = ({ answer_id, ...g }: GradingOut): GradingItem => ({ ...g, answer_id: sid(answer_id) })
const base = (assignmentId: string) => `/assignments/${nid(assignmentId)}`

export const getAssignmentReport = async (assignmentId: string): Promise<AssignmentReport> => {
  const r = await get<ReportOut>(`${base(assignmentId)}/report`)
  return {
    ...r,
    assignment_id: sid(r.assignment_id),
    dependency: r.dependency.map((d) => ({ ...d, student_id: sid(d.student_id) })),
    signals: r.signals.map((d) => ({ ...d, student_id: sid(d.student_id) })),
  }
}
export const getGradingList = async (assignmentId: string) =>
  (await get<GradingOut[]>(`${base(assignmentId)}/grading`)).map(toGrading)
export const gradeAnswer = async (answerId: string, body: { score: number; feedback: string }) =>
  toGrading(await put<GradingOut>(`/answers/${nid(answerId)}/grade`, body))
/** 대화가 없는 학생은 conversation이 비어 있다(화면은 빈 대화로 보여 준다) */
export const getStudentRecord = async (assignmentId: string, studentId: string): Promise<StudentRecord> => {
  const r = await get<RecordOut>(`${base(assignmentId)}/students/${nid(studentId)}/record`)
  return {
    ...r,
    student_id: sid(r.student_id),
    conversation: r.conversation ?? { question_index: 0, turns: [], note: '이 학생은 AI 도움을 쓰지 않았어요.' },
  }
}
export const getMyReport = (assignmentId: string) => get<MyReportResponse>(`${base(assignmentId)}/my-report`)
