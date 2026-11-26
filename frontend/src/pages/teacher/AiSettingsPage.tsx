import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import type { AiPolicy } from '../../api/assignments'
import { getAiDefaults, saveAiDefaults } from '../../api/classes'
import { QueryState } from '../../components/QueryState'
import HintModeOptions from './editor/policy/HintModeOptions'
import PolicyOptions from './editor/policy/PolicyOptions'

/** 교수자: 이 클래스에서 새로 만드는 과제에 미리 채울 AI 도움 정책 */
export default function AiSettingsPage() {
  const classId = Number(useParams().classId)
  const client = useQueryClient()
  const key = ['ai-defaults', classId]
  const saved = useQuery({ queryKey: key, queryFn: () => getAiDefaults(classId) })
  const [edited, setEdited] = useState<AiPolicy | null>(null)
  const save = useMutation({
    mutationFn: (p: AiPolicy) => saveAiDefaults(classId, p),
    onSuccess: (data) => {
      client.setQueryData(key, data)
      setEdited(null)
    },
  })

  const policy = edited ?? saved.data
  if (!policy) return <QueryState isPending={saved.isPending} error={saved.error} />
  const change = (patch: Partial<AiPolicy>) => setEdited({ ...policy, ...patch })

  return (
    <div className="stack">
      <div className="spread">
        <h2>학습 AI 기본값</h2>
        <Link className="btn sm" to={`/teacher/classes/${classId}`}>클래스로</Link>
      </div>
      <p className="lead">
        여기서 정한 값이 새 과제를 만들 때 "AI 도움 정책" 단계에 미리 채워져요. 과제마다 다시 바꿀 수 있고, 이미 만든 과제에는 적용되지 않아요.
      </p>
      <section className="panel stack">
        <h3>힌트 공개 방식</h3>
        <HintModeOptions value={policy.hint_mode} onChange={(hint_mode) => change({ hint_mode })} />
        <hr className="sep" />
        <PolicyOptions policy={policy} onChange={change} />
        <p className="note">지시문 직접 작성은 과제마다 문항이 달라서 과제 설정에서만 할 수 있어요.</p>
        <div className="row">
          <button className="btn primary" disabled={!edited || save.isPending} onClick={() => edited && save.mutate(edited)}>
            기본값 저장
          </button>
          {edited && (
            <button className="btn" onClick={() => setEdited(null)}>
              되돌리기
            </button>
          )}
          {!edited && save.isSuccess && <span className="note">저장했어요. 다음에 만드는 과제부터 적용돼요.</span>}
        </div>
        {save.error && <p className="error-text">{save.error.message}</p>}
      </section>
    </div>
  )
}
