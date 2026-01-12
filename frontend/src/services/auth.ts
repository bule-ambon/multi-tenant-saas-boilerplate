const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

export type AuthTokens = {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export const login = async (email: string, password: string): Promise<AuthTokens> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}))
    const message = payload?.detail ?? 'Login failed'
    throw new Error(message)
  }

  const tokens = (await response.json()) as AuthTokens
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token)
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)
  return tokens
}

export const logout = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

export const getAccessToken = () => localStorage.getItem(ACCESS_TOKEN_KEY)

export const isAuthenticated = () => Boolean(getAccessToken())
