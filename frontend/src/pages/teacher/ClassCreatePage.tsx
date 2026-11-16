import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { createClass } from '../../api/classes'
import { listPlans, type PlanCode } from '../../api/plans'
import { QueryState } from '../../components/QueryState'

const isPlan = (v: string | null): v is PlanCode => v === 'SMALL' || v === 'MEDIUM' || v === 'LARGE'

/** 교수자: 클래스 개설 → 수업 코드 발급 */
export default function ClassCreatePage() {
  const [params] = useSearchParams()
  const client = useQueryClient()
  const plans = useQuery({ queryKey: ['plans'], queryFn: listPlans })
  const fromPlan = params.get('plan')
  const [name, setName] = useState('')
  const [plan, setPlan] = useState<PlanCode>(isPlan(fromPlan) ? fromPlan : 'SMALL')
  const [copied, setCopied] = useState(false)
  const create = useMutation({ mutationFn: createClass, onSuccess: () => client.invalidateQueries({ queryKey: ['classes'] }) })

  if (!plans.data) return <QueryState isPending={plans.isPending} error={plans.error} />

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    create.mutate({ name, plan })
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
          <span className="note">학생은 가입 없이 이 코드와 수업용 ID로 입장해요. 학생 {c.student_limit}명까지 들어올 수 있어요.</span>
        </div>
        <div className="row">
          <Link className="btn primary" to={`/teacher/classes/${c.id}/assignments/new`}>첫 과제 만들기</Link>
          <Link className="btn" to={`/teacher/classes/${c.id}/ai-settings`}>AI 기본값 정하기</Link>
          <Link className="btn" to={`/teacher/classes/${c.id}`}>클래스로 가기</Link>
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
        <select className="inp" value={plan} onChange={(e) => setPlan(e.target.value as PlanCode)}>
          {plans.data.map((p) => (
            <option key={p.code} value={p.code}>
              {p.name} · 학생 {p.student_limit}명 이하 · {p.price.toLocaleString('ko-KR')}원 / 1년
            </option>
          ))}
        </select>
      </label>
      {create.error && <p className="error-text">{create.error.message}</p>}
      <div className="row">
        <button className="btn primary" disabled={create.isPending || !name.trim()}>개설하기</button>
        <Link className="btn" to="/teacher/plans">요금제 보기</Link>
      </div>
    </form>
  )
}
