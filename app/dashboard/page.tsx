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

export default function DashboardPage() {
  const [userStats, setUserStats] = useState<UserStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [apiSettings, setApiSettings] = useState({
    modelName: "",
    apiKey: "",
    provider: "gemini",
  })
  const { toast } = useToast()

  useEffect(() => {
    loadUserData()
    // Simulate real-time updates every 30 seconds
    const interval = setInterval(() => {
      loadUserData()
    }, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadUserData = async () => {
    try {
      setIsLoading(true)
      // Fetch from backend API
      const response = await fetch("/api/user/stats", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setUserStats(data)
      } else {
        // Fallback to mock data
        setUserStats({
          totalQuests: 12,
          completedQuests: 8,
          totalQuizzes: 25,
          averageScore: 85,
          timeSpent: 1440,
          currentLevel: 5,
          experiencePoints: 2450,
          totalXP: 2450,
          xpToNextLevel: 550,
          achievements: [
            {
              id: "1",
              name: "First Steps",
              description: "Complete your first quest",
              icon: "🏃",
              earned: true,
              earnedAt: "2024-01-15",
              rarity: "common",
            },
            {
              id: "2",
              name: "Quiz Master",
              description: "Score 90% or higher on 5 quizzes",
              icon: "🧠",
              earned: true,
              earnedAt: "2024-01-20",
              rarity: "rare",
            },
            {
              id: "3",
              name: "Dedicated Learner",
              description: "Study for 10 hours total",
              icon: "📚",
              earned: false,
              rarity: "epic",
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
              progress: 8,
              maxProgress: 50,
            },
          ],
        })
      }

      // Load API settings from localStorage
      const savedSettings = localStorage.getItem("apiSettings")
      if (savedSettings) {
        setApiSettings(JSON.parse(savedSettings))
      }
    } catch (error) {
      console.error("Failed to load user data:", error)
      // Use mock data on error
      setUserStats({
        totalQuests: 12,
        completedQuests: 8,
        totalQuizzes: 25,
        averageScore: 85,
        timeSpent: 1440,
        currentLevel: 5,
        experiencePoints: 2450,
        totalXP: 2450,
        xpToNextLevel: 550,
        achievements: [],
      })
    } finally {
      setIsLoading(false)
    }
  }

  const saveApiSettings = async () => {
    try {
      localStorage.setItem("apiSettings", JSON.stringify(apiSettings))
      toast({
        title: "Settings Saved",
        description: "Your API settings have been saved successfully.",
      })
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

  if (isLoading || !userStats) {
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

  const levelProgress = (userStats.totalXP / (userStats.totalXP + userStats.xpToNextLevel)) * 100

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-900 via-purple-800 to-purple-900 p-4 md:p-6 lg:p-8">
      {/* Animated Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-pink-500/10 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Header with Animation */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4 animate-in fade-in slide-in-from-top-4 duration-700">
          <div>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-2 bg-gradient-to-r from-white to-purple-200 bg-clip-text text-transparent">
              Dashboard
            </h1>
            <p className="text-purple-200 text-lg">Welcome back, Dr. Smith!</p>
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

        <Tabs defaultValue="overview" className="space-y-6">
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
              <Link href="/game" className="group">
                <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white hover:bg-white/20 transition-all duration-300 cursor-pointer transform hover:scale-105 hover:shadow-2xl hover:shadow-purple-500/50">
                  <CardContent className="p-6">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-gradient-to-br from-purple-600 to-pink-600 rounded-lg group-hover:scale-110 transition-transform duration-300">
                        <Play className="h-6 w-6" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg">Start Quest</h3>
                        <p className="text-sm text-purple-200">Begin a new medical adventure</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>

              <Link href="/quiz" className="group">
                <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white hover:bg-white/20 transition-all duration-300 cursor-pointer transform hover:scale-105 hover:shadow-2xl hover:shadow-green-500/50">
                  <CardContent className="p-6">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-gradient-to-br from-green-600 to-emerald-600 rounded-lg group-hover:scale-110 transition-transform duration-300">
                        <Brain className="h-6 w-6" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg">Take Quiz</h3>
                        <p className="text-sm text-purple-200">Test your medical knowledge</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>

              <Link href="/learning" className="group">
                <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white hover:bg-white/20 transition-all duration-300 cursor-pointer transform hover:scale-105 hover:shadow-2xl hover:shadow-blue-500/50">
                  <CardContent className="p-6">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-gradient-to-br from-blue-600 to-cyan-600 rounded-lg group-hover:scale-110 transition-transform duration-300">
                        <BookOpen className="h-6 w-6" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg">Study Materials</h3>
                        <p className="text-sm text-purple-200">Learn with AI assistance</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            </div>

            {/* Animated Stats Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
              <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white hover:border-green-400 transition-all duration-300 transform hover:scale-105">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <Target className="h-8 w-8 text-green-400 animate-bounce" />
                    <TrendingUp className="h-5 w-5 text-green-400" />
                  </div>
                  <p className="text-sm text-purple-200 mb-1">Quests Completed</p>
                  <p className="text-3xl font-bold mb-2">
                    {userStats.completedQuests}/{userStats.totalQuests}
                  </p>
                  <Progress
                    value={(userStats.completedQuests / userStats.totalQuests) * 100}
                    className="h-2 bg-purple-900"
                  />
                </CardContent>
              </Card>

              <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white hover:border-yellow-400 transition-all duration-300 transform hover:scale-105">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <Star className="h-8 w-8 text-yellow-400 animate-pulse" />
                    <Zap className="h-5 w-5 text-yellow-400" />
                  </div>
                  <p className="text-sm text-purple-200 mb-1">Average Score</p>
                  <p className="text-3xl font-bold">{userStats.averageScore}%</p>
                </CardContent>
              </Card>

              <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white hover:border-blue-400 transition-all duration-300 transform hover:scale-105">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <Clock className="h-8 w-8 text-blue-400" />
                  </div>
                  <p className="text-sm text-purple-200 mb-1">Time Spent</p>
                  <p className="text-3xl font-bold">{Math.floor(userStats.timeSpent / 60)}h</p>
                  <p className="text-xs text-purple-300 mt-1">{userStats.timeSpent % 60}m</p>
                </CardContent>
              </Card>

              <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white hover:border-purple-300 transition-all duration-300 transform hover:scale-105">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <Award className="h-8 w-8 text-purple-400" />
                    <Link href="/dashboard?tab=achievements">
                      <Button variant="ghost" size="sm" className="text-purple-300 hover:text-white">
                        View All
                      </Button>
                    </Link>
                  </div>
                  <p className="text-sm text-purple-200 mb-1">Achievements</p>
                  <p className="text-3xl font-bold">
                    {userStats.achievements.filter((a) => a.earned).length}/{userStats.achievements.length}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Recent Activity with Animations */}
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
                  {[
                    { icon: Trophy, text: "Completed 'Emergency Medicine' quest", time: "2 hours ago", color: "yellow" },
                    { icon: Brain, text: "Scored 92% on Cardiology Quiz", time: "1 day ago", color: "blue" },
                    { icon: BookOpen, text: "Studied 'Pharmacology Basics' for 45 minutes", time: "2 days ago", color: "green" },
                  ].map((activity, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-4 p-4 bg-purple-800/50 backdrop-blur-sm rounded-lg border border-purple-700 hover:border-purple-500 transition-all duration-300 transform hover:scale-[1.02] animate-in fade-in slide-in-from-left"
                      style={{ animationDelay: `${index * 100}ms` }}
                    >
                      <activity.icon className={`h-5 w-5 text-${activity.color}-400 flex-shrink-0`} />
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold truncate">{activity.text}</p>
                        <p className="text-sm text-purple-200">{activity.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="achievements" className="space-y-6 animate-in fade-in duration-500">
            <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Trophy className="h-5 w-5 text-yellow-400" />
                  Your Achievements
                </CardTitle>
                <CardDescription className="text-purple-200">Track your progress and unlock new badges</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {userStats.achievements.map((achievement, index) => (
                    <div
                      key={achievement.id}
                      className={`p-5 rounded-lg border-2 transition-all duration-300 transform hover:scale-105 ${
                        achievement.earned
                          ? `${getRarityColor(achievement.rarity)} shadow-lg shadow-purple-500/50`
                          : "bg-purple-800/50 border-purple-600 opacity-60"
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
            <Link href="/analytics">
              <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white hover:bg-white/20 transition-all cursor-pointer">
                <CardContent className="p-6 text-center">
                  <BarChart3 className="h-12 w-12 mx-auto mb-4 text-purple-400" />
                  <h3 className="text-xl font-semibold mb-2">View Full Analytics</h3>
                  <p className="text-purple-200">See detailed insights and performance metrics</p>
                </CardContent>
              </Card>
            </Link>
          </TabsContent>

          <TabsContent value="settings" className="space-y-6 animate-in fade-in duration-500">
            <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Key className="h-5 w-5" />
                  AI Model Configuration
                </CardTitle>
                <CardDescription className="text-purple-200">
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
                      <SelectTrigger className="bg-purple-800 border-purple-600 text-white">
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
                      value={apiSettings.modelName}
                      onChange={(e) => setApiSettings((prev) => ({ ...prev, modelName: e.target.value }))}
                      placeholder="e.g., gemini-2.5-flash-preview-05-20"
                      className="bg-purple-800 border-purple-600 text-white placeholder-purple-300"
                    />
                  </div>

                  <div>
                    <Label htmlFor="apiKey">API Key</Label>
                    <Input
                      id="apiKey"
                      type="password"
                      value={apiSettings.apiKey}
                      onChange={(e) => setApiSettings((prev) => ({ ...prev, apiKey: e.target.value }))}
                      placeholder="Enter your API key"
                      className="bg-purple-800 border-purple-600 text-white placeholder-purple-300"
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

                  <div className="bg-purple-800 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2 flex items-center gap-2">
                      <Info className="h-4 w-4" />
                      Important Notes
                    </h4>
                    <ul className="text-sm text-purple-200 space-y-1">
                      <li>• Your API key is stored securely and encrypted</li>
                      <li>• If no API key is provided, we'll use our default model</li>
                      <li>• Different models may have varying capabilities and costs</li>
                      <li>• You can change these settings anytime</li>
                    </ul>
                  </div>

                  <Button onClick={saveApiSettings} className="bg-purple-600 hover:bg-purple-700 w-full">
                    Save Settings
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
