import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { logout } from '../../api/auth'
import { listMyClasses } from '../../api/classes'
import { PageHead } from '../../components/PageHead'
import { SideNav } from '../../components/SideNav'

const SECTIONS = [
  { id: 'me', label: '내 정보' },
  { id: 'classes', label: '참여한 클래스' },
  { id: 'record', label: '기록 안내' },
]

/** 학생 마이페이지: 학번 · 참여한 클래스 · 동의한 기록 안내. 학생은 계정 · 비밀번호가 없다 */
export default function StudentMyPage() {
  const navigate = useNavigate()
  const mine = useQuery({ queryKey: ['my-classes'], queryFn: listMyClasses })
  const no = mine.data?.[0]?.student_no ?? '-'
  const leave = () => {
    logout()
    navigate('/')
  }

  return (
    <>
      <PageHead eyebrow="My page" title="마이페이지" />
      <main className="wrap page side-layout">
        <SideNav items={SECTIONS} leaveLabel="나가기" onLeave={leave} />
        <div className="stack" style={{ gap: 40 }}>
          <section className="panel stack" id="me">
            <div className="profile">
              <span className="avatar">{no.slice(-2)}</span>
              <div>
                <h2 className="mono">{no}</h2>
                <p className="note">학생 · 가입 없이 수업 코드로 입장</p>
              </div>
            </div>
            <div className="info">이 탭에서만 입장 상태가 유지돼요. 탭을 닫으면 수업 코드와 학번으로 다시 입장하고, 교수자가 수락하면 이어서 풀 수 있어요.</div>
          </section>

          <section id="classes">
            <div className="sec-h"><h2>참여한 클래스</h2></div>
            <div className="panel card-tbl">
              <table>
                <thead><tr><th>클래스</th><th>학번</th><th>상태</th><th>과제</th></tr></thead>
                <tbody>
                  {mine.data?.map((c) => (
                    <tr key={c.class_id}>
                      <td><b>{c.class_name}</b></td>
                      <td className="mono">{c.student_no}</td>
                      <td>{c.enrollment_status === 'APPROVED' ? <span className="chip good">참여 중</span> : <span className="chip warn">수락 대기</span>}</td>
                      <td>{c.assignments.length}개</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel stack" id="record">
            <h2>기록 안내 · 입장할 때 동의한 내용</h2>
            <dl className="kv-list">
              <dt>저장하는 정보</dt><dd>질문, 풀이 시도, AI 답변, 힌트 사용 이력, 이해 확인 답변</dd>
              <dt>볼 수 있는 사람</dt><dd>본인과 담당 교수자. 반 전체 리포트의 답변 예시는 익명이에요.</dd>
              <dt>보관 기간</dt><dd>학기 종료 후 삭제 (기간은 팀에서 확정)</dd>
              <dt>모델 학습</dt><dd>수업 기록을 모델 학습에 쓰지 않아요.</dd>
              <dt>붙여넣기</dt><dd>길이와 시점만 기록해요. 붙여 넣은 내용은 저장하지 않아요.</dd>
            </dl>
          </section>
        </div>
      </main>
    </>
  )
}
