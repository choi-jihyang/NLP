import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { listMyClasses } from '../../api/classes'
import { LANGUAGE_LABEL } from '../../api/client'
import { formatDue } from '../../components/format'
import { PageHead } from '../../components/PageHead'
import { QueryState } from '../../components/QueryState'
import TaskCard from './TaskCard'

/** 학생 입장 후 첫 화면: 클래스별 과제 카드 + 끝난 과제 */
export default function StudentClassPage() {
  const mine = useQuery({ queryKey: ['my-classes'], queryFn: listMyClasses })
  const classes = mine.data ?? []
  const open = classes.flatMap((c) => c.assignments.filter((a) => a.status !== 'RELEASED'))
  const done = classes.flatMap((c) => c.assignments.filter((a) => a.status === 'RELEASED').map((a) => ({ a, cls: c.class_name })))
  const nearest = open.map((a) => a.due_at).filter((d): d is string => !!d).sort()[0]

  return (
    <>
      <PageHead
        eyebrow="My assignments"
        title="내 과제"
        sub={`진행 중인 과제 ${open.length}개${nearest ? ` · 가장 가까운 마감 ${formatDue(nearest).split(' ').slice(0, 2).join(' ')}` : ''}`}
        actions={<Link className="btn" to="/student/join">+ 다른 클래스 참여</Link>}
      />
      <main className="wrap page">
        <QueryState isPending={mine.isPending} error={mine.error} />
        {mine.data && classes.length === 0 && (
          <div className="panel empty-box">아직 참여한 수업이 없어요. <Link to="/student/join">수업 코드로 입장</Link>해 주세요.</div>
        )}
        {classes.map((c) => (
          <section key={c.class_id} className="stack" style={{ marginBottom: 32 }}>
            <div className="row"><h2>{c.class_name}</h2><span className="chip mono">{c.student_no}</span></div>
            {c.enrollment_status === 'PENDING' && <div className="status wait">교수자가 참여 요청을 수락하면 과제가 보여요.</div>}
            {c.enrollment_status === 'APPROVED' && c.assignments.filter((a) => a.status !== 'RELEASED').length === 0 && (
              <p className="note">진행 중인 과제가 없어요.</p>
            )}
            {c.assignments.filter((a) => a.status !== 'RELEASED').map((a) => <TaskCard key={a.seq} assignment={a} />)}
          </section>
        ))}
        {mine.data && classes.length > 0 && (
          <>
            <div className="sec-h"><h2>끝난 과제</h2></div>
            {done.length === 0 ? (
              <div className="panel empty-box">아직 끝난 과제가 없어요. 교수자가 결과를 공개하면 여기서 내 리포트를 볼 수 있어요.</div>
            ) : (
              <div className="panel card-tbl">
                <table>
                  <thead><tr><th>과제</th><th>클래스</th><th>점수</th><th /></tr></thead>
                  <tbody>
                    {done.map(({ a, cls }) => (
                      <tr key={a.seq}>
                        <td><b>{a.title}</b> <span className="note">{LANGUAGE_LABEL[a.language]}</span></td>
                        <td>{cls}</td>
                        <td>{a.score_text ?? '-'}</td>
                        <td style={{ textAlign: 'right' }}><Link className="btn sm" to={`/student/assignments/${a.seq}/report`}>내 리포트</Link></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </main>
    </>
  )
}
