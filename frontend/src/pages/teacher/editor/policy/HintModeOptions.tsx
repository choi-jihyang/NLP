import type { HintMode } from '../../../../api/assignments'

type Props = { value: HintMode; onChange: (mode: HintMode) => void }

const MODES: { value: HintMode; title: string; desc: string }[] = [
  { value: 'NONE', title: '힌트 없음', desc: 'AI 도움 없이 푸는 시험형 과제예요.' },
  { value: 'CONCEPT', title: '개념만', desc: '관련 개념과 문법만 설명하고, 풀이 단계는 알려주지 않아요.' },
  { value: 'STEP', title: '한 단계씩', desc: '요청할 때마다 풀이를 한 단계씩만 보여주고, 다음 단계는 학생이 예측하게 해요.' },
  { value: 'EARNED', title: '시도한 만큼 열기', desc: '첫 힌트는 바로 주고, 다음 단계는 학생이 자기 코드를 보여줘야 열려요.' },
]

/** 힌트 공개 방식 4가지 */
export default function HintModeOptions({ value, onChange }: Props) {
  return (
    <div className="opts" role="radiogroup" aria-label="힌트 공개 방식">
      {MODES.map((m) => (
        <label className="opt" key={m.value}>
          <input type="radio" name="hint-mode" checked={value === m.value} onChange={() => onChange(m.value)} />
          <strong>
            {m.title} {m.value === 'EARNED' && <span className="chip acc">추천</span>}
          </strong>
          <span>{m.desc}</span>
        </label>
      ))}
    </div>
  )
}
