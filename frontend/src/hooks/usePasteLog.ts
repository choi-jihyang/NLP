import { useCallback } from 'react'

import { logPaste, type PasteField } from '../api/pasteEvents'

/** 붙여넣기 길이·시점만 기록하는 콜백을 만든다. 내용은 보내지 않는다 (불변식 I5) */
export function usePasteLog(questionId: string, enabled: boolean) {
  return useCallback(
    (field: PasteField) => (length: number) => {
      if (!enabled || length === 0) return
      void logPaste({ question_id: questionId, field, length, pasted_at: new Date().toISOString() })
    },
    [questionId, enabled],
  )
}
