import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'

import { getMyReport, type ConceptStatus } from '../../api/reports'
import { formatScore } from '../../components/format'
import { PageHead } from '../../components/PageHead'
import { QueryState } from '../../components/QueryState'

const STATUS: Record<ConceptStatus, { label: string; tone: string }> = {
  CONFIRMED: { label: '이해 확인됨', tone: 'good' },
  NEEDS_WORK: { label: '보완 필요', tone: 'bad' },
  UNCLEAR: { label: '아직 확인 부족', tone: 'warn' },
}

/** 학생: 과제 뒤 내 리포트 (개념별 상태 · 오개념 · 다음에 볼 것) */
export default function MyReportPage() {
  const assignmentId = Number(useParams().assignmentId)
  const report = useQuery({ queryKey: ['my-report', assignmentId], queryFn: () => getMyReport(assignmentId) })
  const back = { to: '/student/classes', label: '내 과제' }
  if (!report.data) {
    return (
      <>
        <PageHead back={back} eyebrow="My report" title="내 리포트" />
        <main className="wrap page"><QueryState isPending={report.isPending} error={report.error} /></main>
      </>
    )
  }
  const r = report.data
  if (!r.released) {
    return (
      <>
        <PageHead back={back} eyebrow="My report" title={r.assignment_title} />
        <main className="wrap page">
          <section className="panel stack narrow">
            <p>아직 결과가 공개되지 않았어요. 교수자가 결과를 공개하면 점수, 정답, 개념별 상태를 여기서 볼 수 있어요.</p>
            <Link className="btn" to="/student/classes">내 과제로</Link>
          </section>
        </main>
      </>
    )
  }

  return (
    <>
      <PageHead back={back} eyebrow="My report" title={r.assignment_title} />
      <main className="wrap page">
      <div className="grid g2" style={{ marginBottom: 20 }}>
        <div className="tile">
          <p className="k">{r.pending_points ? `현재 점수 · ${r.pending_points}점 채점 대기` : '점수'}</p>
          <p className="v">{formatScore(r.score)}<small> / {r.max_score}</small></p>
        </div>
        <div className="tile"><p className="k">받은 힌트</p><p className="v">{r.hint_steps}<small> 단계</small></p></div>
      </div>
      <p className="flow">이 리포트는 확정 판정이 아니에요. 판단 근거를 함께 보여주고, 성적에 자동 반영하지 않아요.</p>
      <section className="panel sec" style={{ marginBottom: 16 }}>
        <h3>문항별 결과와 정답</h3>
        <div className="tbl">
          <table>
            <thead>
              <tr><th>문항</th><th>유형</th><th>내 결과</th><th>정답 · 풀이 방향</th></tr>
            </thead>
            <tbody>
              {r.questions.map((q) => (
                <tr key={q.question_index}>
                  <td className="num">{q.question_index + 1}</td>
                  <td>{q.type_label}</td>
                  <td>{q.result}</td>
                  <td>{q.correct_answer}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <div className="two">
        <section className="panel sec">
          <h3>개념별 상태</h3>
          {r.concepts.map((c) => (
            <div className="concept" key={c.name}>
              <b>{c.name}</b>
              <span className={`chip ${STATUS[c.status].tone}`}>{STATUS[c.status].label}</span>
              <span className="why">{c.reason}</span>
            </div>
          ))}
        </section>
        <div className="stack">
          <section className="panel sec">
            <h3>나의 오개념</h3>
            <ul className="sup">
              {r.misconceptions.map((m) => (
                <li key={m}>{m}</li>
              ))}
            </ul>
            <h3>착각 주의 개념</h3>
            <p className="note">
              {r.overconfident.length ? `"확실해요"를 골랐지만 틀린 문항: ${r.overconfident.join(', ')}` : '없어요.'}
            </p>
          </section>
          <section className="panel sec">
            <h3>다음에 볼 것</h3>
            <ul className="sup">
              {r.next_steps.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
            <div className="row">
              <Link className="btn" to="/student/classes">내 과제로</Link>
            </div>
          </section>
        </div>
      </div>
      </main>
    </>
  )
}
