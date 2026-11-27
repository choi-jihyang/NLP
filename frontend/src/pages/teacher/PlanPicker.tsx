import type { Plan, PlanCode } from '../../api/plans'

type Props = { plans: Plan[]; value: PlanCode; onChange: (plan: PlanCode) => void }

/** 요금제 고르기 카드 3개 */
export default function PlanPicker({ plans, value, onChange }: Props) {
  return (
    <div className="grid g3" role="radiogroup" aria-label="요금제">
      {plans.map((p) => (
        <button key={p.code} type="button" role="radio" aria-checked={p.code === value} className="plan-opt" onClick={() => onChange(p.code)}>
          <b>{p.name}</b>
          <span className="muted">학생 {p.student_limit}명</span>
          <span className="price">{p.price.toLocaleString('ko-KR')}원</span>
        </button>
      ))}
    </div>
  )
}
