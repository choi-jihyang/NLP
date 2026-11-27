import { Link } from 'react-router-dom'

import { Logo } from '../../components/layout/Logo'
import { ThemeToggle } from '../../components/layout/ThemeToggle'

/** 로그인 전 헤더: 로고 · 요금제 · 로그인 · 수업 코드로 입장 · 테마 */
export function HomeNav() {
  return (
    <header className="nav">
      <div className="wrap nav-in">
        <Logo to="/" />
        <div className="nav-right">
          <a className="btn text" href="/#start">요금제</a>
          <Link className="btn text" to="/login">로그인</Link>
          <Link className="btn primary home-join" to="/student/join">수업 코드로 입장</Link>
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
