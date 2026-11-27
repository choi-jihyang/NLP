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
    document.querySelectorAll('.reveal, .hstep').forEach((el) => io.observe(el))
    return () => io.disconnect()
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
