import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'

import { listAssignments, releaseResults } from '../../api/assignments'
import { getClass, listStudents } from '../../api/classes'
import { listJoinRequests } from '../../api/enrollments'
import { QueryState } from '../../components/QueryState'
import AssignmentCard from './AssignmentCard'

/** 클래스 상세: 수업 코드, 과제 목록, 학생 목록 */
export default function ClassDetailPage() {
  const classId = Number(useParams().classId)
  const cls = useQuery({ queryKey: ['class', classId], queryFn: () => getClass(classId) })
  const assignments = useQuery({ queryKey: ['assignments', classId], queryFn: () => listAssignments(classId) })
  const students = useQuery({ queryKey: ['students', classId], queryFn: () => listStudents(classId) })
  const requests = useQuery({ queryKey: ['join-requests', classId], queryFn: () => listJoinRequests(classId) })
  const client = useQueryClient()
  const release = useMutation({
    mutationFn: releaseResults,
    onSuccess: () => client.invalidateQueries({ queryKey: ['assignments', classId] }),
  })
  const base = `/teacher/classes/${classId}`

  return (
    <div className="stack">
      <QueryState isPending={cls.isPending} error={cls.error} />
      {cls.data && (
        <div className="sbar" style={{ marginBottom: 0 }}>
          <h2>{cls.data.name}</h2>
          <div className="kv"><b>{cls.data.student_count}명</b><span>학생</span></div>
          <div className="kv"><b>{cls.data.invite_code}</b><span>수업 코드</span></div>
          <div className="kv"><b>{cls.data.plan}</b><span>플랜 · {cls.data.student_limit}명 이하</span></div>
        </div>
      )}
      <div className="spread">
        <h3>과제</h3>
        <div className="row">
          <Link className="btn" to={`${base}/ai-settings`}>AI 기본값</Link>
          <Link className="btn primary" to={`${base}/assignments/new`}>새 과제 만들기</Link>
        </div>
      </div>
      <QueryState isPending={assignments.isPending} error={assignments.error} />
      {assignments.data?.map((a) => (
        <AssignmentCard
          key={a.seq}
          assignment={a}
          basePath={base}
          releasing={release.isPending && release.variables === a.seq}
          onRelease={() => release.mutate(a.seq)}
        />
      ))}
      {release.error && <p className="error-text">{release.error.message}</p>}
      <section className="panel stack">
        <div className="spread">
          <div className="row">
            <h3>학생</h3>
            {!!requests.data?.length && <span className="chip warn">참여 요청 {requests.data.length}건</span>}
          </div>
          <Link className="btn sm" to={`${base}/students`}>학생 관리</Link>
        </div>
        <div className="row">
          {students.data?.map((s) => (
            <Link key={s.seq} className="btn sm" to={`${base}/students/${s.seq}?assignment=a1`}>
              {s.student_no}
            </Link>
          ))}
        </div>
        <p className="note">학생을 누르면 과제별 기록(힌트, 확인 문제, 참고 신호)을 볼 수 있어요.</p>
      </section>
    </div>
  )
}
