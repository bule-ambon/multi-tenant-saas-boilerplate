const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const ACCESS_TOKEN_EXPIRES_AT_KEY = 'access_token_expires_at'

export type AuthTokens = {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export type RegisterPayload = {
  email: string
  password: string
  full_name?: string
}

export type RegisteredUser = {
  id: string
  email: string
  full_name?: string | null
  is_verified: boolean
  mfa_enabled: boolean
  created_at: string
}

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const storeTokens = (tokens: AuthTokens) => {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token)
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)
  const expiresAt = Date.now() + tokens.expires_in * 1000
  localStorage.setItem(ACCESS_TOKEN_EXPIRES_AT_KEY, String(expiresAt))
}

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
  storeTokens(tokens)
  return tokens
}

export const register = async (payload: RegisterPayload): Promise<RegisteredUser> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}))
    const message = payload?.detail ?? 'Registration failed'
    throw new Error(message)
  }

  return (await response.json()) as RegisteredUser
}

export const refreshTokens = async (): Promise<AuthTokens | null> => {
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    return null
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${refreshToken}` },
  })

  if (!response.ok) {
    logout()
    return null
  }

  const tokens = (await response.json()) as AuthTokens
  storeTokens(tokens)
  return tokens
}

export const logout = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(ACCESS_TOKEN_EXPIRES_AT_KEY)
}

export const getAccessToken = () => localStorage.getItem(ACCESS_TOKEN_KEY)

export const getRefreshToken = () => localStorage.getItem(REFRESH_TOKEN_KEY)

export const getAccessTokenExpiresAt = () => {
  const value = localStorage.getItem(ACCESS_TOKEN_EXPIRES_AT_KEY)
  return value ? Number(value) : null
}

export const isAccessTokenExpired = () => {
  const expiresAt = getAccessTokenExpiresAt()
  if (!expiresAt) {
    return true
  }
  return Date.now() >= expiresAt
}

export const isAuthenticated = () => Boolean(getAccessToken()) && !isAccessTokenExpired()

export const authFetch = async (input: RequestInfo, init?: RequestInit) => {
  const accessToken = getAccessToken()
  const headers = new Headers(init?.headers)
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`)
  }

  const response = await fetch(input, { ...init, headers })
  if (response.status !== 401) {
    return response
  }

  const refreshed = await refreshTokens()
  if (!refreshed) {
    return response
  }

  const retryHeaders = new Headers(init?.headers)
  retryHeaders.set('Authorization', `Bearer ${refreshed.access_token}`)
  return fetch(input, { ...init, headers: retryHeaders })
}
