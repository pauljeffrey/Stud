"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/app/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Input } from "@/app/components/ui/input"
import { Label } from "@/app/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/app/components/ui/select"
import { Checkbox } from "@/app/components/ui/checkbox"
import { ArrowRight, Sparkles, AlertCircle } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { useToast } from "@/app/components/ui/use-toast"

interface GameSettingsField {
  label: string
  values: string[]
}

interface GameSettings {
  profession?: GameSettingsField
  clinical_setting?: GameSettingsField
  era?: GameSettingsField
  natural_conditions?: GameSettingsField
  nation_type?: GameSettingsField
  economic_advantage?: GameSettingsField
}

const INIT_STEPS = [
  { label: "Summoning the Game Master…",      icon: "🎲", pct: 8  },
  { label: "Forging your medical world…",     icon: "🌍", pct: 22 },
  { label: "Generating clinical parameters…", icon: "🔬", pct: 38 },
  { label: "Crafting your first case…",       icon: "📋", pct: 56 },
  { label: "Briefing the clinical team…",     icon: "👨‍⚕️", pct: 72 },
  { label: "Preparing the ward…",             icon: "🏥", pct: 86 },
  { label: "Almost ready…",                   icon: "✨", pct: 94 },
]

function InitProgressOverlay({ progress }: { progress: number }) {
  const stepIndex = INIT_STEPS.findLastIndex((s) => progress >= s.pct) ?? 0
  const step = INIT_STEPS[Math.max(0, stepIndex)]

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex flex-col items-center justify-center gap-8 py-10"
    >
      {/* Pulsing icon */}
      <motion.div
        animate={{ scale: [1, 1.15, 1], rotate: [0, 5, -5, 0] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        className="text-6xl select-none"
      >
        {step.icon}
      </motion.div>

      {/* Step label */}
      <AnimatePresence mode="wait">
        <motion.p
          key={step.label}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.4 }}
          className="text-lg font-semibold text-purple-200 text-center"
        >
          {step.label}
        </motion.p>
      </AnimatePresence>

      {/* Progress bar */}
      <div className="w-full max-w-sm">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Initializing…</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="h-3 bg-black/40 rounded-full overflow-hidden border border-purple-700/30">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-purple-600 via-purple-400 to-blue-500"
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          />
        </div>
        {/* Shimmer overlay */}
        <div className="relative -mt-3 h-3 overflow-hidden rounded-full pointer-events-none">
          <motion.div
            className="absolute top-0 h-full w-12 bg-gradient-to-r from-transparent via-white/25 to-transparent"
            animate={{ x: ["-3rem", "24rem"] }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          />
        </div>
      </div>

      {/* Step dots */}
      <div className="flex gap-2">
        {INIT_STEPS.map((s, i) => (
          <motion.div
            key={i}
            animate={{
              scale: i === stepIndex ? 1.4 : 1,
              backgroundColor: i <= stepIndex ? "rgb(139,92,246)" : "rgb(55,65,81)",
            }}
            transition={{ duration: 0.3 }}
            className="w-2 h-2 rounded-full"
          />
        ))}
      </div>

      <p className="text-xs text-gray-500 text-center">
        This takes about 2–3 minutes — the AI is building a full world for you.
      </p>
    </motion.div>
  )
}

export default function DemoPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const progressRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [hasApiSettings, setHasApiSettings] = useState(false)
  const [savedApiSettings, setSavedApiSettings] = useState<{
    provider?: string
    modelName?: string
    apiKey?: string
  } | null>(null)
  const [gameSettings, setGameSettings] = useState<GameSettings | null>(null)
  const [formData, setFormData] = useState<Record<string, string>>({
    profession: "",
    clinical_setting: "",
    era: "",
    natural_conditions: "",
    nation_type: "",
    economic_advantage: "",
    model_name: "",
    api_key: "",
    provider: "google",
  })
  const [useRandomConfig, setUseRandomConfig] = useState(false)

  // Animate progress bar while loading
  useEffect(() => {
    if (loading) {
      setProgress(2)
      // Advance ~0.5% per second, slowing near 94% ceiling
      progressRef.current = setInterval(() => {
        setProgress((p) => {
          if (p >= 94) return p
          const gap = 94 - p
          return p + Math.max(0.1, gap * 0.003)
        })
      }, 500)
    } else {
      if (progressRef.current) clearInterval(progressRef.current)
      setProgress(0)
    }
    return () => {
      if (progressRef.current) clearInterval(progressRef.current)
    }
  }, [loading])

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null
    setIsLoggedIn(!!token)
    if (token) {
      fetch("/api/user/stats", { headers: { Authorization: `Bearer ${token}` } })
        .then((r) => r.json())
        .then((data) => {
          if (data.success && data.user?.profession) {
            setFormData((prev) => ({ ...prev, profession: data.user.profession }))
          }
        })
        .catch(() => {})
      fetch("/api/user/settings", { headers: { Authorization: `Bearer ${token}` } })
        .then((r) => r.json())
        .then((data) => {
          const s = data.settings || {}
          const has = !!(s.provider || s.modelName || s.apiKey)
          setHasApiSettings(has)
          if (has) setSavedApiSettings(s)
        })
        .catch(() => {})
    } else {
      try {
        const stored =
          typeof window !== "undefined"
            ? localStorage.getItem("apiSettings") || localStorage.getItem("api_settings")
            : null
        if (stored) {
          const parsed = JSON.parse(stored)
          const has = !!(parsed?.provider || parsed?.modelName || parsed?.apiKey)
          setHasApiSettings(has)
          if (has) setSavedApiSettings(parsed)
        }
      } catch {
        setHasApiSettings(false)
      }
    }
  }, [])

  useEffect(() => {
    fetch("/api/game/settings")
      .then((r) => r.json())
      .then((data) => {
        if (data.success && data.settings) setGameSettings(data.settings)
      })
      .catch(() => {})
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("token") : null
      const userStr = typeof window !== "undefined" ? localStorage.getItem("user") : null
      const user = userStr ? JSON.parse(userStr) : null

      const gameConfig: Record<string, unknown> = { total_cases: 6, max_clinical_changes: 6 }
      if (!useRandomConfig) {
        if (formData.profession) gameConfig.profession = formData.profession
        if (formData.clinical_setting) gameConfig.clinical_setting = formData.clinical_setting
        if (formData.era) gameConfig.era = formData.era
        if (formData.natural_conditions) gameConfig.natural_conditions = formData.natural_conditions
        if (formData.nation_type) gameConfig.nation_type = formData.nation_type
        if (formData.economic_advantage) gameConfig.economic_advantage = formData.economic_advantage
      }

      const apiConfig =
        hasApiSettings && savedApiSettings
          ? {
              model_name: savedApiSettings.modelName || undefined,
              api_key: savedApiSettings.apiKey || undefined,
              provider: savedApiSettings.provider || "google",
            }
          : {
              model_name: formData.model_name || undefined,
              api_key: formData.api_key || undefined,
              provider: formData.provider,
            }

      const body: Record<string, unknown> = {
        game_config: gameConfig,
        is_demo: !isLoggedIn,
        ...apiConfig,
      }
      if (isLoggedIn && user?.id) body.user_id = user.id

      const headers: Record<string, string> = { "Content-Type": "application/json" }
      if (token) headers["Authorization"] = `Bearer ${token}`

      const response = await fetch("/api/game/initialize", {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || "Failed to initialize game")
      }

      const data = await response.json()

      // Flash to 100% before navigating
      setProgress(100)

      // Cache full init payload so mediquest skips the re-fetch
      if (typeof window !== "undefined" && data.game_state?.game_id) {
        sessionStorage.setItem(`game_init_${data.game_state.game_id}`, JSON.stringify(data))
      }

      router.push(`/mediquest?game_id=${data.game_state.game_id}`)
    } catch (error: unknown) {
      toast({
        title: "Error",
        description:
          error instanceof Error ? error.message : "Failed to start game. Please try again.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const renderField = (key: string, field: GameSettingsField) => (
    <div key={key} className="space-y-2">
      <Label>{field.label} (Optional)</Label>
      <Select
        value={formData[key] || ""}
        onValueChange={(value) => setFormData((prev) => ({ ...prev, [key]: value }))}
        disabled={useRandomConfig}
      >
        <SelectTrigger className="bg-black/50 border-purple-700/40">
          <SelectValue placeholder="Select or leave empty for random" />
        </SelectTrigger>
        <SelectContent>
          {field.values.map((v) => (
            <SelectItem key={v} value={v}>
              {v}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )

  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-[#0A1128] to-[#4C1D95] text-white py-12 relative overflow-hidden">
      <div className="container mx-auto px-4 max-w-2xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <div className="text-center mb-8 relative z-10">
            <motion.div
              className="inline-block mb-4"
              animate={{ rotate: [0, 360], scale: [1, 1.2, 1] }}
              transition={{
                rotate: { duration: 4, repeat: Infinity, ease: "linear" },
                scale: { duration: 2, repeat: Infinity, ease: "easeInOut" },
              }}
            >
              <Sparkles className="h-16 w-16 text-purple-400" />
            </motion.div>
            <motion.h1
              className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-purple-400 via-purple-300 to-blue-400 bg-clip-text text-transparent"
              animate={{ backgroundPosition: ["0%", "100%", "0%"], scale: [1, 1.02, 1] }}
              transition={{
                backgroundPosition: { duration: 5, repeat: Infinity, ease: "linear" },
                scale: { duration: 3, repeat: Infinity, ease: "easeInOut" },
              }}
              style={{ backgroundSize: "200% auto" }}
            >
              {isLoggedIn ? "Mediquest" : "Try Stud Demo"}
            </motion.h1>
            <p className="text-gray-300 text-lg">
              {isLoggedIn
                ? "Configure your game or use random settings"
                : "Experience 1 test game with 6 clinical scenarios and 6 dynamic changes each"}
            </p>
          </div>

          <Card className="bg-black/60 backdrop-blur-md border-purple-700/40 relative z-10">
            <CardHeader>
              <CardTitle className="text-2xl">
                {loading ? "Building Your World" : isLoggedIn ? "Game Configuration" : "Demo Configuration"}
              </CardTitle>
              {!loading && (
                <CardDescription className="text-gray-400">
                  {isLoggedIn
                    ? "Select values for each setting or use random. All fields are optional."
                    : "Configure your demo experience. Leave fields empty for random selection."}
                </CardDescription>
              )}
            </CardHeader>
            <CardContent>
              <AnimatePresence mode="wait">
                {loading ? (
                  <InitProgressOverlay key="progress" progress={progress} />
                ) : (
                  <motion.form
                    key="form"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onSubmit={handleSubmit}
                    className="space-y-6"
                  >
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="useRandom"
                        checked={useRandomConfig}
                        onCheckedChange={(c) => setUseRandomConfig(!!c)}
                        className="border-purple-700"
                      />
                      <Label htmlFor="useRandom" className="text-sm font-normal cursor-pointer">
                        Use random config (bypass all selections)
                      </Label>
                    </div>

                    {gameSettings && !useRandomConfig && (
                      <div className="space-y-4">
                        <h3 className="text-sm font-semibold text-purple-300">Game Settings</h3>
                        <div className="grid gap-4">
                          {gameSettings.profession && renderField("profession", gameSettings.profession)}
                          {gameSettings.clinical_setting && renderField("clinical_setting", gameSettings.clinical_setting)}
                          {gameSettings.era && renderField("era", gameSettings.era)}
                          {gameSettings.natural_conditions && renderField("natural_conditions", gameSettings.natural_conditions)}
                          {gameSettings.nation_type && renderField("nation_type", gameSettings.nation_type)}
                          {gameSettings.economic_advantage && renderField("economic_advantage", gameSettings.economic_advantage)}
                        </div>
                      </div>
                    )}

                    {!hasApiSettings && (
                      <motion.div
                        className="bg-purple-900/30 border border-purple-700/40 rounded-lg p-4 space-y-4"
                        animate={{
                          borderColor: [
                            "rgba(139,92,246,0.4)",
                            "rgba(139,92,246,0.6)",
                            "rgba(139,92,246,0.4)",
                          ],
                        }}
                        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                      >
                        <div className="flex items-start gap-2">
                          <AlertCircle className="h-5 w-5 text-purple-400 mt-0.5 shrink-0" />
                          <div className="flex-1">
                            <p className="text-sm font-semibold text-purple-300 mb-1">
                              Optional: Use Your Own API Key
                            </p>
                            <p className="text-xs text-gray-400">
                              Provide your own API key. Leave empty to use platform defaults.
                            </p>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="provider">Model Provider</Label>
                          <Select
                            value={formData.provider}
                            onValueChange={(value) =>
                              setFormData((prev) => ({ ...prev, provider: value }))
                            }
                          >
                            <SelectTrigger className="bg-black/50 border-purple-700/40">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="google">Google (Gemini)</SelectItem>
                              <SelectItem value="openai">OpenAI (ChatGPT)</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="model_name">Model Name (Optional)</Label>
                          <Input
                            id="model_name"
                            placeholder="e.g., gemini-2.0-flash-exp or gpt-4"
                            value={formData.model_name}
                            onChange={(e) =>
                              setFormData((prev) => ({ ...prev, model_name: e.target.value }))
                            }
                            className="bg-black/50 border-purple-700/40"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="api_key">API Key (Optional)</Label>
                          <Input
                            id="api_key"
                            type="password"
                            placeholder="Your API key (not saved)"
                            value={formData.api_key}
                            onChange={(e) =>
                              setFormData((prev) => ({ ...prev, api_key: e.target.value }))
                            }
                            className="bg-black/50 border-purple-700/40"
                          />
                        </div>
                      </motion.div>
                    )}

                    <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} className="w-full">
                      <Button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-gradient-to-r from-purple-700 to-purple-900 hover:from-purple-800 hover:to-purple-950 text-white text-lg py-6 relative overflow-hidden"
                      >
                        <motion.div
                          className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
                          animate={{ x: ["-100%", "100%"] }}
                          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                        />
                        <span className="relative z-10">
                          {isLoggedIn ? "Start Game" : "Start Demo Game"}
                        </span>
                        <motion.span
                          className="inline-block ml-2 relative z-10"
                          animate={{ x: [0, 5, 0] }}
                          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                        >
                          <ArrowRight className="h-4 w-4 inline" />
                        </motion.span>
                      </Button>
                    </motion.div>
                  </motion.form>
                )}
              </AnimatePresence>

              {!loading && !isLoggedIn && (
                <div className="mt-6 text-center">
                  <p className="text-sm text-gray-400">
                    After this demo,{" "}
                    <a href="/auth/register" className="text-purple-400 hover:text-purple-300 underline">
                      register for full access
                    </a>
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}
