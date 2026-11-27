import { useEffect, useState } from 'react'

type Props = { items: { id: string; label: string }[]; leaveLabel: string; onLeave: () => void }

/** 마이페이지 옆 메뉴: 섹션으로 이동하고, 지금 보고 있는 섹션을 표시한다 */
export function SideNav({ items, leaveLabel, onLeave }: Props) {
  const [active, setActive] = useState(items[0]?.id ?? '')
  useEffect(() => {
    const spy = () => {
      let current = items[0]?.id ?? ''
      for (const { id } of items) {
        const el = document.getElementById(id)
        if (el && el.getBoundingClientRect().top <= 120) current = id
      }
      if (innerHeight + scrollY >= document.documentElement.scrollHeight - 2) current = items[items.length - 1]?.id ?? current
      setActive(current)
    }
    addEventListener('scroll', spy, { passive: true })
    spy()
    return () => removeEventListener('scroll', spy)
  }, [items])
  return (
    <nav className="side">
      {items.map((i) => (
        <a key={i.id} href={`#${i.id}`} className={active === i.id ? 'on' : undefined}>{i.label}</a>
      ))}
      <button type="button" className="danger" onClick={onLeave}>{leaveLabel}</button>
    </nav>
  )
}
