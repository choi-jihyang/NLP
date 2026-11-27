import type { AiPolicy, HintPenalty } from '../../../../api/assignments'

type Props = { policy: AiPolicy; onChange: (patch: Partial<AiPolicy>) => void }

type Toggle = { key: 'concept_check_enabled' | 'external_signal_enabled'; label: string; text: string }

const TOGGLES: Toggle[] = [
  {
    key: 'concept_check_enabled',
    label: '제출 전 개념 확인',
    text: '힌트 없이 처음 낸 문항은 제출 직전에 내 코드에서 쓴 개념을 한 가지 물어봐요. 답변에 AI 작성 신호(붙여넣기, AI 특유 말투, 입력 시간에 비해 긴 답변 등)가 높으면 질문을 하나 더 해요. 점수에는 반영하지 않고 리포트에 참고로 표시돼요.',
  },
  {
    key: 'external_signal_enabled',
    label: '외부 AI 사용 의심 신호 · 실험 기능',
    text: '붙여넣기 길이·시점, 다른 AI 특유의 서식, 지나치게 짧은 풀이 시간을 함께 보고 참고 신호로 표시해요. 붙여 넣은 내용은 저장하지 않고, 학생에게도 기록 사실을 안내해요.',
  },
]

/** 코드 한도 · 감점 · 확인 문제 · 개념 확인 · 외부 신호 · 리포트 항목 */
export default function PolicyOptions({ policy: p, onChange }: Props) {
  return (
    <>
      <div className="grid3">
        <label className="field">
          <span className="label">힌트에 보여줄 코드 한도</span>
          <select className="inp" value={p.code_line_limit} onChange={(e) => onChange({ code_line_limit: Number(e.target.value) })}>
            <option value={0}>코드 없이 설명만</option>
            <option value={1}>최대 1줄</option>
            <option value={3}>최대 3줄 (추천)</option>
            <option value={5}>최대 5줄</option>
          </select>
        </label>
        <label className="field">
          <span className="label">AI 메시지 · 학생당 (이 과제)</span>
          <input
            className="inp"
            type="number"
            min={1}
            max={200}
            value={p.usage_limit}
            onChange={(e) => onChange({ usage_limit: Math.max(1, Math.min(200, Math.round(Number(e.target.value) || 1))) })}
          />
        </label>
        <label className="field">
          <span className="label">힌트를 쓰면 점수는</span>
          <select className="inp" value={p.hint_penalty} onChange={(e) => onChange({ hint_penalty: e.target.value as HintPenalty })}>
            <option value="NONE">감점 없음</option>
            <option value="PER_STEP">힌트 1단계당 1점 감점</option>
            <option value="PRACTICE">힌트 쓴 문항은 연습으로 처리 (0점)</option>
          </select>
        </label>
        <div className="field">
          <span className="label">AI 없이 확인 문제</span>
          <label className="check">
            <input type="checkbox" checked={p.variant_enabled} onChange={(e) => onChange({ variant_enabled: e.target.checked })} />
            <span>최종 제출 뒤 이해 확인 단계에서, 값을 바꾼 문제와 내 함수를 쓰는 출력 예측 문제를 AI 도움 없이 풀게 해요</span>
          </label>
        </div>
        <label className="field">
          <span className="label">확인 문제 결과는</span>
          <select
            className="inp"
            value={p.variant_graded ? 'true' : 'false'}
            disabled={!p.variant_enabled}
            onChange={(e) => onChange({ variant_graded: e.target.value === 'true' })}
          >
            <option value="false">리포트에만 표시</option>
            <option value="true">점수에 반영 (원문제 50% + 확인 문제 50%)</option>
          </select>
        </label>
      </div>
      <div className="grid3">
        {TOGGLES.map((t) => (
          <div className="field" key={t.key}>
            <span className="label">{t.label}</span>
            <label className="check">
              <input type="checkbox" checked={p[t.key]} onChange={(e) => onChange({ [t.key]: e.target.checked })} />
              <span>{t.text}</span>
            </label>
          </div>
        ))}
      </div>
      <hr className="sep" />
      <div className="field">
        <span className="label">리포트로 받을 정보</span>
        <label className="check">
          <input type="checkbox" checked={p.report_misconceptions} onChange={(e) => onChange({ report_misconceptions: e.target.checked })} />
          <span>반 전체가 틀린 지점 (오답 선택지별 오개념, 자주 실패한 테스트)</span>
        </label>
        <label className="check">
          <input type="checkbox" checked={p.report_dependency} onChange={(e) => onChange({ report_dependency: e.target.checked })} />
          <span>AI로는 풀었지만 혼자서는 못 푼 학생</span>
        </label>
      </div>
    </>
  )
}
