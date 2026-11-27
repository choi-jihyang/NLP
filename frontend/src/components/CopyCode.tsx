import { useState, type MouseEvent } from 'react'

type Props = { code: string }

/** 수업 코드 + 복사 버튼. 카드 링크 안에 있어도 링크로 번지지 않는다 */
export function CopyCode({ code }: Props) {
  const [copied, setCopied] = useState(false)
  const copy = (e: MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    void navigator.clipboard?.writeText(code).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }
  return (
    <span className="code">
      {code}
      <button type="button" onClick={copy}>{copied ? '복사됨 ✓' : '복사'}</button>
    </span>
  )
}
