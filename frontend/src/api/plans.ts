import { get, nid, post, sid } from './client'

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

type PaymentOut = { payment_seq: number; plan: PlanCode; student_limit: number; amount: number; expires_at?: string }

export const listPlans = () => get<Plan[]>('/plans')

/** 결제 목업. 실제 결제 대행(PG) 연동 없이 항상 성공한다. NEW는 클래스 개설 전 이용권, EXTEND는 1년 연장 */
export const payMock = async (body: PaymentRequest): Promise<PaymentResult> => {
  const req = body.kind === 'EXTEND' && body.class_id
    ? { plan: body.plan, kind: 'EXTEND', class_id: nid(body.class_id) }
    : { plan: body.plan, kind: 'NEW' }
  const r = await post<PaymentOut>('/payments', req)
  return { payment_id: sid(r.payment_seq), amount: r.amount, period_end: r.expires_at ?? '' }
}

/** 클래스 개설용(NEW) 이용권 번호 */
export const buyNewPass = async (plan: PlanCode) => (await post<PaymentOut>('/payments', { plan, kind: 'NEW' })).payment_seq
