import type { Question } from '../../../../api/assignments'
import { TYPE_LABEL } from '../questionText'
import ChoiceEditor from './ChoiceEditor'
import CodeTestsEditor from './CodeTestsEditor'
import ProjectEditor from './ProjectEditor'
import ShortAnswerEditor from './ShortAnswerEditor'

type Props = {
  index: number
  question: Question
  onChange: (patch: Partial<Question>) => void
  onRemove: () => void
}

const GRADING = {
  MULTIPLE_CHOICE: { text: '자동 채점 · 정답 대조', tone: 'acc' },
  SHORT_ANSWER: { text: '자동 채점 · 정답 대조', tone: 'acc' },
  CODE: { text: '자동 채점 · 테스트 실행', tone: 'acc' },
  PROJECT: { text: '교수자 직접 채점', tone: 'warn' },
} as const

/** 문항 하나 편집: 공통(문제·코드·배점) + 유형별 정답·채점 */
export default function QuestionEditor({ index, question: q, onChange, onRemove }: Props) {
  const grading = GRADING[q.type]
  const isNew = q.id.startsWith('new-')

  return (
    <div className="item">
      <div className="spread">
        <div className="row">
          <b>문항 {index + 1}</b>
          <span className="chip">{TYPE_LABEL[q.type]}</span>
          <span className={`chip ${grading.tone}`}>{grading.text}</span>
          {isNew && <span className="chip">직접 추가</span>}
        </div>
        <div className="row">
          <label className="row note">
            배점
            <input className="inp pts" type="number" min={0} value={q.points} onChange={(e) => onChange({ points: Math.max(0, Number(e.target.value) || 0) })} />점
          </label>
          <button className="btn sm" onClick={onRemove}>삭제</button>
        </div>
      </div>
      <label className="field">
        <span className="label">문제</span>
        <textarea className="inp" value={q.prompt} placeholder="문제를 입력하세요" onChange={(e) => onChange({ prompt: e.target.value })} />
      </label>
      {q.type !== 'CODE' && (
        <label className="field">
          <span className="label">{q.type === 'PROJECT' ? '요구사항' : '문제 코드'} (선택)</span>
          <textarea className="code" style={{ minHeight: 110 }} spellCheck={false} value={q.code} onChange={(e) => onChange({ code: e.target.value })} />
        </label>
      )}
      {q.type === 'MULTIPLE_CHOICE' && <ChoiceEditor index={index} question={q} onChange={onChange} />}
      {q.type === 'SHORT_ANSWER' && <ShortAnswerEditor question={q} onChange={onChange} />}
      {q.type === 'CODE' && <CodeTestsEditor question={q} onChange={onChange} />}
      {q.type === 'PROJECT' && <ProjectEditor question={q} onChange={onChange} />}
      {isNew && (
        <p className="note">직접 추가한 문항의 힌트, 개념 확인 질문, 확인 문제는 실제 AI를 연결하면 문제와 정답을 바탕으로 자동 생성돼요.</p>
      )}
    </div>
  )
}
