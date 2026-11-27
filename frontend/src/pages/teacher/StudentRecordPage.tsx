import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'

import { listStudents } from '../../api/classes'
import { getStudentRecord } from '../../api/reports'
import { formatScore } from '../../components/format'
import { QueryState } from '../../components/QueryState'
import { PageHead } from '../../components/PageHead'
import { TracePipe } from '../../components/TracePipe'

/** 교수자: 학생 한 명의 과제 기록 */
export default function StudentRecordPage() {
  const { classId: classParam, studentId: studentParam } = useParams()
  const classId = Number(classParam)
  const studentId = Number(studentParam)
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const assignmentId = Number(params.get('assignment'))
  const record = useQuery({ queryKey: ['record', assignmentId, studentId], queryFn: () => getStudentRecord(assignmentId, studentId) })
  const students = useQuery({ queryKey: ['students', classId], queryFn: () => listStudents(classId) })
  const base = `/teacher/classes/${classId}`

  if (!record.data) return <main className="wrap page"><QueryState isPending={record.isPending} error={record.error} /></main>
  const r = record.data
  const name = students.data?.find((s) => s.seq === studentId)?.student_no ?? r.student_name

  return (
    <>
    <PageHead
      back={{ to: base, label: '클래스' }}
      eyebrow="Record"
      title={`${name} · ${r.assignment_title}`}
      actions={
        <>
          <label className="field" style={{ width: 160 }}>
            <select className="inp" aria-label="학생 선택" value={studentId} onChange={(e) => navigate(`${base}/students/${e.target.value}?assignment=${assignmentId}`)}>
              {students.data?.map((s) => (
                <option key={s.seq} value={s.seq}>{s.student_no}</option>
              ))}
            </select>
          </label>
          <Link className="btn" to={`${base}/dashboard?assignment=${assignmentId}`}>반 리포트로</Link>
        </>
      }
    />
    <main className="wrap page">
    <div className="stack">
      <p className="flow">학생에게는 담당 교수자가 이 기록을 볼 수 있다고 첫 접속 때 안내해요.</p>
      <div className="figs">
        <div className="fig">
          <span className="label">원문제 점수</span>
          <b>{formatScore(r.score)} / {r.max_score}</b>
          {r.pending_points > 0 && <span className="note">간단 제작 {r.pending_points}점 채점 대기</span>}
        </div>
        <div className="fig alert">
          <span className="label">혼자 푼 확인 문제</span>
          <b>{r.variant_passed} / {r.variant_total}</b>
          <span className="note">{r.variant_note}</span>
        </div>
        <div className="fig">
          <span className="label">받은 힌트</span>
          <b>{r.hint_steps}단계</b>
          <span className="note">반 평균 {r.class_avg_hint_steps}단계</span>
        </div>
      </div>
      <section className="panel sec">
        <h3>문항별 기록</h3>
        <div className="tbl">
          <table>
            <thead>
              <tr><th>문항</th><th>받은 힌트</th><th>원문제 · 테스트</th><th>확인 문제 (AI 없음)</th><th>개념 확인</th><th>참고 신호</th></tr>
            </thead>
            <tbody>
              {r.rows.map((row) => (
                <tr key={row.question_index}>
                  <td className="num">{row.question_index + 1}</td>
                  <td className="num">{row.hint_steps}단계</td>
                  <td>{row.result}</td>
                  <td>{row.variant}</td>
                  <td>{row.concept_check}</td>
                  <td>{row.signal ? <span className="chip warn">{row.signal}</span> : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      {r.conversation ? (
      <section className="panel sec">
        <h3>문항 {r.conversation.question_index + 1} 대화 요약</h3>
        {r.conversation.turns.map((t, i) => (
          <div className="case" key={i}>
            <p className="say">{t.message}</p>
            <TracePipe classification={t.classification} attempt={t.attempt} leakBlocked={t.leak_blocked} externalSignals={[]} />
          </div>
        ))}
        <p className="note">{r.conversation.note}</p>
      </section>
      ) : (
        <section className="panel sec">
          <h3>대화 요약</h3>
          <p className="note">이 학생은 이 과제에서 AI 도움을 쓰지 않았어요.</p>
        </section>
      )}
    </div>
      </main>
    </>
  )
}
