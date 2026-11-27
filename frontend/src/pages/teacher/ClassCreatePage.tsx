import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRef, useState, type FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { createClass } from '../../api/classes'
import { listPlans, payMock, type PlanCode } from '../../api/plans'
import { PageHead } from '../../components/PageHead'
import { QueryState } from '../../components/QueryState'
import PlanPicker from './PlanPicker'

const isPlan = (v: string | null): v is PlanCode => v === 'SMALL' || v === 'MEDIUM' || v === 'LARGE'

/** 오늘 날짜(한국 시간) YYYY-MM-DD — 시작 날짜는 오늘 이후만 고를 수 있다 */
const todayKst = () => new Date(Date.now() + 9 * 3600_000).toISOString().slice(0, 10)
const plusYear = (ymd: string) => `${Number(ymd.slice(0, 4)) + 1}${ymd.slice(4)}`

/** 클래스 개설: 이름 · 시작 날짜 · 요금제 → "결제하고 개설" 한 번(결제 화면 없음, 목업 결제 후 개설) */
export default function ClassCreatePage() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const client = useQueryClient()
  const plans = useQuery({ queryKey: ['plans'], queryFn: listPlans })
  const fromPlan = params.get('plan')
  const [name, setName] = useState('')
  const [plan, setPlan] = useState<PlanCode>(isPlan(fromPlan) ? fromPlan : 'SMALL')
  const [startsOn, setStartsOn] = useState(todayKst())
  const busy = useRef(false)
  const create = useMutation({
    mutationFn: async () => {
      const { payment_seq } = await payMock({ plan, kind: 'NEW' })
      return createClass({ name: name.trim(), starts_on: startsOn, payment_seq })
    },
    onSuccess: async (c) => {
      await client.invalidateQueries({ queryKey: ['classes'] })
      navigate(`/teacher/classes/${c.seq}`)
    },
  })
  const chosen = plans.data?.find((p) => p.code === plan)

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    // 연달아 눌러도 이용권 · 클래스가 하나만 생기게(isPending은 다음 그림 전까지 바뀌지 않는다)
    if (busy.current) return
    busy.current = true
    create.mutate(undefined, { onSettled: () => (busy.current = false) })
  }

  return (
    <>
      <PageHead back={{ to: '/teacher/classes', label: '내 클래스' }} eyebrow="New class" title="클래스 개설" />
      <main className="wrap page">
        <QueryState isPending={plans.isPending} error={plans.error} />
        {plans.data && (
          <form className="stack mid" onSubmit={handleSubmit}>
            <div className="grid g2">
              <label className="field">
                <span className="label">클래스 이름</span>
                <input value={name} placeholder="예: 프로그래밍 기초 2분반" onChange={(e) => setName(e.target.value)} />
              </label>
              <label className="field">
                <span className="label">시작 날짜</span>
                <input type="date" value={startsOn} min={todayKst()} required onChange={(e) => setStartsOn(e.target.value)} />
              </label>
            </div>
            <span className="label">요금제 · 1년</span>
            <PlanPicker plans={plans.data} value={plan} onChange={setPlan} />
            {chosen && (
              <div className="sum">
                <span className="muted">{startsOn.replaceAll('-', '.')} – {plusYear(startsOn).replaceAll('-', '.')} · 학생 {chosen.student_limit}명</span>
                <b>{chosen.price.toLocaleString('ko-KR')}원</b>
              </div>
            )}
            {create.error && <p className="error-text">{create.error.message}</p>}
            <div className="row">
              <button className="btn primary lg" disabled={create.isPending || !name.trim()}>
                {create.isPending ? '개설 중…' : '결제하고 개설'}
              </button>
              <span className="note">목업 결제예요 · 실제로 결제되지 않아요</span>
            </div>
          </form>
        )}
      </main>
    </>
  )
}
