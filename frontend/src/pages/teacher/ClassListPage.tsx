import { Link } from 'react-router-dom'

import { session } from '../../api/client'
import { PageHead } from '../../components/PageHead'
import { QueryState } from '../../components/QueryState'
import { StatTiles } from '../../components/StatTiles'
import { useTeacherOverview } from '../../hooks/useTeacherOverview'
import ClassCard from './overview/ClassCard'
import TodoList from './overview/TodoList'

/** 교수자 로그인 직후 첫 화면: 인사 · 숫자 · 지금 할 일 · 내 클래스 */
export default function ClassListPage() {
  const { isPending, error, classes, stats, todos } = useTeacherOverview()
  const name = session.user()?.name ?? '교수자'
  return (
    <>
      <PageHead
        eyebrow="Dashboard"
        title={`${name}님, 안녕하세요`}
        sub={todos.length ? `지금 확인할 일이 ${todos.length}건 있어요.` : '지금 확인할 일이 없어요.'}
        actions={<Link className="btn primary" to="/teacher/classes/new">+ 클래스 개설</Link>}
      />
      <main className="wrap page">
        <QueryState isPending={isPending} error={error} />
        <StatTiles
          items={[
            { label: '클래스', value: stats.classes },
            { label: '학생', value: stats.students, unit: '명' },
            { label: '진행 중 과제', value: stats.openAssignments },
            { label: '채점 대기', value: stats.grading, unit: '건', alert: stats.grading > 0 },
          ]}
        />
        <div className="sec-h"><h2>지금 할 일</h2></div>
        <TodoList items={todos} />
        <div className="sec-h"><h2>내 클래스</h2><span className="note">{classes.length}개</span></div>
        <div className="grid g3">
          {classes.map((c) => <ClassCard key={c.info.seq} item={c} />)}
          <Link className="ccard new" to="/teacher/classes/new">
            <span className="plus">+</span>
            <b>새 클래스 개설</b>
            <span className="note">요금제를 고르면 수업 코드가 발급돼요</span>
          </Link>
        </div>
      </main>
    </>
  )
}
