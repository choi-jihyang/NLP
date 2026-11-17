/** 클래스·참여·로그인 예시 저장소. 백엔드 API가 생기면 지운다 */
import type { AiPolicy } from '../assignments'
import type { LoginResult, SignupRequest } from '../auth'
import type { ClassCreate, ClassInfo, MyAssignment, MyClass } from '../classes'
import { respondWith } from './delay'
import { progress } from './progress'
import { DEFAULT_POLICY } from './sampleQuestions'

export const CLASSES: ClassInfo[] = [
  { id: 'c1', name: '프로그래밍 기초 1분반', invite_code: 'TG-4821', student_count: 32, student_limit: 50, plan: 'SMALL', expires_at: '2027-03-01T00:00:00+09:00' },
]

const PLAN_LIMIT = { SMALL: 50, MEDIUM: 100, LARGE: 200 } as const
const aiDefaults: Record<string, AiPolicy> = {}
/** 새 과제 초안에 채울 정책 */
export const defaultPolicyOf = (classId: string): AiPolicy => ({ ...(aiDefaults[classId] ?? DEFAULT_POLICY) })
const newCode = () => `TG-${String(1000 + Math.floor(Math.random() * 9000))}`
const yearLater = () => new Date(Date.now() + 365 * 24 * 3600 * 1000).toISOString()

const SAMPLE_MINE = (): MyAssignment[] => [
  { id: 'a1', title: '3주차 과제 · 반복문과 리스트', language: 'Python', status: statusOf('a1'), due_at: '2026-11-20T23:59:00+09:00', hint_mode: 'EARNED', hint_mode_label: '시도한 만큼 열기', submitted: progress.submitted.a1, total: 5, score_text: progress.released.has('a1') ? '50 / 80 · 간단 제작 채점 대기' : null },
  { id: 'a2', title: '2주차 퀴즈 · 조건문', language: 'Python', status: statusOf('a2'), due_at: '2026-11-13T23:59:00+09:00', hint_mode: 'CONCEPT', hint_mode_label: '개념만', submitted: 5, total: 5, score_text: '45 / 50 · 보완 필요 개념 1개' },
]

function statusOf(id: string): MyAssignment['status'] {
  return !progress.finalized.has(id) ? 'IN_PROGRESS' : progress.released.has(id) ? 'RELEASED' : 'FINALIZED'
}


export const mockClasses = {
  list: () => respondWith(CLASSES),
  get: (id: string) => {
    const found = CLASSES.find((c) => c.id === id)
    return found ? respondWith(found) : Promise.reject(new Error('클래스를 찾을 수 없어요'))
  },
  create: (body: ClassCreate) => {
    if (!body.name.trim()) return Promise.reject(new Error('클래스 이름을 입력해 주세요.'))
    const created: ClassInfo = {
      id: `c${CLASSES.length + 1}`, name: body.name.trim(), invite_code: newCode(), student_count: 0,
      student_limit: PLAN_LIMIT[body.plan], plan: body.plan, expires_at: yearLater(),
    }
    CLASSES.push(created)
    return respondWith(created, 300)
  },
  aiDefaults: (classId: string) => respondWith(defaultPolicyOf(classId)),
  saveAiDefaults: (classId: string, policy: AiPolicy) => {
    aiDefaults[classId] = { ...policy, prompt_mode: 'FORM', custom_prompt: null }
    return respondWith(defaultPolicyOf(classId), 200)
  },
  /** 학생: 참여했거나 요청 중인 클래스. 요청 중이면 과제는 비어 있다 */
  mine: () =>
    respondWith<MyClass[]>(
      CLASSES.filter((c) => ['APPROVED', 'PENDING'].includes(progress.enrollment[c.id])).map((c) => ({
        class_id: c.id,
        class_name: c.name,
        alias: progress.alias,
        enrollment_status: progress.enrollment[c.id] === 'APPROVED' ? 'APPROVED' : 'PENDING',
        assignments: c.id === 'c1' && progress.enrollment[c.id] === 'APPROVED' ? SAMPLE_MINE() : [],
      })),
    ),
  signup: (body: SignupRequest) => {
    if (!body.name.trim()) return Promise.reject(new Error('이름을 입력해 주세요.'))
    if (!body.email.includes('@')) return Promise.reject(new Error('이메일 형식을 확인해 주세요.'))
    if (body.password.length < 8) return Promise.reject(new Error('비밀번호는 8자 이상이어야 해요.'))
    return respondWith<LoginResult>({ access_token: 'mock-token', user: { id: 't2', name: body.name.trim(), email: body.email, role: 'TEACHER' } }, 300)
  },
  login: (body: { email: string; password: string }) => {
    if (!body.email.includes('@') || body.password.length < 4) return Promise.reject(new Error('이메일 또는 비밀번호를 확인해 주세요.'))
    return respondWith<LoginResult>({ access_token: 'mock-token', user: { id: 't1', name: '김교수', email: body.email, role: 'TEACHER' } }, 300)
  },
}
