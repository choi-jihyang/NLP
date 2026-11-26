import type { Question, QuestionType } from '../../../api/assignments'
import { newQuestion, totalPoints, TYPE_LABEL } from './questionText'
import QuestionEditor from './questions/QuestionEditor'

type Props = {
  questions: Question[]
  onChange: (index: number, patch: Partial<Question>) => void
  onReplace: (questions: Question[]) => void
  onPrev: () => void
  onNext: () => void
}

/** STEP 2. 정답과 채점 방식 확인 · 문항 추가 */
export default function StepQuestions({ questions, onChange, onReplace, onPrev, onNext }: Props) {
  return (
    <section className="panel stack">
      <div className="spread">
        <h2>정답과 채점 방식을 확인해 주세요</h2>
        <span className="chip">총점 {totalPoints(questions)}점</span>
      </div>
      <p className="lead">
        퀴즈와 출력 예측은 정답과 대조하고, 코드 작성은 테스트 케이스를 실행해서 자동으로 채점해요. 간단 제작은 교수자가 요구사항을 기준으로 직접 채점해요.
      </p>
      {questions.map((q, i) => (
        <QuestionEditor
          key={q.seq ?? q.key ?? i}
          index={i}
          question={q}
          onChange={(patch) => onChange(i, patch)}
          onRemove={() => onReplace(questions.filter((_, k) => k !== i))}
        />
      ))}
      {!questions.length && <p className="note">아직 문항이 없어요. 아래에서 문항을 추가해 주세요.</p>}
      <div className="addbar">
        <b>문항 추가</b>
        {(Object.keys(TYPE_LABEL) as QuestionType[]).map((t) => (
          <button key={t} className="btn sm" onClick={() => onReplace([...questions, newQuestion(t)])}>
            + {TYPE_LABEL[t]}
          </button>
        ))}
      </div>
      <div className="spread">
        <button className="btn" onClick={onPrev}>이전</button>
        <button className="btn primary" disabled={!questions.length} onClick={onNext}>AI 도움 정하기</button>
      </div>
    </section>
  )
}
