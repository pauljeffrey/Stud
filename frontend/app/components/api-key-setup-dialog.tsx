"use client"

import { useState } from "react"
import Link from "next/link"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/app/components/ui/dialog"
import { Button } from "@/app/components/ui/button"
import { Input } from "@/app/components/ui/input"
import { Label } from "@/app/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/app/components/ui/select"
import { Shield, ExternalLink } from "lucide-react"
import {
  type ApiCredentials,
  validateCredentials,
} from "@/app/lib/api-credentials"

interface ApiKeySetupDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Shown when saved credentials are invalid */
  errorMessage?: string
  isLoggedIn: boolean
  initial?: Partial<ApiCredentials>
  onComplete: (creds: ApiCredentials, saveToAccount: boolean) => void | Promise<void>
}

export function ApiKeySetupDialog({
  open,
  onOpenChange,
  errorMessage,
  isLoggedIn,
  initial,
  onComplete,
}: ApiKeySetupDialogProps) {
  const [step, setStep] = useState<"form" | "save">("form")
  const [provider, setProvider] = useState(initial?.provider || "google")
  const [modelName, setModelName] = useState(initial?.modelName || "")
  const [apiKey, setApiKey] = useState(initial?.apiKey || "")
  const [validationError, setValidationError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const creds: ApiCredentials = { provider, modelName, apiKey }

  const handleContinue = () => {
    const check = validateCredentials(creds)
    if (!check.valid) {
      setValidationError(check.message || "Invalid credentials")
      return
    }
    setValidationError(null)
    if (isLoggedIn) {
      setStep("save")
    } else {
      void finish(false)
    }
  }

  const finish = async (saveToAccount: boolean) => {
    setBusy(true)
    setValidationError(null)
    try {
      await onComplete(creds, saveToAccount)
      onOpenChange(false)
      setStep("form")
    } catch (error: unknown) {
      setValidationError(
        error instanceof Error ? error.message : "Something went wrong. Please try again."
      )
      setStep("form")
    } finally {
      setBusy(false)
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        onOpenChange(v)
        if (!v) setStep("form")
      }}
    >
      <DialogContent className="bg-[#0f0a1f] border-purple-700/50 text-white max-w-md">
        {step === "form" ? (
          <>
            <DialogHeader>
              <DialogTitle>AI credentials required</DialogTitle>
              <DialogDescription className="text-gray-400">
                {errorMessage ||
                  (isLoggedIn
                    ? "Your account needs a valid model name and API key to run Mediquest."
                    : "Enter your provider credentials, or leave blank in demo to use our default model.")}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-2">
              <Button variant="link" className="h-auto p-0 text-purple-300" asChild>
                <Link href="/api-keys" target="_blank">
                  How to get a model name &amp; API key
                  <ExternalLink className="ml-1 h-3 w-3 inline" />
                </Link>
              </Button>

              <div className="space-y-2">
                <Label>Provider</Label>
                <Select value={provider} onValueChange={setProvider}>
                  <SelectTrigger className="bg-black/50 border-purple-700/40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="google">Google (Gemini)</SelectItem>
                    <SelectItem value="openai">OpenAI</SelectItem>
                    <SelectItem value="anthropic">Anthropic</SelectItem>
                    <SelectItem value="openrouter">OpenRouter</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="setup-model">Model name</Label>
                <Input
                  id="setup-model"
                  placeholder="e.g. gemini-2.0-flash or gpt-4o-mini"
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  className="bg-black/50 border-purple-700/40"
                  autoComplete="off"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="setup-key">API key</Label>
                <Input
                  id="setup-key"
                  type="password"
                  placeholder="Paste your API key"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="bg-black/50 border-purple-700/40"
                  autoComplete="off"
                />
              </div>

              {validationError && (
                <p className="text-sm text-red-400">{validationError}</p>
              )}
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => onOpenChange(false)} className="border-purple-700">
                Cancel
              </Button>
              <Button onClick={handleContinue} className="bg-purple-700 hover:bg-purple-800">
                Continue
              </Button>
            </DialogFooter>
          </>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-purple-300" />
                Save your API key?
              </DialogTitle>
              <DialogDescription className="text-gray-400">
                Your API key is encrypted before it is stored on our servers, so you do not need to
                enter it every time. You can remove it anytime from your dashboard.
              </DialogDescription>
            </DialogHeader>

            <DialogFooter className="flex-col sm:flex-row gap-2">
              <Button
                variant="outline"
                className="border-purple-700"
                disabled={busy}
                onClick={() => finish(false)}
              >
                Use this session only
              </Button>
              <Button
                className="bg-purple-700 hover:bg-purple-800"
                disabled={busy}
                onClick={() => finish(true)}
              >
                Yes, save securely
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
