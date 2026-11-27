import type { ReactNode } from 'react'

export type Stat = { label: string; value: ReactNode; unit?: string; alert?: boolean }

type Props = { items: Stat[] }

/** 숫자 칸 4개 줄 (대시보드 · 클래스 상세) */
export function StatTiles({ items }: Props) {
  return (
    <div className="grid g4">
      {items.map((s) => (
        <div key={s.label} className={`tile${s.alert ? ' alert' : ''}`}>
          <p className="k">{s.label}</p>
          <p className="v">{s.value}{s.unit && <small> {s.unit}</small>}</p>
        </div>
      ))}
    </div>
  )
}
