import { Link, NavLink, Outlet } from 'react-router-dom'

export type NavItem = { to: string; label: string }

type Props = {
  subtitle: string
  nav: NavItem[]
}

/** 공통 헤더(그래프 용지 띠 + 탭) + 본문. 교수자·학생 화면이 함께 쓴다. */
export function AppLayout({ subtitle, nav }: Props) {
  return (
    <>
      <header className="top">
        <div className="wrap top-in">
          <Link to="/" className="brand">
            <h1>ThinkGuard</h1>
            <span>{subtitle}</span>
          </Link>
          <span className="chip warn" title="백엔드 API가 생기면 api/ 함수만 실제 호출로 바뀌어요">예시 데이터로 보는 중</span>
          <nav className="tabs">
            {nav.map((n) => (
              <NavLink key={n.to} to={n.to} end className={({ isActive }) => `tab${isActive ? ' active' : ''}`}>
                {n.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="wrap">
        <Outlet />
      </main>
    </>
  )
}
