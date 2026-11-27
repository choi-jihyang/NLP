const DAYS = ['일', '월', '화', '수', '목', '금', '토']

/** "11월 20일(금) 23:59" 형식. 마감이 없으면 "미정" */
export function formatDue(iso: string | null): string {
  if (!iso) return '미정'
  const d = new Date(iso)
  const time = d.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'Asia/Seoul' })
  const [month, day, weekday] = [
    Number(d.toLocaleString('en-US', { month: 'numeric', timeZone: 'Asia/Seoul' })),
    Number(d.toLocaleString('en-US', { day: 'numeric', timeZone: 'Asia/Seoul' })),
    DAYS[new Date(d.toLocaleString('en-US', { timeZone: 'Asia/Seoul' })).getDay()],
  ]
  return `${month}월 ${day}일(${weekday}) ${time}`
}

/** 소수점이 있으면 한 자리까지 */
export const formatScore = (n: number) => (Number.isInteger(n) ? String(n) : n.toFixed(1))

/** "2027년 3월 1일" 형식. 이용 기간처럼 해가 바뀔 수 있는 날짜에 쓴다 */
export const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric', timeZone: 'Asia/Seoul' })

/** "2026.11.26" 형식(한국 시간) */
export const formatDot = (iso: string) => {
  const d = new Date(new Date(iso).getTime() + 9 * 3600_000).toISOString().slice(0, 10)
  return d.replaceAll('-', '.')
}

/** 지금부터 그 시각까지 남은 날 수(올림). 지났으면 음수 */
export const daysUntil = (iso: string) => Math.ceil((new Date(iso).getTime() - Date.now()) / 86_400_000)

/** 클래스 이용 상태: 시작 전 · 진행 중 · 만료 */
export function periodState(startsAt: string, expiresAt: string): { label: string; tone: '' | 'good' | 'bad' } {
  const now = Date.now()
  if (now < new Date(startsAt).getTime()) return { label: '시작 전', tone: '' }
  if (now >= new Date(expiresAt).getTime()) return { label: '만료', tone: 'bad' }
  return { label: '진행 중', tone: 'good' }
}

/** ISO → datetime-local 값 "YYYY-MM-DDTHH:mm"(한국 시간) */
export const toKstLocalInput = (iso: string | null): string =>
  iso ? new Date(new Date(iso).getTime() + 9 * 3600_000).toISOString().slice(0, 16) : ''

/** datetime-local 값(한국 시간으로 본다) → "YYYY-MM-DDTHH:mm:00+09:00". 빈 값이면 null */
export const fromKstLocalInput = (v: string): string | null => (v ? `${v}:00+09:00` : null)
