import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  answerConceptCheck,
  cancelConceptCheck,
  finalizeSubmission,
  getMySubmission,
  runPublicTests,
  submitAnswer,
  type ConceptReply,
  type Submission,
} from '../api/submissions'

type Target = { questionId: string; value: string }

/** 내 제출 상태와 제출·개념 확인·최종 제출 동작 */
export function useSubmission(assignmentId: string) {
  const client = useQueryClient()
  const key = ['submission', assignmentId]
  const query = useQuery({ queryKey: key, queryFn: () => getMySubmission(assignmentId) })
  const onSuccess = (data: Submission) => {
    client.setQueryData(key, data)
    void client.invalidateQueries({ queryKey: ['my-classes'] })
  }

  const submit = useMutation({ mutationFn: (t: Target) => submitAnswer(assignmentId, t.questionId, t.value), onSuccess })
  const conceptCheck = useMutation({
    mutationFn: (t: { questionId: string; body: ConceptReply }) => answerConceptCheck(assignmentId, t.questionId, t.body),
    onSuccess,
  })
  const cancelCheck = useMutation({ mutationFn: (questionId: string) => cancelConceptCheck(assignmentId, questionId), onSuccess })
  const finalize = useMutation({ mutationFn: () => finalizeSubmission(assignmentId), onSuccess })
  const run = useMutation({ mutationFn: (t: Target) => runPublicTests(assignmentId, t.questionId, t.value) })

  return { submission: query.data, query, submit, conceptCheck, cancelCheck, finalize, run }
}
