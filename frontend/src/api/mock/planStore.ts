/** 요금제 · 결제 목업. 실제 결제 대행(PG) 연동 코드는 넣지 않는다 */
import type { Plan, PaymentRequest, PaymentResult } from '../plans'
import { CLASSES } from './classStore'
import { respondWith } from './delay'

const YEAR = 365 * 24 * 3600 * 1000

/** 수익화 기획(발표 자료) 기준. 클래스 하나 · 1년 */
const PLANS: Plan[] = [
  { code: 'SMALL', name: 'Small', student_limit: 50, price: 90000 },
  { code: 'MEDIUM', name: 'Medium', student_limit: 100, price: 150000 },
  { code: 'LARGE', name: 'Large', student_limit: 200, price: 250000 },
]

let seq = 1

export const mockPlans = {
  list: () => respondWith(PLANS),
  pay: (body: PaymentRequest) => {
    const plan = PLANS.find((p) => p.code === body.plan)
    if (!plan) return Promise.reject(new Error('요금제를 찾을 수 없어요.'))
    let periodEnd = new Date(Date.now() + YEAR)
    if (body.kind === 'EXTEND') {
      const cls = CLASSES.find((c) => c.id === body.class_id)
      if (!cls) return Promise.reject(new Error('연장할 클래스를 찾을 수 없어요.'))
      if (cls.student_count > plan.student_limit) {
        return Promise.reject(new Error(`지금 학생이 ${cls.student_count}명이라 ${plan.name}(${plan.student_limit}명 이하)으로는 연장할 수 없어요.`))
      }
      periodEnd = new Date(Math.max(Date.now(), new Date(cls.expires_at).getTime()) + YEAR)
      Object.assign(cls, { expires_at: periodEnd.toISOString(), plan: body.plan, student_limit: plan.student_limit })
    }
    return respondWith<PaymentResult>(
      { payment_id: `pay-${seq++}`, amount: plan.price, period_end: periodEnd.toISOString() },
      500,
    )
  },
}
