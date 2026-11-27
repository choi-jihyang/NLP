import { Link } from 'react-router-dom'

import type { MyAssignment } from '../../api/classes'
import { LANGUAGE_LABEL } from '../../api/client'
import { daysUntil, formatDue } from '../../components/format'

type Props = { assignment: MyAssignment }

const FLOW = ['문항 풀기', '최종 제출', '이해 확인', '내 리포트']
const STEP = { IN_PROGRESS: 0, FINALIZED: 2, RELEASED: 3 } as const
const CHIP = { IN_PROGRESS: ['진행 중', 'acc'], FINALIZED: ['제출 완료 · 결과 공개 전', ''], RELEASED: ['결과 공개됨', 'good'] } as const

/** 내 과제 카드: 상태 · 제출 진행 · 마감 D-day · 다음 단계 버튼 · 흐름 막대 */
export default function TaskCard({ assignment: a }: Props) {
  const base = `/student/assignments/${a.seq}`
  const step = STEP[a.status]
  const [label, tone] = CHIP[a.status]
  const left = a.due_at ? daysUntil(a.due_at) : null
  const action =
    a.status === 'IN_PROGRESS' ? { to: base, text: '이어서 풀기 →' } : a.status === 'FINALIZED' ? { to: `${base}/check`, text: '이해 확인' } : { to: `${base}/report`, text: '내 리포트' }

  return (
    <div className="panel">
      <div className="task">
        <div>
          <div className="row"><h3>{a.title}</h3><span className={`chip ${tone}`}>{label}</span></div>
          <p className="meta">{LANGUAGE_LABEL[a.language]} · 마감 {formatDue(a.due_at)} · AI 도움: {a.hint_mode_label}{a.score_text ? ` · 점수 ${a.score_text}` : ''}</p>
          <div className="dots">
            {Array.from({ length: a.total }, (_, i) => <i key={i} className={i < a.submitted ? 'done' : undefined} />)}
            <span>{a.submitted} / {a.total}문항 제출</span>
          </div>
        </div>
        <div className="row" style={{ gap: 16 }}>
          {a.status === 'IN_PROGRESS' && left !== null && left >= 0 && (
            <div className="due"><b>D-{left}</b><span>{formatDue(a.due_at).split(' ').slice(0, 2).join(' ')}</span></div>
          )}
          <Link className={`btn${a.status === 'IN_PROGRESS' ? ' primary' : ''}`} to={action.to}>{action.text}</Link>
        </div>
      </div>
      <div className="flowline">
        {FLOW.map((f, i) => (
          <div key={f} className={i === step ? 'on' : undefined}><small>0{i + 1}</small>{f}</div>
        ))}
      </div>
    </div>
  )
}
