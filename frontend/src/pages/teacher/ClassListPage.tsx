import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { listClasses } from '../../api/classes'
import { QueryState } from '../../components/QueryState'

/** 내 클래스 목록 */
export default function ClassListPage() {
  const classes = useQuery({ queryKey: ['classes'], queryFn: listClasses })

  return (
    <div className="stack">
      <div className="spread">
        <h2>내 클래스</h2>
        <Link className="btn primary" to="/teacher/classes/new">클래스 개설</Link>
      </div>
      <QueryState isPending={classes.isPending} error={classes.error} />
      {classes.data?.map((c) => (
        <div className="acard" key={c.id}>
          <div className="stack" style={{ gap: 6 }}>
            <h3>{c.name}</h3>
            <span className="note">
              학생 {c.student_count} / {c.student_limit}명 · {c.plan} · 수업 코드 <span className="mono">{c.invite_code}</span>
            </span>
          </div>
          <Link className="btn" to={`/teacher/classes/${c.id}`}>열기</Link>
        </div>
      ))}
    </div>
  )
}
