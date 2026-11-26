import { get, post } from './client'

/** 수익화 기획: 학생은 무료, 교수자가 학생 수에 맞는 클래스 이용권(1년)을 산다 */
export type PlanCode = 'SMALL' | 'MEDIUM' | 'LARGE'

/** 금액은 원 단위 정수. 클래스 하나 · 1년 기준 */
export type Plan = {
  code: PlanCode
  name: string
  student_limit: number
  price: number
}

export type PaymentKind = 'NEW' | 'EXTEND'
/** NEW: 클래스 개설 전 이용권(class_id 없음) · EXTEND: 내 클래스 1년 연장(class_id 필수) */
export type PaymentRequest = { plan: PlanCode; kind: 'NEW' } | { plan: PlanCode; kind: 'EXTEND'; class_id: number }
export type PaymentResult = {
  payment_seq: number
  plan: PlanCode
  student_limit: number
  amount: number
  /** EXTEND만: 연장한 클래스와 늘어난 만료 시각 */
  class_id?: number
  expires_at?: string
}

export const listPlans = () => get<Plan[]>('/plans')
/** 결제 목업. 실제 결제 대행(PG) 연동 없이 항상 성공한다 */
export const payMock = (body: PaymentRequest) => post<PaymentResult>('/payments', body)
