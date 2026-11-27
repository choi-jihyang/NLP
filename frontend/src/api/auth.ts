import { post, session, type Role } from './client'

export type { Role }
export type User = { seq: number; name: string; email: string; role: Role }
export type LoginResult = { access_token: string; user: User }

const keep = (r: LoginResult): LoginResult => {
  session.save(r.access_token, r.user.role, { name: r.user.name, email: r.user.email })
  return r
}

export const login = async (body: { email: string; password: string }) => keep(await post<LoginResult>('/auth/login', body))

export type SignupRequest = { name: string; email: string; password: string }
/** 교수자 계정 만들기. 학생은 가입 없이 수업 코드로 입장한다 */
export const signup = async (body: SignupRequest) => keep(await post<LoginResult>('/auth/signup', body))

export const logout = () => session.clear()
