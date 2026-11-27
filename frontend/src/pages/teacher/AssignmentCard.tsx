import { Link } from 'react-router-dom'

import type { AssignmentSummary } from '../../api/assignments'
import { formatDue } from '../../components/format'

type Props = { assignment: AssignmentSummary; basePath: string; releasing: boolean; onRelease: () => void }

const STATUS = { OPEN: ['진행 중', 'good'], CLOSED: ['마감', ''], DRAFT: ['작성 중', 'warn'] } as const
const HINT = { NONE: '힌트 없음', CONCEPT: '개념만', STEP: '한 단계씩', EARNED: '시도한 만큼 열기' } as const

/** 과제 목록의 카드 한 장: 상태 · 제출 진행 · 리포트 · 채점 · 결과 공개 · 설정 */
export default function AssignmentCard({ assignment: a, basePath, releasing, onRelease }: Props) {
  const [label, tone] = STATUS[a.status]
  const rate = a.student_count ? (a.submitted_count / a.student_count) * 100 : 0
  const live = a.status !== 'DRAFT'

  return (
    <div className="acard panel">
      <div className="stack" style={{ gap: 6 }}>
        <div className="row">
          <h3>{a.title}</h3>
          <span className={`chip ${tone}`}>{label}</span>
          {a.results_released && <span className="chip acc">결과 공개됨</span>}
        </div>
        <span className="note">
          {a.kinds || '문항 없음'} · 마감 {formatDue(a.due_at)} · AI 도움 {a.hint_mode ? HINT[a.hint_mode] : '미정'}
        </span>
        <div className="row">
          <div className="track" style={{ flex: 1, maxWidth: 260 }}><i style={{ width: `${rate}%` }} /></div>
          <span className="note">제출 {a.submitted_count} / {a.student_count}명</span>
        </div>
      </div>
      <div className="row">
        {live && <Link className="btn sm" to={`${basePath}/dashboard?assignment=${a.seq}`}>리포트</Link>}
        {live && a.kinds.includes('간단 제작') && (
          <Link className="btn sm" to={`${basePath}/assignments/${a.seq}/grading`}>채점</Link>
        )}
        <Link className="btn sm" to={`${basePath}/assignments/${a.seq}/edit`}>{live ? '설정' : '이어서 작성'}</Link>
        {live && !a.results_released && (
          <button className="btn sm primary" disabled={releasing} onClick={onRelease} title="점수·정답·내 리포트를 학생에게 공개해요">
            결과 공개
          </button>
        )}
      </div>
    </div>
  )
}
