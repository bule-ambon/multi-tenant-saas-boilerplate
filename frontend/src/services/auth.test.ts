import { beforeEach, describe, expect, it } from 'vitest'
import { isAuthenticated } from './auth'

const ACCESS_TOKEN_KEY = 'access_token'
const ACCESS_TOKEN_EXPIRES_AT_KEY = 'access_token_expires_at'

const createMemoryStorage = () => {
  let store: Record<string, string> = {}
  return {
    getItem: (key: string) => (key in store ? store[key] : null),
    setItem: (key: string, value: string) => {
      store[key] = value
    },
    removeItem: (key: string) => {
      delete store[key]
    },
    clear: () => {
      store = {}
    },
  }
}

const storage = createMemoryStorage()

Object.defineProperty(globalThis, 'localStorage', {
  value: storage,
  writable: false,
})

describe('auth session checks', () => {
  beforeEach(() => {
    storage.clear()
  })

  it('returns false when no access token exists', () => {
    expect(isAuthenticated()).toBe(false)
  })

  it('returns false when access token is expired', () => {
    storage.setItem(ACCESS_TOKEN_KEY, 'token')
    storage.setItem(ACCESS_TOKEN_EXPIRES_AT_KEY, String(Date.now() - 1000))
    expect(isAuthenticated()).toBe(false)
  })

  it('returns true when access token is valid', () => {
    storage.setItem(ACCESS_TOKEN_KEY, 'token')
    storage.setItem(ACCESS_TOKEN_EXPIRES_AT_KEY, String(Date.now() + 60_000))
    expect(isAuthenticated()).toBe(true)
  })
})
