import { Route, Routes } from 'react-router-dom'

import { AppLayout, type NavItem } from './components/layout/AppLayout'
import HomePage from './pages/HomePage'
import LoginPage from './pages/auth/LoginPage'
import SignupPage from './pages/auth/SignupPage'
import JoinClassPage from './pages/student/JoinClassPage'
import SolvePage from './pages/student/SolvePage'
import StudentClassPage from './pages/student/StudentClassPage'
import AiSettingsPage from './pages/teacher/AiSettingsPage'
import AssignmentEditorPage from './pages/teacher/AssignmentEditorPage'
import ClassCreatePage from './pages/teacher/ClassCreatePage'
import ClassDetailPage from './pages/teacher/ClassDetailPage'
import ClassListPage from './pages/teacher/ClassListPage'
import DashboardPage from './pages/teacher/DashboardPage'
import GradingPage from './pages/teacher/GradingPage'
import PlansPage from './pages/teacher/PlansPage'

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
      </Route>

      <Route path="/student" element={<AppLayout subtitle="학생" nav={STUDENT_NAV} />}>
        <Route path="join" element={<JoinClassPage />} />
        <Route path="classes" element={<StudentClassPage />} />
        <Route path="assignments/:assignmentId" element={<SolvePage />} />
      </Route>
    </Routes>
  )
}
