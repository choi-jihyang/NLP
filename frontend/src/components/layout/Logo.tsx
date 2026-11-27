import { Link } from 'react-router-dom'

type Props = { to: string }

/** 방패(guard) 안에 커서 · 생각 점(think) */
export function Logo({ to }: Props) {
  return (
    <Link className="logo" to={to} aria-label="ThinkGuard 처음으로">
      <svg viewBox="0 0 32 32" fill="none" aria-hidden="true">
        <path d="M16 2.5 4.5 7v8.2c0 7 4.9 12.4 11.5 14.3 6.6-1.9 11.5-7.3 11.5-14.3V7L16 2.5Z" fill="var(--logo)" />
        <path d="M11 12.5 14.5 16 11 19.5" stroke="var(--surface)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
        <rect x="16.2" y="18.2" width="5.5" height="2.2" rx="1.1" fill="var(--surface)" />
        <circle cx="21.5" cy="10.5" r="2" fill="var(--syn-k)" />
      </svg>
      ThinkGuard
    </Link>
  )
}
