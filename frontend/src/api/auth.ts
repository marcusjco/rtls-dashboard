import api from './client'
import type { User } from '../types'

export const login = (username: string, password: string) =>
  api.post('/auth/login', { username, password }).then((r) => r.data)

export const getMe = (): Promise<User> =>
  api.get('/auth/me').then((r) => r.data)
