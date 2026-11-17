import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'

import { getGradingList, gradeAnswer, type GradingItem } from '../../../api/reports'
import { QueryState } from '../../../components/QueryState'
import GradeCard from './GradeCard'

/** 교수자: 간단 제작 문항 직접 채점 */
export default function GradingPage() {
  const { classId = '', assignmentId = '' } = useParams()
  const client = useQueryClient()
  const key = ['grading', assignmentId]
  const list = useQuery({ queryKey: key, queryFn: () => getGradingList(assignmentId) })
  const grade = useMutation({
    mutationFn: (v: { answerId: string; score: number; feedback: string }) => gradeAnswer(v.answerId, { score: v.score, feedback: v.feedback }),
    onSuccess: (saved: GradingItem) =>
      client.setQueryData<GradingItem[]>(key, (old) => old?.map((g) => (g.answer_id === saved.answer_id ? saved : g))),
  })

  if (!list.data) return <QueryState isPending={list.isPending} error={list.error} />
  const pending = list.data.filter((g) => g.score === null).length

  return (
    <div className="stack">
      <div className="sbar">
        <h2>간단 제작 채점</h2>
        <span className="chip warn">교수자 직접 채점</span>
        <div className="kv">
          <b>{pending}건</b>
          <span>채점 대기</span>
        </div>
        <Link className="btn sm" to={`/teacher/classes/${classId}/dashboard?assignment=${assignmentId}`}>반 리포트로</Link>
      </div>
      <p className="note">요구사항별 채점 기준을 보며 점수를 입력한 뒤 확정하면 학생 점수에 바로 반영돼요.</p>
      {list.data.map((item) => (
        <GradeCard
          key={item.answer_id}
          item={item}
          saving={grade.isPending && grade.variables?.answerId === item.answer_id}
          error={grade.error && grade.variables?.answerId === item.answer_id ? grade.error.message : null}
          onSave={(body) => grade.mutate({ answerId: item.answer_id, ...body })}
        />
      ))}
      {!list.data.length && <p className="note">아직 제출한 학생이 없어요.</p>}
    </div>
  )
}
