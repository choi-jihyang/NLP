import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'

import { listAssignments, releaseResults } from '../../api/assignments'
import { getClass, listStudents } from '../../api/classes'
import { listJoinRequests } from '../../api/enrollments'
import { QueryState } from '../../components/QueryState'
import { StatTiles } from '../../components/StatTiles'
import AssignmentCard from './AssignmentCard'
import ClassHeader from './ClassHeader'

/** 클래스 상세(과제 탭): 숫자 · 과제 카드 · 학생 목록 */
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
  const list = assignments.data ?? []
  const live = list.filter((a) => a.status !== 'DRAFT')
  // 학생별 기록은 과제 단위라 배포된 첫 과제로 연다. 없으면 기록 링크를 두지 않는다
  const recordId = live[0]?.seq ?? null

  return (
    <>
      <ClassHeader classId={classId} />
      <main className="wrap page">
        <QueryState isPending={cls.isPending} error={cls.error} />
        {cls.data && (
          <StatTiles
            items={[
              { label: '학생', value: cls.data.student_count, unit: `/ ${cls.data.student_limit}명` },
              { label: '과제', value: live.length },
              { label: '최종 제출', value: live.reduce((n, a) => n + a.submitted_count, 0), unit: `/ ${live.reduce((n, a) => n + a.student_count, 0)}명` },
              { label: '참여 요청', value: requests.data?.length ?? 0, unit: '건', alert: !!requests.data?.length },
            ]}
          />
        )}
        <div className="sec-h">
          <h2>과제</h2>
          <Link className="btn text" to={`${base}/ai-settings`}>AI 기본값 →</Link>
        </div>
        <QueryState isPending={assignments.isPending} error={assignments.error} />
        <div className="stack">
          {list.length === 0 && !assignments.isPending && <div className="panel empty-box">아직 과제가 없어요.</div>}
          {list.map((a) => (
            <AssignmentCard
              key={a.seq}
              assignment={a}
              basePath={base}
              releasing={release.isPending && release.variables === a.seq}
              onRelease={() => release.mutate(a.seq)}
            />
          ))}
        </div>
        {release.error && <p className="error-text">{release.error.message}</p>}
        <div className="sec-h">
          <div className="row">
            <h2>학생</h2>
            {!!requests.data?.length && <span className="chip warn">참여 요청 {requests.data.length}건</span>}
          </div>
          <Link className="btn text" to={`${base}/students`}>학생 관리 →</Link>
        </div>
        <div className="panel stack">
          <div className="row">
            {students.data?.map((s) =>
              recordId ? (
                <Link key={s.seq} className="btn sm mono" to={`${base}/students/${s.seq}?assignment=${recordId}`}>{s.student_no}</Link>
              ) : (
                <span key={s.seq} className="chip mono">{s.student_no}</span>
              ),
            )}
            {students.data?.length === 0 && <span className="note">아직 참여한 학생이 없어요.</span>}
          </div>
          <p className="note">학생을 누르면 과제별 기록(힌트, 확인 문제, 참고 신호)을 볼 수 있어요.</p>
        </div>
      </main>
    </>
  )
}
