import { useMutation, useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { getPolicyPreview, publishAssignment, saveAssignment, simulateAttacks, type Assignment } from '../../../api/assignments'
import { LANGUAGE_LABEL } from '../../../api/client'
import SimulationList from './SimulationList'

type Props = { draft: Assignment; onSaved: (saved: Assignment) => void; onPrev: () => void }

/** STEP 4. 설정 요약 확인 · 우회 요청 시뮬레이션 · 배포 */
export default function StepReview({ draft, onSaved, onPrev }: Props) {
  const p = draft.policy
  const preview = useQuery({ queryKey: ['policy-preview', draft], queryFn: () => getPolicyPreview(draft) })
  const simulate = useMutation({ mutationFn: () => simulateAttacks(draft) })
  const deploy = useMutation({
    mutationFn: async () => {
      const saved = await saveAssignment(draft)
      onSaved(saved)
      const { invite_code } = await publishAssignment(saved.seq ?? 0)
      return { saved, invite_code }
    },
  })
  const base = `/teacher/classes/${draft.class_id}`

  return (
    <>
      <section className="panel stack">
        <h2>{draft.title || '이름 없는 과제'}</h2>
        <div className="row">
          {[draft.audience, LANGUAGE_LABEL[draft.language], draft.course].filter(Boolean).map((t) => (
            <span className="chip" key={t}>{t}</span>
          ))}
          {p.code_line_limit > 0 && <span className="chip acc">힌트 코드 {p.code_line_limit}줄 이내</span>}
          {preview.data && <span className="chip acc">{preview.data.hint_mode_label}</span>}
          {p.prompt_mode === 'CUSTOM' && <span className="chip acc">직접 쓴 지시문</span>}
          {p.variant_enabled && <span className="chip acc">AI 없이 확인 문제</span>}
          {p.concept_check_enabled && <span className="chip acc">제출 전 개념 확인</span>}
          {p.external_signal_enabled && <span className="chip warn">외부 AI 의심 신호 · 실험</span>}
        </div>
        <div className="stack">
          <h3>학생은 이렇게 경험해요</h3>
          <ul className="summary">
            {preview.data?.lines.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
        </div>
      </section>
      <section className="panel stack" style={{ marginTop: 16 }}>
        <div className="spread">
          <h3>학생처럼 졸라보기</h3>
          <button className="btn sm" disabled={simulate.isPending} onClick={() => simulate.mutate()}>
            {simulate.data ? '다시 실행' : '실행하기'}
          </button>
        </div>
        <p className="lead">배포 전에 학생들이 자주 쓰는 우회 요청과, 다른 AI의 답을 붙여 넣는 경우를 자동으로 보내 보고 AI가 설정대로 답하는지 확인해요.</p>
        {simulate.isPending && <p className="note">보내 보는 중…</p>}
        {simulate.data && <SimulationList cases={simulate.data} questions={draft.questions} custom={p.prompt_mode === 'CUSTOM'} />}
      </section>
      <div style={{ marginTop: 16 }}>
        {deploy.data ? (
          <div className="deploy">
            <div className="spread">
              <div>
                <span className="label">학생 입장 코드</span>
                <div className="invite">{deploy.data.invite_code}</div>
              </div>
              <span className="chip good">배포됨</span>
            </div>
            <p>학생에게 수업 코드를 공유하면 바로 과제를 시작할 수 있어요. 학생은 가입 없이 수업 코드와 학번으로 입장해요.</p>
            <div className="row">
              <Link className="btn primary" to={base}>클래스로 돌아가기</Link>
              <Link className="btn" to={`${base}/dashboard?assignment=${deploy.data.saved.seq}`}>반 리포트 보기</Link>
            </div>
          </div>
        ) : (
          <div className="spread">
            <button className="btn" onClick={onPrev}>이전</button>
            <button className="btn primary" disabled={deploy.isPending} onClick={() => deploy.mutate()}>학생에게 배포하기</button>
          </div>
        )}
        {deploy.error && <p className="error-text">{deploy.error.message}</p>}
      </div>
    </>
  )
}
