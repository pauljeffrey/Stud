"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { apiFetch, isAuthenticated } from "@/app/lib/auth"

export interface AppNotification {
  id: string
  type: string
  title: string
  message?: string
  related_id?: string
  read: boolean
  created_at: string
}

const POLL_MS = 20_000

/**
 * Polls /api/notifications since there's no push/WebSocket transport in this
 * deployment. Used for background-job completions (document ingestion,
 * topic-focused quiz generation) so the user doesn't have to wait on a
 * blocking request — they get told when it's ready instead.
 */
export function useNotifications() {
  const [notifications, setNotifications] = useState<AppNotification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const seenIds = useRef<Set<string>>(new Set())
  const [newlyArrived, setNewlyArrived] = useState<AppNotification[]>([])

  const refresh = useCallback(async () => {
    if (!isAuthenticated()) return
    try {
      const res = await apiFetch("/api/notifications")
      if (!res.ok) return
      const data = await res.json()
      const list: AppNotification[] = data.notifications || []

      if (seenIds.current.size > 0) {
        const fresh = list.filter((n) => !n.read && !seenIds.current.has(n.id))
        if (fresh.length > 0) setNewlyArrived((prev) => [...fresh, ...prev])
      }
      seenIds.current = new Set(list.map((n) => n.id))

      setNotifications(list)
      setUnreadCount(data.unread_count ?? 0)
    } catch {
      /* ignore — will retry on next poll */
    }
  }, [])

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, POLL_MS)
    return () => clearInterval(interval)
  }, [refresh])

  const markRead = useCallback(async (id: string) => {
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)))
    setUnreadCount((c) => Math.max(0, c - 1))
    try {
      await apiFetch(`/api/notifications/${id}/read`, { method: "POST" })
    } catch {
      /* best-effort */
    }
  }, [])

  const markAllRead = useCallback(async () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
    setUnreadCount(0)
    try {
      await apiFetch("/api/notifications/read-all", { method: "POST" })
    } catch {
      /* best-effort */
    }
  }, [])

  const consumeNewlyArrived = useCallback(() => {
    setNewlyArrived([])
  }, [])

  return { notifications, unreadCount, refresh, markRead, markAllRead, newlyArrived, consumeNewlyArrived }
}
