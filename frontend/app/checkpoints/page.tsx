"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Button } from "@/app/components/ui/button"
import { Badge } from "@/app/components/ui/badge"
import { Skeleton } from "@/app/components/ui/skeleton"
import { apiFetch } from "@/app/lib/auth"
import { Input } from "@/app/components/ui/input"
import { Label } from "@/app/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/app/components/ui/dialog"
import {
  Save,
  Play,
  Trash2,
  Clock,
  Calendar,
  ArrowLeft,
  Plus,
  Edit,
  MoreVertical,
} from "lucide-react"
import Link from "next/link"
import { useToast } from "@/app/components/ui/use-toast"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/app/components/ui/dropdown-menu"

interface Checkpoint {
  id: string
  checkpointId: string
  checkpointName: string
  gameStateId: string
  description?: string
  scenario: string
  patientName: string
  score: number
  phase: string
  createdAt: string
}

export default function CheckpointsPage() {
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [newCheckpointName, setNewCheckpointName] = useState("")
  const [newCheckpointDescription, setNewCheckpointDescription] = useState("")
  const { toast } = useToast()

  useEffect(() => {
    loadCheckpoints()
  }, [])

  const loadCheckpoints = async () => {
    try {
      setIsLoading(true)
      const response = await apiFetch("/api/game/checkpoints")

      if (response.ok) {
        const data = await response.json()
        setCheckpoints(data.checkpoints || [])
      } else {
        // Mock data
        setCheckpoints([
          {
            id: "1",
            checkpointId: "checkpoint-1",
            checkpointName: "Emergency Room - Initial Assessment",
            gameStateId: "game-1",
            description: "Patient arrived with chest pain",
            scenario: "Emergency Department - Chest Pain",
            patientName: "Sarah Johnson",
            score: 250,
            phase: "Initial Assessment",
            createdAt: "2024-01-20T10:30:00Z",
          },
          {
            id: "2",
            checkpointId: "checkpoint-2",
            checkpointName: "ICU - Critical Care",
            gameStateId: "game-2",
            description: "Post-surgery monitoring",
            scenario: "ICU - Post-Operative Care",
            patientName: "Michael Chen",
            score: 450,
            phase: "Critical Care",
            createdAt: "2024-01-18T14:20:00Z",
          },
        ])
      }
    } catch (error) {
      console.error("Failed to load checkpoints:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleLoadCheckpoint = async (checkpointId: string) => {
    try {
      const response = await apiFetch(`/api/game/checkpoints/${checkpointId}`)

      if (response.ok) {
        const data = await response.json()
        const gameState = data.game_state
        const gameId = gameState?.game_id
        if (!gameId) throw new Error("Checkpoint has no game state to resume")

        sessionStorage.setItem(
          `game_init_${gameId}`,
          JSON.stringify({ success: true, game_state: gameState })
        )
        window.location.href = `/mediquest?game_id=${gameId}`
      } else {
        toast({
          title: "Error",
          description: "Failed to load checkpoint.",
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to load checkpoint.",
        variant: "destructive",
      })
    }
  }

  const handleDeleteCheckpoint = async (checkpointId: string) => {
    try {
      const response = await apiFetch(`/api/game/checkpoints/${checkpointId}`, {
        method: "DELETE",
      })

      if (response.ok) {
        setCheckpoints(checkpoints.filter((c) => c.checkpointId !== checkpointId))
        toast({
          title: "Checkpoint Deleted",
          description: "Checkpoint has been deleted successfully.",
        })
      } else {
        throw new Error("Failed to delete checkpoint")
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete checkpoint.",
        variant: "destructive",
      })
    }
  }

  const handleCreateCheckpoint = async () => {
    // This would typically be called from the game page
    // For now, just show a message
    toast({
      title: "Info",
      description: "Create checkpoints from within a game session.",
    })
    setShowCreateDialog(false)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-purple-900 via-purple-800 to-purple-900 p-4">
        <div className="max-w-7xl mx-auto space-y-6">
          <Skeleton className="h-16 w-full bg-purple-800/50" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-64 bg-purple-800/50" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-900 via-purple-800 to-purple-900 p-4 md:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 animate-in fade-in slide-in-from-top-4 duration-700">
          <div>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-2 bg-gradient-to-r from-white to-purple-200 bg-clip-text text-transparent flex items-center gap-3">
              <Save className="h-10 w-10 text-purple-400" />
              Game Checkpoints
            </h1>
            <p className="text-purple-200 text-lg">Save and resume your game progress</p>
          </div>
          <div className="flex gap-4">
            <Link href="/demo">
              <Button className="bg-purple-600 hover:bg-purple-700">
                <Play className="h-4 w-4 mr-2" />
                New Game
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button variant="outline" className="border-purple-400 text-white hover:bg-purple-800">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
            </Link>
          </div>
        </div>

        {/* Checkpoints Grid */}
        {checkpoints.length === 0 ? (
          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
            <CardContent className="p-12 text-center">
              <Save className="h-16 w-16 mx-auto mb-4 text-purple-400 opacity-50" />
              <h3 className="text-xl font-semibold mb-2">No Checkpoints Yet</h3>
              <p className="text-purple-200 mb-6">Start a game and save checkpoints to resume later</p>
              <Link href="/demo">
                <Button className="bg-purple-600 hover:bg-purple-700">
                  <Play className="h-4 w-4 mr-2" />
                  Start New Game
                </Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
            {checkpoints.map((checkpoint, index) => (
              <Card
                key={checkpoint.id}
                className="bg-white/10 backdrop-blur-sm border-purple-400 text-white hover:border-purple-300 transition-all duration-300 transform hover:scale-105 animate-in fade-in slide-in-from-bottom"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg mb-2">{checkpoint.checkpointName}</CardTitle>
                      {checkpoint.description && (
                        <CardDescription className="text-purple-200 text-sm">
                          {checkpoint.description}
                        </CardDescription>
                      )}
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" className="text-purple-300 hover:text-white">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent className="bg-purple-900 border-purple-600">
                        <DropdownMenuItem
                          onClick={() => handleLoadCheckpoint(checkpoint.checkpointId)}
                          className="text-white hover:bg-purple-800 cursor-pointer"
                        >
                          <Play className="h-4 w-4 mr-2" />
                          Load
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => handleDeleteCheckpoint(checkpoint.checkpointId)}
                          className="text-red-400 hover:bg-red-900/20 cursor-pointer"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-purple-200">Scenario</span>
                      <span className="font-semibold">{checkpoint.scenario}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-purple-200">Patient</span>
                      <span className="font-semibold">{checkpoint.patientName}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-purple-200">Phase</span>
                      <Badge variant="secondary" className="bg-purple-700 text-white">
                        {checkpoint.phase}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-purple-200">Score</span>
                      <span className="font-bold text-yellow-400">{checkpoint.score}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-purple-300 pt-2 border-t border-purple-700">
                    <Calendar className="h-3 w-3" />
                    <span>{new Date(checkpoint.createdAt).toLocaleDateString()}</span>
                    <Clock className="h-3 w-3 ml-2" />
                    <span>{new Date(checkpoint.createdAt).toLocaleTimeString()}</span>
                  </div>
                  <Button
                    onClick={() => handleLoadCheckpoint(checkpoint.checkpointId)}
                    className="w-full bg-purple-600 hover:bg-purple-700"
                  >
                    <Play className="h-4 w-4 mr-2" />
                    Resume Game
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}




