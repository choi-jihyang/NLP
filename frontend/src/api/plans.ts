import { mockPlans } from './mock/planStore'

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
export type PaymentRequest = { plan: PlanCode; kind: PaymentKind; class_id: string | null }
export type PaymentResult = { payment_id: string; amount: number; period_end: string }

export const listPlans = () => mockPlans.list()
/** 결제 목업. 실제 결제 대행(PG) 연동 없이 항상 성공한다 */
export const payMock = (body: PaymentRequest) => mockPlans.pay(body)
