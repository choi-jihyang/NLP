import { useQueries, useQuery } from '@tanstack/react-query'

import { listAssignments, type AssignmentSummary } from '../api/assignments'
import { listClasses, type ClassInfo } from '../api/classes'
import { listJoinRequests, type PendingRequest } from '../api/enrollments'
import { getGradingList } from '../api/reports'
import { daysUntil } from '../components/format'

export type TodoItem = { kind: 'GRADING' | 'JOIN' | 'DUE'; title: string; meta: string; to: string }
export type ClassOverview = { info: ClassInfo; assignments: AssignmentSummary[]; requests: PendingRequest[]; grading: number }

/** 교수자 대시보드: 내 클래스마다 과제 · 참여 요청 · 채점 대기를 모아 숫자와 할 일을 만든다(새 API 없이) */
export function useTeacherOverview() {
  const classes = useQuery({ queryKey: ['classes'], queryFn: listClasses })
  const list = classes.data ?? []
  const assignments = useQueries({
    queries: list.map((c) => ({ queryKey: ['assignments', c.seq], queryFn: () => listAssignments(c.seq) })),
  })
  const requests = useQueries({
    queries: list.map((c) => ({ queryKey: ['join-requests', c.seq], queryFn: () => listJoinRequests(c.seq) })),
  })
  const published = assignments.flatMap((q) => (q.data ?? []).filter((a) => a.status !== 'DRAFT'))
  const grading = useQueries({
    queries: published.map((a) => ({ queryKey: ['grading', a.seq], queryFn: () => getGradingList(a.seq) })),
  })
  const pendingBy = new Map(published.map((a, i) => [a.seq, (grading[i]?.data ?? []).filter((g) => g.score === null).length]))

  const overview: ClassOverview[] = list.map((info, i) => {
    const items = assignments[i]?.data ?? []
    return { info, assignments: items, requests: requests[i]?.data ?? [], grading: items.reduce((n, a) => n + (pendingBy.get(a.seq) ?? 0), 0) }
  })

  const todos: TodoItem[] = []
  for (const { info, assignments: items, requests: reqs } of overview) {
    const base = `/teacher/classes/${info.seq}`
    for (const a of items) {
      const n = pendingBy.get(a.seq) ?? 0
      if (n > 0) todos.push({ kind: 'GRADING', title: `간단 제작 채점 ${n}건`, meta: `${info.name} · ${a.title}`, to: `${base}/assignments/${a.seq}/grading` })
    }
    if (reqs.length > 0) {
      const who = reqs.map((r) => r.student_no + (r.is_reentry ? '(다시 입장)' : '')).join(', ')
      todos.push({ kind: 'JOIN', title: `참여 요청 ${reqs.length}건`, meta: `${info.name} · ${who}`, to: `${base}/students` })
    }
    for (const a of items) {
      const left = a.due_at ? daysUntil(a.due_at) : null
      if (a.status === 'OPEN' && left !== null && left >= 0 && left <= 7) {
        todos.push({ kind: 'DUE', title: `마감 ${left}일 전 · 제출 ${a.submitted_count} / ${a.student_count}명`, meta: `${info.name} · ${a.title}`, to: `${base}/dashboard?assignment=${a.seq}` })
      }
    }
  }

  const all = overview.flatMap((o) => o.assignments)
  return {
    isPending: classes.isPending,
    error: classes.error,
    classes: overview,
    stats: {
      classes: list.length,
      students: list.reduce((n, c) => n + c.student_count, 0),
      openAssignments: all.filter((a) => a.status === 'OPEN').length,
      grading: overview.reduce((n, o) => n + o.grading, 0),
    },
    todos,
  }
}
