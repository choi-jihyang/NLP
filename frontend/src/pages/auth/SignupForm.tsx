import { useMutation } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'

import { signup } from '../../api/auth'

type Props = { onDone: () => void }

/** 교수자 계정 만들기 폼. 학생은 가입 없이 수업 코드로 입장한다 */
export default function SignupForm({ onDone }: Props) {
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' })
  const mutation = useMutation({ mutationFn: signup, onSuccess: onDone })
  const mismatch = form.confirm.length > 0 && form.password !== form.confirm
  const set = (key: keyof typeof form) => (value: string) => setForm((f) => ({ ...f, [key]: value }))

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (mismatch) return
    mutation.mutate({ name: form.name, email: form.email, password: form.password })
  }

  return (
    <form className="stack" onSubmit={handleSubmit}>
      <h2>교수자 계정 만들기</h2>
      <label className="field">
        <span className="label">이름</span>
        <input autoComplete="name" value={form.name} onChange={(e) => set('name')(e.target.value)} />
      </label>
      <label className="field">
        <span className="label">이메일</span>
        <input type="email" autoComplete="email" value={form.email} onChange={(e) => set('email')(e.target.value)} />
      </label>
      <label className="field">
        <span className="label">비밀번호 · 8자 이상</span>
        <input type="password" autoComplete="new-password" value={form.password} onChange={(e) => set('password')(e.target.value)} />
      </label>
      <label className="field">
        <span className="label">비밀번호 확인</span>
        <input type="password" autoComplete="new-password" value={form.confirm} onChange={(e) => set('confirm')(e.target.value)} />
      </label>
      {mismatch && <p className="error-text">비밀번호가 서로 달라요.</p>}
      {mutation.error && <p className="error-text">{mutation.error.message}</p>}
      <button className="btn primary lg" disabled={mutation.isPending || mismatch}>
        {mutation.isPending ? '만드는 중…' : '계정 만들기'}
      </button>
    </form>
  )
}
