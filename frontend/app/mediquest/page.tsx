"use client"

import { Suspense, useState, useEffect, useRef } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { Button } from "@/app/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Textarea } from "@/app/components/ui/textarea"
import { Badge } from "@/app/components/ui/badge"
import { Input } from "@/app/components/ui/input"
import { Label } from "@/app/components/ui/label"
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
  Eye,
  EyeOff,
  Users,
  Loader2,
  Trophy,
  AlertCircle,
  CheckCircle2,
  XCircle,
} from "lucide-react"
import { useToast } from "@/app/components/ui/use-toast"
import { motion, AnimatePresence } from "framer-motion"

interface GameState {
  game_id: string
  user_id: string
  game_world: {
    world_description: string
    hospital_name?: string
    department?: string
  }
  case_state: {
    case_state_id: string
    clinical_case_scenario_description: string
    question: string
    diagnosis?: string
    examination_findings: Record<string, any>
    investigation_results: Record<string, any>
    options?: string[]
    answer?: string
    reason_for_answer?: string
    clue?: string
    time_limit_seconds: number
    time_remaining_seconds: number
    n_changes: number
    max_clinical_changes: number
    clue_used: boolean
  }
  npc_states: Array<{
    npc_id: string
    name: string
    role: string
    personality_description: string
  }>
  current_case_number: number
  total_cases: number
  user_performance: Array<{
    score: number
    analysis: string
    strengths: string[]
    weaknesses: string[]
  }>
  achievements: Array<{
    type: string
    title: string
    description: string
  }>
  game_master_chat_history: Array<{ role: string; content: string }>
}

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
  const [showInvestigations, setShowInvestigations] = useState(false)
  const [showExamination, setShowExamination] = useState(false)
  const [gameMasterChatOpen, setGameMasterChatOpen] = useState(false)
  const [npcChatOpen, setNpcChatOpen] = useState(false)
  const [selectedNpc, setSelectedNpc] = useState<string | null>(null)
  const [gameMasterMessage, setGameMasterMessage] = useState("")
  const [npcMessage, setNpcMessage] = useState("")
  const [chatPosition, setChatPosition] = useState<"right" | "left">("right")
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

  const chatEndRef = useRef<HTMLDivElement>(null)
  const gameMasterChatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (gameId) {
      loadGameState()
    } else {
      router.push("/demo")
    }
  }, [gameId])

  useEffect(() => {
    if (gameState?.case_state.time_remaining_seconds) {
      setTimeRemaining(gameState.case_state.time_remaining_seconds)
    }
  }, [gameState])

  useEffect(() => {
    if (timeRemaining > 0) {
      const timer = setInterval(() => {
        setTimeRemaining((prev) => {
          if (prev <= 1) {
            handleTimeUp()
            return 0
          }
          return prev - 1
        })
      }, 1000)
      return () => clearInterval(timer)
    }
  }, [timeRemaining])

  const loadGameState = async () => {
    try {
      const response = await fetch(`/api/game/${gameId}`)
      if (!response.ok) throw new Error("Failed to load game")
      const data = await response.json()
      setGameState(data.game_state)
      setLoading(false)
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load game state",
        variant: "destructive"
      })
      router.push("/demo")
    }
  }

  const handleTimeUp = () => {
    toast({
      title: "Time's Up!",
      description: "Please submit your answer",
      variant: "destructive"
    })
  }

  const handleUseClue = async () => {
    if (!gameState) return

    try {
      const response = await fetch("/api/game/use-clue", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          game_state: gameState,
          ...modelConfig
        })
      })

      if (!response.ok) throw new Error("Failed to use clue")

      const data = await response.json()
      setGameState(data.game_state)
      setShowClue(true)
      setTimeRemaining(data.game_state.case_state.time_remaining_seconds)

      toast({
        title: "Clue Used",
        description: "Penalty applied. Case difficulty increased.",
        variant: "destructive"
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to use clue",
        variant: "destructive"
      })
    }
  }

  const handleSubmitAnswer = async () => {
    if (!gameState) return

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
          game_state: gameState,
          answer,
          time_taken: timeTaken,
          ...modelConfig
        })
      })

      if (!response.ok) throw new Error("Failed to submit answer")

      const data = await response.json()
      setGameState(data.game_state)
      setShowAnswer(true)
      setShowReason(true)

      toast({
        title: `Score: ${data.performance.score}/10`,
        description: data.performance.analysis,
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to submit answer",
        variant: "destructive"
      })
    }
  }

  const handleGameMasterChat = async () => {
    if (!gameState || !gameMasterMessage.trim()) return

    const userMessage = gameMasterMessage
    setGameMasterMessage("")

    try {
      const response = await fetch("/api/game/master-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          game_state: gameState,
          user_message: userMessage,
          ...modelConfig
        })
      })

      if (!response.ok) throw new Error("Failed to send message")

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let accumulatedResponse = ""

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split("\n")

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = JSON.parse(line.slice(6))
              accumulatedResponse += data.content

              // Update chat history
              setGameState((prev) => {
                if (!prev) return prev
                const newHistory = [...prev.game_master_chat_history]
                if (newHistory[newHistory.length - 1]?.role !== "assistant") {
                  newHistory.push({ role: "assistant", content: accumulatedResponse })
                } else {
                  newHistory[newHistory.length - 1].content = accumulatedResponse
                }
                return { ...prev, game_master_chat_history: newHistory }
              })

              if (data.complete && data.updated_game_state) {
                setGameState(data.updated_game_state)
              }
            }
          }
        }
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to send message",
        variant: "destructive"
      })
    }
  }

  const handleNPCChat = async () => {
    if (!gameState || !selectedNpc || !npcMessage.trim()) return

    const userMessage = npcMessage
    setNpcMessage("")

    try {
      const npc = gameState.npc_states.find(n => n.npc_id === selectedNpc)
      if (!npc) return

      const response = await fetch("/api/game/npc-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          game_state: gameState,
          npc_id: selectedNpc,
          user_message: userMessage,
          chat_history: [],
          ...modelConfig
        })
      })

      if (!response.ok) throw new Error("Failed to send message")

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let accumulatedResponse = ""

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split("\n")

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = JSON.parse(line.slice(6))
              accumulatedResponse += data.content
            }
          }
        }
      }

      toast({
        title: `${npc.name} responded`,
        description: accumulatedResponse.substring(0, 100) + "...",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to send message",
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

  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-[#0A1128] to-[#4C1D95] text-white p-4 relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          className="absolute top-10 left-10 w-64 h-64 bg-purple-900/20 rounded-full blur-3xl"
          animate={{
            x: [0, 50, 0],
            y: [0, 30, 0],
            scale: [1, 1.2, 1],
            rotate: [0, 90, 180, 360],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <motion.div
          className="absolute bottom-10 right-10 w-80 h-80 bg-blue-900/20 rounded-full blur-3xl"
          animate={{
            x: [0, -50, 0],
            y: [0, -30, 0],
            scale: [1, 1.3, 1],
            rotate: [360, 270, 180, 0],
          }}
          transition={{
            duration: 12,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      </div>
      <div className="container mx-auto grid grid-cols-1 lg:grid-cols-3 gap-4 h-[calc(100vh-2rem)] relative z-10">
        {/* Left Column - Game World & Case Info */}
        <div className="space-y-4 overflow-y-auto">
          {/* Game World */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Card className="bg-black/60 backdrop-blur-md border-purple-700/40">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Trophy className="h-5 w-5 text-purple-400" />
                  Game World
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-300">{gameState.game_world.world_description}</p>
                {gameState.game_world.hospital_name && (
                  <Badge className="mt-2 bg-purple-700">{gameState.game_world.hospital_name}</Badge>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* Case Scenario */}
          <Card className="bg-black/60 backdrop-blur-md border-purple-700/40">
            <CardHeader>
              <CardTitle>Case Scenario</CardTitle>
              <CardDescription className="text-gray-400">
                Case {gameState.current_case_number}/{gameState.total_cases}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm">{gameState.case_state.clinical_case_scenario_description}</p>
            </CardContent>
          </Card>

          {/* Examination Findings - Collapsible */}
          <Collapsible open={showExamination} onOpenChange={setShowExamination}>
            <Card className="bg-black/60 backdrop-blur-md border-purple-700/40">
              <CollapsibleTrigger className="w-full">
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle>Examination Findings</CardTitle>
                  {showExamination ? <ChevronUp /> : <ChevronDown />}
                </CardHeader>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <CardContent>
                  <pre className="text-xs text-gray-300 whitespace-pre-wrap">
                    {JSON.stringify(gameState.case_state.examination_findings, null, 2)}
                  </pre>
                </CardContent>
              </CollapsibleContent>
            </Card>
          </Collapsible>

          {/* Investigation Results - Collapsible */}
          <Collapsible open={showInvestigations} onOpenChange={setShowInvestigations}>
            <Card className="bg-black/60 backdrop-blur-md border-purple-700/40">
              <CollapsibleTrigger className="w-full">
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle>Investigation Results</CardTitle>
                  {showInvestigations ? <ChevronUp /> : <ChevronDown />}
                </CardHeader>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <CardContent>
                  <pre className="text-xs text-gray-300 whitespace-pre-wrap">
                    {JSON.stringify(gameState.case_state.investigation_results, null, 2)}
                  </pre>
                </CardContent>
              </CollapsibleContent>
            </Card>
          </Collapsible>

          {/* Achievements */}
          {gameState.achievements.length > 0 ? (
            <Card className="bg-black/60 backdrop-blur-md border-purple-700/40">
              <CardHeader>
                <CardTitle>Achievements</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {gameState.achievements.map((achievement, idx) => (
                  <Badge key={idx} className="bg-purple-700">
                    {achievement.title}
                  </Badge>
                ))}
              </CardContent>
            </Card>
          ) : null}
        </div>

        {/* Center Column - Question & Answer */}
        <div className="space-y-4 overflow-y-auto">
          {/* Timer & Question */}
          <Card className="bg-black/60 backdrop-blur-md border-purple-700/40">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Question</CardTitle>
                <motion.div 
                  className="flex items-center gap-2 text-purple-400"
                  animate={{
                    scale: [1, 1.1, 1],
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                >
                  <Clock className="h-5 w-5" />
                  <span className="font-mono text-lg">{formatTime(timeRemaining)}</span>
                </motion.div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-lg">{gameState.case_state.question}</p>

              {/* Multiple Choice Options */}
              {gameState.case_state.options && (
                <div className="space-y-2">
                  {gameState.case_state.options.map((option, idx) => (
                    <Button
                      key={idx}
                      variant={selectedOption === option ? "default" : "outline"}
                      className="w-full justify-start text-left bg-black/50 border-purple-700/40 hover:bg-purple-700/30"
                      onClick={() => setSelectedOption(option)}
                    >
                      {String.fromCharCode(65 + idx)}. {option}
                    </Button>
                  ))}
                </div>
              )}

              {/* Open-ended Answer */}
              {!gameState.case_state.options && (
                <Textarea
                  placeholder="Type your answer here..."
                  value={userAnswer}
                  onChange={(e) => setUserAnswer(e.target.value)}
                  className="bg-black/50 border-purple-700/40 min-h-[150px]"
                />
              )}

              {/* Action Buttons */}
              <div className="flex gap-2">
                <Button
                  onClick={handleUseClue}
                  disabled={showClue || gameState.case_state.clue_used}
                  variant="outline"
                  className="flex-1 border-purple-700/40 hover:bg-purple-700/30"
                >
                  <Lightbulb className="h-4 w-4 mr-2" />
                  {gameState.case_state.clue_used ? "Clue Used" : "Use Clue"}
                </Button>
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="flex-1"
                >
                  <Button
                    onClick={handleSubmitAnswer}
                    className="w-full bg-gradient-to-r from-purple-700 to-purple-900 hover:from-purple-800 hover:to-purple-950"
                  >
                    Submit Answer
                  </Button>
                </motion.div>
              </div>

              {/* Clue (Hidden by default) */}
              <AnimatePresence>
                {showClue && gameState.case_state.clue && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="bg-purple-900/30 border border-purple-500/50 rounded-lg p-4"
                  >
                    <motion.p 
                      className="text-sm"
                      animate={{
                        scale: [1, 1.02, 1],
                      }}
                      transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: "easeInOut"
                      }}
                    >
                      <strong>Clue:</strong> {gameState.case_state.clue}
                    </motion.p>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Answer (Hidden by default) */}
              <AnimatePresence>
                {showAnswer && gameState.case_state.answer && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="bg-green-900/30 border border-green-500/50 rounded-lg p-4"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle2 className="h-5 w-5 text-purple-400" />
                      <strong>Correct Answer:</strong>
                    </div>
                    <p className="text-sm">{gameState.case_state.answer}</p>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Reason for Answer (Hidden by default) */}
              <AnimatePresence>
                {showReason && gameState.case_state.reason_for_answer && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="bg-blue-900/30 border border-blue-400/50 rounded-lg p-4"
                  >
                    <motion.div 
                      className="flex items-center gap-2 mb-2"
                      animate={{
                        scale: [1, 1.05, 1],
                      }}
                      transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: "easeInOut"
                      }}
                    >
                      <motion.div
                        animate={{
                          rotate: [0, -15, 15, 0],
                        }}
                        transition={{
                          duration: 2,
                          repeat: Infinity,
                          ease: "easeInOut"
                        }}
                      >
                        <AlertCircle className="h-5 w-5 text-blue-300" />
                      </motion.div>
                      <strong>Explanation:</strong>
                    </motion.div>
                    <motion.p 
                      className="text-sm"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.2 }}
                    >
                      {gameState.case_state.reason_for_answer}
                    </motion.p>
                  </motion.div>
                )}
              </AnimatePresence>
            </CardContent>
          </Card>

          {/* Performance Summary */}
          {gameState.user_performance.length > 0 && (
            <Card className="bg-black/60 backdrop-blur-md border-purple-700/40">
              <CardHeader>
                <CardTitle>Performance</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {gameState.user_performance.map((perf, idx) => (
                  <div key={idx} className="border-b border-purple-700/40 pb-2">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm">Case {idx + 1}</span>
                      <Badge className={perf.score >= 7 ? "bg-purple-700" : perf.score >= 5 ? "bg-purple-600" : "bg-purple-800"}>
                        {perf.score}/10
                      </Badge>
                    </div>
                    <p className="text-xs text-gray-400">{perf.analysis}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Column - Chat Windows */}
        <div className={`space-y-4 overflow-y-auto ${chatPosition === "left" ? "lg:order-first" : ""}`}>
          {/* Chat Position Toggle */}
          <Button
            onClick={() => setChatPosition(chatPosition === "right" ? "left" : "right")}
            variant="outline"
            size="sm"
            className="w-full border-purple-700/40"
          >
            Move Chat {chatPosition === "right" ? "Left" : "Right"}
          </Button>

          {/* Game Master Chat */}
          <Card className="bg-black/60 backdrop-blur-md border-purple-700/40">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageCircle className="h-5 w-5" />
                Game Master
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="h-64 overflow-y-auto space-y-2">
                {gameState.game_master_chat_history.map((msg, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.1 }}
                    className={`p-2 rounded-lg ${
                      msg.role === "user" ? "bg-purple-700/30 ml-4" : "bg-blue-800/30 mr-4"
                    }`}
                  >
                    <motion.p 
                      className="text-sm"
                      animate={{
                        scale: [1, 1.01, 1],
                      }}
                      transition={{
                        duration: 3,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: idx * 0.1
                      }}
                    >
                      {msg.content}
                    </motion.p>
                  </motion.div>
                ))}
                <div ref={gameMasterChatEndRef} />
              </div>
              <div className="flex gap-2">
                <Input
                  value={gameMasterMessage}
                  onChange={(e) => setGameMasterMessage(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && handleGameMasterChat()}
                  placeholder="Ask the Game Master..."
                  className="bg-black/50 border-purple-700/40"
                />
                <Button onClick={handleGameMasterChat} size="icon">
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* NPC Chat */}
          <Card className="bg-black/60 backdrop-blur-md border-purple-700/40">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                NPC Chat
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Select value={selectedNpc || ""} onValueChange={setSelectedNpc}>
                <SelectTrigger className="bg-black/50 border-purple-700/40">
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

              {selectedNpc && (
                <>
                  <div className="h-48 overflow-y-auto space-y-2 bg-black/30 rounded-lg p-2">
                    <p className="text-xs text-gray-400">Chat with NPC...</p>
                  </div>
                  <div className="flex gap-2">
                    <Input
                      value={npcMessage}
                      onChange={(e) => setNpcMessage(e.target.value)}
                      onKeyPress={(e) => e.key === "Enter" && handleNPCChat()}
                      placeholder="Ask NPC..."
                      className="bg-black/50 border-purple-700/40"
                    />
                    <Button onClick={handleNPCChat} size="icon" disabled={!selectedNpc}>
                      <Send className="h-4 w-4" />
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Model Configuration */}
          <Card className="bg-black/60 backdrop-blur-md border-purple-700/40">
            <CardHeader>
              <CardTitle className="text-sm">Model Config</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Select
                value={modelConfig.provider}
                onValueChange={(value) => setModelConfig({ ...modelConfig, provider: value })}
              >
                <SelectTrigger className="bg-black/50 border-purple-700/40 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="google">Google</SelectItem>
                  <SelectItem value="openai">OpenAI</SelectItem>
                </SelectContent>
              </Select>
              <Input
                placeholder="Model name (optional)"
                value={modelConfig.model_name}
                onChange={(e) => setModelConfig({ ...modelConfig, model_name: e.target.value })}
                className="bg-black/50 border-purple-700/40 text-xs"
              />
              <Input
                type="password"
                placeholder="API key (optional)"
                value={modelConfig.api_key}
                onChange={(e) => setModelConfig({ ...modelConfig, api_key: e.target.value })}
                className="bg-black/50 border-purple-700/40 text-xs"
              />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
