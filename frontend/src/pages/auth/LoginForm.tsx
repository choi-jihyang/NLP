import { useMutation } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'

import { login } from '../../api/auth'

type Props = { onDone: () => void }

/** 교수자 로그인 폼 */
export default function LoginForm({ onDone }: Props) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const mutation = useMutation({ mutationFn: login, onSuccess: onDone })

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    mutation.mutate({ email, password })
  }

  return (
    <form className="stack" onSubmit={handleSubmit}>
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
      <button className="btn primary lg" disabled={mutation.isPending || !email || !password}>
        {mutation.isPending ? '로그인 중…' : '로그인'}
      </button>
    </form>
  )
}
