"use client"

import { useState, useEffect } from "react"
import { Button } from "@/app/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs"
import { Input } from "@/app/components/ui/input"
import { Label } from "@/app/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/app/components/ui/select"
import { Badge } from "@/app/components/ui/badge"
import { Progress } from "@/app/components/ui/progress"
import { Skeleton } from "@/app/components/ui/skeleton"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/app/components/ui/dialog"
import {
  Trophy,
  Star,
  BookOpen,
  Play,
  Settings,
  User,
  Brain,
  Target,
  Clock,
  Award,
  Key,
  Info,
  TrendingUp,
  Users,
  BarChart3,
  Sparkles,
  Zap,
  CheckCircle2,
  XCircle,
  Loader2,
} from "lucide-react"
import { useToast } from "@/app/components/ui/use-toast"
import Link from "next/link"
import { motion } from "framer-motion"

interface UserStats {
  totalQuests: number
  completedQuests: number
  totalQuizzes: number
  averageScore: number
  timeSpent: number
  achievements: Achievement[]
  currentLevel: number
  experiencePoints: number
  totalXP: number
  xpToNextLevel: number
}

interface Achievement {
  id: string
  name: string
  description: string
  icon: string
  earned: boolean
  earnedAt?: string
  rarity?: "common" | "rare" | "epic" | "legendary"
  progress?: number
  maxProgress?: number
}

interface RecentGame {
  id: string
  game_id?: string
  case_id: string
  current_case_number: number
  total_cases: number
  created_at: string
  updated_at: string
  completed_at?: string
  is_completed: boolean
}

interface RecentQuiz {
  id: string
  quiz_id: string
  title: string
  score: number
  time_spent: number
  completed_at: string
}

interface RecentActivity {
  type: "game" | "quiz"
  id: string
  title: string
  timestamp: string
  completed?: boolean
  score?: number
}

const VALID_TABS = ["overview", "achievements", "analytics", "settings"] as const

export default function DashboardPage() {
  const [userStats, setUserStats] = useState<UserStats | null>(null)
  const [recentGames, setRecentGames] = useState<RecentGame[]>([])
  const [recentQuizzes, setRecentQuizzes] = useState<RecentQuiz[]>([])
  const [recentActivities, setRecentActivities] = useState<RecentActivity[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState("overview")
  const [apiSettings, setApiSettings] = useState({
    modelName: "",
    apiKey: "",
    provider: "gemini",
  })
  const { toast } = useToast()

  useEffect(() => {
    loadUserData(true)
    // Honour ?tab= URL parameter so "View All" deep links work
    const params = new URLSearchParams(window.location.search)
    const tab = params.get("tab")
    if (tab && (VALID_TABS as readonly string[]).includes(tab)) {
      setActiveTab(tab)
    }
  }, [])

  const loadUserData = async (isInitialLoad = true) => {
    try {
      if (isInitialLoad) {
        setIsLoading(true)
      }
      const token = localStorage.getItem("token")
      if (!token) {
        // Redirect to login if no token
        window.location.href = "/auth/login"
        return
      }

      // Fetch user stats
      const statsResponse = await fetch("/api/user/stats", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (statsResponse.ok) {
        const statsData = await statsResponse.json()
        if (statsData.success && statsData.stats) {
          const stats = statsData.stats
          setUserStats({
            totalQuests: stats.totalQuests ?? 0,
            completedQuests: stats.completedQuests ?? 0,
            totalQuizzes: stats.totalQuizzes ?? 0,
            averageScore: stats.averageScore ?? 0,
            timeSpent: stats.timeSpent ?? 0,
            currentLevel: stats.currentLevel ?? 1,
            experiencePoints: stats.experiencePoints ?? 0,
            totalXP: stats.totalXP ?? stats.experiencePoints ?? 0,
            xpToNextLevel: stats.xpToNextLevel ?? 1000,
            achievements: statsData.achievements ?? [],
          })
        } else if (statsData.stats) {
          setUserStats({ ...statsData.stats, achievements: statsData.achievements ?? [] })
        } else {
          // Fallback when response ok but structure unexpected
          setUserStats({
            totalQuests: 0,
            completedQuests: 0,
            totalQuizzes: 0,
            averageScore: 0,
            timeSpent: 0,
            currentLevel: 1,
            experiencePoints: 0,
            totalXP: 0,
            xpToNextLevel: 1000,
            achievements: [],
          })
        }
      } else {
        // API error — show zeroed state so new users see a clean slate
        setUserStats({
          totalQuests: 0,
          completedQuests: 0,
          totalQuizzes: 0,
          averageScore: 0,
          timeSpent: 0,
          currentLevel: 1,
          experiencePoints: 0,
          totalXP: 0,
          xpToNextLevel: 1000,
          achievements: [],
        })
      }

      // Fetch recent games
      const gamesResponse = await fetch("/api/user/recent-games?limit=3", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      if (gamesResponse.ok) {
        const gamesData = await gamesResponse.json()
        if (gamesData.success) {
          setRecentGames(gamesData.games || [])
        }
      }

      // Fetch recent quizzes
      const quizzesResponse = await fetch("/api/user/recent-quizzes?limit=3", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      if (quizzesResponse.ok) {
        const quizzesData = await quizzesResponse.json()
        if (quizzesData.success) {
          setRecentQuizzes(quizzesData.quizzes || [])
        }
      }

      // Fetch recent activities
      const activitiesResponse = await fetch("/api/user/recent-activities?limit=5", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      if (activitiesResponse.ok) {
        const activitiesData = await activitiesResponse.json()
        if (activitiesData.success) {
          setRecentActivities(activitiesData.activities || [])
        }
      }

      // Load API settings from database (or fallback to localStorage)
      const settingsResponse = await fetch("/api/user/settings", {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (settingsResponse.ok) {
        const settingsData = await settingsResponse.json()
        if (settingsData.success && settingsData.settings) {
          const s = settingsData.settings
          setApiSettings({
            provider: s.provider || "gemini",
            modelName: s.modelName || "",
            apiKey: s.apiKey || "",
          })
        }
      } else {
        const savedSettings = localStorage.getItem("apiSettings")
        if (savedSettings) {
          setApiSettings(JSON.parse(savedSettings))
        }
      }
    } catch (error) {
      console.error("Failed to load user data:", error)
      setUserStats({
        totalQuests: 0,
        completedQuests: 0,
        totalQuizzes: 0,
        averageScore: 0,
        timeSpent: 0,
        currentLevel: 1,
        experiencePoints: 0,
        totalXP: 0,
        xpToNextLevel: 1000,
        achievements: [],
      })
    } finally {
      setIsLoading(false)
    }
  }

  const saveApiSettings = async () => {
    try {
      const token = localStorage.getItem("token")
      if (token) {
        const response = await fetch("/api/user/settings", {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            provider: apiSettings.provider,
            modelName: apiSettings.modelName,
            apiKey: apiSettings.apiKey,
          }),
        })
        if (response.ok) {
          localStorage.setItem("apiSettings", JSON.stringify(apiSettings))
          toast({
            title: "Settings Saved",
            description: "Your API settings have been saved to your account.",
          })
        } else {
          throw new Error("Failed to save")
        }
      } else {
        localStorage.setItem("apiSettings", JSON.stringify(apiSettings))
        toast({
          title: "Settings Saved",
          description: "Saved locally (log in to sync across devices).",
        })
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save API settings.",
        variant: "destructive",
      })
    }
  }

  const getProviderInstructions = (provider: string) => {
    const instructions = {
      gemini: {
        name: "Google Gemini",
        steps: [
          "Go to Google AI Studio (https://aistudio.google.com/)",
          "Sign in with your Google account",
          "Click on 'Get API Key'",
          "Create a new API key or use an existing one",
          "Copy the API key and paste it above",
        ],
      },
      openai: {
        name: "OpenAI",
        steps: [
          "Go to OpenAI Platform (https://platform.openai.com/)",
          "Sign in to your account",
          "Navigate to API Keys section",
          "Click 'Create new secret key'",
          "Copy the API key and paste it above",
        ],
      },
      anthropic: {
        name: "Anthropic Claude",
        steps: [
          "Go to Anthropic Console (https://console.anthropic.com/)",
          "Sign in to your account",
          "Navigate to API Keys",
          "Generate a new API key",
          "Copy the API key and paste it above",
        ],
      },
    }
    return instructions[provider as keyof typeof instructions] || instructions.gemini
  }

  const getRarityColor = (rarity?: string) => {
    switch (rarity) {
      case "legendary":
        return "border-yellow-500 bg-gradient-to-br from-yellow-600/20 to-orange-600/20"
      case "epic":
        return "border-purple-500 bg-gradient-to-br from-purple-600/20 to-pink-600/20"
      case "rare":
        return "border-blue-500 bg-gradient-to-br from-blue-600/20 to-cyan-600/20"
      default:
        return "border-gray-500 bg-gradient-to-br from-gray-600/20 to-gray-700/20"
    }
  }

  if (isLoading && !userStats) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-purple-900 via-purple-800 to-purple-900 p-4">
        <div className="max-w-7xl mx-auto space-y-6">
          <Skeleton className="h-16 w-full bg-purple-800/50" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-32 bg-purple-800/50" />
            ))}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-32 bg-purple-800/50" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (!userStats) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-purple-900 via-purple-800 to-purple-900 p-4 flex items-center justify-center">
        <p className="text-purple-200">Unable to load dashboard. Try refreshing or sign in again.</p>
      </div>
    )
  }

  const totalForLevel = userStats.totalXP + userStats.xpToNextLevel
  const levelProgress = totalForLevel > 0 ? (userStats.totalXP / totalForLevel) * 100 : 0

  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-[#0A1128] to-[#4C1D95] p-4 md:p-6 lg:p-8 relative overflow-x-hidden">
      {/* Animated Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
        <motion.div
          className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-900/30 rounded-full blur-3xl"
          animate={{
            x: [0, 100, -50, 0],
            y: [0, 50, -30, 0],
            scale: [1, 1.3, 0.9, 1],
            rotate: [0, 90, 180, 360],
          }}
          transition={{
            duration: 12,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <motion.div
          className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-900/30 rounded-full blur-3xl"
          animate={{
            x: [0, -100, 50, 0],
            y: [0, -50, 30, 0],
            scale: [1, 1.4, 0.8, 1],
            rotate: [360, 270, 180, 0],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      </div>

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Header with Animation */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="text-gray-400 text-lg"
            >
              Welcome back, {userStats ? "Dr. " + (localStorage.getItem("user") ? JSON.parse(localStorage.getItem("user") || "{}").name?.split(" ")[0] || "User" : "User") : "User"}!
            </motion.p>
          </div>
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <Badge
              variant="secondary"
              className="bg-gradient-to-r from-purple-600 to-pink-600 text-white text-lg px-4 py-2 animate-pulse"
            >
              <Sparkles className="h-4 w-4 mr-2" />
              Level {userStats.currentLevel}
            </Badge>
            <div className="text-white text-right bg-purple-800/50 backdrop-blur-sm rounded-lg p-3 border border-purple-600">
              <p className="text-sm text-purple-200">Experience Points</p>
              <p className="text-2xl font-bold bg-gradient-to-r from-yellow-400 to-orange-400 bg-clip-text text-transparent">
                {userStats.experiencePoints.toLocaleString()} XP
              </p>
              <Progress value={levelProgress} className="mt-2 h-2" />
            </div>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="bg-purple-800/80 backdrop-blur-sm text-white border border-purple-600">
            <TabsTrigger value="overview" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">
              <User className="h-4 w-4 mr-2" />
              <span className="hidden sm:inline">Overview</span>
            </TabsTrigger>
            <TabsTrigger value="achievements" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">
              <Trophy className="h-4 w-4 mr-2" />
              <span className="hidden sm:inline">Achievements</span>
            </TabsTrigger>
            <TabsTrigger value="analytics" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">
              <BarChart3 className="h-4 w-4 mr-2" />
              <span className="hidden sm:inline">Analytics</span>
            </TabsTrigger>
            <TabsTrigger value="settings" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">
              <Settings className="h-4 w-4 mr-2" />
              <span className="hidden sm:inline">Settings</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6 animate-in fade-in duration-500">
            {/* Quick Actions with Hover Effects */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
              <Link href="/mediquest" className="group">
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Card className="bg-black/60 backdrop-blur-md border-purple-700/40 text-white hover:border-purple-500/60 transition-all duration-300 cursor-pointer hover:shadow-2xl hover:shadow-purple-500/50">
                    <CardContent className="p-6">
                      <div className="flex items-center gap-4">
                        <motion.div
                          className="p-3 bg-gradient-to-br from-purple-700 to-purple-900 rounded-lg"
                          whileHover={{ rotate: 360 }}
                          transition={{ duration: 0.5 }}
                        >
                          <Play className="h-6 w-6" />
                        </motion.div>
                        <div>
                          <h3 className="font-semibold text-lg">Start Quest</h3>
                          <p className="text-sm text-gray-400">Begin a new medical adventure</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              </Link>

              <Link href="/quiz" className="group">
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Card className="bg-black/60 backdrop-blur-md border-purple-700/40 text-white hover:border-purple-500/60 transition-all duration-300 cursor-pointer hover:shadow-2xl hover:shadow-blue-500/50">
                    <CardContent className="p-6">
                      <div className="flex items-center gap-4">
                        <motion.div
                          className="p-3 bg-gradient-to-br from-blue-800 to-blue-900 rounded-lg"
                          whileHover={{ rotate: 360 }}
                          transition={{ duration: 0.5 }}
                        >
                          <Brain className="h-6 w-6" />
                        </motion.div>
                        <div>
                          <h3 className="font-semibold text-lg">Take Quiz</h3>
                          <p className="text-sm text-gray-400">Test your medical knowledge</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              </Link>

              <Link href="/study" className="group">
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Card className="bg-black/60 backdrop-blur-md border-purple-700/40 text-white hover:border-purple-500/60 transition-all duration-300 cursor-pointer hover:shadow-2xl hover:shadow-purple-500/50">
                    <CardContent className="p-6">
                      <div className="flex items-center gap-4">
                        <motion.div
                          className="p-3 bg-gradient-to-br from-purple-800 to-purple-900 rounded-lg"
                          whileHover={{ rotate: 360 }}
                          transition={{ duration: 0.5 }}
                        >
                          <BookOpen className="h-6 w-6" />
                        </motion.div>
                        <div>
                          <h3 className="font-semibold text-lg">Study Materials</h3>
                          <p className="text-sm text-gray-400">Learn with AI assistance</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              </Link>
            </div>

            {/* Animated Stats Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                whileHover={{ scale: 1.05 }}
              >
                <Card className="bg-black/60 backdrop-blur-md border-purple-700/40 text-white hover:border-purple-500/60 transition-all duration-300">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <motion.div
                        animate={{ rotate: [0, 10, -10, 0] }}
                        transition={{ duration: 2, repeat: Infinity }}
                      >
                        <Target className="h-8 w-8 text-purple-400" />
                      </motion.div>
                      <TrendingUp className="h-5 w-5 text-purple-400" />
                    </div>
                    <p className="text-sm text-gray-400 mb-1">Quests Completed</p>
                    <p className="text-3xl font-bold mb-2">
                      {userStats.completedQuests}/{userStats.totalQuests}
                    </p>
                    <Progress
                      value={userStats.totalQuests > 0 ? (userStats.completedQuests / userStats.totalQuests) * 100 : 0}
                      className="h-2 bg-purple-900/50"
                    />
                  </CardContent>
                </Card>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                whileHover={{ scale: 1.05 }}
              >
                <Card className="bg-black/60 backdrop-blur-md border-purple-700/40 text-white hover:border-purple-500/60 transition-all duration-300">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <motion.div
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 2, repeat: Infinity }}
                      >
                        <Star className="h-8 w-8 text-purple-400" />
                      </motion.div>
                      <Zap className="h-5 w-5 text-purple-400" />
                    </div>
                    <p className="text-sm text-gray-400 mb-1">Average Score</p>
                    <p className="text-3xl font-bold">{userStats.averageScore}%</p>
                  </CardContent>
                </Card>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                whileHover={{ scale: 1.05 }}
              >
                <Card className="bg-black/60 backdrop-blur-md border-purple-700/40 text-white hover:border-purple-500/60 transition-all duration-300">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <motion.div
                        animate={{ rotate: [0, 360] }}
                        transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                      >
                        <Clock className="h-8 w-8 text-blue-400" />
                      </motion.div>
                    </div>
                    <p className="text-sm text-gray-400 mb-1">Time Spent</p>
                    <p className="text-3xl font-bold">{Math.floor(userStats.timeSpent / 60)}h</p>
                    <p className="text-xs text-gray-500 mt-1">{userStats.timeSpent % 60}m</p>
                  </CardContent>
                </Card>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                whileHover={{ scale: 1.05 }}
              >
                <Card className="bg-black/60 backdrop-blur-md border-purple-700/40 text-white hover:border-purple-500/60 transition-all duration-300">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <Award className="h-8 w-8 text-purple-400" />
                      <Link href="/dashboard?tab=achievements">
                        <Button variant="ghost" size="sm" className="text-purple-300 hover:text-white">
                          View All
                        </Button>
                      </Link>
                    </div>
                    <p className="text-sm text-gray-400 mb-1">Achievements</p>
                    <p className="text-3xl font-bold">
                      {userStats.achievements?.filter((a) => a.earned).length ?? 0}/{userStats.achievements?.length ?? 0}
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            </div>

            {/* Recent Activity - real data from API */}
            <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5 text-yellow-400 animate-pulse" />
                  Recent Activity
                </CardTitle>
                <CardDescription className="text-purple-200">Your latest learning activities</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {recentActivities.length > 0 ? (
                    recentActivities.map((activity) => {
                      const Icon = activity.type === "game" ? Trophy : Brain
                      const href = activity.type === "game" ? "/mediquest" : "/quiz"
                      const timeStr = activity.timestamp
                        ? new Date(activity.timestamp).toLocaleDateString(undefined, {
                            month: "short",
                            day: "numeric",
                            hour: "numeric",
                            minute: "2-digit",
                          })
                        : "Recently"
                      return (
                        <Link
                          key={activity.id}
                          href={href}
                          className="flex items-center gap-4 p-4 bg-purple-800/50 backdrop-blur-sm rounded-lg border border-purple-700 hover:border-purple-500 transition-all duration-300 transform hover:scale-[1.02] cursor-pointer"
                        >
                          <Icon className="h-5 w-5 text-purple-400 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <p className="font-semibold truncate">{activity.title}</p>
                            <p className="text-sm text-purple-200">
                              {activity.type === "quiz" && activity.score != null ? `Score: ${activity.score}% • ` : ""}
                              {timeStr}
                            </p>
                          </div>
                        </Link>
                      )
                    })
                  ) : (
                    <p className="text-purple-300 py-6 text-center">No recent activity yet. Start a quest or take a quiz!</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="achievements" className="space-y-6 animate-in fade-in duration-500">
            <Card className="bg-black/60 backdrop-blur-md border-purple-700/40 text-white">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Trophy className="h-5 w-5 text-purple-400" />
                  Your Achievements
                </CardTitle>
                <CardDescription className="text-gray-400">Track your progress and unlock new badges</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {(userStats.achievements ?? []).map((achievement, index) => (
                    <div
                      key={achievement.id}
                      className={`p-5 rounded-lg border-2 transition-all duration-300 transform hover:scale-105 ${
                        achievement.earned
                          ? `${getRarityColor(achievement.rarity)} shadow-lg shadow-purple-500/50`
                          : "bg-purple-900/30 border-purple-700/40 opacity-60"
                      } animate-in fade-in slide-in-from-bottom`}
                      style={{ animationDelay: `${index * 100}ms` }}
                    >
                      <div className="flex items-start gap-3 mb-3">
                        <span className="text-3xl">{achievement.icon}</span>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <h3 className="font-semibold text-lg">{achievement.name}</h3>
                            {achievement.earned ? (
                              <CheckCircle2 className="h-5 w-5 text-green-400" />
                            ) : (
                              <XCircle className="h-5 w-5 text-gray-400" />
                            )}
                          </div>
                          {achievement.earned && achievement.earnedAt && (
                            <p className="text-xs text-purple-200 mt-1">
                              Earned on {new Date(achievement.earnedAt).toLocaleDateString()}
                            </p>
                          )}
                          {achievement.rarity && (
                            <Badge
                              variant="outline"
                              className={`mt-2 text-xs ${
                                achievement.rarity === "legendary"
                                  ? "border-yellow-500 text-yellow-400"
                                  : achievement.rarity === "epic"
                                    ? "border-purple-500 text-purple-400"
                                    : achievement.rarity === "rare"
                                      ? "border-blue-500 text-blue-400"
                                      : "border-gray-500 text-gray-400"
                              }`}
                            >
                              {achievement.rarity.toUpperCase()}
                            </Badge>
                          )}
                        </div>
                      </div>
                      <p className="text-sm text-purple-200 mb-3">{achievement.description}</p>
                      {!achievement.earned && achievement.progress !== undefined && achievement.maxProgress && (
                        <div>
                          <div className="flex justify-between text-xs text-purple-300 mb-1">
                            <span>Progress</span>
                            <span>
                              {achievement.progress}/{achievement.maxProgress}
                            </span>
                          </div>
                          <Progress value={(achievement.progress / achievement.maxProgress) * 100} className="h-2" />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="analytics" className="space-y-6 animate-in fade-in duration-500">
            <Card className="bg-black/60 backdrop-blur-md border-purple-700/40 text-white">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-purple-400" />
                  Performance Analytics
                </CardTitle>
                <CardDescription className="text-gray-400">Your learning metrics at a glance</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="p-4 bg-purple-900/40 rounded-lg border border-purple-700/40">
                    <p className="text-sm text-gray-400 mb-1">Quests Completed</p>
                    <p className="text-3xl font-bold text-white">{userStats?.completedQuests ?? 0}</p>
                    <p className="text-xs text-purple-300 mt-1">out of {userStats?.totalQuests ?? 0} total</p>
                    <Progress
                      value={userStats && userStats.totalQuests > 0 ? (userStats.completedQuests / userStats.totalQuests) * 100 : 0}
                      className="mt-2 h-2"
                    />
                  </div>
                  <div className="p-4 bg-purple-900/40 rounded-lg border border-purple-700/40">
                    <p className="text-sm text-gray-400 mb-1">Quizzes Taken</p>
                    <p className="text-3xl font-bold text-white">{userStats?.totalQuizzes ?? 0}</p>
                    <p className="text-xs text-purple-300 mt-1">Average score: {userStats?.averageScore ?? 0}%</p>
                    <Progress value={userStats?.averageScore ?? 0} className="mt-2 h-2" />
                  </div>
                  <div className="p-4 bg-purple-900/40 rounded-lg border border-purple-700/40">
                    <p className="text-sm text-gray-400 mb-1">Total Study Time</p>
                    <p className="text-3xl font-bold text-white">{Math.floor((userStats?.timeSpent ?? 0) / 60)}h {(userStats?.timeSpent ?? 0) % 60}m</p>
                    <p className="text-xs text-purple-300 mt-1">Keep it up!</p>
                  </div>
                  <div className="p-4 bg-purple-900/40 rounded-lg border border-purple-700/40">
                    <p className="text-sm text-gray-400 mb-1">Achievements Earned</p>
                    <p className="text-3xl font-bold text-white">
                      {userStats?.achievements?.filter((a) => a.earned).length ?? 0}
                    </p>
                    <p className="text-xs text-purple-300 mt-1">out of {userStats?.achievements?.length ?? 0} total</p>
                    <Progress
                      value={
                        userStats && userStats.achievements?.length
                          ? (userStats.achievements.filter((a) => a.earned).length / userStats.achievements.length) * 100
                          : 0
                      }
                      className="mt-2 h-2"
                    />
                  </div>
                </div>
                <div className="p-4 bg-purple-900/40 rounded-lg border border-purple-700/40">
                  <p className="text-sm text-gray-400 mb-2">Level Progress</p>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-white font-semibold">Level {userStats?.currentLevel ?? 1}</span>
                    <span className="text-purple-300 text-sm">{userStats?.experiencePoints ?? 0} / {(userStats?.experiencePoints ?? 0) + (userStats?.xpToNextLevel ?? 1000)} XP</span>
                  </div>
                  <Progress
                    value={
                      userStats && userStats.xpToNextLevel > 0
                        ? (userStats.experiencePoints / (userStats.experiencePoints + userStats.xpToNextLevel)) * 100
                        : 0
                    }
                    className="h-3"
                  />
                  <p className="text-xs text-gray-500 mt-1">{userStats?.xpToNextLevel ?? 1000} XP to next level</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="settings" className="space-y-6 animate-in fade-in duration-500">
            <Card className="bg-black/60 backdrop-blur-md border-purple-700/40 text-white">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Key className="h-5 w-5 text-purple-400" />
                  AI Model Configuration
                </CardTitle>
                <CardDescription className="text-gray-400">
                  Configure your preferred AI model and API key for personalized experience
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="provider">AI Provider</Label>
                    <Select
                      value={apiSettings.provider}
                      onValueChange={(value) => setApiSettings((prev) => ({ ...prev, provider: value }))}
                    >
                      <SelectTrigger className="bg-black/50 border-purple-700/40 text-white">
                        <SelectValue placeholder="Select AI provider" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="gemini">Google Gemini</SelectItem>
                        <SelectItem value="openai">OpenAI GPT</SelectItem>
                        <SelectItem value="anthropic">Anthropic Claude</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="modelName">Model Name</Label>
                    <Input
                      id="modelName"
                      name="ai-model-name"
                      autoComplete="off"
                      value={apiSettings.modelName}
                      onChange={(e) => setApiSettings((prev) => ({ ...prev, modelName: e.target.value }))}
                      placeholder="e.g., gemini-2.5-flash-preview-05-20"
                      className="bg-black/50 border-purple-700/40 text-white placeholder-gray-500"
                    />
                  </div>

                  <div>
                    <Label htmlFor="apiKey">API Key</Label>
                    <Input
                      id="apiKey"
                      name="ai-api-key"
                      type="password"
                      autoComplete="new-password"
                      value={apiSettings.apiKey}
                      onChange={(e) => setApiSettings((prev) => ({ ...prev, apiKey: e.target.value }))}
                      placeholder="Enter your API key"
                      className="bg-black/50 border-purple-700/40 text-white placeholder-gray-500"
                    />
                  </div>

                  <Dialog>
                    <DialogTrigger asChild>
                      <Button
                        variant="outline"
                        className="border-purple-400 text-white hover:bg-purple-800 bg-transparent"
                      >
                        <Info className="h-4 w-4 mr-2" />
                        How to get API Key
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="bg-purple-900 text-white border-purple-500">
                      <DialogHeader>
                        <DialogTitle>
                          How to get {getProviderInstructions(apiSettings.provider).name} API Key
                        </DialogTitle>
                        <DialogDescription className="text-purple-200">
                          Follow these steps to obtain your API key:
                        </DialogDescription>
                      </DialogHeader>
                      <div className="space-y-2">
                        {getProviderInstructions(apiSettings.provider).steps.map((step, index) => (
                          <div key={index} className="flex gap-3">
                            <span className="flex-shrink-0 w-6 h-6 bg-purple-600 rounded-full flex items-center justify-center text-sm">
                              {index + 1}
                            </span>
                            <p className="text-sm">{step}</p>
                          </div>
                        ))}
                      </div>
                    </DialogContent>
                  </Dialog>

                  <div className="bg-purple-900/30 border border-purple-700/40 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2 flex items-center gap-2 text-purple-300">
                      <Info className="h-4 w-4" />
                      Important Notes
                    </h4>
                    <ul className="text-sm text-gray-400 space-y-1">
                      <li>• Your API key is encrypted and stored securely on the server</li>
                      <li>• If no API key is provided and USE_API_KEY=true, we'll use our default model</li>
                      <li>• If USE_API_KEY=false, you must provide an API key to use the platform</li>
                      <li>• Different models may have varying capabilities and costs</li>
                      <li>• You can change these settings anytime</li>
                    </ul>
                  </div>

                  <motion.div
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <Button 
                      onClick={saveApiSettings} 
                      className="w-full bg-gradient-to-r from-purple-700 to-purple-900 hover:from-purple-800 hover:to-purple-950 relative overflow-hidden"
                    >
                      <motion.div
                        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
                        animate={{
                          x: ["-100%", "100%"],
                        }}
                        transition={{
                          duration: 2,
                          repeat: Infinity,
                          ease: "linear"
                        }}
                      />
                      <span className="relative z-10">Save Settings</span>
                    </Button>
                  </motion.div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
