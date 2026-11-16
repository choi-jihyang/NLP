import type { AnswerState, StudentQuestion } from '../../../api/submissions'

/** 채팅을 막아야 하는 이유. 없으면 null. 문항을 제출해도 최종 제출 전까지는 AI 도움이 열려 있다 */
export function chatLock(q: StudentQuestion, answer: AnswerState | undefined, finalized: boolean) {
  if (finalized) return { title: '최종 제출한 과제예요', note: '최종 제출한 뒤에는 AI 도움이 닫혀요.' }
  if (!q.ai_enabled) return { title: '이 문항은 AI 도움 없이 풀어요', note: '교수자가 이 문항의 AI 도움을 꺼 두었어요.' }
  if (answer?.status === 'AWAITING_CHECK')
    return { title: '개념 확인 질문에 먼저 답해 주세요', note: '답하는 동안에는 AI 도움을 쓸 수 없어요.' }
  return null
}
