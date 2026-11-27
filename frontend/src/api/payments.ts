import type { PlanCode } from './plans'

/** 마이페이지 결제 내역 한 줄. 결제는 비용이 드는 기능이라 시연에서는 예시 데이터만 보여 준다(결정 11/27, API 없음) */
export type PaymentHistoryRow = { date: string; title: string; plan: PlanCode; student_limit: number; amount: number }

const EXAMPLE_ROWS: PaymentHistoryRow[] = [
  { date: '2026-11-26', title: '새 클래스 · test', plan: 'SMALL', student_limit: 50, amount: 90000 },
  { date: '2026-11-22', title: '새 클래스 · 프로그래밍 기초 1분반', plan: 'SMALL', student_limit: 50, amount: 90000 },
]

/** 예시 결제 내역. 실제 결제 기록이 아니다 */
export const listPaymentHistory = (): Promise<PaymentHistoryRow[]> => Promise.resolve(EXAMPLE_ROWS)
