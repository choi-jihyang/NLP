import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { listClasses, type ClassInfo } from '../../api/classes'
import { listPlans, payMock, type PlanCode } from '../../api/plans'
import { QueryState } from '../../components/QueryState'
import ExtendList from './plans/ExtendList'
import PlanCard from './plans/PlanCard'

/** 교수자: 요금제 비교 · 결제 목업 · 이용 기간 연장 */
export default function PlansPage() {
  const [params] = useSearchParams()
  const client = useQueryClient()
  const plans = useQuery({ queryKey: ['plans'], queryFn: listPlans })
  const classes = useQuery({ queryKey: ['classes'], queryFn: listClasses })
  const [code, setCode] = useState<PlanCode>('SMALL')
  const pay = useMutation({ mutationFn: payMock })
  const extend = useMutation({
    mutationFn: (c: ClassInfo) => payMock({ plan: c.plan, kind: 'EXTEND', class_id: c.seq }),
    onSuccess: () => client.invalidateQueries({ queryKey: ['classes'] }),
  })

  if (!plans.data) return <QueryState isPending={plans.isPending} error={plans.error} />
  const plan = plans.data.find((p) => p.code === code) ?? plans.data[0]

  return (
    <div className="stack">
      {params.get('welcome') && (
        <div className="status">
          <div>✓</div>
          <div>계정을 만들었어요. 요금제를 고르고 첫 클래스를 개설해 보세요.</div>
        </div>
      )}
      <div className="spread">
        <h2>요금제</h2>
        <span className="chip warn">결제 목업 · 실제 결제 없음</span>
      </div>
      <p className="lead">학생은 무료예요. 교수자가 학생 수에 맞는 클래스 이용권(1년)을 사면, 학생은 수업 코드로 들어와요. 기능은 모두 같고 학생 수 상한만 달라요.</p>
      <div className="opts">
        {plans.data.map((p) => (
          <PlanCard key={p.code} plan={p} selected={p.code === code} onSelect={() => setCode(p.code)} />
        ))}
      </div>
      <section className="panel stack">
        <div className="kv">
          <b>{plan.price.toLocaleString('ko-KR')}원</b>
          <span>
            {plan.name} · 학생 {plan.student_limit}명 이하 · 클래스 1개 · 1년
          </span>
        </div>
        {pay.data ? (
          <div className="deploy">
            <b>결제가 완료됐어요 (목업)</b>
            <span className="note">
              {pay.data.amount.toLocaleString('ko-KR')}원 · 클래스를 개설한 날부터 1년
            </span>
            <div className="row">
              <Link className="btn primary" to={`/teacher/classes/new?plan=${pay.data.plan}&payment=${pay.data.payment_seq}`}>이 요금제로 클래스 개설</Link>
            </div>
          </div>
        ) : (
          <div className="row">
            <button
              className="btn primary"
              disabled={pay.isPending}
              onClick={() => pay.mutate({ plan: code, kind: 'NEW' })}
            >
              결제하기 (목업)
            </button>
            <span className="note">누르면 실제 결제 없이 바로 성공으로 처리돼요.</span>
          </div>
        )}
        {pay.error && <p className="error-text">{pay.error.message}</p>}
      </section>
      <ExtendList
        classes={classes.data ?? []}
        busyId={extend.isPending ? (extend.variables?.seq ?? null) : null}
        onExtend={(c) => extend.mutate(c)}
      />
      {extend.error && <p className="error-text">{extend.error.message}</p>}
    </div>
  )
}
