import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { getHealth } from '../api/health'

/** 시작 화면. 교수자·학생 입구와 백엔드 연결 상태 */
export default function HomePage() {
  const health = useQuery({ queryKey: ['health'], queryFn: getHealth, retry: false })

  return (
    <main className="wrap">
      <section className="hero stack">
        <h2>AI와 함께, 스스로 생각하는 과제</h2>
        <p className="lead">
          프로그래밍 과제에서 완성 코드 대신 다음 한 단계를 받고, 과제가 끝나면 AI 없이 내 코드를 설명해요.
        </p>
      </section>
      <div className="cards2">
        <Link className="rolecard" to="/login">
          <span className="chip acc">교수자</span>
          <strong>과제를 등록하고 반 리포트 보기</strong>
          <span className="note">과제 파일을 올리고 AI 도움 범위를 정해요.</span>
        </Link>
        <Link className="rolecard" to="/student/join">
          <span className="chip acc">학생</span>
          <strong>수업 코드로 과제 풀기</strong>
          <span className="note">무료예요. 교수자가 알려준 수업 코드가 필요해요.</span>
        </Link>
      </div>
      <div className="row" style={{ marginTop: 18 }}>
        {health.isPending && <span className="chip">백엔드 확인 중…</span>}
        {health.isError && <span className="chip warn">백엔드에 연결할 수 없어요 · backend 서버를 켜 주세요</span>}
        {health.data && (
          <span className="chip good">
            백엔드 연결됨 · LLM {health.data.llm_provider} · 분류기 {health.data.classifier}
          </span>
        )}
      </div>
    </main>
  )
}
