import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { getHealth } from '../api/health'

/** 시작 화면. 백엔드 연결 상태를 함께 보여준다. */
export default function HomePage() {
  const health = useQuery({ queryKey: ['health'], queryFn: getHealth })

  return (
    <main className="wrap stack">
      <h2>ThinkGuard</h2>
      <p className="lead">정답 대신 생각하는 과정을 돕는, 교수자용 학습 AI 플랫폼</p>
      <div className="row">
        {health.isPending && <span className="chip">백엔드 확인 중…</span>}
        {health.isError && <span className="chip bad">백엔드 연결 실패 — backend 서버가 켜져 있는지 확인</span>}
        {health.data && (
          <span className="chip good">
            백엔드 연결됨 · LLM {health.data.llm_provider} · 분류기 {health.data.classifier}
          </span>
        )}
      </div>
      <div className="row">
        <Link className="btn primary" to="/login">로그인</Link>
        <Link className="btn" to="/signup">회원가입</Link>
        <Link className="btn" to="/teacher/classes">교수자 화면</Link>
        <Link className="btn" to="/student/join">학생 화면</Link>
      </div>
    </main>
  )
}
