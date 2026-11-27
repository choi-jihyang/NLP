import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { listPlans } from '../../api/plans'
import { PageHead } from '../../components/PageHead'
import { QueryState } from '../../components/QueryState'

/** 요금제: 카드만. 결제는 클래스 개설 때, 연장은 마이페이지에서 */
export default function PlansPage() {
  const plans = useQuery({ queryKey: ['plans'], queryFn: listPlans })
  return (
    <>
      <PageHead
        eyebrow="Pricing"
        title="요금제"
        sub="클래스 하나 · 1년 · 기능은 모두 같아요"
        actions={<Link className="btn" to="/teacher/classes/new">클래스 만들러 가기 →</Link>}
      />
      <main className="wrap page">
        <QueryState isPending={plans.isPending} error={plans.error} />
        <div className="grid g3">
          {plans.data?.map((p, i) => (
            <div key={p.code} className="panel stack" style={i === 1 ? { borderColor: 'var(--accent)' } : undefined}>
              <p className="eyebrow">{p.name}</p>
              <h2>{p.price.toLocaleString('ko-KR')}원 <span className="note">/ 1년</span></h2>
              <p className="muted">학생 {p.student_limit}명까지</p>
              <Link className={`btn${i === 1 ? ' primary' : ''}`} to={`/teacher/classes/new?plan=${p.code}`}>이 요금제로 만들기</Link>
            </div>
          ))}
        </div>
        <p className="note" style={{ marginTop: 20 }}>결제는 클래스를 만들 때 해요 · 기간이 끝나면 마이페이지에서 연장</p>
      </main>
    </>
  )
}
