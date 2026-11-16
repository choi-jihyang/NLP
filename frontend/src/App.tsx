import { Route, Routes } from 'react-router-dom'

import { AppLayout, type NavItem } from './components/layout/AppLayout'
import HomePage from './pages/HomePage'
import LoginPage from './pages/auth/LoginPage'
import SignupPage from './pages/auth/SignupPage'
import ConsentPage from './pages/student/ConsentPage'
import JoinClassPage from './pages/student/JoinClassPage'
import MyReportPage from './pages/student/MyReportPage'
import StudentClassPage from './pages/student/StudentClassPage'
import UnderstandingCheckPage from './pages/student/check/UnderstandingCheckPage'
import SolvePage from './pages/student/solve/SolvePage'
import AiSettingsPage from './pages/teacher/AiSettingsPage'
import ClassCreatePage from './pages/teacher/ClassCreatePage'
import ClassDetailPage from './pages/teacher/ClassDetailPage'
import ClassListPage from './pages/teacher/ClassListPage'
import PlansPage from './pages/teacher/PlansPage'
import StudentRecordPage from './pages/teacher/StudentRecordPage'
import ClassStudentsPage from './pages/teacher/students/ClassStudentsPage'
import AssignmentEditorPage from './pages/teacher/editor/AssignmentEditorPage'
import GradingPage from './pages/teacher/grading/GradingPage'
import DashboardPage from './pages/teacher/report/DashboardPage'

const TEACHER_NAV: NavItem[] = [
  { to: '/teacher/classes', label: '내 클래스' },
  { to: '/teacher/plans', label: '요금제' },
]
const STUDENT_NAV: NavItem[] = [
  { to: '/student/classes', label: '내 과제' },
  { to: '/student/join', label: '클래스 참여' },
]

// TODO: 로그인 구현 시 역할별 접근 제한(가드) 추가
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />

      <Route path="/teacher" element={<AppLayout subtitle="교수자" nav={TEACHER_NAV} />}>
        <Route path="plans" element={<PlansPage />} />
        <Route path="classes" element={<ClassListPage />} />
        <Route path="classes/new" element={<ClassCreatePage />} />
        <Route path="classes/:classId" element={<ClassDetailPage />} />
        <Route path="classes/:classId/ai-settings" element={<AiSettingsPage />} />
        <Route path="classes/:classId/assignments/new" element={<AssignmentEditorPage />} />
        <Route path="classes/:classId/assignments/:assignmentId/edit" element={<AssignmentEditorPage />} />
        <Route path="classes/:classId/assignments/:assignmentId/grading" element={<GradingPage />} />
        <Route path="classes/:classId/dashboard" element={<DashboardPage />} />
        <Route path="classes/:classId/students" element={<ClassStudentsPage />} />
        <Route path="classes/:classId/students/:studentId" element={<StudentRecordPage />} />
      </Route>

      <Route path="/student" element={<AppLayout subtitle="학생" nav={STUDENT_NAV} />}>
        <Route path="join" element={<JoinClassPage />} />
        <Route path="consent" element={<ConsentPage />} />
        <Route path="classes" element={<StudentClassPage />} />
        <Route path="assignments/:assignmentId" element={<SolvePage />} />
        <Route path="assignments/:assignmentId/check" element={<UnderstandingCheckPage />} />
        <Route path="assignments/:assignmentId/report" element={<MyReportPage />} />
      </Route>
    </Routes>
  )
}
