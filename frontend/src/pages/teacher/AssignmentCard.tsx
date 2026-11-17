import { Link } from 'react-router-dom'

import type { AssignmentSummary } from '../../api/assignments'
import { formatDue } from '../../components/format'

type Props = { assignment: AssignmentSummary; basePath: string; releasing: boolean; onRelease: () => void }

const STATUS = { OPEN: ['진행 중', 'acc'], CLOSED: ['마감', ''], DRAFT: ['작성 중', 'warn'] } as const
const HINT = { NONE: '힌트 없음', CONCEPT: '개념만', STEP: '한 단계씩', EARNED: '시도한 만큼 열기' } as const

/** 과제 목록의 카드 한 장 */
export default function AssignmentCard({ assignment: a, basePath, releasing, onRelease }: Props) {
  const [label, tone] = STATUS[a.status]
  const rate = a.student_count ? (a.submitted_count / a.student_count) * 100 : 0

  return (
    <div className="acard">
      <div className="stack" style={{ gap: 6 }}>
        <div className="row">
          <h3>{a.title}</h3>
          <span className={`chip ${tone}`}>{label}</span>
          {a.todo && <span className="chip warn">{a.todo}</span>}
          {a.results_released && <span className="chip good">결과 공개됨</span>}
        </div>
        <span className="note">
          {a.kinds || '문항 없음'} · 마감 {formatDue(a.due_at)} · AI 도움 {a.hint_mode ? HINT[a.hint_mode] : '미정'}
        </span>
        <div className="row">
          <div className="prog" style={{ flex: 1, maxWidth: 260 }}>
            <i style={{ width: `${rate}%` }} />
          </div>
          <span className="note">
            제출 {a.submitted_count} / {a.student_count}명
          </span>
        </div>
      </div>
      <div className="row">
        {a.status !== 'DRAFT' && (
          <Link className="btn sm" to={`${basePath}/dashboard?assignment=${a.id}`}>리포트</Link>
        )}
        {a.todo?.includes('채점') && (
          <Link className="btn sm" to={`${basePath}/assignments/${a.id}/grading`}>채점</Link>
        )}
        {a.status !== 'DRAFT' && !a.results_released && (
          <button className="btn sm" disabled={releasing} onClick={onRelease} title="점수·정답·내 리포트를 학생에게 공개해요">
            결과 공개
          </button>
        )}
        <Link className="btn sm" to={`${basePath}/assignments/${a.id}/edit`}>
          {a.status === 'DRAFT' ? '이어서 작성' : '설정'}
        </Link>
      </div>
    </div>
  )
}
