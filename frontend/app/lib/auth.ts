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

async function refreshAccessToken(): Promise<boolean> {
  const token = getToken()
  if (!token) return false
  try {
    const res = await fetch("/api/auth/refresh", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) return false
    const data = (await res.json().catch(() => null)) as { token?: string } | null
    if (data?.token && typeof data.token === "string") {
      localStorage.setItem(TOKEN_KEY, data.token)
      emitAuthChange()
      return true
    }
  } catch {
    /* ignore */
  }
  return false
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
  let res = await fetch(input, { ...init, headers })
  if (res.status === 401 && typeof window !== "undefined") {
    const ok = await refreshAccessToken()
    if (ok) {
      const h2 = new Headers(init.headers || {})
      const t2 = getToken()
      if (t2 && !h2.has("Authorization")) h2.set("Authorization", `Bearer ${t2}`)
      res = await fetch(input, { ...init, headers: h2 })
    }
    if (res.status === 401) {
      clearAuth()
      const next = encodeURIComponent(window.location.pathname + window.location.search)
      if (!window.location.pathname.startsWith("/auth/")) {
        window.location.replace(`/auth/login?next=${next}`)
      }
    }
  }
  return res
}

/** Returns the milliseconds until the JWT expires (negative if already expired). */
function msUntilExpiry(token: string | null): number {
  if (!token) return -1
  const parts = token.split(".")
  if (parts.length !== 3) return Infinity // opaque token; assume valid
  try {
    const payload = JSON.parse(atob(parts[1].replace(/-/g, "+").replace(/_/g, "/")))
    if (typeof payload.exp !== "number") return Infinity
    return payload.exp * 1000 - Date.now()
  } catch {
    return Infinity
  }
}

/** React hook: live auth state across tabs and within the same tab.
 *  Also proactively refreshes the JWT when it is within 2 hours of expiry
 *  so users stay logged in without hitting a 401 mid-session. */
export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [ready, setReady] = useState(false)

  const sync = useCallback(() => {
    setUser(getUser())
    setToken(getToken())
  }, [])

  // Proactive refresh: renew the JWT before it expires so the user stays logged in.
  const proactiveRefresh = useCallback(async () => {
    const t = getToken()
    if (!t) return
    const remaining = msUntilExpiry(t)
    // Refresh if token expires within 2 hours (and is not already expired)
    if (remaining > 0 && remaining < 2 * 60 * 60 * 1000) {
      const ok = await refreshAccessToken()
      if (ok) sync()
    }
  }, [sync])

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

    // Run once on mount, then every 30 minutes
    proactiveRefresh()
    const refreshInterval = setInterval(proactiveRefresh, 30 * 60 * 1000)

    // Also refresh when the user returns to the tab
    const onVisibility = () => {
      if (document.visibilityState === "visible") proactiveRefresh()
    }
    document.addEventListener("visibilitychange", onVisibility)

    return () => {
      window.removeEventListener("storage", onStorage)
      window.removeEventListener(AUTH_EVENT, onCustom as EventListener)
      clearInterval(refreshInterval)
      document.removeEventListener("visibilitychange", onVisibility)
    }
  }, [sync, proactiveRefresh])

  const logout = useCallback(async () => {
    const token = getToken()
    // Clear local auth immediately — the user is logged out on this device right away.
    clearAuth()
    // Notify the server in the background (best-effort; never block the redirect).
    if (token) {
      fetch("/api/auth/logout", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      }).catch(() => null)
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
