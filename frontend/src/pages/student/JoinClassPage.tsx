import { useMutation, useQuery } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { listMyClasses } from '../../api/classes'
import { session } from '../../api/client'
import { getMyEnrollment, joinClass, type JoinResult } from '../../api/enrollments'
import { PageHead } from '../../components/PageHead'
import ConsentCard from './ConsentCard'

const STATUS_TEXT = {
  PENDING: '아직 수락 전이에요. 조금 뒤에 다시 확인해 주세요.',
  REJECTED: '교수자가 참여 요청을 거절했어요. 학번이 맞는지 교수자에게 확인해 주세요.',
  REMOVED: '이 수업에서 내보내졌어요. 담당 교수자에게 문의해 주세요.',
} as const

/** 수업 입장 → 기록 안내 동의 → (명단에 없으면) 참여 요청 대기를 한 화면에서 차례로 */
export default function JoinClassPage() {
  const navigate = useNavigate()
  const inside = session.role() === 'STUDENT' && !!session.token()
  const mine = useQuery({ queryKey: ['my-classes'], queryFn: listMyClasses, enabled: inside })
  const knownNo = mine.data?.[0]?.student_no ?? ''
  const [inviteCode, setInviteCode] = useState(inside ? '' : 'TG-4821')
  const [typedNo, setTypedNo] = useState('')
  const studentNo = knownNo || typedNo
  const [joined, setJoined] = useState<JoinResult | null>(null)
  const [approved, setApproved] = useState(false)
  const join = useMutation({
    mutationFn: joinClass,
    onSuccess: (r) => {
      setJoined(r)
      setApproved(r.status === 'APPROVED')
    },
  })
  const check = useMutation({
    mutationFn: (classId: number) => getMyEnrollment(classId),
    onSuccess: (r) => r.status === 'APPROVED' && setApproved(true),
  })

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    join.mutate({ invite_code: inviteCode.trim(), student_no: studentNo.trim() })
  }

  const body = (() => {
    if (joined && approved) {
      return <ConsentCard classId={joined.class_id} className={joined.class_name} onDone={() => navigate('/student/classes')} />
    }
    if (joined) {
      const status = check.data?.status
      return (
        <section className="panel stack narrow" style={{ textAlign: 'center' }}>
          <span className="wait-dot" aria-hidden="true">⋯</span>
          <h2>참여 요청을 보냈어요</h2>
          <p className="muted"><b>{joined.class_name}</b> 교수자가 수락하면 들어갈 수 있어요 · 학번 <b className="mono">{studentNo}</b></p>
          {status && status !== 'APPROVED' && <div className="status wait" role="status">{STATUS_TEXT[status]}</div>}
          <div className="row" style={{ justifyContent: 'center' }}>
            <button className="btn primary" disabled={check.isPending} onClick={() => check.mutate(joined.class_id)}>수락됐는지 확인</button>
            <Link className="btn" to="/">처음으로</Link>
          </div>
        </section>
      )
    }
    return (
      <form className="panel stack narrow" onSubmit={handleSubmit}>
        <h2>수업 입장</h2>
        <label className="field">
          <span className="label">수업 코드</span>
          <input className="mono" value={inviteCode} placeholder="예: TG-1234" onChange={(e) => setInviteCode(e.target.value)} />
        </label>
        {knownNo ? (
          <p className="note">학번 <b className="mono">{knownNo}</b>로 들어가요</p>
        ) : (
          <label className="field">
            <span className="label">학번</span>
            <input className="mono" value={typedNo} placeholder="예: 20260004" onChange={(e) => setTypedNo(e.target.value)} />
          </label>
        )}
        {join.error && <p className="error-text">{join.error.message}</p>}
        <button className="btn primary lg" disabled={join.isPending || !inviteCode.trim() || !studentNo.trim()}>
          {join.isPending ? '확인 중…' : '입장하기'}
        </button>
        <p className="note">가입 없이 들어와요 · 명단에 없으면 참여 요청이 가요</p>
      </form>
    )
  })()

  return (
    <>
      <PageHead eyebrow="Join" title="수업 입장" sub="교수자가 알려준 수업 코드를 입력하세요" />
      <main className="wrap page">{body}</main>
    </>
  )
}
