import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'

import { getClass, listStudents } from '../../../api/classes'
import {
  decideJoinRequest,
  getRosterSettings,
  listJoinRequests,
  removeStudent,
  saveRosterSettings,
  type RosterSettings,
} from '../../../api/enrollments'
import { QueryState } from '../../../components/QueryState'
import JoinRequestList from './JoinRequestList'
import RosterEditor from './RosterEditor'
import StudentList from './StudentList'

/** 교수자: 학생 관리 (참여 요청 수락·거절, 명단 미리 넣기, 내보내기) */
export default function ClassStudentsPage() {
  const { classId = '' } = useParams()
  const client = useQueryClient()
  const cls = useQuery({ queryKey: ['class', classId], queryFn: () => getClass(classId) })
  const students = useQuery({ queryKey: ['students', classId], queryFn: () => listStudents(classId) })
  const requests = useQuery({ queryKey: ['join-requests', classId], queryFn: () => listJoinRequests(classId) })
  const roster = useQuery({ queryKey: ['roster', classId], queryFn: () => getRosterSettings(classId) })
  const refresh = () =>
    Promise.all(
      [['students', classId], ['join-requests', classId], ['class', classId], ['classes']].map((queryKey) =>
        client.invalidateQueries({ queryKey }),
      ),
    )

  const decide = useMutation({
    mutationFn: (v: { id: string; approve: boolean }) => decideJoinRequest(classId, v.id, v.approve),
    onSuccess: refresh,
  })
  const remove = useMutation({ mutationFn: (id: string) => removeStudent(classId, id), onSuccess: refresh })
  const save = useMutation({
    mutationFn: (body: RosterSettings) => saveRosterSettings(classId, body),
    onSuccess: (data) => {
      client.setQueryData(['roster', classId], data)
      return refresh()
    },
  })

  if (!cls.data || !students.data || !requests.data || !roster.data) {
    const error = cls.error ?? students.error ?? requests.error ?? roster.error
    return <QueryState isPending={!error} error={error} />
  }
  const base = `/teacher/classes/${classId}`
  const error = decide.error ?? remove.error ?? save.error

  return (
    <div className="stack">
      <div className="sbar" style={{ marginBottom: 0 }}>
        <h2>{cls.data.name} · 학생 관리</h2>
        <div className="kv">
          <b>{cls.data.invite_code}</b>
          <span>수업 코드</span>
        </div>
        <Link className="btn sm" to={base}>클래스로</Link>
      </div>
      {error && <p className="error-text">{error.message}</p>}
      <div className="two">
        <div className="stack">
          <JoinRequestList
            requests={requests.data}
            busyId={decide.isPending ? (decide.variables?.id ?? null) : null}
            onDecide={(id, approve) => decide.mutate({ id, approve })}
          />
          <RosterEditor key={roster.dataUpdatedAt} settings={roster.data} saving={save.isPending} onSave={(body) => save.mutate(body)} />
        </div>
        <StudentList
          students={students.data}
          count={cls.data.student_count}
          limit={cls.data.student_limit}
          basePath={base}
          busyId={remove.isPending ? (remove.variables ?? null) : null}
          onRemove={(id) => remove.mutate(id)}
        />
      </div>
    </div>
  )
}
