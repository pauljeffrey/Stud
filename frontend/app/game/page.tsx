"use client"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/app/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Textarea } from "@/app/components/ui/textarea"
import { Badge } from "@/app/components/ui/badge"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/app/components/ui/dialog"
import {
  Heart,
  Stethoscope,
  Clock,
  MessageCircle,
  Send,
  Volume2,
  VolumeX,
  Save,
  Trophy,
  Star,
  Dice6,
  Users,
  Loader2,
} from "lucide-react"
import { useToast } from "@/app/components/ui/use-toast"

interface GameState {
  userId: string
  caseId: string
  currentScenario: string
  patientInfo: {
    name: string
    age: number
    gender: string
    chiefComplaint: string
    vitals: {
      heartRate: number
      bloodPressure: string
      temperature: number
      respiratoryRate: number
      oxygenSaturation: number
    }
    background: string
    currentCondition: string
  }
  gameProgress: {
    currentPhase: string
    completedActions: string[]
    score: number
    timeElapsed: number
    diceRolls: number
    lastDiceResult: number
  }
  inventory: string[]
  chatHistory: Array<{
    role: "user" | "ai" | "system" | "npc"
    content: string
    timestamp: Date
    npcName?: string
  }>
  npcs: Array<{
    name: string
    role: string
    available: boolean
    mood: string
  }>
}

export default function GamePage() {
  const [gameState, setGameState] = useState<GameState>({
    userId: "user_123",
    caseId: "case_emergency_001",
    currentScenario: "Emergency Department - Chest Pain",
    patientInfo: {
      name: "Sarah Johnson",
      age: 45,
      gender: "Female",
      chiefComplaint: "Severe chest pain for the past 2 hours",
      vitals: {
        heartRate: 110,
        bloodPressure: "150/95",
        temperature: 37.2,
        respiratoryRate: 22,
        oxygenSaturation: 96,
      },
      background: "45-year-old female with history of hypertension and diabetes",
      currentCondition: "Appears anxious, clutching chest, diaphoretic",
    },
    gameProgress: {
      currentPhase: "Initial Assessment",
      completedActions: [],
      score: 0,
      timeElapsed: 0,
      diceRolls: 0,
      lastDiceResult: 0,
    },
    inventory: ["Stethoscope", "Blood Pressure Cuff", "Thermometer", "Pulse Oximeter"],
    chatHistory: [
      {
        role: "system",
        content:
          "Welcome to MediQuest! You are now treating Sarah Johnson in the Emergency Department. Begin your assessment.",
        timestamp: new Date(),
      },
    ],
    npcs: [
      { name: "Nurse Kelly", role: "Nurse", available: true, mood: "helpful" },
      { name: "Dr. Martinez", role: "Cardiologist", available: false, mood: "busy" },
      { name: "Sarah Johnson", role: "Patient", available: true, mood: "anxious" },
    ],
  })

  const [userInput, setUserInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [audioEnabled, setAudioEnabled] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [showDiceDialog, setShowDiceDialog] = useState(false)
  const [diceAnimation, setDiceAnimation] = useState(false)
  const { toast } = useToast()
  const chatEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [gameState.chatHistory])

  // Game timer
  useEffect(() => {
    const timer = setInterval(() => {
      setGameState((prev) => ({
        ...prev,
        gameProgress: {
          ...prev.gameProgress,
          timeElapsed: prev.gameProgress.timeElapsed + 1,
        },
      }))
    }, 1000)

    return () => clearInterval(timer)
  }, [])

  const rollDice = async () => {
    setDiceAnimation(true)
    setShowDiceDialog(true)

    // Animate dice roll
    await new Promise((resolve) => setTimeout(resolve, 1000))

    const diceResult = Math.floor(Math.random() * 11)

    setGameState((prev) => ({
      ...prev,
      gameProgress: {
        ...prev.gameProgress,
        diceRolls: prev.gameProgress.diceRolls + 1,
        lastDiceResult: diceResult,
      },
    }))

    setDiceAnimation(false)

    // Apply dice effect to scenario
    await applyDiceEffect(diceResult)

    setTimeout(() => setShowDiceDialog(false), 2000)
  }

  const applyDiceEffect = async (diceResult: number) => {
    try {
      const response = await fetch("/api/game/dice-effect", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          game_state: gameState,
          dice_result: diceResult,
        }),
      })

      if (!response.ok) throw new Error("Failed to apply dice effect")

      const reader = response.body?.getReader()
      if (!reader) throw new Error("No response body")

      const aiMessage = {
        role: "system" as const,
        content: "",
        timestamp: new Date(),
      }

      setGameState((prev) => ({
        ...prev,
        chatHistory: [...prev.chatHistory, aiMessage],
      }))

      // Stream the response
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = new TextDecoder().decode(value)
        const lines = chunk.split("\n")

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.content) {
                setGameState((prev) => ({
                  ...prev,
                  chatHistory: prev.chatHistory.map((msg, index) =>
                    index === prev.chatHistory.length - 1 ? { ...msg, content: msg.content + data.content } : msg,
                  ),
                }))
              }
              if (data.patientUpdate) {
                setGameState((prev) => ({
                  ...prev,
                  patientInfo: { ...prev.patientInfo, ...data.patientUpdate },
                }))
              }
            } catch (e) {
              // Ignore parsing errors
            }
          }
        }
      }
    } catch (error) {
      console.error("Dice effect error:", error)
      toast({
        title: "Error",
        description: "Failed to apply dice effect.",
        variant: "destructive",
      })
    }
  }

  const handleSendMessage = async () => {
    if (!userInput.trim()) return

    const userMessage = {
      role: "user" as const,
      content: userInput,
      timestamp: new Date(),
    }

    setGameState((prev) => ({
      ...prev,
      chatHistory: [...prev.chatHistory, userMessage],
    }))

    setUserInput("")
    setIsLoading(true)

    try {
      const response = await fetch("/api/game/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          gameState,
          userMessage: userInput,
        }),
      })

      if (!response.ok) throw new Error("Failed to get AI response")

      const reader = response.body?.getReader()
      if (!reader) throw new Error("No response body")

      const aiMessage = {
        role: "ai" as const,
        content: "",
        timestamp: new Date(),
      }

      setGameState((prev) => ({
        ...prev,
        chatHistory: [...prev.chatHistory, aiMessage],
      }))

      // Stream the response
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = new TextDecoder().decode(value)
        const lines = chunk.split("\n")

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.content) {
                setGameState((prev) => ({
                  ...prev,
                  chatHistory: prev.chatHistory.map((msg, index) =>
                    index === prev.chatHistory.length - 1 ? { ...msg, content: msg.content + data.content } : msg,
                  ),
                }))
              }
              if (data.scoreUpdate) {
                setGameState((prev) => ({
                  ...prev,
                  gameProgress: {
                    ...prev.gameProgress,
                    score: prev.gameProgress.score + data.scoreUpdate,
                  },
                }))
              }
            } catch (e) {
              // Ignore parsing errors
            }
          }
        }
      }
    } catch (error) {
      console.error("Chat error:", error)
      toast({
        title: "Error",
        description: "Failed to get response. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const talkToNPC = async (npcName: string) => {
    if (!gameState.npcs.find((npc) => npc.name === npcName)?.available) {
      toast({
        title: "NPC Unavailable",
        description: `${npcName} is not available right now.`,
        variant: "destructive",
      })
      return
    }

    setIsLoading(true)

    try {
      const response = await fetch("/api/game/npc-chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          gameState,
          npcName,
        }),
      })

      if (!response.ok) throw new Error("Failed to talk to NPC")

      const reader = response.body?.getReader()
      if (!reader) throw new Error("No response body")

      const npcMessage = {
        role: "npc" as const,
        content: "",
        timestamp: new Date(),
        npcName,
      }

      setGameState((prev) => ({
        ...prev,
        chatHistory: [...prev.chatHistory, npcMessage],
      }))

      // Stream the NPC response
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = new TextDecoder().decode(value)
        const lines = chunk.split("\n")

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.content) {
                setGameState((prev) => ({
                  ...prev,
                  chatHistory: prev.chatHistory.map((msg, index) =>
                    index === prev.chatHistory.length - 1 ? { ...msg, content: msg.content + data.content } : msg,
                  ),
                }))
              }
            } catch (e) {
              // Ignore parsing errors
            }
          }
        }
      }
    } catch (error) {
      console.error("NPC chat error:", error)
      toast({
        title: "Error",
        description: "Failed to talk to NPC.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const saveGame = async () => {
    try {
      const response = await fetch("/api/game/save", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ gameState }),
      })

      if (!response.ok) throw new Error("Failed to save game")

      toast({
        title: "Game Saved",
        description: "Your progress has been saved successfully.",
      })
    } catch (error) {
      toast({
        title: "Save Failed",
        description: "Failed to save game. Please try again.",
        variant: "destructive",
      })
    }
  }

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-900 to-purple-700 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">MediQuest</h1>
            <p className="text-purple-200">{gameState.currentScenario}</p>
          </div>
          <div className="flex items-center gap-4">
            <Button
              onClick={rollDice}
              variant="outline"
              className="border-purple-400 text-white hover:bg-purple-800 bg-transparent"
            >
              <Dice6 className="h-4 w-4 mr-2" />
              Roll Dice ({gameState.gameProgress.diceRolls})
            </Button>
            <Button
              onClick={() => setIsMuted(!isMuted)}
              variant="outline"
              className="border-purple-400 text-white hover:bg-purple-800 bg-transparent"
            >
              {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
            </Button>
            <Button
              onClick={saveGame}
              variant="outline"
              className="border-purple-400 text-white hover:bg-purple-800 bg-transparent"
            >
              <Save className="h-4 w-4 mr-2" />
              Save Game
            </Button>
          </div>
        </div>

        {/* Game Stats */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Trophy className="h-5 w-5 text-yellow-400" />
                <div>
                  <p className="text-sm text-purple-200">Score</p>
                  <p className="text-xl font-bold">{gameState.gameProgress.score}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-blue-400" />
                <div>
                  <p className="text-sm text-purple-200">Time</p>
                  <p className="text-xl font-bold">{formatTime(gameState.gameProgress.timeElapsed)}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Heart className="h-5 w-5 text-red-400" />
                <div>
                  <p className="text-sm text-purple-200">Heart Rate</p>
                  <p className="text-xl font-bold">{gameState.patientInfo.vitals.heartRate} BPM</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Star className="h-5 w-5 text-green-400" />
                <div>
                  <p className="text-sm text-purple-200">Phase</p>
                  <p className="text-lg font-bold">{gameState.gameProgress.currentPhase}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Dice6 className="h-5 w-5 text-purple-400" />
                <div>
                  <p className="text-sm text-purple-200">Last Roll</p>
                  <p className="text-xl font-bold">{gameState.gameProgress.lastDiceResult || "-"}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Game Area */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Patient Information & NPCs */}
          <div className="lg:col-span-1">
            <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white mb-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Stethoscope className="h-5 w-5" />
                  Patient Information
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-purple-200">Name</p>
                    <p className="font-semibold">{gameState.patientInfo.name}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-purple-200">Age</p>
                      <p className="font-semibold">{gameState.patientInfo.age}</p>
                    </div>
                    <div>
                      <p className="text-sm text-purple-200">Gender</p>
                      <p className="font-semibold">{gameState.patientInfo.gender}</p>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-purple-200">Chief Complaint</p>
                    <p className="font-semibold">{gameState.patientInfo.chiefComplaint}</p>
                  </div>
                  <div>
                    <p className="text-sm text-purple-200">Current Condition</p>
                    <p className="font-semibold">{gameState.patientInfo.currentCondition}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* NPCs */}
            <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white mb-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  Available NPCs
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {gameState.npcs.map((npc, index) => (
                    <div
                      key={index}
                      className={`p-3 rounded-lg border ${
                        npc.available
                          ? "bg-purple-800 border-purple-600 cursor-pointer hover:bg-purple-700"
                          : "bg-purple-900 border-purple-700 opacity-60"
                      }`}
                      onClick={() => npc.available && talkToNPC(npc.name)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-semibold">{npc.name}</p>
                          <p className="text-sm text-purple-200">{npc.role}</p>
                        </div>
                        <Badge
                          variant="secondary"
                          className={`text-xs ${npc.available ? "bg-green-600" : "bg-red-600"} text-white`}
                        >
                          {npc.mood}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Vital Signs */}
            <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Heart className="h-5 w-5" />
                  Vital Signs
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-purple-200">Heart Rate</span>
                    <span className="font-semibold">{gameState.patientInfo.vitals.heartRate} BPM</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-purple-200">Blood Pressure</span>
                    <span className="font-semibold">{gameState.patientInfo.vitals.bloodPressure} mmHg</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-purple-200">Temperature</span>
                    <span className="font-semibold">{gameState.patientInfo.vitals.temperature}°C</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-purple-200">Respiratory Rate</span>
                    <span className="font-semibold">{gameState.patientInfo.vitals.respiratoryRate}/min</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-purple-200">O2 Saturation</span>
                    <span className="font-semibold">{gameState.patientInfo.vitals.oxygenSaturation}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Chat Interface */}
          <div className="lg:col-span-2">
            <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white h-[700px] flex flex-col">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageCircle className="h-5 w-5" />
                  Game Master & NPCs
                </CardTitle>
                <CardDescription className="text-purple-200">
                  Interact with the AI Game Master and NPCs to progress through the scenario.
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col">
                {/* Chat History */}
                <div className="flex-1 overflow-y-auto mb-4 space-y-4 max-h-96">
                  {gameState.chatHistory.map((message, index) => (
                    <div
                      key={index}
                      className={`p-3 rounded-lg ${
                        message.role === "user"
                          ? "bg-purple-600 ml-8"
                          : message.role === "ai"
                            ? "bg-purple-800 mr-8"
                            : message.role === "npc"
                              ? "bg-green-800 mr-8"
                              : "bg-purple-900 text-center"
                      }`}
                    >
                      {message.npcName && (
                        <p className="text-xs text-green-300 mb-1 font-semibold">{message.npcName}:</p>
                      )}
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      <p className="text-xs text-purple-300 mt-1">{message.timestamp.toLocaleTimeString()}</p>
                    </div>
                  ))}
                  {isLoading && (
                    <div className="bg-purple-800 mr-8 p-3 rounded-lg flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <p className="text-sm">AI is thinking...</p>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>

                {/* Input Area */}
                <div className="flex gap-2">
                  <Textarea
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    placeholder="Describe your actions, ask questions, or make medical decisions..."
                    className="flex-1 bg-purple-800 border-purple-600 text-white placeholder-purple-300 resize-none"
                    rows={3}
                    onKeyPress={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault()
                        handleSendMessage()
                      }
                    }}
                  />
                  <Button
                    onClick={handleSendMessage}
                    disabled={isLoading || !userInput.trim()}
                    className="bg-purple-600 hover:bg-purple-700"
                  >
                    {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Dice Roll Dialog */}
        <Dialog open={showDiceDialog} onOpenChange={setShowDiceDialog}>
          <DialogContent className="bg-purple-900 text-white border-purple-500">
            <DialogHeader>
              <DialogTitle>Dice Roll Result</DialogTitle>
              <DialogDescription className="text-purple-200">
                The dice of fate has been cast! This will affect the scenario.
              </DialogDescription>
            </DialogHeader>
            <div className="flex flex-col items-center py-8">
              <div className={`text-6xl mb-4 ${diceAnimation ? "animate-bounce" : ""}`}>🎲</div>
              {!diceAnimation && (
                <div className="text-center">
                  <p className="text-4xl font-bold text-yellow-400 mb-2">{gameState.gameProgress.lastDiceResult}</p>
                  <p className="text-purple-200">
                    {gameState.gameProgress.lastDiceResult >= 7
                      ? "Favorable outcome!"
                      : gameState.gameProgress.lastDiceResult >= 4
                        ? "Moderate change"
                        : "Challenging situation!"}
                  </p>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  )
}
