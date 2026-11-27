import { useMutation, useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { getMySubmission } from '../../../api/submissions'
import { getUnderstandingCheck, submitUnderstandingCheck, type Confidence } from '../../../api/understanding'
import { CodeBlock } from '../../../components/CodeBlock'
import { PageHead } from '../../../components/PageHead'
import { QueryState } from '../../../components/QueryState'
import CheckItemCard from './CheckItemCard'

/** 학생: 과제를 다 낸 뒤 AI 없이 하는 이해 확인 */
export default function UnderstandingCheckPage() {
  const assignmentId = Number(useParams().assignmentId)
  const check = useQuery({ queryKey: ['understanding', assignmentId], queryFn: () => getUnderstandingCheck(assignmentId) })
  const submission = useQuery({ queryKey: ['submission', assignmentId], queryFn: () => getMySubmission(assignmentId) })
  const [explanation, setExplanation] = useState('')
  const [values, setValues] = useState<Record<string, string>>({})
  const [confidence, setConfidence] = useState<Record<string, Confidence>>({})
  const result = useMutation({
    mutationFn: () =>
      submitUnderstandingCheck(assignmentId, {
        explanation,
        answers: (check.data?.items ?? []).map((i) => ({
          question_id: i.question_id,
          value: values[i.question_id] ?? '',
          confidence: confidence[i.question_id] ?? null,
        })),
      }),
  })

  const head = (
    <PageHead
      back={{ to: '/student/classes', label: '내 과제' }}
      eyebrow="Understanding check"
      title="이해 확인"
      sub="AI 없이 · 한 번만 낼 수 있어요"
    />
  )
  if (!check.data || !submission.data) {
    return (
      <>
        {head}
        <main className="wrap page">
          <QueryState isPending={check.isPending || submission.isPending} error={check.error ?? submission.error} />
        </main>
      </>
    )
  }
  if (!submission.data.finalized) {
    return (
      <>
        {head}
        <main className="wrap page">
          <section className="panel stack narrow">
            <p>과제를 최종 제출한 뒤에 할 수 있어요.</p>
            <Link className="btn primary" to={`/student/assignments/${assignmentId}`}>과제로 돌아가기</Link>
          </section>
        </main>
      </>
    )
  }
  const { items } = check.data
  const done = !!result.data
  const ready = explanation.trim().length > 0 && items.every((i) => (values[i.question_id] ?? '').trim())

  return (
    <>
      {head}
      <main className="wrap page">
      <div className="grid g3" style={{ marginBottom: 24 }}>
        <div className="tile"><p className="k">도움</p><p className="v" style={{ fontSize: '1.3rem' }}>AI 없음</p></div>
        <div className="tile"><p className="k">예상 시간</p><p className="v" style={{ fontSize: '1.3rem' }}>약 3~5분</p></div>
        <div className="tile"><p className="k">점수</p><p className="v" style={{ fontSize: '1.3rem' }}>자동 반영 안 됨</p></div>
      </div>
      <p className="flow">최종 제출 → 이해 확인 → 교수자가 결과를 공개하면 내 리포트</p>
      <div className="stack mid" style={{ margin: 0 }}>
        <section className="panel stack">
          <b>1. 내 코드 설명하기</b>
          <p className="qtext">{check.data.explain_prompt}</p>
          <CodeBlock code={check.data.explain_code} />
          <textarea
            className="inp"
            aria-label="내 코드 설명"
            placeholder="본인 말로 적어 주세요"
            value={explanation}
            disabled={done}
            onChange={(e) => setExplanation(e.target.value)}
          />
        </section>
        {items.map((item, k) => (
          <CheckItemCard
            key={item.question_id}
            number={k + 2}
            item={item}
            value={values[item.question_id] ?? ''}
            confidence={confidence[item.question_id] ?? null}
            done={done}
            onChange={(v) => setValues((s) => ({ ...s, [item.question_id]: v }))}
            onConfidence={(v) => setConfidence((s) => ({ ...s, [item.question_id]: v }))}
          />
        ))}
        {done && (
          <div className="status">
            <div>✓</div>
            <div>이해 확인을 제출했어요. 결과는 교수자가 공개하면 내 리포트에서 함께 볼 수 있어요.</div>
          </div>
        )}
        <div className="row">
          {done ? (
            <Link className="btn primary" to="/student/classes">내 과제로</Link>
          ) : (
            <button className="btn primary" disabled={!ready || result.isPending} onClick={() => result.mutate()}>
              제출하기
            </button>
          )}
          <span className="note">이 단계 결과는 점수에 자동 반영되지 않아요.</span>
        </div>
        {result.error && <p className="error-text">{result.error.message}</p>}
      </div>
      </main>
    </>
  )
}
