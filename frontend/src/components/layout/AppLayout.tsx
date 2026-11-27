import { useQuery } from '@tanstack/react-query'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import { logout } from '../../api/auth'
import { listMyClasses } from '../../api/classes'
import { session, type Role } from '../../api/client'
import { Logo } from './Logo'
import { ThemeToggle } from './ThemeToggle'

type Props = { role: Role }

const right = ({ isActive }: { isActive: boolean }) => `btn text${isActive ? ' on' : ''}`

/** 공통 헤더: 로고 · 메뉴 · (교수자) 요금제 · 마이페이지 · 로그아웃 / (학생) 마이페이지 · 나가기 · 테마 */
export function AppLayout({ role }: Props) {
  const navigate = useNavigate()
  const teacher = role === 'TEACHER'
  const mine = useQuery({ queryKey: ['my-classes'], queryFn: listMyClasses, enabled: !teacher && !!session.token() })
  const name = teacher ? (session.user()?.name ?? '교수자') : (mine.data?.[0]?.student_no ?? null)
  const leave = () => {
    logout()
    navigate('/')
  }

  return (
    <>
      <header className="nav">
        <div className="wrap nav-in">
          <Logo to={teacher ? '/teacher/classes' : '/student/classes'} />
          <nav className="menu">
            {teacher ? (
              <NavLink to="/teacher/classes" end>내 클래스</NavLink>
            ) : (
              <>
                <NavLink to="/student/classes" end>내 과제</NavLink>
                <NavLink to="/student/join" end>클래스 참여</NavLink>
              </>
            )}
          </nav>
          <div className="nav-right">
            {name && (
              <span className="who">
                <span className="avatar">{teacher ? name.slice(0, 1) : name.slice(-2)}</span>
                <span className={teacher ? undefined : 'mono'}>{name}</span>
              </span>
            )}
            {teacher && <NavLink className={right} to="/teacher/plans">요금제</NavLink>}
            <NavLink className={right} to={teacher ? '/teacher/mypage' : '/student/mypage'}>마이페이지</NavLink>
            <button type="button" className="btn ghost sm" onClick={leave}>{teacher ? '로그아웃' : '나가기'}</button>
            <ThemeToggle />
          </div>
        </div>
      </header>
      <Outlet />
    </>
  )
}
