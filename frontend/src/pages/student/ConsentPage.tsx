import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { acceptConsent } from '../../api/enrollments'

/** 첫 접속 기록 동의. 무엇을 저장하고 누가 보는지 먼저 알린다 */
export default function ConsentPage() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [declined, setDeclined] = useState(false)
  const mutation = useMutation({
    mutationFn: () => acceptConsent(Number(params.get('class'))),
    onSuccess: () => navigate('/student/classes'),
  })

  return (
    <section className="panel stack mid" style={{ margin: '0 auto' }}>
      <h2>시작하기 전에 확인해 주세요</h2>
      <p>
        이 수업에서는 질문과 풀이 시도, AI의 답변, 개념 확인 결과를 학습 지원을 위해 저장합니다. 담당 교사는 이
        기록을 확인할 수 있습니다.
      </p>
      <dl className="kvlist">
        <dt>저장하는 정보</dt>
        <dd>질문, 풀이 시도, AI 답변, 힌트 사용 이력, 이해 확인 답변</dd>
        <dt>볼 수 있는 사람</dt>
        <dd>본인과 담당 교수자. 반 전체 리포트의 답변 예시는 익명이에요.</dd>
        <dt>보관 기간</dt>
        <dd>학기 종료 후 삭제 (기간은 팀에서 확정)</dd>
        <dt>모델 학습</dt>
        <dd>수업 기록을 모델 학습에 쓰지 않아요.</dd>
      </dl>
      <div className="fixed">
        <b>붙여넣기 참고 신호</b>
        <span className="note">
          답 칸이나 채팅에 붙여넣으면 내용은 저장하지 않고 길이와 시점만 기록해요. 교수자에게 참고 신호로만
          보이고, 판정이나 점수에는 쓰이지 않아요.
        </span>
      </div>
      {declined && (
        <div className="status wait" role="status">
          동의하지 않으면 이 수업의 AI 도움 과제를 이용할 수 없어요. 담당 교수자에게 다른 제출 방법을 문의해 주세요.
        </div>
      )}
      <div className="row">
        <button className="btn primary" disabled={mutation.isPending} onClick={() => mutation.mutate()}>
          동의하고 시작
        </button>
        <button className="btn" onClick={() => setDeclined(true)}>동의하지 않음</button>
      </div>
      <p className="note">삭제·문의: 담당 교수자 또는 서비스 문의 창구</p>
    </section>
  )
}
