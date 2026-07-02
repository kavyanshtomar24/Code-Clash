import { createContext } from 'react'
import type { User } from '../lib/types'

export type AuthContextValue = {
  user?: User
  isAuthenticated: boolean
  isLoading: boolean
  login: (payload: { username_or_email: string; password: string }) => Promise<void>
  register: (payload: { username: string; email: string; password: string }) => Promise<void>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)
