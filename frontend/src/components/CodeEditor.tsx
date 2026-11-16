import type { ClipboardEvent, KeyboardEvent } from 'react'

type Props = {
  id: string
  value: string
  onChange: (value: string) => void
  disabled?: boolean
  label?: string
  minHeight?: number
  onPaste?: (length: number) => void
}

/** 코드 입력창. Tab 키는 들여쓰기(공백 4칸)로 쓴다 */
export function CodeEditor({ id, value, onChange, disabled, label, minHeight, onPaste }: Props) {
  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key !== 'Tab') return
    e.preventDefault()
    const el = e.currentTarget
    const { selectionStart: start, selectionEnd: end } = el
    onChange(value.slice(0, start) + '    ' + value.slice(end))
    requestAnimationFrame(() => el.setSelectionRange(start + 4, start + 4))
  }
  const handlePaste = (e: ClipboardEvent<HTMLTextAreaElement>) => onPaste?.(e.clipboardData.getData('text').length)

  return (
    <textarea
      id={id}
      className="inp code"
      aria-label={label ?? '코드 입력'}
      spellCheck={false}
      value={value}
      disabled={disabled}
      style={minHeight ? { minHeight } : undefined}
      onChange={(e) => onChange(e.target.value)}
      onKeyDown={handleKey}
      onPaste={handlePaste}
    />
  )
}
