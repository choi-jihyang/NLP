type Props = { step: number; enabled: boolean; onSelect: (step: number) => void }

const STEPS = ['과제 불러오기', '문항 · 채점', 'AI 도움 정책', '확인 · 배포']

/** 과제 만들기 4단계 표시. 문항을 불러오기 전에는 다음 단계로 못 간다 */
export default function Stepper({ step, enabled, onSelect }: Props) {
  return (
    <div className="stepper">
      {STEPS.map((label, i) => {
        const n = i + 1
        return (
          <button
            key={label}
            className={`st ${step === n ? 'on' : step > n ? 'done' : ''}`}
            disabled={!enabled && n > 1}
            aria-current={step === n ? 'step' : undefined}
            onClick={() => onSelect(n)}
          >
            <b>STEP {n}</b>
            {label}
          </button>
        )
      })}
    </div>
  )
}
