import type { ReactNode } from 'react'
import { Route, Routes, useParams } from 'react-router-dom'

import { AppLayout } from './components/layout/AppLayout'
import HomePage from './pages/HomePage'
import AuthPage from './pages/auth/AuthPage'
import ConsentPage from './pages/student/ConsentPage'
import JoinClassPage from './pages/student/JoinClassPage'
import MyReportPage from './pages/student/MyReportPage'
import StudentClassPage from './pages/student/StudentClassPage'
import StudentMyPage from './pages/student/StudentMyPage'
import UnderstandingCheckPage from './pages/student/check/UnderstandingCheckPage'
import SolvePage from './pages/student/solve/SolvePage'
import AiSettingsPage from './pages/teacher/AiSettingsPage'
import ClassCreatePage from './pages/teacher/ClassCreatePage'
import ClassDetailPage from './pages/teacher/ClassDetailPage'
import ClassHeader from './pages/teacher/ClassHeader'
import ClassListPage from './pages/teacher/ClassListPage'
import PlansPage from './pages/teacher/PlansPage'
import StudentRecordPage from './pages/teacher/StudentRecordPage'
import TeacherMyPage from './pages/teacher/TeacherMyPage'
import ClassStudentsPage from './pages/teacher/students/ClassStudentsPage'
import AssignmentEditorPage from './pages/teacher/editor/AssignmentEditorPage'
import GradingPage from './pages/teacher/grading/GradingPage'
import DashboardPage from './pages/teacher/report/DashboardPage'

/** 화면 머리가 없는 화면: 본문 여백만 */
const Plain = ({ children }: { children: ReactNode }) => <main className="wrap page">{children}</main>

/** 클래스 탭(학생 · AI 기본값) 화면: 클래스 머리 아래에 본문 */
function ClassTab({ children }: { children: ReactNode }) {
  const classId = Number(useParams().classId)
  return (
    <>
      <ClassHeader classId={classId} />
      <Plain>{children}</Plain>
    </>
  )
}

// TODO: 로그인 구현 시 역할별 접근 제한(가드) 추가
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<AuthPage tab="login" />} />
      <Route path="/signup" element={<AuthPage tab="signup" />} />

      <Route path="/teacher" element={<AppLayout role="TEACHER" />}>
        <Route path="plans" element={<PlansPage />} />
        <Route path="mypage" element={<TeacherMyPage />} />
        <Route path="classes" element={<ClassListPage />} />
        <Route path="classes/new" element={<ClassCreatePage />} />
        <Route path="classes/:classId" element={<ClassDetailPage />} />
        <Route path="classes/:classId/ai-settings" element={<ClassTab><AiSettingsPage /></ClassTab>} />
        <Route path="classes/:classId/students" element={<ClassTab><ClassStudentsPage /></ClassTab>} />
        <Route path="classes/:classId/assignments/new" element={<AssignmentEditorPage />} />
        <Route path="classes/:classId/assignments/:assignmentId/edit" element={<AssignmentEditorPage />} />
        <Route path="classes/:classId/assignments/:assignmentId/grading" element={<GradingPage />} />
        <Route path="classes/:classId/dashboard" element={<DashboardPage />} />
        <Route path="classes/:classId/students/:studentId" element={<StudentRecordPage />} />
      </Route>

      <Route path="/student" element={<AppLayout role="STUDENT" />}>
        <Route path="join" element={<JoinClassPage />} />
        <Route path="consent" element={<ConsentPage />} />
        <Route path="classes" element={<StudentClassPage />} />
        <Route path="mypage" element={<StudentMyPage />} />
        <Route path="assignments/:assignmentId" element={<SolvePage />} />
        <Route path="assignments/:assignmentId/check" element={<UnderstandingCheckPage />} />
        <Route path="assignments/:assignmentId/report" element={<MyReportPage />} />
      </Route>
    </Routes>
  )
}
