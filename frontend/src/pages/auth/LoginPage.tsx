import { useMutation } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { login } from '../../api/auth'

/** 교수자 로그인. 학생은 계정 없이 수업 코드로 입장한다 */
export default function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('teacher@school.ac.kr')
  const [password, setPassword] = useState('password')
  const mutation = useMutation({ mutationFn: login, onSuccess: () => navigate('/teacher/classes') })

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    mutation.mutate({ email, password })
  }

  return (
    <main className="wrap">
      <form className="panel stack narrow" onSubmit={handleSubmit}>
        <h2>교수자 로그인</h2>
        <label className="field">
          <span className="label">이메일</span>
          <input type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label className="field">
          <span className="label">비밀번호</span>
          <input type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        {mutation.error && <p className="error-text">{mutation.error.message}</p>}
        <button className="btn primary" disabled={mutation.isPending}>
          {mutation.isPending ? '로그인 중…' : '로그인'}
        </button>
        <hr className="sep" />
        <div className="spread">
          <span className="note">처음이신가요?</span>
          <Link className="btn sm" to="/signup">교수자 계정 만들기</Link>
        </div>
        <p className="note">학생은 계정 없이 수업 코드로 입장해요.</p>
      </form>
    </main>
  )
}
