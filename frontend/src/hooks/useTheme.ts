import { useCallback, useState } from 'react'

export type Theme = 'light' | 'dark'

/** index.html의 첫 그림 전 스크립트와 같은 키 */
const KEY = 'tg-theme'
const current = (): Theme => (document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light')

/** 라이트 · 다크 전환. 고른 값은 이 브라우저에 기억한다 */
export function useTheme(): { theme: Theme; toggle: () => void } {
  const [theme, setTheme] = useState<Theme>(current)
  const toggle = useCallback(() => {
    const next: Theme = current() === 'dark' ? 'light' : 'dark'
    document.documentElement.setAttribute('data-theme', next)
    try {
      localStorage.setItem(KEY, next)
    } catch {
      // 저장하지 못해도 이번 화면은 바뀐다
    }
    setTheme(next)
  }, [])
  return { theme, toggle }
}
