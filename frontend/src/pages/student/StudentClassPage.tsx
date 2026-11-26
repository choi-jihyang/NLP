import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { LANGUAGE_LABEL } from '../../api/client'
import { listMyClasses } from '../../api/classes'
import { formatDue } from '../../components/format'
import { QueryState } from '../../components/QueryState'

const STATUS = {
  IN_PROGRESS: { label: '진행 중', tone: 'acc' },
  FINALIZED: { label: '제출 완료 · 결과 공개 전', tone: '' },
  RELEASED: { label: '결과 공개됨', tone: 'good' },
} as const

/** 학생: 참여한 클래스의 과제 목록 */
export default function StudentClassPage() {
  const classes = useQuery({ queryKey: ['my-classes'], queryFn: listMyClasses })

  return (
    <div className="stack">
      <h2>내 과제</h2>
      <QueryState isPending={classes.isPending} error={classes.error} />
      {classes.data?.map((c) => (
        <section className="stack" key={c.class_id}>
          <div className="spread">
            <h3>{c.class_name}</h3>
            <span className="note">{c.student_no}</span>
          </div>
          {c.enrollment_status === 'PENDING' && (
            <div className="status wait">참여 요청을 보냈어요. 교수자가 수락하면 과제가 보여요.</div>
          )}
          {c.assignments.map((a) => (
            <div className="acard" key={a.seq}>
              <div className="stack" style={{ gap: 6 }}>
                <div className="row">
                  <h3>{a.title}</h3>
                  <span className={`chip ${STATUS[a.status].tone}`}>{STATUS[a.status].label}</span>
                </div>
                <span className="note">
                  {LANGUAGE_LABEL[a.language]} · 마감 {formatDue(a.due_at)} · AI 도움: {a.hint_mode_label}
                </span>
                {a.score_text ? (
                  <span className="note">점수 {a.score_text}</span>
                ) : (
                  <div className="row">
                    <div className="prog" style={{ flex: 1, maxWidth: 260 }}>
                      <i style={{ width: `${(a.submitted / a.total) * 100}%` }} />
                    </div>
                    <span className="note">{a.submitted} / {a.total}문항 제출</span>
                  </div>
                )}
              </div>
              {a.status === 'RELEASED' ? (
                <Link className="btn" to={`/student/assignments/${a.seq}/report`}>내 리포트</Link>
              ) : a.status === 'FINALIZED' ? (
                <Link className="btn" to={`/student/assignments/${a.seq}/check`}>이해 확인</Link>
              ) : (
                <Link className="btn primary" to={`/student/assignments/${a.seq}`}>{a.submitted ? '이어서 풀기' : '풀기'}</Link>
              )}
            </div>
          ))}
        </section>
      ))}
    </div>
  )
}
