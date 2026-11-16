import { mockReports } from './mock/reportStore'

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

export const getAssignmentReport = (assignmentId: string) => mockReports.report(assignmentId)
export const getGradingList = (assignmentId: string) => mockReports.grading(assignmentId)
export const gradeAnswer = (answerId: string, body: { score: number; feedback: string }) => mockReports.grade(answerId, body)
export const getStudentRecord = (assignmentId: string, studentId: string) => mockReports.record(assignmentId, studentId)
export const getMyReport = (assignmentId: string) => mockReports.myReport(assignmentId)
