import { Link } from 'react-router-dom'

import type { TodoItem } from '../../../hooks/useTeacherOverview'

type Props = { items: TodoItem[] }

const ICON: Record<TodoItem['kind'], string> = { GRADING: '✎', JOIN: '+', DUE: '◷' }
const GO: Record<TodoItem['kind'], string> = { GRADING: '채점하기 →', JOIN: '수락 · 거절 →', DUE: '리포트 →' }

/** 지금 할 일: 채점 대기 · 참여 요청 · 마감 가까운 과제 */
export default function TodoList({ items }: Props) {
  if (items.length === 0) return <div className="panel empty-box">지금 할 일이 없어요.</div>
  return (
    <div className="panel todo">
      {items.map((t) => (
        <Link key={t.kind + t.to} to={t.to}>
          <span className={`ic${t.kind === 'GRADING' ? ' warn' : ''}`} aria-hidden="true">{ICON[t.kind]}</span>
          <span><b>{t.title}</b><span className="m">{t.meta}</span></span>
          <span className="go">{GO[t.kind]}</span>
        </Link>
      ))}
    </div>
  )
}
