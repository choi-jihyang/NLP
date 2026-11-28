import { useMutation, useQuery } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { listMyClasses } from '../../api/classes'
import { session } from '../../api/client'
import { clearReentryTicket, getMyEnrollment, joinClass, type JoinResult } from '../../api/enrollments'
import ConsentCard from './ConsentCard'

const STATUS_TEXT = {
  PENDING: '아직 수락 전이에요. 조금 뒤에 다시 확인해 주세요.',
  REJECTED: '교수자가 참여 요청을 거절했어요. 학번이 맞는지 교수자에게 확인해 주세요.',
  REMOVED: '이 수업에서 내보내졌어요. 담당 교수자에게 문의해 주세요.',
} as const

type Props = {
  /** true면 카드(panel)로 감싼다. 로그인 화면 탭 안에서는 false */
  framed?: boolean
  /** 수락되면 부를 함수. 없으면 이 자리에서 기록 안내 동의를 보여 준다 */
  onApproved?: (classId: number) => void
}

/** 수업 코드 + 학번 입장 → (명단에 없으면) 참여 요청 대기 → 기록 안내 동의. 수업 입장 화면 · 로그인 화면 학생 탭이 함께 쓴다 */
export default function JoinFlow({ framed = true, onApproved }: Props) {
  const navigate = useNavigate()
  const box = framed ? 'panel stack narrow' : 'stack'
  // 이미 입장한 학생만 학번을 고정한다(로그아웃 뒤 남은 학번으로 들어가지 않게)
  const inside = session.role() === 'STUDENT' && !!session.token()
  const mine = useQuery({ queryKey: ['my-classes'], queryFn: listMyClasses, enabled: inside })
  const knownNo = inside ? (mine.data?.[0]?.student_no ?? '') : ''
  const [inviteCode, setInviteCode] = useState(inside ? '' : 'TG-4821')
  const [typedNo, setTypedNo] = useState('')
  const studentNo = knownNo || typedNo
  const [joined, setJoined] = useState<JoinResult | null>(null)
  const [approved, setApproved] = useState(false)
  const approve = (r: JoinResult) => {
    if (onApproved) onApproved(r.class_id)
    else setApproved(true)
  }
  const join = useMutation({
    mutationFn: joinClass,
    onSuccess: (r) => {
      setJoined(r)
      if (r.status === 'APPROVED') approve(r)
    },
  })
  const check = useMutation({
    mutationFn: (classId: number) => getMyEnrollment(classId),
    onSuccess: (r) => r.status === 'APPROVED' && joined && approve(joined),
  })
  const retype = () => {
    clearReentryTicket()
    setJoined(null)
    check.reset()
    join.reset()
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    join.mutate({ invite_code: inviteCode.trim(), student_no: studentNo.trim() })
  }

  if (joined && approved) {
    return <ConsentCard classId={joined.class_id} className={joined.class_name} onDone={() => navigate('/student/classes')} />
  }
  if (joined) {
    const status = check.data?.status
    return (
      <section className={box} style={{ textAlign: 'center' }}>
        <span className="wait-dot" aria-hidden="true">⋯</span>
        <h2>참여 요청을 보냈어요</h2>
        <p className="muted"><b>{joined.class_name}</b> 교수자가 수락하면 들어갈 수 있어요 · 학번 <b className="mono">{studentNo}</b></p>
        {status && status !== 'APPROVED' && <div className="status wait" role="status">{STATUS_TEXT[status]}</div>}
        {check.error && <p className="error-text">{check.error.message}</p>}
        <div className="row" style={{ justifyContent: 'center' }}>
          <button className="btn primary" disabled={check.isPending} onClick={() => check.mutate(joined.class_id)}>수락됐는지 확인</button>
          {!knownNo && <button className="btn" onClick={retype}>학번 다시 입력</button>}
          <Link className="btn" to="/">처음으로</Link>
        </div>
      </section>
    )
  }
  return (
    <form className={box} onSubmit={handleSubmit}>
      {framed && <h2>수업 입장</h2>}
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
}
