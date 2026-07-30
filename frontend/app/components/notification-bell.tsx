"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Bell, CheckCheck } from "lucide-react"
import { Button } from "@/app/components/ui/button"
import { useToast } from "@/app/components/ui/use-toast"
import { useNotifications, type AppNotification } from "@/app/lib/notifications"

export default function NotificationBell() {
  const { notifications, unreadCount, markRead, markAllRead, newlyArrived, consumeNewlyArrived } =
    useNotifications()
  const [open, setOpen] = useState(false)
  const { toast } = useToast()
  const router = useRouter()

  const handleNotificationClick = (n: AppNotification) => {
    if (!n.read) markRead(n.id)
    if (n.type === "quiz_ready" && n.related_id) {
      setOpen(false)
      router.push(`/quiz?quizId=${n.related_id}`)
    }
  }

  useEffect(() => {
    if (newlyArrived.length === 0) return
    for (const n of newlyArrived) {
      toast({
        title: n.title,
        description: n.message,
        variant: n.type === "document_failed" || n.type === "quiz_failed" ? "destructive" : undefined,
      })
    }
    consumeNewlyArrived()
  }, [newlyArrived, consumeNewlyArrived, toast])

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="icon"
        className="relative text-white hover:bg-purple-800"
        onClick={() => setOpen((v) => !v)}
        aria-label="Notifications"
      >
        <Bell className="h-4 w-4" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-bold text-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </Button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 z-50 mt-2 w-80 max-h-96 overflow-y-auto rounded-lg border border-purple-700/40 bg-black/95 backdrop-blur-md shadow-xl">
            <div className="flex items-center justify-between px-3 py-2 border-b border-purple-700/40">
              <span className="text-sm font-semibold text-white">Notifications</span>
              {unreadCount > 0 && (
                <button
                  onClick={() => markAllRead()}
                  className="flex items-center gap-1 text-xs text-purple-300 hover:text-purple-200"
                >
                  <CheckCheck className="h-3 w-3" />
                  Mark all read
                </button>
              )}
            </div>
            {notifications.length === 0 ? (
              <p className="p-4 text-xs text-gray-400 text-center">No notifications yet.</p>
            ) : (
              <ul>
                {notifications.map((n) => (
                  <li
                    key={n.id}
                    onClick={() => handleNotificationClick(n)}
                    className={`px-3 py-2 border-b border-purple-900/40 cursor-pointer text-xs ${
                      n.read ? "text-gray-400" : "text-white bg-purple-900/20"
                    }`}
                  >
                    <p className="font-medium">{n.title}</p>
                    {n.message && <p className="text-gray-400 mt-0.5">{n.message}</p>}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </div>
  )
}
