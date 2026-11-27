import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { logout } from '../../api/auth'
import { listClasses } from '../../api/classes'
import { session } from '../../api/client'
import { listPaymentHistory } from '../../api/payments'
import { formatDot } from '../../components/format'
import { PageHead } from '../../components/PageHead'
import { SideNav } from '../../components/SideNav'

const SECTIONS = [
  { id: 'account', label: '계정 정보' },
  { id: 'password', label: '비밀번호 변경' },
  { id: 'usage', label: '이용 중인 클래스' },
  { id: 'payments', label: '결제 내역' },
]
const UI_ONLY = '아직 화면만 있어요 · 저장되지 않아요'

/** 교수자 마이페이지. 새 API 없이: 이름 · 이메일은 로그인 때 받은 값, 저장 · 비밀번호 · 연장은 화면만, 결제 내역은 예시 */
export default function TeacherMyPage() {
  const navigate = useNavigate()
  const user = session.user()
  const classes = useQuery({ queryKey: ['classes'], queryFn: listClasses })
  const payments = useQuery({ queryKey: ['payment-history'], queryFn: listPaymentHistory })
  const [notice, setNotice] = useState<string | null>(null)
  const uiOnly = (where: string) => setNotice(`${where}: ${UI_ONLY}`)
  const leave = () => {
    logout()
    navigate('/')
  }

  return (
    <>
      <PageHead eyebrow="My page" title="마이페이지" />
      <main className="wrap page side-layout">
        <SideNav items={SECTIONS} leaveLabel="로그아웃" onLeave={leave} />
        <div className="stack" style={{ gap: 40 }}>
          {notice && <div className="info" role="status">{notice}</div>}
          <section className="panel stack" id="account">
            <div className="profile">
              <span className="avatar">{user?.name.slice(0, 1) ?? '?'}</span>
              <div>
                <h2>{user?.name ?? '교수자'}</h2>
                <p className="note">교수자 계정</p>
              </div>
            </div>
            <div className="grid g2">
              <label className="field"><span className="label">이름</span><input defaultValue={user?.name ?? ''} /></label>
              <label className="field"><span className="label">이메일 · 로그인 아이디</span><input className="inp" value={user?.email ?? ''} readOnly /></label>
            </div>
            <div className="row" style={{ justifyContent: 'flex-end' }}>
              <button type="button" className="btn primary sm" onClick={() => uiOnly('이름 저장')}>저장</button>
            </div>
          </section>

          <section className="panel stack" id="password">
            <h2>비밀번호 변경</h2>
            <div className="grid g3">
              <label className="field"><span className="label">지금 비밀번호</span><input type="password" autoComplete="current-password" /></label>
              <label className="field"><span className="label">새 비밀번호 · 8자 이상</span><input type="password" autoComplete="new-password" /></label>
              <label className="field"><span className="label">새 비밀번호 확인</span><input type="password" autoComplete="new-password" /></label>
            </div>
            <div className="row" style={{ justifyContent: 'flex-end' }}>
              <button type="button" className="btn sm" onClick={() => uiOnly('비밀번호 변경')}>비밀번호 바꾸기</button>
            </div>
          </section>

          <section id="usage">
            <div className="sec-h"><h2>이용 중인 클래스</h2></div>
            <div className="panel card-tbl">
              <table>
                <thead><tr><th>클래스</th><th>요금제</th><th>학생</th><th>이용 기간</th><th /></tr></thead>
                <tbody>
                  {classes.data?.map((c) => (
                    <tr key={c.seq}>
                      <td><b>{c.name}</b></td>
                      <td><span className="chip">{c.plan}</span></td>
                      <td>{c.student_count} / {c.student_limit}명</td>
                      <td className="mono">{formatDot(c.starts_at)} – {formatDot(c.expires_at)}</td>
                      <td style={{ textAlign: 'right' }}>
                        <button type="button" className="btn sm" onClick={() => uiOnly(`${c.name} 1년 연장`)}>1년 연장</button>
                      </td>
                    </tr>
                  ))}
                  {classes.data?.length === 0 && <tr><td colSpan={5} className="note">아직 클래스가 없어요.</td></tr>}
                </tbody>
              </table>
            </div>
          </section>

          <section id="payments">
            <div className="sec-h"><h2>결제 내역</h2><span className="chip warn">예시 데이터 · 실제 결제 없음</span></div>
            <div className="panel card-tbl">
              <table>
                <thead><tr><th>날짜</th><th>내용</th><th>요금제</th><th style={{ textAlign: 'right' }}>금액</th></tr></thead>
                <tbody>
                  {payments.data?.map((p) => (
                    <tr key={p.date + p.title}>
                      <td className="mono">{p.date.replaceAll('-', '.')}</td>
                      <td>{p.title}</td>
                      <td>{p.plan} · {p.student_limit}명</td>
                      <td style={{ textAlign: 'right' }}>{p.amount.toLocaleString('ko-KR')}원</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </main>
    </>
  )
}
