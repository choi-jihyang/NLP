import type { ClassInfo } from '../../../api/classes'
import { formatDate } from '../../../components/format'

type Props = { classes: ClassInfo[]; busyId: number | null; onExtend: (c: ClassInfo) => void }

/** 이미 개설한 클래스의 이용 기간 연장 (목업) */
export default function ExtendList({ classes, busyId, onExtend }: Props) {
  if (!classes.length) return null
  return (
    <section className="panel stack">
      <h3>이용 기간 연장</h3>
      <p className="note">개설한 클래스는 최대 1년 쓸 수 있어요. 연장하면 지금 만료일에서 1년이 늘어나요.</p>
      {classes.map((c) => (
        <div className="spread" key={c.seq}>
          <div className="stack" style={{ gap: 2 }}>
            <b>{c.name}</b>
            <span className="note">
              {c.plan} · 학생 {c.student_limit}명 · 만료 {formatDate(c.expires_at)}
            </span>
          </div>
          <button className="btn sm" disabled={busyId === c.seq} onClick={() => onExtend(c)}>1년 연장 (목업)</button>
        </div>
      ))}
    </section>
  )
}
