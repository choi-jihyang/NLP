import { useEffect, useRef, useState, type RefObject } from 'react'

/** 화면에 처음 보일 때 `.reveal` · `.hstep` 요소에 `.in`을 붙인다(메인 스크롤 등장 효과) */
export function useReveal(): void {
  useEffect(() => {
    const io = new IntersectionObserver(
      (entries) =>
        entries.forEach((e) => {
          if (!e.isIntersecting) return
          e.target.classList.add('in')
          io.unobserve(e.target)
        }),
      { threshold: 0.15 },
    )
    const watch = () => document.querySelectorAll('.reveal:not(.in), .hstep:not(.in)').forEach((el) => io.observe(el))
    watch()
    // 요금제 카드처럼 서버 응답 뒤에 생기는 요소도 지켜본다(새로고침하면 카드가 투명하게 남던 문제)
    const mo = new MutationObserver(watch)
    mo.observe(document.body, { childList: true, subtree: true })
    return () => {
      io.disconnect()
      mo.disconnect()
    }
  }, [])
}

/** 이 요소가 한 번이라도 보였는지 */
export function useSeen<T extends Element>(): [RefObject<T | null>, boolean] {
  const ref = useRef<T | null>(null)
  const [seen, setSeen] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const io = new IntersectionObserver(([e]) => e.isIntersecting && setSeen(true), { threshold: 0.4 })
    io.observe(el)
    return () => io.disconnect()
  }, [])
  return [ref, seen]
}
