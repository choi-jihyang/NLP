import type { AiPolicy, HintMode } from './assignments'
import { get, post, put, type Language } from './client'
import type { PlanCode } from './plans'

export type ClassInfo = {
  seq: number
  name: string
  invite_code: string
  plan: PlanCode
  student_limit: number
  student_count: number
  starts_at: string
  expires_at: string
}

export type ClassStudent = { seq: number; student_no: string }

/** 학생 "내 과제" 화면의 한 줄 */
export type MyAssignment = {
  seq: number
  title: string
  language: Language
  /** 푸는 중 → 최종 제출(결과 공개 전) → 결과 공개 */
  status: 'IN_PROGRESS' | 'FINALIZED' | 'RELEASED'
  due_at: string | null
  hint_mode: HintMode
  hint_mode_label: string
  submitted: number
  total: number
  /** 결과가 공개된 뒤에만 채워진다 */
  score_text: string | null
}

export type MyClass = {
  class_id: number
  class_name: string
  student_no: string
  /** 참여 요청이 아직 수락되지 않았으면 PENDING (과제는 비어 있다) */
  enrollment_status: 'APPROVED' | 'PENDING'
  assignments: MyAssignment[]
}

/** 결제 목업(NEW) 이용권으로 개설. 시작 날짜는 오늘 이후(한국 시간), 만료는 시작 + 1년 */
export type ClassCreate = { name: string; starts_on: string; payment_seq: number }

export const listClasses = () => get<ClassInfo[]>('/classes')
/** 클래스 개설. 수업 코드가 새로 발급된다 */
export const createClass = (body: ClassCreate) => post<ClassInfo>('/classes', body)
/** 이 클래스에서 새로 만드는 과제에 미리 채울 AI 도움 정책 */
export const getAiDefaults = (classId: number) => get<AiPolicy>(`/classes/${classId}/ai-defaults`)
export const saveAiDefaults = (classId: number, policy: AiPolicy) => put<AiPolicy>(`/classes/${classId}/ai-defaults`, policy)
export const getClass = (classId: number) => get<ClassInfo>(`/classes/${classId}`)
export const listStudents = (classId: number) => get<ClassStudent[]>(`/classes/${classId}/students`)
/** 학생: 참여한 클래스와 과제 목록 */
export const listMyClasses = () => get<MyClass[]>('/me/classes')
