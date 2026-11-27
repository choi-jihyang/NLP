import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'

import { acceptConsent } from '../../api/enrollments'

type Props = { classId: number; className?: string; onDone: () => void }

/** 기록 안내 동의 카드. 무엇을 저장하고 누가 보는지 먼저 알린다(입장 화면 · 다시 입장 뒤 동의 화면이 함께 쓴다) */
export default function ConsentCard({ classId, className, onDone }: Props) {
  const [declined, setDeclined] = useState(false)
  const mutation = useMutation({ mutationFn: () => acceptConsent(classId), onSuccess: onDone })

  if (declined) {
    return (
      <section className="panel stack narrow" style={{ textAlign: 'center' }}>
        <h2>입장하지 않았어요</h2>
        <p className="muted">동의해야 이 수업의 AI 도움 과제를 풀 수 있어요. 다른 제출 방법은 담당 교수자에게 문의해 주세요.</p>
        <button className="btn" onClick={() => setDeclined(false)}>다시 보기</button>
      </section>
    )
  }

  return (
    <section className="panel stack mid" style={{ margin: '0 auto' }}>
      {className && <p className="eyebrow">{className}</p>}
      <h2>시작하기 전에 확인해 주세요</h2>
      <p>이 수업에서는 질문과 풀이 시도, AI의 답변, 개념 확인 결과를 학습 지원을 위해 저장합니다. 담당 교사는 이 기록을 확인할 수 있습니다.</p>
      <dl className="kv-list">
        <dt>저장하는 정보</dt>
        <dd>질문, 풀이 시도, AI 답변, 힌트 사용 이력, 이해 확인 답변</dd>
        <dt>볼 수 있는 사람</dt>
        <dd>본인과 담당 교수자. 반 전체 리포트의 답변 예시는 익명이에요.</dd>
        <dt>보관 기간</dt>
        <dd>학기 종료 후 삭제 (기간은 팀에서 확정)</dd>
        <dt>모델 학습</dt>
        <dd>수업 기록을 모델 학습에 쓰지 않아요.</dd>
        <dt>붙여넣기</dt>
        <dd>내용은 저장하지 않고 길이와 시점만 기록해요. 교수자에게 참고 신호로만 보이고 점수에는 쓰이지 않아요.</dd>
      </dl>
      {mutation.error && <p className="error-text">{mutation.error.message}</p>}
      <div className="row">
        <button className="btn primary" disabled={mutation.isPending} onClick={() => mutation.mutate()}>동의하고 시작</button>
        <button className="btn" onClick={() => setDeclined(true)}>동의하지 않음</button>
      </div>
      <p className="note">삭제·문의: 담당 교수자 또는 서비스 문의 창구</p>
    </section>
  )
}
