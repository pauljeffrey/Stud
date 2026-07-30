"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Badge } from "@/app/components/ui/badge"
import { Progress } from "@/app/components/ui/progress"
import { Skeleton } from "@/app/components/ui/skeleton"
import { Button } from "@/app/components/ui/button"
import { Trophy, Sparkles, CheckCircle2, XCircle, Filter } from "lucide-react"
import Link from "next/link"
import { apiFetch } from "@/app/lib/auth"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/app/components/ui/select"

interface Achievement {
  id: string
  name: string
  description: string
  icon: string
  earned: boolean
  earnedAt?: string
  rarity: "common" | "rare" | "epic" | "legendary"
  category: "game" | "quiz" | "learning" | "social"
  progress?: number
  maxProgress?: number
  points: number
}

export default function AchievementsPage() {
  const [achievements, setAchievements] = useState<Achievement[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filter, setFilter] = useState<"all" | "earned" | "unearned" | "common" | "rare" | "epic" | "legendary">("all")
  const [categoryFilter, setCategoryFilter] = useState<"all" | "game" | "quiz" | "learning" | "social">("all")

  useEffect(() => {
    loadAchievements()
  }, [])

  const loadAchievements = async () => {
    try {
      setIsLoading(true)
      // Fetch from backend
      const response = await apiFetch("/api/achievements")

      if (response.ok) {
        const data = await response.json()
        setAchievements(data)
      } else {
        // Mock data
        setAchievements([
          {
            id: "1",
            name: "First Steps",
            description: "Complete your first quest",
            icon: "🏃",
            earned: true,
            earnedAt: "2024-01-15",
            rarity: "common",
            category: "game",
            points: 10,
          },
          {
            id: "2",
            name: "Quiz Master",
            description: "Score 90% or higher on 5 quizzes",
            icon: "🧠",
            earned: true,
            earnedAt: "2024-01-20",
            rarity: "rare",
            category: "quiz",
            points: 50,
            progress: 5,
            maxProgress: 5,
          },
          {
            id: "3",
            name: "Dedicated Learner",
            description: "Study for 10 hours total",
            icon: "📚",
            earned: false,
            rarity: "epic",
            category: "learning",
            points: 100,
            progress: 6,
            maxProgress: 10,
          },
          {
            id: "4",
            name: "Game Champion",
            description: "Complete 50 games",
            icon: "🏆",
            earned: false,
            rarity: "legendary",
            category: "game",
            points: 200,
            progress: 8,
            maxProgress: 50,
          },
          {
            id: "5",
            name: "Perfect Score",
            description: "Score 100% on a quiz",
            icon: "⭐",
            earned: false,
            rarity: "rare",
            category: "quiz",
            points: 75,
          },
          {
            id: "6",
            name: "Social Butterfly",
            description: "Add 10 friends",
            icon: "👥",
            earned: false,
            rarity: "rare",
            category: "social",
            points: 50,
            progress: 3,
            maxProgress: 10,
          },
        ])
      }
    } catch (error) {
      console.error("Failed to load achievements:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const getRarityColor = (rarity: string) => {
    switch (rarity) {
      case "legendary":
        return "border-yellow-500 bg-gradient-to-br from-yellow-600/30 to-orange-600/30 shadow-yellow-500/50"
      case "epic":
        return "border-purple-500 bg-gradient-to-br from-purple-600/30 to-pink-600/30 shadow-purple-500/50"
      case "rare":
        return "border-blue-500 bg-gradient-to-br from-blue-600/30 to-cyan-600/30 shadow-blue-500/50"
      default:
        return "border-gray-500 bg-gradient-to-br from-gray-600/30 to-gray-700/30"
    }
  }

  const getRarityBadgeColor = (rarity: string) => {
    switch (rarity) {
      case "legendary":
        return "bg-yellow-600 text-yellow-100 border-yellow-500"
      case "epic":
        return "bg-purple-600 text-purple-100 border-purple-500"
      case "rare":
        return "bg-blue-600 text-blue-100 border-blue-500"
      default:
        return "bg-gray-600 text-gray-100 border-gray-500"
    }
  }

  const filteredAchievements = achievements.filter((achievement) => {
    if (filter === "earned" && !achievement.earned) return false
    if (filter === "unearned" && achievement.earned) return false
    if (filter !== "all" && filter !== "earned" && filter !== "unearned" && achievement.rarity !== filter) return false
    if (categoryFilter !== "all" && achievement.category !== categoryFilter) return false
    return true
  })

  const earnedCount = achievements.filter((a) => a.earned).length
  const totalPoints = achievements.filter((a) => a.earned).reduce((sum, a) => sum + a.points, 0)

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-purple-900 via-purple-800 to-purple-900 p-4">
        <div className="max-w-7xl mx-auto space-y-6">
          <Skeleton className="h-16 w-full bg-purple-800/50" />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Skeleton key={i} className="h-48 bg-purple-800/50" />
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
              <Trophy className="h-10 w-10 text-yellow-400" />
              Achievements
            </h1>
            <p className="text-purple-200 text-lg">Unlock badges and track your progress</p>
          </div>
          <Link href="/dashboard">
            <Button variant="outline" className="border-purple-400 text-white hover:bg-purple-800">
              Back to Dashboard
            </Button>
          </Link>
        </div>

        {/* Stats Summary */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 md:gap-6 animate-in fade-in duration-500">
          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
            <CardContent className="p-6 text-center">
              <div className="text-4xl font-bold mb-2 bg-gradient-to-r from-yellow-400 to-orange-400 bg-clip-text text-transparent">
                {earnedCount}/{achievements.length}
              </div>
              <p className="text-purple-200">Achievements Unlocked</p>
              <Progress value={(earnedCount / achievements.length) * 100} className="mt-4" />
            </CardContent>
          </Card>
          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
            <CardContent className="p-6 text-center">
              <div className="text-4xl font-bold mb-2 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                {totalPoints}
              </div>
              <p className="text-purple-200">Total Points Earned</p>
            </CardContent>
          </Card>
          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
            <CardContent className="p-6 text-center">
              <div className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                {achievements.filter((a) => a.rarity === "legendary" && a.earned).length}
              </div>
              <p className="text-purple-200">Legendary Achievements</p>
            </CardContent>
          </Card>
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
                  <SelectItem value="all">All Achievements</SelectItem>
                  <SelectItem value="earned">Earned</SelectItem>
                  <SelectItem value="unearned">Not Earned</SelectItem>
                  <SelectItem value="common">Common</SelectItem>
                  <SelectItem value="rare">Rare</SelectItem>
                  <SelectItem value="epic">Epic</SelectItem>
                  <SelectItem value="legendary">Legendary</SelectItem>
                </SelectContent>
              </Select>
              <Select value={categoryFilter} onValueChange={(value: any) => setCategoryFilter(value)}>
                <SelectTrigger className="bg-purple-800 border-purple-600 text-white w-full sm:w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  <SelectItem value="game">Game</SelectItem>
                  <SelectItem value="quiz">Quiz</SelectItem>
                  <SelectItem value="learning">Learning</SelectItem>
                  <SelectItem value="social">Social</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Achievements Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
          {filteredAchievements.map((achievement, index) => (
            <Card
              key={achievement.id}
              className={`${getRarityColor(achievement.rarity)} border-2 text-white transition-all duration-300 transform hover:scale-105 hover:shadow-2xl ${
                achievement.earned ? "animate-in fade-in slide-in-from-bottom" : "opacity-75"
              }`}
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className="text-4xl">{achievement.icon}</span>
                    <div>
                      <h3 className="font-bold text-lg">{achievement.name}</h3>
                      <Badge className={`${getRarityBadgeColor(achievement.rarity)} text-xs mt-1`}>
                        {achievement.rarity.toUpperCase()}
                      </Badge>
                    </div>
                  </div>
                  {achievement.earned ? (
                    <CheckCircle2 className="h-6 w-6 text-green-400 flex-shrink-0" />
                  ) : (
                    <XCircle className="h-6 w-6 text-gray-400 flex-shrink-0" />
                  )}
                </div>
                <p className="text-purple-200 mb-4 text-sm">{achievement.description}</p>
                {achievement.earned && achievement.earnedAt && (
                  <p className="text-xs text-purple-300 mb-3">
                    Earned on {new Date(achievement.earnedAt).toLocaleDateString()}
                  </p>
                )}
                {!achievement.earned && achievement.progress !== undefined && achievement.maxProgress && (
                  <div className="mb-3">
                    <div className="flex justify-between text-xs text-purple-300 mb-2">
                      <span>Progress</span>
                      <span>
                        {achievement.progress}/{achievement.maxProgress}
                      </span>
                    </div>
                    <Progress value={(achievement.progress / achievement.maxProgress) * 100} className="h-2" />
                  </div>
                )}
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-purple-600">
                  <span className="text-xs text-purple-300">Points:</span>
                  <span className="font-bold text-yellow-400">{achievement.points} XP</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredAchievements.length === 0 && (
          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
            <CardContent className="p-12 text-center">
              <Trophy className="h-16 w-16 mx-auto mb-4 text-purple-400 opacity-50" />
              <p className="text-purple-200 text-lg">No achievements match your filters</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}




