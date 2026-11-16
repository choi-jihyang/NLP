import { useState } from 'react'

import type { JoinMode, RosterSettings } from '../../../api/enrollments'

type Props = { settings: RosterSettings; saving: boolean; onSave: (body: RosterSettings) => void }

/** 입장 방식 + 수업 전에 미리 넣어 두는 학생 명단 (한 줄에 수업용 ID 하나) */
export default function RosterEditor({ settings, saving, onSave }: Props) {
  const [mode, setMode] = useState<JoinMode>(settings.join_mode)
  const [text, setText] = useState(settings.roster.join('\n'))
  const roster = text.split(/[\n,]/).map((s) => s.trim()).filter(Boolean)
  const changed = mode !== settings.join_mode || roster.join('\n') !== settings.roster.join('\n')

  return (
    <section className="panel stack">
      <h3>입장 방식 · 학생 명단</h3>
      <div className="seg" role="group" aria-label="입장 방식">
        <button aria-pressed={mode === 'APPROVAL'} onClick={() => setMode('APPROVAL')}>명단 확인 후 입장</button>
        <button aria-pressed={mode === 'OPEN'} onClick={() => setMode('OPEN')}>코드만 있으면 바로 입장</button>
      </div>
      <p className="note">
        {mode === 'APPROVAL'
          ? '명단에 있는 ID는 바로 들어오고, 명단에 없는 ID는 참여 요청으로 와요. 요청은 위에서 수락하거나 거절해요.'
          : '수업 코드를 아는 학생은 누구나 바로 들어와요. 명단은 참고용으로만 남아요.'}
      </p>
      <label className="field">
        <span className="label">미리 넣어 둘 수업용 ID · 한 줄에 하나 (쉼표로 구분해도 돼요)</span>
        <textarea
          className="inp mono"
          style={{ minHeight: 140 }}
          placeholder={'예:\n20231234\n20235678\n학생 31'}
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
      </label>
      <div className="row">
        <button className="btn primary" disabled={!changed || saving} onClick={() => onSave({ join_mode: mode, roster })}>
          저장
        </button>
        <span className="note">명단 {roster.length}명 · 이미 요청한 학생이 명단에 있으면 저장할 때 바로 받아 줘요.</span>
      </div>
      <p className="note">학번처럼 학생을 알아볼 수 있는 ID를 쓸지, 익명 ID를 쓸지는 팀에서 정해야 해요.</p>
    </section>
  )
}
