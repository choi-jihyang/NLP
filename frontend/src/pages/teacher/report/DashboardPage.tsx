import { useQuery } from '@tanstack/react-query'
import { Link, useParams, useSearchParams } from 'react-router-dom'

import { getAssignment } from '../../../api/assignments'
import { getAssignmentReport } from '../../../api/reports'
import { QueryState } from '../../../components/QueryState'
import { PageHead } from '../../../components/PageHead'
import MistakeSection from './MistakeSection'
import PairChart from './PairChart'
import StudentTables from './StudentTables'

/** 교수자: 과제별 반 리포트 */
export default function DashboardPage() {
  const classId = Number(useParams().classId)
  const [params] = useSearchParams()
  const assignmentId = Number(params.get('assignment'))
  const report = useQuery({ queryKey: ['report', assignmentId], queryFn: () => getAssignmentReport(assignmentId) })
  const assignment = useQuery({ queryKey: ['assignment', assignmentId], queryFn: () => getAssignment(assignmentId) })

  if (!report.data || !assignment.data) {
    return <main className="wrap page"><QueryState isPending={report.isPending || assignment.isPending} error={report.error ?? assignment.error} /></main>
  }
  const r = report.data
  const p = assignment.data.policy
  const base = `/teacher/classes/${classId}`
  const hasProject = assignment.data.questions.some((q) => q.type === 'PROJECT')

  return (
    <>
    <PageHead
      back={{ to: base, label: '클래스' }}
      eyebrow="Report"
      title={`${r.title} · 반 리포트`}
      sub={`최종 제출 ${r.submitted_count}명 기준`}
      actions={hasProject && <Link className="btn primary" to={`${base}/assignments/${assignmentId}/grading`}>간단 제작 채점</Link>}
    />
    <main className="wrap page">
    <div className="stack">
      <div className="figs">
        <div className="fig">
          <span className="label">제출</span>
          <b>{r.submitted_count}명</b>
          <span className="note">{r.student_count}명 중</span>
        </div>
        <div className="fig">
          <span className="label">AI 도움을 받은 원문제 정답률</span>
          <b>{r.assisted_correct_rate}%</b>
          <span className="note">자동 채점 {r.question_stats.length}문항 평균</span>
        </div>
        <div className="fig alert">
          <span className="label">혼자 푼 확인 문제 정답률</span>
          {r.alone_variant_rate === null ? (
            <>
              <b>—</b>
              <span className="note">이 과제에는 확인 문제가 없었어요</span>
            </>
          ) : (
            <>
              <b>{r.alone_variant_rate}%</b>
              <span className="note">원문제보다 {r.assisted_correct_rate - r.alone_variant_rate}%p 낮아요</span>
            </>
          )}
        </div>
        {p.concept_check_enabled && (
          <div className="fig">
            <span className="label">혼자 푼 문항 개념 확인</span>
            <b>{r.concept_check_ok_rate}%</b>
            <span className="note">설명 충분 · {100 - r.concept_check_ok_rate}%는 설명 부족</span>
          </div>
        )}
      </div>
      <PairChart stats={r.question_stats} />
      {p.report_misconceptions && <MistakeSection mistakes={r.mistakes} supplement={r.supplement} />}
      <StudentTables
        dependency={p.report_dependency ? r.dependency : null}
        signals={p.external_signal_enabled ? r.signals : null}
        recordPath={(id) => `${base}/students/${id}?assignment=${assignmentId}`}
      />
    </div>
      </main>
    </>
  )
}
