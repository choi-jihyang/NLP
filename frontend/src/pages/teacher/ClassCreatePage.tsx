import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { createClass } from '../../api/classes'
import { listPlans, payMock, type PlanCode } from '../../api/plans'
import { formatDate } from '../../components/format'
import { QueryState } from '../../components/QueryState'

const isPlan = (v: string | null): v is PlanCode => v === 'SMALL' || v === 'MEDIUM' || v === 'LARGE'

/** 오늘 날짜(한국 시간) YYYY-MM-DD — 시작 날짜는 오늘 이후만 고를 수 있다 */
const todayKst = () => new Date(Date.now() + 9 * 3600_000).toISOString().slice(0, 10)

/** 교수자: 클래스 개설 → 수업 코드 발급 */
export default function ClassCreatePage() {
  const [params] = useSearchParams()
  const client = useQueryClient()
  const plans = useQuery({ queryKey: ['plans'], queryFn: listPlans })
  const fromPlan = params.get('plan')
  const [name, setName] = useState('')
  const [plan, setPlan] = useState<PlanCode>(isPlan(fromPlan) ? fromPlan : 'SMALL')
  const [startsOn, setStartsOn] = useState(todayKst())
  const [copied, setCopied] = useState(false)
  // 요금제 화면에서 결제(목업)하고 왔으면 그 이용권을, 아니면 여기서 이용권을 만든 뒤 개설한다
  const paidSeq = Number(params.get('payment')) || null
  const create = useMutation({
    mutationFn: async () => {
      const payment_seq = paidSeq ?? (await payMock({ plan, kind: 'NEW' })).payment_seq
      return createClass({ name, starts_on: startsOn, payment_seq })
    },
    onSuccess: () => client.invalidateQueries({ queryKey: ['classes'] }),
  })

  if (!plans.data) return <QueryState isPending={plans.isPending} error={plans.error} />

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    create.mutate()
  }

  if (create.data) {
    const c = create.data
    return (
      <section className="panel stack narrow">
        <h2>{c.name}</h2>
        <div className="deploy">
          <span className="label">학생 입장 코드</span>
          <div className="row">
            <span className="invite">{c.invite_code}</span>
            <button className="btn sm" onClick={() => void navigator.clipboard?.writeText(c.invite_code).then(() => setCopied(true))}>
              {copied ? '복사했어요' : '복사'}
            </button>
          </div>
          <span className="note">
            학생은 가입 없이 이 코드와 학번으로 입장해요. 학생 {c.student_limit}명까지 · {formatDate(c.starts_at)}부터 {formatDate(c.expires_at)}까지
          </span>
        </div>
        <div className="row">
          <Link className="btn primary" to={`/teacher/classes/${c.seq}/assignments/new`}>첫 과제 만들기</Link>
          <Link className="btn" to={`/teacher/classes/${c.seq}/ai-settings`}>AI 기본값 정하기</Link>
          <Link className="btn" to={`/teacher/classes/${c.seq}`}>클래스로 가기</Link>
        </div>
      </section>
    )
  }

  return (
    <form className="panel stack narrow" onSubmit={handleSubmit}>
      <h2>클래스 개설</h2>
      <p className="lead">분반 하나를 클래스 하나로 만들어요. 개설하면 학생 입장 코드가 발급돼요.</p>
      <label className="field">
        <span className="label">클래스 이름</span>
        <input className="inp" value={name} placeholder="예: 프로그래밍 기초 2분반" onChange={(e) => setName(e.target.value)} />
      </label>
      <label className="field">
        <span className="label">요금제 · 학생 수 상한은 요금제에 따라 정해져요</span>
        <select className="inp" value={plan} disabled={!!paidSeq} onChange={(e) => setPlan(e.target.value as PlanCode)}>
          {plans.data.map((p) => (
            <option key={p.code} value={p.code}>
              {p.name} · 학생 {p.student_limit}명 이하 · {p.price.toLocaleString('ko-KR')}원 / 1년
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        <span className="label">시작 날짜 · 학생은 이날부터 입장할 수 있고, 1년 뒤 만료돼요</span>
        <input className="inp" type="date" value={startsOn} min={todayKst()} required onChange={(e) => setStartsOn(e.target.value)} />
      </label>
      {create.error && <p className="error-text">{create.error.message}</p>}
      <div className="row">
        <button className="btn primary" disabled={create.isPending || !name.trim()}>개설하기</button>
        <Link className="btn" to="/teacher/plans">요금제 보기</Link>
      </div>
    </form>
  )
}
