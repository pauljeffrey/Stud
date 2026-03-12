"use client"

import React, { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Skeleton } from "@/app/components/ui/skeleton"
import { Button } from "@/app/components/ui/button"
import { Badge } from "@/app/components/ui/badge"
import { Progress } from "@/app/components/ui/progress"
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Clock,
  Target,
  Brain,
  BookOpen,
  Trophy,
  Calendar,
  ArrowLeft,
  Play,
  Star,
} from "lucide-react"
import Link from "next/link"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/app/components/ui/select"

interface AnalyticsData {
  totalGames: number
  totalQuizzes: number
  totalLearningHours: number
  averageScore: number
  gamesCreated: number
  gamesPlayed: number
  gamesCompleted: number
  quizzesTaken: number
  quizzesPassed: number
  documentsUploaded: number
  apiRequests: number
  weeklyStats: {
    games: number
    quizzes: number
    learningHours: number
  }
  monthlyStats: {
    games: number
    quizzes: number
    learningHours: number
  }
  scoreTrend: number[]
  activityByDay: { day: string; games: number; quizzes: number; learning: number }[]
}

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [timeRange, setTimeRange] = useState<"7d" | "30d" | "90d" | "all">("30d")

  useEffect(() => {
    loadAnalytics()
  }, [timeRange])

  const loadAnalytics = async () => {
    try {
      setIsLoading(true)
      const response = await fetch(`/api/analytics?range=${timeRange}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setAnalytics(data)
      } else {
        // Mock data
        setAnalytics({
          totalGames: 45,
          totalQuizzes: 120,
          totalLearningHours: 24.5,
          averageScore: 87,
          gamesCreated: 45,
          gamesPlayed: 42,
          gamesCompleted: 38,
          quizzesTaken: 120,
          quizzesPassed: 105,
          documentsUploaded: 15,
          apiRequests: 1250,
          weeklyStats: {
            games: 8,
            quizzes: 15,
            learningHours: 3.5,
          },
          monthlyStats: {
            games: 32,
            quizzes: 85,
            learningHours: 12.5,
          },
          scoreTrend: [82, 85, 84, 87, 86, 89, 87],
          activityByDay: [
            { day: "Mon", games: 3, quizzes: 5, learning: 1.5 },
            { day: "Tue", games: 2, quizzes: 4, learning: 1.2 },
            { day: "Wed", games: 4, quizzes: 6, learning: 2.0 },
            { day: "Thu", games: 3, quizzes: 5, learning: 1.8 },
            { day: "Fri", games: 5, quizzes: 7, learning: 2.2 },
            { day: "Sat", games: 6, quizzes: 8, learning: 2.5 },
            { day: "Sun", games: 4, quizzes: 6, learning: 1.8 },
          ],
        })
      }
    } catch (error) {
      console.error("Failed to load analytics:", error)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading || !analytics) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-purple-900 via-purple-800 to-purple-900 p-4">
        <div className="max-w-7xl mx-auto space-y-6">
          <Skeleton className="h-16 w-full bg-purple-800/50" />
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-32 bg-purple-800/50" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  const completionRate = analytics.gamesPlayed > 0 ? (analytics.gamesCompleted / analytics.gamesPlayed) * 100 : 0
  const quizPassRate = analytics.quizzesTaken > 0 ? (analytics.quizzesPassed / analytics.quizzesTaken) * 100 : 0

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-900 via-purple-800 to-purple-900 p-4 md:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 animate-in fade-in slide-in-from-top-4 duration-700">
          <div>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-2 bg-gradient-to-r from-white to-purple-200 bg-clip-text text-transparent flex items-center gap-3">
              <BarChart3 className="h-10 w-10 text-purple-400" />
              Analytics Dashboard
            </h1>
            <p className="text-purple-200 text-lg">Track your learning progress and performance</p>
          </div>
          <div className="flex gap-4">
            <Select value={timeRange} onValueChange={(value: any) => setTimeRange(value)}>
              <SelectTrigger className="bg-purple-800 border-purple-600 text-white w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7d">7 Days</SelectItem>
                <SelectItem value="30d">30 Days</SelectItem>
                <SelectItem value="90d">90 Days</SelectItem>
                <SelectItem value="all">All Time</SelectItem>
              </SelectContent>
            </Select>
            <Link href="/dashboard">
              <Button variant="outline" className="border-purple-400 text-white hover:bg-purple-800">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
            </Link>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white hover:border-green-400 transition-all transform hover:scale-105">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <Play className="h-8 w-8 text-green-400" />
                <TrendingUp className="h-5 w-5 text-green-400" />
              </div>
              <p className="text-sm text-purple-200 mb-1">Games Completed</p>
              <p className="text-3xl font-bold">{analytics.gamesCompleted}</p>
              <p className="text-xs text-purple-300 mt-2">
                {completionRate.toFixed(1)}% completion rate
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white hover:border-blue-400 transition-all transform hover:scale-105">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <Brain className="h-8 w-8 text-blue-400" />
                <TrendingUp className="h-5 w-5 text-blue-400" />
              </div>
              <p className="text-sm text-purple-200 mb-1">Quizzes Passed</p>
              <p className="text-3xl font-bold">{analytics.quizzesPassed}</p>
              <p className="text-xs text-purple-300 mt-2">
                {quizPassRate.toFixed(1)}% pass rate
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white hover:border-yellow-400 transition-all transform hover:scale-105">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <Star className="h-8 w-8 text-yellow-400" />
                <TrendingUp className="h-5 w-5 text-yellow-400" />
              </div>
              <p className="text-sm text-purple-200 mb-1">Average Score</p>
              <p className="text-3xl font-bold">{analytics.averageScore}%</p>
              <p className="text-xs text-purple-300 mt-2">Across all quizzes</p>
            </CardContent>
          </Card>

          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white hover:border-purple-300 transition-all transform hover:scale-105">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <Clock className="h-8 w-8 text-purple-400" />
                <BookOpen className="h-5 w-5 text-purple-400" />
              </div>
              <p className="text-sm text-purple-200 mb-1">Learning Hours</p>
              <p className="text-3xl font-bold">{analytics.totalLearningHours.toFixed(1)}h</p>
              <p className="text-xs text-purple-300 mt-2">Total study time</p>
            </CardContent>
          </Card>
        </div>

        {/* Performance Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Performance Overview
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-purple-200">Game Completion Rate</span>
                  <span className="font-semibold">{completionRate.toFixed(1)}%</span>
                </div>
                <Progress value={completionRate} className="h-3" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-purple-200">Quiz Pass Rate</span>
                  <span className="font-semibold">{quizPassRate.toFixed(1)}%</span>
                </div>
                <Progress value={quizPassRate} className="h-3" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-purple-200">Average Score</span>
                  <span className="font-semibold">{analytics.averageScore}%</span>
                </div>
                <Progress value={analytics.averageScore} className="h-3" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Activity Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-purple-800/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Play className="h-5 w-5 text-green-400" />
                  <span>Games Created</span>
                </div>
                <span className="font-bold text-xl">{analytics.gamesCreated}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-purple-800/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Brain className="h-5 w-5 text-blue-400" />
                  <span>Quizzes Taken</span>
                </div>
                <span className="font-bold text-xl">{analytics.quizzesTaken}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-purple-800/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <BookOpen className="h-5 w-5 text-purple-400" />
                  <span>Documents Uploaded</span>
                </div>
                <span className="font-bold text-xl">{analytics.documentsUploaded}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-purple-800/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <BarChart3 className="h-5 w-5 text-yellow-400" />
                  <span>API Requests</span>
                </div>
                <span className="font-bold text-xl">{analytics.apiRequests.toLocaleString()}</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Weekly Activity Chart */}
        <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
          <CardHeader>
            <CardTitle>Weekly Activity</CardTitle>
            <CardDescription className="text-purple-200">Your activity breakdown by day</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-7 gap-2">
              {analytics.activityByDay.map((day, index) => {
                const maxActivity = Math.max(
                  ...analytics.activityByDay.map((d) => d.games + d.quizzes + d.learning)
                )
                const activityHeight = ((day.games + day.quizzes + day.learning) / maxActivity) * 100

                return (
                  <div key={day.day} className="flex flex-col items-center gap-2">
                    <div className="w-full bg-purple-800/50 rounded-t-lg overflow-hidden h-32 flex flex-col justify-end">
                      <div
                        className="bg-gradient-to-t from-purple-600 to-pink-600 w-full transition-all duration-500 animate-in slide-in-from-bottom"
                        style={{
                          height: `${activityHeight}%`,
                          animationDelay: `${index * 100}ms`,
                        }}
                      />
                    </div>
                    <span className="text-xs text-purple-200 font-semibold">{day.day}</span>
                    <span className="text-xs text-purple-300">
                      {day.games + day.quizzes + Math.round(day.learning)}
                    </span>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* Score Trend */}
        <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Score Trend
            </CardTitle>
            <CardDescription className="text-purple-200">Your performance over time</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-end justify-between h-48 gap-2">
              {analytics.scoreTrend.map((score, index) => {
                const maxScore = Math.max(...analytics.scoreTrend)
                const height = (score / maxScore) * 100

                return (
                  <div key={index} className="flex-1 flex flex-col items-center gap-2">
                    <div className="w-full bg-purple-800/50 rounded-t-lg overflow-hidden h-full flex flex-col justify-end">
                      <div
                        className="bg-gradient-to-t from-green-600 to-emerald-600 w-full transition-all duration-500 animate-in slide-in-from-bottom"
                        style={{
                          height: `${height}%`,
                          animationDelay: `${index * 100}ms`,
                        }}
                      />
                    </div>
                    <span className="text-xs text-purple-200">{score}%</span>
                    <span className="text-xs text-purple-300">Day {index + 1}</span>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

