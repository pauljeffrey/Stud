"use client"

import { useEffect, useState } from "react"
import { AlertTriangle } from "lucide-react"
import { resolveCredentials, hasUsableCredentials } from "@/app/lib/api-credentials"

/**
 * Persistent disclaimer shown whenever the user hasn't configured their own
 * API key/model. Every mode (demo, mediquest, quiz, study) silently falls
 * back to a shared free OpenRouter model in that case, which is slower and
 * prone to rate limits — this keeps that expectation visible everywhere
 * instead of a one-off toast in a single mode.
 */
export function FreeModelNotice({ className }: { className?: string }) {
  const [usingFree, setUsingFree] = useState(false)

  useEffect(() => {
    setUsingFree(!hasUsableCredentials(resolveCredentials()))
  }, [])

  if (!usingFree) return null

  return (
    <div
      className={`flex items-start gap-2 rounded-lg border border-amber-700/40 bg-amber-950/20 px-3 py-2 text-xs text-amber-200 ${className || ""}`}
    >
      <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
      <span>
        Using a shared free model — responses may be slower or rate-limited. Add your own API key
        in Settings for more reliable results.
      </span>
    </div>
  )
}
