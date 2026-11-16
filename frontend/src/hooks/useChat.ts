import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { getChat, sendChat, type ChatState, type HelpChoice } from '../api/chat'

/** 문항별 학습 AI 대화 */
export function useChat(assignmentId: string, questionId: string) {
  const client = useQueryClient()
  const key = ['chat', assignmentId, questionId]
  const query = useQuery({ queryKey: key, queryFn: () => getChat(assignmentId, questionId) })
  const send = useMutation({
    mutationFn: (body: { message: string; choice?: HelpChoice; pasted?: boolean }) =>
      sendChat({ assignment_id: assignmentId, question_id: questionId, ...body }),
    onSuccess: (data: ChatState) => {
      client.setQueryData(key, data)
      // 힌트 단계가 바뀌면 문항 쪽(혼자 푼 문항 여부)도 다시 읽는다
      void client.invalidateQueries({ queryKey: ['submission', assignmentId] })
    },
  })
  return { chat: query.data, query, send }
}
