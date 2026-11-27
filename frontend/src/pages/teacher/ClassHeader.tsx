import { useQuery } from '@tanstack/react-query'
import { Link, NavLink } from 'react-router-dom'

import { getClass } from '../../api/classes'
import { listJoinRequests } from '../../api/enrollments'
import { CopyCode } from '../../components/CopyCode'
import { daysUntil, formatDot, periodState } from '../../components/format'
import { PageHead } from '../../components/PageHead'

type Props = { classId: number }

/** 클래스 머리: 상태 · 요금제 · 기간 · 수업 코드 · 새 과제 + 탭(과제 · 학생 · AI 기본값) */
export default function ClassHeader({ classId }: Props) {
  const cls = useQuery({ queryKey: ['class', classId], queryFn: () => getClass(classId) })
  const requests = useQuery({ queryKey: ['join-requests', classId], queryFn: () => listJoinRequests(classId) })
  const base = `/teacher/classes/${classId}`
  const c = cls.data
  const state = c ? periodState(c.starts_at, c.expires_at) : null
  const left = c ? Math.max(0, daysUntil(c.expires_at)) : 0

  return (
    <PageHead
      back={{ to: '/teacher/classes', label: '내 클래스' }}
      title={c?.name ?? '클래스'}
      sub={
        c && (
          <span className="row">
            {state && <span className={`chip ${state.tone}`}>{state.label}</span>}
            <span className="chip">{c.plan} · {c.student_limit}명 이하</span>
            <span>{formatDot(c.starts_at)} – {formatDot(c.expires_at)} · 남은 기간 {left}일</span>
          </span>
        )
      }
      actions={
        c && (
          <>
            <CopyCode code={c.invite_code} />
            <Link className="btn primary" to={`${base}/assignments/new`}>+ 새 과제 만들기</Link>
          </>
        )
      }
    >
      <nav className="subtabs">
        <NavLink to={base} end>과제</NavLink>
        <NavLink to={`${base}/students`}>
          학생{!!requests.data?.length && <span className="chip warn">요청 {requests.data.length}</span>}
        </NavLink>
        <NavLink to={`${base}/ai-settings`}>AI 기본값</NavLink>
      </nav>
    </PageHead>
  )
}
