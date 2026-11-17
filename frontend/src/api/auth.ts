import { mockClasses } from './mock/classStore'

export type Role = 'TEACHER' | 'STUDENT'
export type User = { id: string; name: string; email: string; role: Role }
export type LoginResult = { access_token: string; user: User }

export const login = (body: { email: string; password: string }) => mockClasses.login(body)

export type SignupRequest = { name: string; email: string; password: string }
/** 교수자 계정 만들기. 학생은 가입 없이 수업 코드로 입장한다 */
export const signup = (body: SignupRequest) => mockClasses.signup(body)
