/** 여러 예시 저장소가 함께 보는 진행 상태. 백엔드가 생기면 지운다 */
import type { EnrollmentStatus } from '../enrollments'

export const progress = {
  /** 교수자가 결과를 공개한 과제 */
  released: new Set<string>(['a2']),
  /** 이 학생이 최종 제출한 과제 */
  finalized: new Set<string>(['a2']),
  /** 이 학생이 낸 문항 수 */
  submitted: { a1: 0, a2: 5 } as Record<string, number>,
  /** 이 학생의 클래스별 참여 상태 */
  enrollment: { c1: 'APPROVED' } as Record<string, EnrollmentStatus>,
  /** 이 학생의 수업용 ID */
  alias: '학생 03',
}
