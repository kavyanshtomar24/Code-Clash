import { useMemo, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { endpoints, tokenStore } from '../lib/api'
import { AuthContext, type AuthContextValue } from './auth-context'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient()
  const [hasToken, setHasToken] = useState(Boolean(tokenStore.access))

  const userQuery = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: endpoints.auth.me,
    enabled: hasToken,
    retry: false,
  })

  const value = useMemo<AuthContextValue>(
    () => ({
      user: userQuery.data,
      isAuthenticated: Boolean(userQuery.data && hasToken),
      isLoading: userQuery.isLoading,
      async login(payload) {
        const tokens = await endpoints.auth.login(payload)
        tokenStore.set(tokens)
        setHasToken(true)
        await queryClient.invalidateQueries({ queryKey: ['auth'] })
      },
      async register(payload) {
        await endpoints.auth.register(payload)
        const tokens = await endpoints.auth.login({
          username_or_email: payload.username,
          password: payload.password,
        })
        tokenStore.set(tokens)
        setHasToken(true)
        await queryClient.invalidateQueries({ queryKey: ['auth'] })
      },
      async logout() {
        try {
          await endpoints.auth.logout()
        } finally {
          tokenStore.clear()
          setHasToken(false)
          queryClient.clear()
        }
      },
    }),
    [hasToken, queryClient, userQuery.data, userQuery.isLoading],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
