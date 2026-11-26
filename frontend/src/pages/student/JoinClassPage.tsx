import { useMutation } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { getMyEnrollment, joinClass, type JoinResult } from '../../api/enrollments'

const STATUS_TEXT = {
  PENDING: '아직 수락 전이에요. 조금 뒤에 다시 확인해 주세요.',
  REJECTED: '교수자가 참여 요청을 거절했어요. 학번이 맞는지 교수자에게 확인해 주세요.',
  REMOVED: '이 수업에서 내보내졌어요. 담당 교수자에게 문의해 주세요.',
} as const

/** 수업 코드와 학번으로 입장. 명단에 없으면 참여 요청을 보내고 교수자 수락을 기다린다 */
export default function JoinClassPage() {
  const navigate = useNavigate()
  const [inviteCode, setInviteCode] = useState('TG-4821')
  const [studentNo, setStudentNo] = useState('')
  const [pending, setPending] = useState<JoinResult | null>(null)
  const join = useMutation({
    mutationFn: joinClass,
    onSuccess: (r) => (r.status === 'APPROVED' ? navigate(`/student/consent?class=${r.class_id}`) : setPending(r)),
  })
  const check = useMutation({
    mutationFn: (classId: number) => getMyEnrollment(classId),
    onSuccess: (r) => r.status === 'APPROVED' && pending && navigate(`/student/consent?class=${pending.class_id}`),
  })

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    join.mutate({ invite_code: inviteCode, student_no: studentNo })
  }

  if (pending) {
    const status = check.data?.status
    return (
      <section className="panel stack narrow">
        <h2>참여 요청을 보냈어요</h2>
        <p>
          <b>{pending.class_name}</b> 교수자가 수락하면 들어갈 수 있어요. 학번: <b>{studentNo}</b>
        </p>
        {status && status !== 'APPROVED' && (
          <div className="status wait" role="status">
            {STATUS_TEXT[status]}
          </div>
        )}
        <div className="row">
          <button className="btn primary" disabled={check.isPending} onClick={() => check.mutate(pending.class_id)}>
            수락됐는지 확인
          </button>
          <Link className="btn" to="/student/classes">내 과제로</Link>
        </div>
      </section>
    )
  }

  return (
    <form className="panel stack narrow" onSubmit={handleSubmit}>
      <h2>수업 입장</h2>
      <p className="lead">교수자가 알려준 수업 코드를 입력하세요. 가입은 필요 없어요.</p>
      <label className="field">
        <span className="label">수업 코드</span>
        <input className="inp mono" value={inviteCode} onChange={(e) => setInviteCode(e.target.value)} />
      </label>
      <label className="field">
        <span className="label">학번</span>
        <input className="inp" value={studentNo} placeholder="예: 20260004" onChange={(e) => setStudentNo(e.target.value)} />
      </label>
      {join.error && <p className="error-text">{join.error.message}</p>}
      <button className="btn primary" disabled={join.isPending}>
        {join.isPending ? '확인 중…' : '입장하기'}
      </button>
      <p className="note">교수자가 미리 넣어 둔 명단에 있으면 바로 들어가고, 없으면 참여 요청이 가요.</p>
    </form>
  )
}
