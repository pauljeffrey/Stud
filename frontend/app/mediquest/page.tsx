"use client"

import { Suspense, useState, useEffect, useRef } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { Button } from "@/app/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Textarea } from "@/app/components/ui/textarea"
import { Badge } from "@/app/components/ui/badge"
import { Input } from "@/app/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/app/components/ui/select"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/app/components/ui/collapsible"
import {
  Clock,
  MessageCircle,
  Send,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  Users,
  Loader2,
  CheckCircle2,
  X,
  Activity,
  Stethoscope,
} from "lucide-react"
import { useToast } from "@/app/components/ui/use-toast"
import { motion, AnimatePresence } from "framer-motion"

import {
  type GameState,
  mergeBackendFromResponse,
  mergeInitToBackend,
  normalizeFromInitResponse,
  normalizeGameState,
  readApiError,
  readSseStream,
  toBackendPayload,
} from "@/app/lib/game-state"

export default function MediquestPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-black flex items-center justify-center text-gray-300">
          Loading…
        </div>
      }
    >
      <MediquestPageContent />
    </Suspense>
  )
}

function MediquestPageContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const { toast } = useToast()
  const gameId = searchParams.get("game_id")

  const [gameState, setGameState] = useState<GameState | null>(null)
  const [loading, setLoading] = useState(true)
  const [timeRemaining, setTimeRemaining] = useState(0)
  const [userAnswer, setUserAnswer] = useState("")
  const [selectedOption, setSelectedOption] = useState("")
  const [showAnswer, setShowAnswer] = useState(false)
  const [showClue, setShowClue] = useState(false)
  const [showReason, setShowReason] = useState(false)
  const [selectedNpc, setSelectedNpc] = useState<string | null>(null)
  const [gameMasterMessage, setGameMasterMessage] = useState("")
  const [npcMessage, setNpcMessage] = useState("")
  const [isGameMasterStreaming, setIsGameMasterStreaming] = useState(false)
  const [npcChatHistory, setNpcChatHistory] = useState<
    Record<string, Array<{ role: string; content: string }>>
  >({})
  const [worldOpen, setWorldOpen] = useState(true)
  const [examOpen, setExamOpen] = useState(false)
  const [investOpen, setInvestOpen] = useState(false)
  const [scenarioOpen, setScenarioOpen] = useState(false)
  const [showIntro, setShowIntro] = useState(false)
  const backendStateRef = useRef<Record<string, unknown>>({})
  const timeRemainingRef = useRef(0)
  const timeUpHandledRef = useRef(false)
  const introDismissedRef = useRef(false)
  const [modelConfig, setModelConfig] = useState({
    model_name: "",
    api_key: "",
    provider: "google"
  })

  useEffect(() => {
    const loadApiConfig = () => {
      const token = typeof window !== "undefined" ? localStorage.getItem("token") : null
      if (token) {
        fetch("/api/user/settings", { headers: { Authorization: `Bearer ${token}` } })
          .then((r) => r.json())
          .then((data) => {
            const s = data.settings || {}
            if (s.provider || s.modelName || s.apiKey) {
              setModelConfig({
                provider: s.provider || "google",
                model_name: s.modelName || "",
                api_key: s.apiKey || "",
              })
            }
          })
          .catch(() => {})
      } else {
        try {
          const stored = localStorage.getItem("apiSettings") || localStorage.getItem("api_settings")
          if (stored) {
            const s = JSON.parse(stored)
            if (s?.provider || s?.modelName || s?.apiKey) {
              setModelConfig({
                provider: s.provider || "google",
                model_name: s.modelName || "",
                api_key: s.apiKey || "",
              })
            }
          }
        } catch {
          // ignore
        }
      }
    }
    loadApiConfig()
  }, [])

  const gameMasterChatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    gameMasterChatEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [gameState?.game_master_chat_history, isGameMasterStreaming])

  useEffect(() => {
    if (gameId) {
      loadGameState()
    } else {
      router.push("/demo")
    }
  }, [gameId])

  const caseKey = gameState
    ? `${gameState.game_id}:${gameState.case_state.case_state_id}`
    : null

  useEffect(() => {
    if (!caseKey || !gameState) return
    const initial = gameState.case_state.time_remaining_seconds
    timeRemainingRef.current = initial
    setTimeRemaining(initial)
    timeUpHandledRef.current = false

    const timer = setInterval(() => {
      if (timeRemainingRef.current <= 0) return
      timeRemainingRef.current -= 1
      setTimeRemaining(timeRemainingRef.current)
      if (timeRemainingRef.current <= 0 && !timeUpHandledRef.current) {
        timeUpHandledRef.current = true
        toast({
          title: "Time's Up!",
          description: "Please submit your answer",
          variant: "destructive",
        })
      }
    }, 1000)

    return () => clearInterval(timer)
  }, [caseKey, toast])

  const syncFromResponse = (raw: Record<string, unknown>, prev: GameState | null) => {
    backendStateRef.current = mergeBackendFromResponse(backendStateRef.current, raw)
    const next = normalizeGameState(raw, undefined, prev)
    if (typeof raw.case_state === "object" && raw.case_state) {
      const cs = raw.case_state as Record<string, unknown>
      if (cs.time_remaining_seconds != null) {
        timeRemainingRef.current = Number(cs.time_remaining_seconds)
        setTimeRemaining(timeRemainingRef.current)
      }
    }
    return next
  }

  const gamePayload = () =>
    gameState ? toBackendPayload(backendStateRef.current, gameState) : null

  const apiModelFields = () => {
    const fields: Record<string, string> = { provider: modelConfig.provider }
    if (modelConfig.model_name) fields.model_name = modelConfig.model_name
    if (modelConfig.api_key) fields.api_key = modelConfig.api_key
    return fields
  }

  useEffect(() => {
    if (!caseKey) return
    introDismissedRef.current = false
    setShowIntro(true)
    setScenarioOpen(false)
  }, [caseKey])

  const dismissIntro = () => {
    if (introDismissedRef.current) return
    introDismissedRef.current = true
    setShowIntro(false)
    setScenarioOpen(true)
  }

  const loadGameState = async () => {
    try {
      // Use cached init payload from demo page (avoids extra round-trip)
      if (typeof window !== "undefined") {
        const cached = sessionStorage.getItem(`game_init_${gameId}`)
        if (cached) {
          const data = JSON.parse(cached)
          backendStateRef.current = mergeInitToBackend(data)
          setGameState(normalizeFromInitResponse(data))
          setLoading(false)
          return
        }
      }

      const response = await fetch(`/api/game/${gameId}`)
      if (!response.ok) throw new Error("Failed to load game")
      const data = await response.json()
      backendStateRef.current = (data.game_state ?? {}) as Record<string, unknown>
      setGameState(normalizeGameState(data.game_state))
      setLoading(false)
    } catch (error) {
      setLoading(false)
      toast({
        title: "Error",
        description: "Failed to load game state",
        variant: "destructive"
      })
      router.push("/demo")
    }
  }

  const handleUseClue = async () => {
    if (!gameState) return
    const payload = gamePayload()
    if (!payload) return

    try {
      const response = await fetch("/api/game/use-clue", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          game_state: payload,
          ...apiModelFields()
        })
      })

      if (!response.ok) throw new Error(await readApiError(response))

      const data = await response.json()
      setGameState((prev) => syncFromResponse(data.game_state, prev))
      setShowClue(true)

      toast({
        title: "Clue Used",
        description: "Penalty applied. Case difficulty increased.",
        variant: "destructive"
      })
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to use clue",
        variant: "destructive"
      })
    }
  }

  const handleSubmitAnswer = async () => {
    if (!gameState) return
    const payload = gamePayload()
    if (!payload) return

    const answer = selectedOption || userAnswer
    if (!answer) {
      toast({
        title: "Error",
        description: "Please provide an answer",
        variant: "destructive"
      })
      return
    }

    try {
      const timeTaken = gameState.case_state.time_limit_seconds - timeRemaining
      const response = await fetch("/api/game/submit-answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          game_state: payload,
          answer,
          time_taken: timeTaken,
          ...apiModelFields()
        })
      })

      if (!response.ok) throw new Error(await readApiError(response))

      const data = await response.json()
      setGameState((prev) => syncFromResponse(data.game_state, prev))
      setShowAnswer(true)
      setShowReason(true)

      toast({
        title: `Score: ${data.performance.score}/10`,
        description: data.performance.analysis,
      })
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to submit answer",
        variant: "destructive"
      })
    }
  }

  const handleGameMasterChat = async () => {
    if (!gameState || !gameMasterMessage.trim() || isGameMasterStreaming) return
    const payload = gamePayload()
    if (!payload) return

    const userMessage = gameMasterMessage
    setGameMasterMessage("")
    setIsGameMasterStreaming(true)
    setGameState((prev) =>
      prev
        ? {
            ...prev,
            game_master_chat_history: [
              ...(prev.game_master_chat_history ?? []),
              { role: "user", content: userMessage },
            ],
          }
        : prev
    )

    try {
      const response = await fetch("/api/game/master-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          game_state: payload,
          user_message: userMessage,
          ...apiModelFields()
        })
      })

      if (!response.ok) throw new Error(await readApiError(response))

      let accumulatedResponse = ""
      await readSseStream(response, (data) => {
        if (data.error) throw new Error(String(data.error))
        if (typeof data.content === "string") {
          accumulatedResponse += data.content
        }

        setGameState((prev) => {
          if (!prev) return prev
          const newHistory = [...(prev.game_master_chat_history ?? [])]
          if (newHistory[newHistory.length - 1]?.role !== "assistant") {
            newHistory.push({ role: "assistant", content: accumulatedResponse })
          } else {
            newHistory[newHistory.length - 1].content = accumulatedResponse
          }
          return { ...prev, game_master_chat_history: newHistory }
        })

        if (data.complete && data.updated_game_state) {
          setGameState((prev) =>
            syncFromResponse(data.updated_game_state as Record<string, unknown>, prev)
          )
        }
      })
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to send message",
        variant: "destructive"
      })
    } finally {
      setIsGameMasterStreaming(false)
    }
  }

  const handleNPCChat = async () => {
    if (!gameState || !selectedNpc || !npcMessage.trim()) return
    const payload = gamePayload()
    if (!payload) return

    const userMessage = npcMessage
    setNpcMessage("")
    setNpcChatHistory((prev) => ({
      ...prev,
      [selectedNpc]: [...(prev[selectedNpc] ?? []), { role: "user", content: userMessage }],
    }))

    try {
      const npc = gameState.npc_states.find(n => n.npc_id === selectedNpc)
      if (!npc) return

      const response = await fetch("/api/game/npc-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          game_state: payload,
          npc_id: selectedNpc,
          user_message: userMessage,
          chat_history: npcChatHistory[selectedNpc] ?? [],
          ...apiModelFields()
        })
      })

      if (!response.ok) throw new Error(await readApiError(response))

      let accumulatedResponse = ""
      await readSseStream(response, (data) => {
        if (data.error) throw new Error(String(data.error))
        if (typeof data.content === "string") {
          accumulatedResponse += data.content
        }
        setNpcChatHistory((prev) => {
          const history = [...(prev[selectedNpc] ?? [])]
          if (history[history.length - 1]?.role !== "assistant") {
            history.push({ role: "assistant", content: accumulatedResponse })
          } else {
            history[history.length - 1].content = accumulatedResponse
          }
          return { ...prev, [selectedNpc]: history }
        })
      })
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to send message",
        variant: "destructive"
      })
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-black via-[#0A1128] to-[#4C1D95] flex items-center justify-center">
        <Loader2 className="h-12 w-12 animate-spin text-purple-400" />
      </div>
    )
  }

  if (!gameState) {
    return null
  }

  const panelClass =
    "flex flex-col rounded-lg border border-purple-700/40 bg-black/60 backdrop-blur-md overflow-hidden min-h-0"
  const examData = gameState.case_state.examination_findings ?? {}
  const vitals =
    (examData.vitals as Record<string, unknown>) ??
    (examData.Vitals as Record<string, unknown>) ??
    null

  return (
    <div className="h-screen overflow-hidden bg-gradient-to-b from-black via-[#0A1128] to-[#4C1D95] text-white p-2 relative">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          className="absolute top-0 left-0 w-72 h-72 bg-purple-900/20 rounded-full blur-3xl"
          animate={{ x: [0, 40, 0], y: [0, 20, 0], scale: [1, 1.15, 1] }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute bottom-0 right-0 w-96 h-96 bg-blue-900/20 rounded-full blur-3xl"
          animate={{ x: [0, -40, 0], y: [0, -20, 0], scale: [1, 1.2, 1] }}
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>

      <AnimatePresence>
        {showIntro && (
          <motion.div
            key="scenario-intro"
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <motion.div
              className="absolute inset-0 bg-black/85"
              initial={{ opacity: 1 }}
              animate={{ opacity: 0 }}
              transition={{ duration: 60, ease: "linear" }}
              onAnimationComplete={() => {
                if (!introDismissedRef.current) dismissIntro()
              }}
            />
            <motion.div
              initial={{ scale: 0.95, y: 12, opacity: 0 }}
              animate={{ scale: 1, y: 0, opacity: 1 }}
              className="relative max-w-2xl w-full rounded-xl border border-purple-500/50 bg-gradient-to-br from-purple-950/95 to-black/95 p-6 shadow-2xl"
            >
              <Button
                size="icon"
                variant="ghost"
                className="absolute top-2 right-2 text-gray-300 hover:text-white"
                onClick={dismissIntro}
              >
                <X className="h-4 w-4" />
              </Button>
              <Badge className="mb-3 bg-purple-700">Mission Briefing</Badge>
              <h2 className="text-xl font-semibold mb-2">Enter the World</h2>
              <p className="text-sm text-gray-300 mb-4">{gameState.game_world.world_description}</p>
              <h3 className="text-sm font-medium text-purple-300 mb-1">Clinical Scenario</h3>
              <p className="text-sm leading-relaxed">
                {gameState.case_state.clinical_case_scenario_description}
              </p>
              <p className="text-xs text-gray-500 mt-4">Auto-continuing in 60 seconds…</p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="relative z-10 h-full flex flex-col gap-2">
        <motion.div
          className="flex items-center justify-between rounded-lg border border-purple-700/40 bg-black/60 px-3 py-2 backdrop-blur-md shrink-0"
          animate={{ boxShadow: ["0 0 0 rgba(168,85,247,0)", "0 0 20px rgba(168,85,247,0.15)", "0 0 0 rgba(168,85,247,0)"] }}
          transition={{ duration: 3, repeat: Infinity }}
        >
          <div className="flex items-center gap-2">
            <Badge className="bg-purple-800 text-xs">
              Case {gameState.current_case_number}/{gameState.total_cases}
            </Badge>
            {gameState.game_world.hospital_name && (
              <span className="text-xs text-purple-200 hidden sm:inline">
                {gameState.game_world.hospital_name}
              </span>
            )}
          </div>
          <motion.div
            className="flex items-center gap-2 text-purple-300"
            animate={timeRemaining <= 30 ? { scale: [1, 1.08, 1] } : {}}
            transition={{ duration: 1, repeat: timeRemaining <= 30 ? Infinity : 0 }}
          >
            <Clock className="h-4 w-4" />
            <span className="font-mono text-lg">{formatTime(timeRemaining)}</span>
          </motion.div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-2 flex-1 min-h-0">
          {/* Section 1 — World & clinical data */}
          <section className="flex flex-col gap-1.5 min-h-0 h-full">
            <Collapsible open={worldOpen} onOpenChange={setWorldOpen} className={panelClass}>
              <CollapsibleTrigger className="flex items-center justify-between px-3 py-2 text-sm font-medium hover:bg-purple-900/20">
                <span className="flex items-center gap-2"><Activity className="h-4 w-4 text-purple-400" />World</span>
                {worldOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </CollapsibleTrigger>
              <CollapsibleContent className="px-3 pb-2 text-xs text-gray-300 overflow-y-auto max-h-28">
                {gameState.game_world.world_description}
              </CollapsibleContent>
            </Collapsible>

            <Collapsible open={examOpen} onOpenChange={setExamOpen} className={`${panelClass} flex-1`}>
              <CollapsibleTrigger className="flex items-center justify-between px-3 py-2 text-sm font-medium hover:bg-purple-900/20">
                <span className="flex items-center gap-2"><Stethoscope className="h-4 w-4 text-purple-400" />Examination</span>
                {examOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </CollapsibleTrigger>
              <CollapsibleContent className="px-3 pb-2 overflow-y-auto flex-1 min-h-0">
                <pre className="text-[10px] text-gray-400 whitespace-pre-wrap">
                  {JSON.stringify(examData, null, 2)}
                </pre>
              </CollapsibleContent>
            </Collapsible>

            <Collapsible open={investOpen} onOpenChange={setInvestOpen} className={`${panelClass} flex-1`}>
              <CollapsibleTrigger className="flex items-center justify-between px-3 py-2 text-sm font-medium hover:bg-purple-900/20">
                <span className="flex items-center gap-2"><Activity className="h-4 w-4 text-blue-400" />Vitals & Labs</span>
                {investOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </CollapsibleTrigger>
              <CollapsibleContent className="px-3 pb-2 overflow-y-auto flex-1 min-h-0 space-y-2">
                {vitals && (
                  <pre className="text-[10px] text-amber-200/90 whitespace-pre-wrap">
                    {JSON.stringify(vitals, null, 2)}
                  </pre>
                )}
                <pre className="text-[10px] text-gray-400 whitespace-pre-wrap">
                  {JSON.stringify(gameState.case_state.investigation_results, null, 2)}
                </pre>
              </CollapsibleContent>
            </Collapsible>
          </section>

          {/* Section 2 — Scenario, question, actions, NPC */}
          <section className="flex flex-col gap-1.5 min-h-0 h-full">
            {!showIntro && (
              <Collapsible open={scenarioOpen} onOpenChange={setScenarioOpen} className={panelClass}>
                <CollapsibleTrigger className="flex items-center justify-between px-3 py-2 text-sm font-medium hover:bg-purple-900/20">
                  <span>Clinical Scenario</span>
                  {scenarioOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </CollapsibleTrigger>
                <CollapsibleContent className="px-3 pb-2 text-xs overflow-y-auto max-h-20">
                  {gameState.case_state.clinical_case_scenario_description}
                </CollapsibleContent>
              </Collapsible>
            )}

            <Card className={`${panelClass} shrink-0`}>
              <CardHeader className="py-2 px-3">
                <CardTitle className="text-sm">Question</CardTitle>
              </CardHeader>
              <CardContent className="px-3 pb-3 space-y-2">
                <p className="text-sm font-medium">{gameState.case_state.question}</p>
                {gameState.case_state.options ? (
                  <div className="grid gap-1">
                    {gameState.case_state.options.map((option, idx) => (
                      <Button
                        key={idx}
                        size="sm"
                        variant={selectedOption === option ? "default" : "outline"}
                        className="h-8 justify-start text-left text-xs bg-black/50 border-purple-700/40"
                        onClick={() => setSelectedOption(option)}
                      >
                        {String.fromCharCode(65 + idx)}. {option}
                      </Button>
                    ))}
                  </div>
                ) : (
                  <Textarea
                    placeholder="Your answer…"
                    value={userAnswer}
                    onChange={(e) => setUserAnswer(e.target.value)}
                    className="bg-black/50 border-purple-700/40 min-h-[72px] text-sm"
                  />
                )}
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={handleUseClue}
                    disabled={showClue || gameState.case_state.clue_used}
                    variant="outline"
                    className="flex-1 h-8 text-xs border-purple-700/40"
                  >
                    <Lightbulb className="h-3 w-3 mr-1" />
                    {gameState.case_state.clue_used ? "Clue Used" : "Use Clue"}
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleSubmitAnswer}
                    className="flex-1 h-8 text-xs bg-purple-700 hover:bg-purple-800"
                  >
                    Submit
                  </Button>
                </div>
                {showClue && gameState.case_state.clue && (
                  <p className="text-xs text-purple-200 border border-purple-600/40 rounded p-2">
                    <strong>Clue:</strong> {gameState.case_state.clue}
                  </p>
                )}
                {showAnswer && gameState.case_state.answer && (
                  <p className="text-xs text-green-200 border border-green-600/40 rounded p-2">
                    <CheckCircle2 className="h-3 w-3 inline mr-1" />
                    {gameState.case_state.answer}
                  </p>
                )}
                {showReason && gameState.case_state.reason_for_answer && (
                  <p className="text-xs text-blue-200 border border-blue-600/40 rounded p-2">
                    {gameState.case_state.reason_for_answer}
                  </p>
                )}
              </CardContent>
            </Card>

            <Card className={`${panelClass} flex-1`}>
              <CardHeader className="py-2 px-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Users className="h-4 w-4" /> NPC Chat
                </CardTitle>
              </CardHeader>
              <CardContent className="px-3 pb-3 flex flex-col flex-1 min-h-0 gap-2">
                <Select value={selectedNpc || ""} onValueChange={setSelectedNpc}>
                  <SelectTrigger className="h-8 bg-black/50 border-purple-700/40 text-xs">
                    <SelectValue placeholder="Select NPC" />
                  </SelectTrigger>
                  <SelectContent>
                    {gameState.npc_states.map((npc) => (
                      <SelectItem key={npc.npc_id} value={npc.npc_id}>
                        {npc.name} ({npc.role})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <div className="flex-1 min-h-0 overflow-y-auto rounded bg-black/30 p-2 space-y-1">
                  {selectedNpc ? (
                    (npcChatHistory[selectedNpc] ?? []).map((msg, idx) => (
                      <div
                        key={idx}
                        className={`text-xs p-1.5 rounded ${
                          msg.role === "user" ? "bg-purple-700/30 ml-2" : "bg-blue-800/30 mr-2"
                        }`}
                      >
                        {msg.content}
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-gray-500">Select an NPC to chat</p>
                  )}
                </div>
                <div className="flex gap-1 shrink-0">
                  <Input
                    value={npcMessage}
                    onChange={(e) => setNpcMessage(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleNPCChat()}
                    placeholder="Ask NPC…"
                    disabled={!selectedNpc}
                    className="h-8 text-xs bg-black/50 border-purple-700/40"
                  />
                  <Button size="icon" className="h-8 w-8 shrink-0" onClick={handleNPCChat} disabled={!selectedNpc}>
                    <Send className="h-3 w-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </section>

          {/* Section 3 — Game Master */}
          <section className="flex flex-col min-h-0 h-full">
            <Card className={`${panelClass} h-full`}>
              <CardHeader className="py-2 px-3 shrink-0">
                <CardTitle className="text-sm flex items-center gap-2">
                  <MessageCircle className="h-4 w-4" /> Game Master
                </CardTitle>
              </CardHeader>
              <CardContent className="px-3 pb-3 flex flex-col flex-1 min-h-0 gap-2">
                <div className="flex-1 min-h-0 overflow-y-auto space-y-1 rounded bg-black/30 p-2">
                  {(gameState.game_master_chat_history ?? []).map((msg, idx) => (
                    <div
                      key={idx}
                      className={`text-xs p-1.5 rounded whitespace-pre-wrap ${
                        msg.role === "user" ? "bg-purple-700/30 ml-2" : "bg-blue-800/30 mr-2"
                      }`}
                    >
                      {msg.content}
                    </div>
                  ))}
                  {isGameMasterStreaming &&
                    (gameState.game_master_chat_history ?? []).slice(-1)[0]?.role !== "assistant" && (
                      <p className="text-xs text-gray-400 flex items-center gap-1">
                        <Loader2 className="h-3 w-3 animate-spin" /> Thinking…
                      </p>
                    )}
                  <div ref={gameMasterChatEndRef} />
                </div>
                <div className="flex gap-1 shrink-0">
                  <Input
                    value={gameMasterMessage}
                    onChange={(e) => setGameMasterMessage(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && !isGameMasterStreaming && handleGameMasterChat()}
                    placeholder={isGameMasterStreaming ? "Responding…" : "Ask Game Master…"}
                    disabled={isGameMasterStreaming}
                    className="h-8 text-xs bg-black/50 border-purple-700/40"
                  />
                  <Button
                    size="icon"
                    className="h-8 w-8 shrink-0"
                    onClick={handleGameMasterChat}
                    disabled={isGameMasterStreaming}
                  >
                    {isGameMasterStreaming ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <Send className="h-3 w-3" />
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </section>
        </div>
      </div>
    </div>
  )
}

