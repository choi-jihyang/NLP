import { useState } from 'react'
import { Link } from 'react-router-dom'

import type { ClassStudent } from '../../../api/classes'

type Props = {
  students: ClassStudent[]
  count: number
  limit: number
  basePath: string
  busyId: string | null
  onRemove: (studentId: string) => void
}

/** 참여 중인 학생. 기록 보기 · 내보내기(한 번 더 확인) */
export default function StudentList({ students, count, limit, basePath, busyId, onRemove }: Props) {
  const [confirmId, setConfirmId] = useState<string | null>(null)

  return (
    <section className="panel stack">
      <div className="spread">
        <h3>참여 학생</h3>
        <span className="chip">
          {count} / {limit}명
        </span>
      </div>
      {!students.length && <p className="note">아직 들어온 학생이 없어요. 수업 코드를 학생들에게 알려 주세요.</p>}
      {students.map((s) => (
        <div className="spread" key={s.id}>
          <b>{s.alias}</b>
          {confirmId === s.id ? (
            <div className="row">
              <span className="note">내보내면 과제와 AI 도움에 더 들어올 수 없어요. 제출 기록은 남아요.</span>
              <button className="btn sm primary" disabled={busyId === s.id} onClick={() => onRemove(s.id)}>내보내기</button>
              <button className="btn sm" onClick={() => setConfirmId(null)}>취소</button>
            </div>
          ) : (
            <div className="row">
              <Link className="btn sm" to={`${basePath}/students/${s.id}?assignment=a1`}>기록 보기</Link>
              <button className="btn sm" onClick={() => setConfirmId(s.id)}>내보내기</button>
            </div>
          )}
        </div>
      ))}
    </section>
  )
}
