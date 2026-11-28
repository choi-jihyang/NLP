import { useState } from 'react'
import { Link } from 'react-router-dom'

import type { ClassStudent } from '../../../api/classes'

type Props = {
  students: ClassStudent[]
  count: number
  limit: number
  basePath: string
  /** 기록 보기로 열 과제. null이면 버튼을 숨긴다 */
  recordAssignmentId: number | null
  busyId: number | null
  onRemove: (studentId: number) => void
}

/** 참여 중인 학생. 기록 보기 · 내보내기(한 번 더 확인) */
export default function StudentList({ students, count, limit, basePath, recordAssignmentId, busyId, onRemove }: Props) {
  const [confirmId, setConfirmId] = useState<number | null>(null)

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
        <div className="spread" key={s.seq}>
          <b>{s.student_no}</b>
          {confirmId === s.seq ? (
            <div className="row">
              <span className="note">내보내면 과제와 AI 도움에 더 들어올 수 없어요. 제출 기록은 남아요.</span>
              <button className="btn sm primary" disabled={busyId === s.seq} onClick={() => onRemove(s.seq)}>내보내기</button>
              <button className="btn sm" onClick={() => setConfirmId(null)}>취소</button>
            </div>
          ) : (
            <div className="row">
              {recordAssignmentId !== null && (
                <Link className="btn sm" to={`${basePath}/students/${s.seq}?assignment=${recordAssignmentId}`}>기록 보기</Link>
              )}
              <button className="btn sm" onClick={() => setConfirmId(s.seq)}>내보내기</button>
            </div>
          )}
        </div>
      ))}
    </section>
  )
}
