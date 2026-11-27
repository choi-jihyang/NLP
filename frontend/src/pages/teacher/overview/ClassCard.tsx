import { Link } from 'react-router-dom'

import { CopyCode } from '../../../components/CopyCode'
import { formatDot, periodState } from '../../../components/format'
import type { ClassOverview } from '../../../hooks/useTeacherOverview'

type Props = { item: ClassOverview }

/** 내 클래스 카드: 상태 · 요금제 · 수업 코드 · 학생 수 막대 · 이용 기간 */
export default function ClassCard({ item }: Props) {
  const { info, assignments, grading } = item
  const state = periodState(info.starts_at, info.expires_at)
  const pct = Math.min(100, Math.round((info.student_count / info.student_limit) * 100))
  const count = assignments.filter((a) => a.status !== 'DRAFT').length
  return (
    <Link className="ccard" to={`/teacher/classes/${info.seq}`}>
      <div className="spread">
        <span className={`chip ${state.tone}`}>{state.label}</span>
        <span className="chip">{info.plan}</span>
      </div>
      <div>
        <h3>{info.name}</h3>
        <p className="note" style={{ marginTop: 4 }}>{formatDot(info.starts_at)} – {formatDot(info.expires_at)}</p>
      </div>
      <span><CopyCode code={info.invite_code} /></span>
      <div className="meter">
        <div className="lbl"><span>학생</span><span><b>{info.student_count}</b> / {info.student_limit}명</span></div>
        <div className="track"><i style={{ width: `${pct}%` }} /></div>
      </div>
      <div className="foot">
        <span>{count ? `과제 ${count}개` : '과제 없음'}{grading ? ` · 채점 대기 ${grading}` : ''}</span>
        <span>열기 →</span>
      </div>
    </Link>
  )
}
