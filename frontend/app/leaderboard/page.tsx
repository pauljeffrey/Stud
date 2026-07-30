"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Badge } from "@/app/components/ui/badge"
import { Skeleton } from "@/app/components/ui/skeleton"
import { Button } from "@/app/components/ui/button"
import { Trophy, Crown, Medal, Award, Users, TrendingUp, Target } from "lucide-react"
import Link from "next/link"
import { apiFetch } from "@/app/lib/auth"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/app/components/ui/select"
import { Avatar, AvatarFallback, AvatarImage } from "@/app/components/ui/avatar"

interface LeaderboardEntry {
  rank: number
  userId: string
  userName: string
  avatarUrl?: string
  score: number
  level: number
  xp: number
  gamesCompleted: number
  quizzesCompleted: number
  averageScore: number
}

export default function LeaderboardPage() {
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [category, setCategory] = useState<"overall" | "games" | "quizzes" | "learning">("overall")
  const [period, setPeriod] = useState<"daily" | "weekly" | "monthly" | "all_time">("all_time")
  const [currentUserRank, setCurrentUserRank] = useState<number | null>(null)

  useEffect(() => {
    loadLeaderboard()
  }, [category, period])

  const loadLeaderboard = async () => {
    try {
      setIsLoading(true)
      const response = await apiFetch(`/api/leaderboard?category=${category}&period=${period}`)

      if (response.ok) {
        const data = await response.json()
        setLeaderboard(data.leaderboard || [])
        setCurrentUserRank(data.userRank || null)
      } else {
        // Mock data
        setLeaderboard([
          {
            rank: 1,
            userId: "user1",
            userName: "Dr. Sarah Chen",
            score: 15420,
            level: 15,
            xp: 15420,
            gamesCompleted: 45,
            quizzesCompleted: 120,
            averageScore: 94,
          },
          {
            rank: 2,
            userId: "user2",
            userName: "Dr. Michael Rodriguez",
            score: 14230,
            level: 14,
            xp: 14230,
            gamesCompleted: 38,
            quizzesCompleted: 105,
            averageScore: 91,
          },
          {
            rank: 3,
            userId: "user3",
            userName: "Dr. Emily Johnson",
            score: 13850,
            level: 13,
            xp: 13850,
            gamesCompleted: 42,
            quizzesCompleted: 98,
            averageScore: 89,
          },
          {
            rank: 4,
            userId: "user4",
            userName: "Dr. James Wilson",
            score: 12500,
            level: 12,
            xp: 12500,
            gamesCompleted: 35,
            quizzesCompleted: 87,
            averageScore: 87,
          },
          {
            rank: 5,
            userId: "user5",
            userName: "Dr. Lisa Anderson",
            score: 11800,
            level: 11,
            xp: 11800,
            gamesCompleted: 32,
            quizzesCompleted: 82,
            averageScore: 85,
          },
        ])
        setCurrentUserRank(12)
      }
    } catch (error) {
      console.error("Failed to load leaderboard:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const getRankIcon = (rank: number) => {
    if (rank === 1) return <Crown className="h-6 w-6 text-yellow-400" />
    if (rank === 2) return <Medal className="h-6 w-6 text-gray-400" />
    if (rank === 3) return <Medal className="h-6 w-6 text-orange-400" />
    return <span className="text-lg font-bold text-purple-300">#{rank}</span>
  }

  const getRankBadgeColor = (rank: number) => {
    if (rank === 1) return "bg-gradient-to-r from-yellow-600 to-orange-600"
    if (rank === 2) return "bg-gradient-to-r from-gray-400 to-gray-600"
    if (rank === 3) return "bg-gradient-to-r from-orange-400 to-orange-600"
    return "bg-purple-800"
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-purple-900 via-purple-800 to-purple-900 p-4">
        <div className="max-w-7xl mx-auto space-y-6">
          <Skeleton className="h-16 w-full bg-purple-800/50" />
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-20 w-full bg-purple-800/50" />
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
              Leaderboard
            </h1>
            <p className="text-purple-200 text-lg">Compete with medical professionals worldwide</p>
          </div>
          <Link href="/dashboard">
            <Button variant="outline" className="border-purple-400 text-white hover:bg-purple-800">
              Back to Dashboard
            </Button>
          </Link>
        </div>

        {/* Filters */}
        <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
          <CardContent className="p-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <label className="text-sm text-purple-200 mb-2 block">Category</label>
                <Select value={category} onValueChange={(value: any) => setCategory(value)}>
                  <SelectTrigger className="bg-purple-800 border-purple-600 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="overall">Overall</SelectItem>
                    <SelectItem value="games">Games</SelectItem>
                    <SelectItem value="quizzes">Quizzes</SelectItem>
                    <SelectItem value="learning">Learning</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex-1">
                <label className="text-sm text-purple-200 mb-2 block">Period</label>
                <Select value={period} onValueChange={(value: any) => setPeriod(value)}>
                  <SelectTrigger className="bg-purple-800 border-purple-600 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="daily">Daily</SelectItem>
                    <SelectItem value="weekly">Weekly</SelectItem>
                    <SelectItem value="monthly">Monthly</SelectItem>
                    <SelectItem value="all_time">All Time</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Top 3 Podium */}
        {leaderboard.length >= 3 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {/* 2nd Place */}
            <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white order-2 md:order-1 transform hover:scale-105 transition-all">
              <CardContent className="p-6 text-center">
                <div className="flex justify-center mb-4">
                  <div className="relative">
                    <Avatar className="h-20 w-20 border-4 border-gray-400">
                      <AvatarImage src={leaderboard[1].avatarUrl} />
                      <AvatarFallback>{leaderboard[1].userName.charAt(0)}</AvatarFallback>
                    </Avatar>
                    <div className="absolute -top-2 -right-2 bg-gray-600 rounded-full p-1">
                      <Medal className="h-5 w-5 text-white" />
                    </div>
                  </div>
                </div>
                <Badge className="bg-gray-600 mb-2">2nd Place</Badge>
                <h3 className="font-bold text-lg mb-1">{leaderboard[1].userName}</h3>
                <p className="text-2xl font-bold text-gray-300">{leaderboard[1].score.toLocaleString()}</p>
                <p className="text-sm text-purple-200 mt-2">Level {leaderboard[1].level}</p>
              </CardContent>
            </Card>

            {/* 1st Place */}
            <Card className="bg-gradient-to-br from-yellow-600/30 to-orange-600/30 backdrop-blur-sm border-yellow-400 border-2 text-white order-1 md:order-2 transform hover:scale-105 transition-all shadow-2xl shadow-yellow-500/50">
              <CardContent className="p-6 text-center">
                <div className="flex justify-center mb-4">
                  <div className="relative">
                    <Avatar className="h-24 w-24 border-4 border-yellow-400">
                      <AvatarImage src={leaderboard[0].avatarUrl} />
                      <AvatarFallback>{leaderboard[0].userName.charAt(0)}</AvatarFallback>
                    </Avatar>
                    <div className="absolute -top-2 -right-2 bg-yellow-600 rounded-full p-1">
                      <Crown className="h-6 w-6 text-white" />
                    </div>
                  </div>
                </div>
                <Badge className="bg-yellow-600 mb-2">1st Place</Badge>
                <h3 className="font-bold text-xl mb-1">{leaderboard[0].userName}</h3>
                <p className="text-3xl font-bold text-yellow-300">{leaderboard[0].score.toLocaleString()}</p>
                <p className="text-sm text-purple-200 mt-2">Level {leaderboard[0].level}</p>
              </CardContent>
            </Card>

            {/* 3rd Place */}
            <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white order-3 transform hover:scale-105 transition-all">
              <CardContent className="p-6 text-center">
                <div className="flex justify-center mb-4">
                  <div className="relative">
                    <Avatar className="h-20 w-20 border-4 border-orange-400">
                      <AvatarImage src={leaderboard[2].avatarUrl} />
                      <AvatarFallback>{leaderboard[2].userName.charAt(0)}</AvatarFallback>
                    </Avatar>
                    <div className="absolute -top-2 -right-2 bg-orange-600 rounded-full p-1">
                      <Medal className="h-5 w-5 text-white" />
                    </div>
                  </div>
                </div>
                <Badge className="bg-orange-600 mb-2">3rd Place</Badge>
                <h3 className="font-bold text-lg mb-1">{leaderboard[2].userName}</h3>
                <p className="text-2xl font-bold text-orange-300">{leaderboard[2].score.toLocaleString()}</p>
                <p className="text-sm text-purple-200 mt-2">Level {leaderboard[2].level}</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Rest of Leaderboard */}
        <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Rankings
            </CardTitle>
            <CardDescription className="text-purple-200">
              {category === "overall" ? "Overall" : category.charAt(0).toUpperCase() + category.slice(1)} rankings
              for {period === "all_time" ? "all time" : period}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {leaderboard.slice(3).map((entry, index) => (
                <div
                  key={entry.userId}
                  className="flex items-center gap-4 p-4 bg-purple-800/50 backdrop-blur-sm rounded-lg border border-purple-700 hover:border-purple-500 transition-all duration-300 transform hover:scale-[1.02] animate-in fade-in slide-in-from-left"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div className="flex-shrink-0 w-12 text-center">
                    <span className="text-lg font-bold text-purple-300">#{entry.rank}</span>
                  </div>
                  <Avatar className="h-12 w-12 border-2 border-purple-600">
                    <AvatarImage src={entry.avatarUrl} />
                    <AvatarFallback>{entry.userName.charAt(0)}</AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold truncate">{entry.userName}</h3>
                    <div className="flex items-center gap-4 mt-1 text-sm text-purple-200">
                      <span>Level {entry.level}</span>
                      <span>•</span>
                      <span>{entry.gamesCompleted} games</span>
                      <span>•</span>
                      <span>{entry.quizzesCompleted} quizzes</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-bold text-yellow-400">{entry.score.toLocaleString()}</p>
                    <p className="text-xs text-purple-300">points</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Current User Rank */}
        {currentUserRank !== null && (
          <Card className="bg-gradient-to-r from-purple-600/50 to-pink-600/50 backdrop-blur-sm border-purple-400 text-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-purple-200 mb-1">Your Rank</p>
                  <p className="text-3xl font-bold">#{currentUserRank}</p>
                </div>
                <Target className="h-12 w-12 text-purple-300" />
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}




