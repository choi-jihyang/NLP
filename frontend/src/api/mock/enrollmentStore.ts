/** 참여 · 명단 · 참여 요청 · 내보내기 예시 저장소. 백엔드 API가 생기면 지운다 */
import type { ClassStudent } from '../classes'
import type { JoinMode, JoinRequest, JoinResult, PendingRequest, RosterSettings } from '../enrollments'
import { CLASSES } from './classStore'
import { respondWith } from './delay'
import { progress } from './progress'

type ClassMembers = { students: ClassStudent[]; requests: PendingRequest[]; removed: Set<string>; roster: string[]; mode: JoinMode }

const hoursAgo = (h: number) => new Date(Date.now() - h * 3600 * 1000).toISOString()

const members: Record<string, ClassMembers> = {
  c1: {
    students: ['03', '05', '07', '09', '11', '13', '15', '20', '22', '24', '26', '27'].map((n) => ({ id: `s${n}`, alias: `학생 ${n}` })),
    requests: [
      { id: 'r1', alias: '학생 31', requested_at: hoursAgo(5) },
      { id: 'r2', alias: '김민수', requested_at: hoursAgo(1) },
    ],
    removed: new Set(),
    roster: [],
    mode: 'APPROVAL',
  },
}
let seq = 100

const of = (classId: string): ClassMembers =>
  (members[classId] ??= { students: [], requests: [], removed: new Set(), roster: [], mode: 'APPROVAL' })
const classOf = (classId: string) => {
  const cls = CLASSES.find((c) => c.id === classId)
  if (!cls) throw new Error('클래스를 찾을 수 없어요')
  return cls
}
const norm = (alias: string) => alias.trim().replace(/\s+/g, ' ')

function admit(classId: string, alias: string): ClassStudent {
  const cls = classOf(classId)
  if (cls.student_count >= cls.student_limit) throw new Error('정원이 가득 찼어요. 요금제를 올리거나 다른 학생을 내보낸 뒤 다시 시도해 주세요.')
  const student = { id: `s${seq++}`, alias }
  of(classId).students.push(student)
  cls.student_count += 1
  return student
}

const fail = (e: unknown) => Promise.reject(e instanceof Error ? e : new Error(String(e)))

export const mockEnrollments = {
  students: (classId: string) => respondWith(of(classId).students),
  join: (body: JoinRequest) => {
    const cls = CLASSES.find((c) => c.invite_code === body.invite_code.trim().toUpperCase())
    if (!cls) return fail('없는 수업 코드예요. 교수자가 알려준 코드를 다시 확인해 주세요.')
    if (new Date(cls.expires_at).getTime() < Date.now()) return fail('이용 기간이 끝난 수업이에요.')
    const alias = norm(body.alias)
    if (!alias) return fail('수업용 ID를 입력해 주세요.')
    const m = of(cls.id)
    if (m.removed.has(alias)) return fail('이 수업에서 내보내진 ID예요. 담당 교수자에게 문의해 주세요.')
    progress.alias = alias
    const done = (status: JoinResult['status']) => {
      progress.enrollment[cls.id] = status
      return respondWith<JoinResult>({ class_id: cls.id, class_name: cls.name, status }, 300)
    }
    if (m.students.some((s) => s.alias === alias)) return done('APPROVED')
    if (m.mode === 'OPEN' || m.roster.includes(alias)) {
      try {
        admit(cls.id, alias)
      } catch (e) {
        return fail(e)
      }
      return done('APPROVED')
    }
    if (!m.requests.some((r) => r.alias === alias)) m.requests.push({ id: `r${seq++}`, alias, requested_at: new Date().toISOString() })
    return done('PENDING')
  },
  mine: (classId: string) => respondWith({ status: progress.enrollment[classId] ?? 'REJECTED' }),
  consent: (_classId: string) => respondWith({ ok: true }),
  requests: (classId: string) => respondWith(of(classId).requests),
  decide: (classId: string, requestId: string, approve: boolean) => {
    const m = of(classId)
    const req = m.requests.find((r) => r.id === requestId)
    if (!req) return fail('이미 처리한 요청이에요.')
    if (approve) {
      try {
        admit(classId, req.alias)
      } catch (e) {
        return fail(e)
      }
    }
    m.requests = m.requests.filter((r) => r.id !== requestId)
    if (req.alias === progress.alias) progress.enrollment[classId] = approve ? 'APPROVED' : 'REJECTED'
    return respondWith({ ok: true }, 200)
  },
  remove: (classId: string, studentId: string) => {
    const m = of(classId)
    const student = m.students.find((s) => s.id === studentId)
    if (!student) return fail('학생을 찾을 수 없어요.')
    m.students = m.students.filter((s) => s.id !== studentId)
    m.removed.add(student.alias)
    classOf(classId).student_count -= 1
    if (student.alias === progress.alias) progress.enrollment[classId] = 'REMOVED'
    return respondWith({ ok: true }, 200)
  },
  roster: (classId: string) => respondWith<RosterSettings>({ join_mode: of(classId).mode, roster: of(classId).roster }),
  saveRoster: (classId: string, body: RosterSettings) => {
    const m = of(classId)
    m.mode = body.join_mode
    m.roster = [...new Set(body.roster.map(norm).filter(Boolean))]
    // 명단에 있는 학생이 이미 요청해 두었다면 바로 받아 준다
    for (const r of m.requests.filter((x) => m.roster.includes(x.alias))) {
      try {
        admit(classId, r.alias)
        m.requests = m.requests.filter((x) => x.id !== r.id)
        if (r.alias === progress.alias) progress.enrollment[classId] = 'APPROVED'
      } catch {
        break
      }
    }
    return respondWith<RosterSettings>({ join_mode: m.mode, roster: m.roster }, 200)
  },
}
