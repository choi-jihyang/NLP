import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { getChat, sendChat, type ChatState, type HelpChoice } from '../api/chat'

/** 문항별 학습 AI 대화 */
export function useChat(assignmentId: number, questionId: number | null) {
  const client = useQueryClient()
  const key = ['chat', assignmentId, questionId]
  const query = useQuery({ queryKey: key, queryFn: () => getChat(assignmentId, questionId ?? 0), enabled: questionId != null })
  const send = useMutation({
    // 붙여넣기는 입력 칸의 onPaste가 /paste-events로 따로 기록한다(I5) — 여기서는 보내지 않는다
    mutationFn: ({ message, choice }: { message: string; choice?: HelpChoice; pasted?: boolean }) =>
      sendChat({ assignment_id: assignmentId, question_id: questionId ?? 0, message, choice }),
    onSuccess: (data: ChatState) => {
      client.setQueryData(key, data)
      // 힌트 단계가 바뀌면 문항 쪽(혼자 푼 문항 여부)도 다시 읽는다
      void client.invalidateQueries({ queryKey: ['submission', assignmentId] })
    },
  })
  return { chat: query.data, query, send }
}
