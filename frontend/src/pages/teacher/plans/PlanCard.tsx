import type { Plan } from '../../../api/plans'

type Props = { plan: Plan; selected: boolean; onSelect: () => void }

/** 요금제 비교 카드 한 장. 기능은 같고 학생 수 상한만 다르다 */
export default function PlanCard({ plan, selected, onSelect }: Props) {
  return (
    <label className="opt">
      <input type="radio" name="plan" checked={selected} onChange={onSelect} />
      <b className="mono" style={{ fontSize: '1.4rem' }}>{plan.price.toLocaleString('ko-KR')}원</b>
      <strong>
        {plan.name} · 학생 {plan.student_limit}명 이하
      </strong>
      <span>클래스당 1년</span>
    </label>
  )
}
