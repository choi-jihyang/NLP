import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

type Props = {
  eyebrow?: string
  title: ReactNode
  sub?: ReactNode
  back?: { to: string; label: string }
  actions?: ReactNode
  /** 머리 아래쪽(탭 등) */
  children?: ReactNode
}

/** 그래프 용지 배경의 화면 머리: 작은 라벨 · 제목 · 한 줄 설명 · 주요 버튼 */
export function PageHead({ eyebrow, title, sub, back, actions, children }: Props) {
  return (
    <section className="head">
      <div className="wrap">
        {back && <Link className="back" to={back.to}>← {back.label}</Link>}
        <div className="head-row" style={back ? { marginTop: 8 } : undefined}>
          <div>
            {eyebrow && <p className="eyebrow">{eyebrow}</p>}
            <h1>{title}</h1>
            {sub && <p className="sub">{sub}</p>}
          </div>
          {actions && <div className="row">{actions}</div>}
        </div>
        {children}
      </div>
    </section>
  )
}
