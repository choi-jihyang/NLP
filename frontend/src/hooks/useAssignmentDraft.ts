import { useMutation, useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import {
  createBlankDraft,
  createDraftFromSample,
  extractFromFile,
  getAssignment,
  type Assignment,
  type Question,
} from '../api/assignments'

type LoadSource = { kind: 'SAMPLE' } | { kind: 'BLANK' } | { kind: 'FILE'; file: File }

/** 과제 만들기 화면의 편집 중인 과제. 서버에는 배포할 때 한 번에 저장한다 */
export function useAssignmentDraft(classId: number, assignmentId: number | undefined) {
  const initial = useQuery({
    queryKey: ['assignment-draft', classId, assignmentId ?? 'new'],
    queryFn: () => (assignmentId ? getAssignment(assignmentId) : createBlankDraft(classId)),
    staleTime: Infinity,
  })
  const [edited, setEdited] = useState<Assignment | null>(null)
  const [loaded, setLoaded] = useState(!!assignmentId)
  const draft = edited ?? initial.data ?? null

  const update = (patch: Partial<Assignment>) => draft && setEdited({ ...draft, ...patch })
  const updatePolicy = (patch: Partial<Assignment['policy']>) => draft && setEdited({ ...draft, policy: { ...draft.policy, ...patch } })
  const updateQuestion = (index: number, patch: Partial<Question>) =>
    draft && setEdited({ ...draft, questions: draft.questions.map((q, i) => (i === index ? { ...q, ...patch } : q)) })
  const setQuestions = (questions: Question[]) => draft && setEdited({ ...draft, questions })

  const load = useMutation({
    mutationFn: (src: LoadSource) =>
      src.kind === 'SAMPLE' ? createDraftFromSample(classId) : src.kind === 'BLANK' ? createBlankDraft(classId) : extractFromFile(classId, src.file),
    onSuccess: (found) => {
      // 교수자가 먼저 적어 둔 과목·대상·설명은 유지하고 문항만 채운다. 언어는 파일(테스트)에 맞춘다
      const keep = draft ?? found
      setEdited({
        ...found,
        seq: keep.seq,
        class_id: keep.class_id ?? found.class_id,
        course: keep.course || found.course,
        audience: keep.audience || found.audience,
        description: keep.description || found.description,
        title: keep.title && keep.title !== '새 과제' ? keep.title : found.title,
      })
      setLoaded(true)
    },
  })

  return { draft, query: initial, loaded, load, update, updatePolicy, updateQuestion, setQuestions }
}
