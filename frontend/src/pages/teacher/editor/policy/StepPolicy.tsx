import { useMutation } from '@tanstack/react-query'

import { getPromptDraft, type AiPolicy, type Assignment } from '../../../../api/assignments'
import HintModeOptions from './HintModeOptions'
import PolicyOptions from './PolicyOptions'

type Props = {
  draft: Assignment
  onChange: (patch: Partial<AiPolicy>) => void
  onPrev: () => void
  onNext: () => void
}

/** STEP 3. 학생이 AI에게 받을 수 있는 도움 (양식 / 지시문 직접 작성) */
export default function StepPolicy({ draft, onChange, onPrev, onNext }: Props) {
  const p = draft.policy
  const custom = p.prompt_mode === 'CUSTOM'
  const prompt = useMutation({ mutationFn: () => getPromptDraft(draft), onSuccess: (text) => onChange({ custom_prompt: text }) })

  const toCustom = () => {
    onChange({ prompt_mode: 'CUSTOM' })
    if (p.custom_prompt === null) prompt.mutate()
  }

  return (
    <section className="panel stack">
      <div className="spread">
        <h2>학생이 AI에게 받을 수 있는 도움</h2>
        <div className="seg" role="group" aria-label="설정 방식">
          <button aria-pressed={!custom} onClick={() => onChange({ prompt_mode: 'FORM' })}>양식으로 고르기</button>
          <button aria-pressed={custom} onClick={toCustom}>지시문 직접 작성</button>
        </div>
      </div>
      {custom ? (
        <div className="stack">
          <div className="spread">
            <h3>AI 튜터 지시문</h3>
            <button className="btn sm" disabled={prompt.isPending} onClick={() => prompt.mutate()}>양식 기준으로 다시 만들기</button>
          </div>
          <p className="note">아래 선택 내용으로 만든 지시문에서 시작해요. 말투, 설명 방식, 수업에서 쓰는 용어 등을 자유롭게 고쳐 쓰세요.</p>
          <textarea
            className="inp prompt"
            aria-label="AI 튜터 지시문"
            spellCheck={false}
            value={p.custom_prompt ?? (prompt.isPending ? '지시문을 만드는 중…' : '')}
            onChange={(e) => onChange({ custom_prompt: e.target.value })}
          />
          <div className="fixed">
            <b>지시문과 상관없이 항상 적용되는 규칙</b>
            <ul>
              <li>AI 답변은 학생에게 가기 전에 누출 검사를 거쳐요. 정답, 출력값, 그대로 제출할 수 있는 완성 코드가 담기면 차단하고 다시 써요.</li>
              <li>학생이 하지 않은 시도나 생각을 AI가 지어내서 말하지 않아요.</li>
              <li>확인 문제와 이해 확인 단계에는 AI 도움이 열리지 않아요.</li>
              <li>학생 이름과 학번은 AI에 전달하지 않아요.</li>
            </ul>
          </div>
          <h3>누출 검사 기준이 될 공개 수준</h3>
          <p className="note">지시문을 직접 써도, 여기서 고른 수준을 넘는 답변은 차단돼요.</p>
          <HintModeOptions value={p.hint_mode} onChange={(hint_mode) => onChange({ hint_mode })} />
        </div>
      ) : (
        <div className="stack">
          <HintModeOptions value={p.hint_mode} onChange={(hint_mode) => onChange({ hint_mode })} />
          <p className="note">고른 내용은 AI가 지켜야 하는 규칙으로 자동 변환돼요. 어떤 설정이든 정답이 담긴 답변은 학생에게 보내기 전에 걸러집니다.</p>
        </div>
      )}
      <hr className="sep" />
      <PolicyOptions policy={p} onChange={onChange} />
      <div className="spread">
        <button className="btn" onClick={onPrev}>이전</button>
        <button className="btn primary" onClick={onNext}>설정 확인하기</button>
      </div>
    </section>
  )
}
