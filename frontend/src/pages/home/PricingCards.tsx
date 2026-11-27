import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { listPlans } from '../../api/plans'

const FEATURES = ['과제 파일 불러오기 · 4단계 과제 만들기', '문항별 AI 도움 정책 · 배포 전 졸라보기', '반 리포트 · 채점 · 학생별 기록']

/** 메인 ⑥: 요금제 3개 → 로그인 뒤 그 요금제로 클래스 개설 */
export function PricingCards() {
  const plans = useQuery({ queryKey: ['plans'], queryFn: listPlans })
  return (
    <section className="block" id="start" style={{ paddingTop: 24 }}>
      <div className="wrap">
        <div className="sec-head reveal">
          <div>
            <p className="eyebrow">Pricing</p>
            <h2 style={{ marginTop: 10 }}>요금제</h2>
          </div>
          <p className="muted">클래스 하나 · 1년. 기능은 모두 같고 학생 수 상한만 달라요.</p>
        </div>
        <div className="start">
          {(plans.data ?? []).map((p, i) => (
            <div key={p.code} className={`sc reveal${i === 1 ? ' feature' : ''}`}>
              <p className="eyebrow">{p.name}</p>
              <h3 style={{ marginTop: 8 }}>학생 {p.student_limit}명</h3>
              <p className="price"><b>{p.price.toLocaleString('ko-KR')}원</b> / 1년</p>
              <ul>{FEATURES.map((f) => <li key={f}>{f}</li>)}</ul>
              <Link className={`btn lg${i === 1 ? ' primary' : ''}`} to={`/login?plan=${p.code}`}>{p.name} 시작하기</Link>
            </div>
          ))}
          {plans.isError && <p className="error-text">요금제를 불러오지 못했어요.</p>}
        </div>
      </div>
    </section>
  )
}
