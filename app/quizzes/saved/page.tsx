"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Button } from "@/app/components/ui/button"
import { Badge } from "@/app/components/ui/badge"
import { Skeleton } from "@/app/components/ui/skeleton"
import {
  Brain,
  Clock,
  Star,
  Play,
  Trash2,
  Calendar,
  ArrowLeft,
  BookOpen,
  MoreVertical,
  Filter,
} from "lucide-react"
import Link from "next/link"
import { useToast } from "@/app/components/ui/use-toast"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/app/components/ui/dropdown-menu"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/app/components/ui/select"

interface SavedQuiz {
  id: string
  quizId: string
  title: string
  quizType: string
  totalQuestions: number
  timeLimit: number
  difficulty: string
  savedAt: string
  lastTaken?: string
  bestScore?: number
  timesTaken: number
}

export default function SavedQuizzesPage() {
  const [savedQuizzes, setSavedQuizzes] = useState<SavedQuiz[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filter, setFilter] = useState<"all" | "multiple_choice" | "true_false" | "open_ended">("all")
  const [sortBy, setSortBy] = useState<"recent" | "score" | "title">("recent")
  const { toast } = useToast()

  useEffect(() => {
    loadSavedQuizzes()
  }, [filter, sortBy])

  const loadSavedQuizzes = async () => {
    try {
      setIsLoading(true)
      const response = await fetch("/api/quiz/saved", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setSavedQuizzes(data.quizzes || [])
      } else {
        // Mock data
        setSavedQuizzes([
          {
            id: "1",
            quizId: "quiz-1",
            title: "Cardiology Fundamentals",
            quizType: "multiple_choice",
            totalQuestions: 20,
            timeLimit: 30,
            difficulty: "intermediate",
            savedAt: "2024-01-20T10:00:00Z",
            lastTaken: "2024-01-22T14:30:00Z",
            bestScore: 92,
            timesTaken: 3,
          },
          {
            id: "2",
            quizId: "quiz-2",
            title: "Emergency Medicine Protocols",
            quizType: "multiple_choice",
            totalQuestions: 15,
            timeLimit: 20,
            difficulty: "advanced",
            savedAt: "2024-01-18T09:00:00Z",
            lastTaken: "2024-01-19T16:45:00Z",
            bestScore: 88,
            timesTaken: 2,
          },
          {
            id: "3",
            quizId: "quiz-3",
            title: "Pharmacology Basics",
            quizType: "true_false",
            totalQuestions: 25,
            timeLimit: 15,
            difficulty: "beginner",
            savedAt: "2024-01-15T11:00:00Z",
            bestScore: 95,
            timesTaken: 5,
          },
        ])
      }
    } catch (error) {
      console.error("Failed to load saved quizzes:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleTakeQuiz = (quizId: string) => {
    window.location.href = `/quiz?quizId=${quizId}`
  }

  const handleRemoveSaved = async (quizId: string) => {
    try {
      const response = await fetch(`/api/quiz/saved/${quizId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      })

      if (response.ok) {
        setSavedQuizzes(savedQuizzes.filter((q) => q.quizId !== quizId))
        toast({
          title: "Quiz Removed",
          description: "Quiz has been removed from your saved list.",
        })
      } else {
        throw new Error("Failed to remove quiz")
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to remove quiz.",
        variant: "destructive",
      })
    }
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "beginner":
        return "bg-green-600"
      case "intermediate":
        return "bg-yellow-600"
      case "advanced":
        return "bg-red-600"
      default:
        return "bg-purple-600"
    }
  }

  const filteredAndSorted = savedQuizzes
    .filter((quiz) => filter === "all" || quiz.quizType === filter)
    .sort((a, b) => {
      switch (sortBy) {
        case "recent":
          return new Date(b.savedAt).getTime() - new Date(a.savedAt).getTime()
        case "score":
          return (b.bestScore || 0) - (a.bestScore || 0)
        case "title":
          return a.title.localeCompare(b.title)
        default:
          return 0
      }
    })

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
              <BookOpen className="h-10 w-10 text-purple-400" />
              Saved Quizzes
            </h1>
            <p className="text-purple-200 text-lg">Access your favorite quizzes anytime</p>
          </div>
          <div className="flex gap-4">
            <Link href="/quiz">
              <Button className="bg-purple-600 hover:bg-purple-700">
                <Brain className="h-4 w-4 mr-2" />
                Create New Quiz
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

        {/* Filters */}
        <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
          <CardContent className="p-4">
            <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
              <div className="flex items-center gap-2">
                <Filter className="h-5 w-5 text-purple-300" />
                <span className="font-semibold">Filters:</span>
              </div>
              <Select value={filter} onValueChange={(value: any) => setFilter(value)}>
                <SelectTrigger className="bg-purple-800 border-purple-600 text-white w-full sm:w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="multiple_choice">Multiple Choice</SelectItem>
                  <SelectItem value="true_false">True/False</SelectItem>
                  <SelectItem value="open_ended">Open Ended</SelectItem>
                </SelectContent>
              </Select>
              <Select value={sortBy} onValueChange={(value: any) => setSortBy(value)}>
                <SelectTrigger className="bg-purple-800 border-purple-600 text-white w-full sm:w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="recent">Most Recent</SelectItem>
                  <SelectItem value="score">Best Score</SelectItem>
                  <SelectItem value="title">Title A-Z</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Quizzes Grid */}
        {filteredAndSorted.length === 0 ? (
          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
            <CardContent className="p-12 text-center">
              <BookOpen className="h-16 w-16 mx-auto mb-4 text-purple-400 opacity-50" />
              <h3 className="text-xl font-semibold mb-2">No Saved Quizzes</h3>
              <p className="text-purple-200 mb-6">Save quizzes while taking them to access them here</p>
              <Link href="/quiz">
                <Button className="bg-purple-600 hover:bg-purple-700">
                  <Brain className="h-4 w-4 mr-2" />
                  Browse Quizzes
                </Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
            {filteredAndSorted.map((quiz, index) => (
              <Card
                key={quiz.id}
                className="bg-white/10 backdrop-blur-sm border-purple-400 text-white hover:border-purple-300 transition-all duration-300 transform hover:scale-105 animate-in fade-in slide-in-from-bottom"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg mb-2">{quiz.title}</CardTitle>
                      <div className="flex flex-wrap gap-2">
                        <Badge className={getDifficultyColor(quiz.difficulty)}>
                          {quiz.difficulty}
                        </Badge>
                        <Badge variant="outline" className="border-purple-500 text-purple-300">
                          {quiz.quizType.replace("_", " ")}
                        </Badge>
                      </div>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" className="text-purple-300 hover:text-white">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent className="bg-purple-900 border-purple-600">
                        <DropdownMenuItem
                          onClick={() => handleRemoveSaved(quiz.quizId)}
                          className="text-red-400 hover:bg-red-900/20 cursor-pointer"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Remove
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-purple-200">Questions</span>
                      <span className="font-semibold">{quiz.totalQuestions}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-purple-200 flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        Time Limit
                      </span>
                      <span className="font-semibold">{quiz.timeLimit} min</span>
                    </div>
                    {quiz.bestScore !== undefined && (
                      <div className="flex items-center justify-between">
                        <span className="text-purple-200 flex items-center gap-1">
                          <Star className="h-3 w-3" />
                          Best Score
                        </span>
                        <span className="font-bold text-yellow-400">{quiz.bestScore}%</span>
                      </div>
                    )}
                    <div className="flex items-center justify-between">
                      <span className="text-purple-200">Times Taken</span>
                      <span className="font-semibold">{quiz.timesTaken}</span>
                    </div>
                  </div>
                  {quiz.lastTaken && (
                    <div className="flex items-center gap-2 text-xs text-purple-300 pt-2 border-t border-purple-700">
                      <Calendar className="h-3 w-3" />
                      <span>Last taken: {new Date(quiz.lastTaken).toLocaleDateString()}</span>
                    </div>
                  )}
                  <Button
                    onClick={() => handleTakeQuiz(quiz.quizId)}
                    className="w-full bg-purple-600 hover:bg-purple-700"
                  >
                    <Play className="h-4 w-4 mr-2" />
                    Take Quiz
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




