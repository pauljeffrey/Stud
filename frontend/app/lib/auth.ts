"use client"

import { useEffect, useState, useCallback } from "react"

const TOKEN_KEY = "token"
const USER_KEY = "user"
const AUTH_EVENT = "stud-auth-changed"

export interface AuthUser {
  id: string
  email: string
  name: string
  profession?: string
  user_type?: string
  age?: number
  avatar_url?: string
}

function emitAuthChange() {
  if (typeof window === "undefined") return
  window.dispatchEvent(new CustomEvent(AUTH_EVENT))
}

export function saveAuth(token: string, user: AuthUser) {
  if (typeof window === "undefined") return
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
  emitAuthChange()
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem(TOKEN_KEY)
}

export function getUser(): AuthUser | null {
  if (typeof window === "undefined") return null
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export function clearAuth() {
  if (typeof window === "undefined") return
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
  emitAuthChange()
}

/** Best-effort JWT expiry check (no signature verify; that's the server's job). */
function isJwtFresh(token: string | null): boolean {
  if (!token) return false
  const parts = token.split(".")
  if (parts.length !== 3) return true // opaque session token; trust until 401
  try {
    const payload = JSON.parse(atob(parts[1].replace(/-/g, "+").replace(/_/g, "/")))
    if (typeof payload.exp !== "number") return true
    return payload.exp * 1000 > Date.now() + 5_000 // 5s clock skew
  } catch {
    return true
  }
}

export function isAuthenticated(): boolean {
  return isJwtFresh(getToken())
}

export function getAuthHeaders(): Record<string, string> {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/**
 * Authenticated fetch. Attaches Bearer token and, on 401, clears local auth and
 * redirects to /auth/login (preserves the current path as `next`). Use this
 * everywhere the user must be authenticated.
 */
export async function apiFetch(input: RequestInfo, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers || {})
  const token = getToken()
  if (token && !headers.has("Authorization")) headers.set("Authorization", `Bearer ${token}`)
  const res = await fetch(input, { ...init, headers })
  if (res.status === 401 && typeof window !== "undefined") {
    clearAuth()
    const next = encodeURIComponent(window.location.pathname + window.location.search)
    if (!window.location.pathname.startsWith("/auth/")) {
      window.location.replace(`/auth/login?next=${next}`)
    }
  }
  return res
}

/** React hook: live auth state across tabs and within the same tab. */
export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [ready, setReady] = useState(false)

  const sync = useCallback(() => {
    setUser(getUser())
    setToken(getToken())
  }, [])

  useEffect(() => {
    sync()
    setReady(true)
    if (typeof window === "undefined") return
    const onStorage = (e: StorageEvent) => {
      if (e.key === TOKEN_KEY || e.key === USER_KEY) sync()
    }
    const onCustom = () => sync()
    window.addEventListener("storage", onStorage)
    window.addEventListener(AUTH_EVENT, onCustom as EventListener)
    return () => {
      window.removeEventListener("storage", onStorage)
      window.removeEventListener(AUTH_EVENT, onCustom as EventListener)
    }
  }, [sync])

  const logout = useCallback(async () => {
    try {
      await apiFetch("/api/auth/logout", { method: "POST" }).catch(() => null)
    } finally {
      clearAuth()
    }
  }, [])

  return {
    user,
    token,
    ready,
    isAuthenticated: !!token && isJwtFresh(token),
    logout,
  }
}
