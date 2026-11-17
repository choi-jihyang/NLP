import { useMutation } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { signup } from '../../api/auth'

/** 교수자 계정 만들기. 학생은 가입 없이 수업 코드로 입장한다 */
export default function SignupPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' })
  const mutation = useMutation({ mutationFn: signup, onSuccess: () => navigate('/teacher/plans?welcome=1') })
  const mismatch = form.confirm.length > 0 && form.password !== form.confirm
  const set = (key: keyof typeof form) => (value: string) => setForm((f) => ({ ...f, [key]: value }))

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (mismatch) return
    mutation.mutate({ name: form.name, email: form.email, password: form.password })
  }

  return (
    <form className="panel stack narrow" onSubmit={handleSubmit}>
      <h2>교수자 계정 만들기</h2>
      <p className="lead">계정을 만들면 요금제를 고르고 클래스를 개설할 수 있어요.</p>
      <label className="field">
        <span className="label">이름</span>
        <input className="inp" autoComplete="name" value={form.name} onChange={(e) => set('name')(e.target.value)} />
      </label>
      <label className="field">
        <span className="label">이메일</span>
        <input className="inp" type="email" autoComplete="email" value={form.email} onChange={(e) => set('email')(e.target.value)} />
      </label>
      <label className="field">
        <span className="label">비밀번호 · 8자 이상</span>
        <input className="inp" type="password" autoComplete="new-password" value={form.password} onChange={(e) => set('password')(e.target.value)} />
      </label>
      <label className="field">
        <span className="label">비밀번호 확인</span>
        <input className="inp" type="password" autoComplete="new-password" value={form.confirm} onChange={(e) => set('confirm')(e.target.value)} />
      </label>
      {mismatch && <p className="error-text">비밀번호가 서로 달라요.</p>}
      {mutation.error && <p className="error-text">{mutation.error.message}</p>}
      <button className="btn primary" disabled={mutation.isPending || mismatch}>
        {mutation.isPending ? '만드는 중…' : '계정 만들기'}
      </button>
      <div className="row">
        <span className="note">이미 계정이 있나요?</span>
        <Link className="btn sm" to="/login">로그인</Link>
      </div>
      <p className="note">학생은 가입하지 않아요. 교수자가 알려준 수업 코드로 바로 입장해요.</p>
    </form>
  )
}
