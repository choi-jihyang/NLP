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
