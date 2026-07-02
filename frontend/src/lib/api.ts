import axios, { AxiosError } from 'axios'
import type {
  Battle,
  CodeforcesContest,
  CodeforcesProfile,
  DashboardAnalytics,
  Friend,
  FriendRequest,
  LeaderboardRow,
  Notification,
  PaginatedProblems,
  ProblemDetail,
  RunResult,
  Submission,
  SubmissionList,
  Tag,
  TokenResponse,
  User,
  UserStats,
} from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
})

export const tokenStore = {
  get access() {
    return localStorage.getItem('codeclash.access')
  },
  get refresh() {
    return localStorage.getItem('codeclash.refresh')
  },
  set(tokens: TokenResponse) {
    localStorage.setItem('codeclash.access', tokens.access_token)
    localStorage.setItem('codeclash.refresh', tokens.refresh_token)
  },
  clear() {
    localStorage.removeItem('codeclash.access')
    localStorage.removeItem('codeclash.refresh')
  },
}

api.interceptors.request.use((config) => {
  const token = tokenStore.access
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config
    if (error.response?.status === 401 && tokenStore.refresh && original && !(original as { _retry?: boolean })._retry) {
      ;(original as { _retry?: boolean })._retry = true
      try {
        const { data } = await axios.post<TokenResponse>(`${API_BASE_URL}/api/v1/auth/refresh`, {
          refresh_token: tokenStore.refresh,
        })
        tokenStore.set(data)
        original.headers.Authorization = `Bearer ${data.access_token}`
        return api(original)
      } catch {
        tokenStore.clear()
      }
    }
    return Promise.reject(error)
  },
)

export function errorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) return detail.map((item) => item.msg).join(', ')
    if (error.message) return error.message
  }
  return 'Something went wrong'
}

export const endpoints = {
  auth: {
    register: (payload: { username: string; email: string; password: string }) =>
      api.post<User>('/auth/register', payload).then((r) => r.data),
    login: (payload: { username_or_email: string; password: string }) =>
      api.post<TokenResponse>('/auth/login', payload).then((r) => r.data),
    logout: () => api.post('/auth/logout', { access_token: tokenStore.access, refresh_token: tokenStore.refresh }),
    me: () => api.get<User>('/auth/me').then((r) => r.data),
  },
  users: {
    stats: () => api.get<UserStats>('/users/stats').then((r) => r.data),
    publicStats: (username: string) => api.get<UserStats>(`/users/stats/${username}`).then((r) => r.data),
    profile: (username: string) => api.get<User>(`/users/profile/${username}`).then((r) => r.data),
    update: (payload: Partial<Pick<User, 'bio' | 'profile_picture' | 'codeforces_handle'>>) =>
      api.put<User>('/users/profile', payload).then((r) => r.data),
    search: (q: string) => api.get<Array<Pick<User, 'id' | 'username' | 'profile_picture' | 'rating'>>>('/users/search', { params: { q } }).then((r) => r.data),
  },
  problems: {
    list: (params: { difficulty?: string; tag?: string; search?: string; page?: number; per_page?: number }) =>
      api.get<PaginatedProblems>('/problems/', { params }).then((r) => r.data),
    tags: () => api.get<Tag[]>('/problems/tags').then((r) => r.data),
    detail: (slug: string) => api.get<ProblemDetail>(`/problems/${slug}`).then((r) => r.data),
  },
  submissions: {
    run: (payload: { problem_id: string; language: string; code: string; input?: string }) =>
      api.post<RunResult>('/submissions/run', payload).then((r) => r.data),
    submit: (payload: { problem_id: string; language: string; code: string }) =>
      api.post<Submission>('/submissions/', payload).then((r) => r.data),
    history: (params?: { page?: number; per_page?: number; problem_id?: string }) =>
      api.get<SubmissionList>('/submissions/history', { params }).then((r) => r.data),
    byProblem: (problemId: string) => api.get<Submission[]>(`/submissions/problem/${problemId}`).then((r) => r.data),
  },
  analytics: {
    dashboard: () => api.get<DashboardAnalytics>('/analytics/dashboard').then((r) => r.data),
  },
  friends: {
    list: () => api.get<Friend[]>('/friends/').then((r) => r.data),
    requests: () => api.get<FriendRequest[]>('/friends/requests').then((r) => r.data),
    request: (receiver_username: string) => api.post<FriendRequest>('/friends/request', { receiver_username }).then((r) => r.data),
    accept: (id: string) => api.post(`/friends/accept/${id}`).then((r) => r.data),
    reject: (id: string) => api.post(`/friends/reject/${id}`).then((r) => r.data),
    remove: (id: string) => api.delete(`/friends/${id}`).then((r) => r.data),
    compare: (id: string) => api.get(`/friends/compare/${id}`).then((r) => r.data),
  },
  battles: {
    create: (payload: { problem_id: string; duration_seconds: number; opponent_username?: string }) =>
      api.post<Battle>('/battles/', payload).then((r) => r.data),
    join: (id: string) => api.post<Battle>(`/battles/${id}/join`).then((r) => r.data),
    cancel: (id: string) => api.post<Battle>(`/battles/${id}/cancel`).then((r) => r.data),
    end: (id: string) => api.post<Battle>(`/battles/${id}/end`).then((r) => r.data),
    submit: (id: string, payload: { problem_id: string; language: string; code: string }) =>
      api.post<Submission>(`/battles/${id}/submit`, payload).then((r) => r.data),
    history: () => api.get<Battle[]>('/battles/history').then((r) => r.data),
    detail: (id: string) => api.get<Battle>(`/battles/${id}`).then((r) => r.data),
  },
  notifications: {
    list: () => api.get<Notification[]>('/notifications/').then((r) => r.data),
    unread: () => api.get<{ unread_count: number }>('/notifications/unread-count').then((r) => r.data),
    read: (id: string) => api.put<Notification>(`/notifications/${id}/read`).then((r) => r.data),
    readAll: () => api.put('/notifications/read-all').then((r) => r.data),
  },
  codeforces: {
    profile: () => api.get<CodeforcesProfile>('/codeforces/profile').then((r) => r.data),
    contests: () => api.get<CodeforcesContest[]>('/codeforces/contests').then((r) => r.data),
    link: (handle: string) => api.post<CodeforcesProfile>('/codeforces/link', { handle }).then((r) => r.data),
    sync: () => api.post<CodeforcesProfile>('/codeforces/sync').then((r) => r.data),
    unlink: () => api.delete('/codeforces/unlink').then((r) => r.data),
  },
  leaderboard: {
    list: (limit = 100) => api.get<LeaderboardRow[]>('/leaderboard/', { params: { limit } }).then((r) => r.data),
  },
}
