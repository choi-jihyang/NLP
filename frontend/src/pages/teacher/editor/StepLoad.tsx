import { useState } from 'react'
import type { Assignment, Language } from '../../../api/assignments'
import { LANGUAGE_LABEL } from '../../../api/client'
import { fromKstLocalInput, toKstLocalInput } from '../../../components/format'
import { typeSummary, totalPoints } from './questionText'

type Props = {
  draft: Assignment
  loaded: boolean
  loading: boolean
  fileName: string | null
  error: Error | null
  onChange: (patch: Partial<Assignment>) => void
  onFile: (file: File) => void
  onSample: () => void
  onBlank: () => void
  onNext: () => void
}

const LANGUAGES: Language[] = ['C', 'PYTHON', 'JAVA', 'JAVASCRIPT']
type Start = 'FILE' | 'SAMPLE' | 'BLANK'

const STARTS: { value: Start; title: string; desc: string }[] = [
  { value: 'FILE', title: '파일 불러오기', desc: '양식에 맞춘 .md 파일을 올려요.' },
  { value: 'SAMPLE', title: '샘플로 시작', desc: 'C 이진수 과제 5문항으로 둘러봐요.' },
  { value: 'BLANK', title: '빈 과제로 시작', desc: '문항을 하나씩 직접 추가해요.' },
]

const AUDIENCES = ['대학 1학년', '대학 2학년', '비전공 교양', '고등학교 정보', '코딩 테스트 준비반']

/** STEP 1. 과목·대상·언어를 적고 과제 파일을 불러온다 */
export default function StepLoad({ draft, loaded, loading, fileName, error, onChange, onFile, onSample, onBlank, onNext }: Props) {
  const [start, setStart] = useState<Start>('FILE')
  const pick = (value: Start) => {
    setStart(value)
    if (value === 'SAMPLE') onSample()
    if (value === 'BLANK') onBlank()
  }
  return (
    <section className="panel stack">
      <h2>어떤 과제에 AI 도움을 붙일까요?</h2>
      <p className="lead">
        과목과 대상을 적고 이미 갖고 있는 과제 파일을 올리면, 문항과 테스트 케이스를 찾아 다음 단계의 양식을 채워 드려요. 파일 없이 직접 추가할 수도 있어요.
      </p>
      <div className="grid3">
        <label className="field">
          <span className="label">과목 이름</span>
          <input className="inp" value={draft.course} placeholder="예: 프로그래밍 기초" onChange={(e) => onChange({ course: e.target.value })} />
        </label>
        <label className="field">
          <span className="label">대상</span>
          <input className="inp" list="audience-options" value={draft.audience} placeholder="예: 대학 1학년, 비전공 교양" onChange={(e) => onChange({ audience: e.target.value })} />
          <datalist id="audience-options">
            {AUDIENCES.map((a) => (
              <option key={a} value={a} />
            ))}
          </datalist>
        </label>
        <label className="field">
          <span className="label">언어 · 코드 실행 채점에 쓰여요</span>
          <select className="inp" value={draft.language} onChange={(e) => onChange({ language: e.target.value as Language })}>
            {LANGUAGES.map((l) => (
              <option key={l} value={l}>{LANGUAGE_LABEL[l]}{l === 'C' || l === 'PYTHON' ? '' : ' (코드 실행 미지원)'}</option>
            ))}
          </select>
        </label>
      </div>
      <div className="grid3">
        <label className="field" style={{ gridColumn: 'span 2' }}>
          <span className="label">과제 이름</span>
          <input className="inp" value={draft.title} onChange={(e) => onChange({ title: e.target.value })} />
        </label>
        <label className="field">
          <span className="label">마감 · 한국 시간</span>
          <input
            className="inp"
            type="datetime-local"
            value={toKstLocalInput(draft.due_at)}
            onChange={(e) => onChange({ due_at: fromKstLocalInput(e.target.value) })}
          />
        </label>
      </div>
      <label className="field">
        <span className="label">과제 설명 · AI가 도움을 줄 때 참고해요 (선택)</span>
        <textarea
          className="inp"
          value={draft.description}
          placeholder="예: 반복문을 처음 배운 학생들이에요. 리스트 컴프리헨션은 아직 안 배웠으니 힌트에서 쓰지 말아 주세요."
          onChange={(e) => onChange({ description: e.target.value })}
        />
      </label>
      <p className="note">퀴즈, 출력 예측, 코드 작성, 간단 제작 같은 문항 유형은 다음 단계에서 문항마다 정해요.</p>
      <h3>어떻게 시작할까요?</h3>
      <div className="opts" role="radiogroup" aria-label="시작 방법">
        {STARTS.map((o) => (
          <label className="opt" key={o.value}>
            <input type="radio" name="start" checked={start === o.value} disabled={loading} onChange={() => pick(o.value)} />
            <strong>{o.title}</strong>
            <span>{o.desc}</span>
          </label>
        ))}
      </div>
      {start === 'FILE' && (
        <>
          <label className="drop">
            <strong>과제 파일 올리기</strong>
            <span className="note">정해진 양식의 마크다운(.md) · 눌러서 선택</span>
            <input type="file" accept=".md,.markdown,.txt" onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])} />
          </label>
          <div className="row">
            <span className="note">양식에 맞춰 쓰면 문항을 자동으로 찾아요.</span>
            <a className="btn sm" href="/thinkguard-assignment-template.md" download>양식 받기 (.md)</a>
            <a className="btn sm" href="/thinkguard-assignment-example.md" download>예시 받기 (.md)</a>
          </div>
        </>
      )}
      {loading && (
        <div className="status wait">
          <div className="spin" />
          <div>{fileName ? `${fileName}에서 ` : ''}문항, 코드, 정답, 테스트 케이스, 배점을 찾는 중이에요…</div>
        </div>
      )}
      {!loading && loaded && (
        <div className="status">
          <div>✓</div>
          <div>
            <b>문항 {draft.questions.length}개를 찾았어요.</b> {typeSummary(draft.questions)} · 총 {totalPoints(draft.questions)}점. 다음 단계에서 정답과 테스트 케이스가 맞는지 확인해 주세요.
          </div>
        </div>
      )}
      {error && <p className="error-text">{error.message}</p>}
      {start === 'FILE' && <p className="note">양식에 맞춘 .md 파일만 읽어요. 양식이 다르면 틀린 곳을 알려 줘요.</p>}
      <div className="spread">
        <span />
        <button className="btn primary" disabled={!loaded || loading} onClick={onNext}>문항 확인하기</button>
      </div>
    </section>
  )
}
