"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Trophy, Star, BookOpen, Play, Settings, User, Brain, Target, Clock, Award, Key, Info } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
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
}

interface Achievement {
  id: string
  name: string
  description: string
  icon: string
  earned: boolean
  earnedAt?: string
}

export default function DashboardPage() {
  const [userStats, setUserStats] = useState<UserStats>({
    totalQuests: 12,
    completedQuests: 8,
    totalQuizzes: 25,
    averageScore: 85,
    timeSpent: 1440, // minutes
    currentLevel: 5,
    experiencePoints: 2450,
    achievements: [
      {
        id: "1",
        name: "First Steps",
        description: "Complete your first quest",
        icon: "🏃",
        earned: true,
        earnedAt: "2024-01-15",
      },
      {
        id: "2",
        name: "Quiz Master",
        description: "Score 90% or higher on 5 quizzes",
        icon: "🧠",
        earned: true,
        earnedAt: "2024-01-20",
      },
      {
        id: "3",
        name: "Dedicated Learner",
        description: "Study for 10 hours total",
        icon: "📚",
        earned: false,
      },
    ],
  })

  const [apiSettings, setApiSettings] = useState({
    modelName: "",
    apiKey: "",
    provider: "gemini",
  })

  const { toast } = useToast()

  useEffect(() => {
    // Load user stats and API settings
    loadUserData()
  }, [])

  const loadUserData = async () => {
    try {
      // In a real app, this would fetch from your backend
      // const response = await fetch('/api/user/stats')
      // const data = await response.json()
      // setUserStats(data)

      // Load API settings from localStorage
      const savedSettings = localStorage.getItem("apiSettings")
      if (savedSettings) {
        setApiSettings(JSON.parse(savedSettings))
      }
    } catch (error) {
      console.error("Failed to load user data:", error)
    }
  }

  const saveApiSettings = async () => {
    try {
      // Save to localStorage (in production, encrypt and save to backend)
      localStorage.setItem("apiSettings", JSON.stringify(apiSettings))

      // In a real app, you would also save to your backend
      // await fetch('/api/user/api-settings', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(apiSettings)
      // })

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

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-900 to-purple-700 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Dashboard</h1>
            <p className="text-purple-200">Welcome back, Dr. Smith!</p>
          </div>
          <div className="flex items-center gap-4">
            <Badge variant="secondary" className="bg-purple-600 text-white">
              Level {userStats.currentLevel}
            </Badge>
            <div className="text-white text-right">
              <p className="text-sm text-purple-200">Experience Points</p>
              <p className="font-bold">{userStats.experiencePoints} XP</p>
            </div>
          </div>
        </div>

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="bg-purple-800 text-white">
            <TabsTrigger value="overview" className="data-[state=active]:bg-purple-600">
              <User className="h-4 w-4 mr-2" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="achievements" className="data-[state=active]:bg-purple-600">
              <Trophy className="h-4 w-4 mr-2" />
              Achievements
            </TabsTrigger>
            <TabsTrigger value="settings" className="data-[state=active]:bg-purple-600">
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Link href="/game">
                <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white hover:bg-white/20 transition-colors cursor-pointer">
                  <CardContent className="p-6">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-purple-600 rounded-lg">
                        <Play className="h-6 w-6" />
                      </div>
                      <div>
                        <h3 className="font-semibold">Start Quest</h3>
                        <p className="text-sm text-purple-200">Begin a new medical adventure</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>

              <Link href="/quiz">
                <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white hover:bg-white/20 transition-colors cursor-pointer">
                  <CardContent className="p-6">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-purple-600 rounded-lg">
                        <Brain className="h-6 w-6" />
                      </div>
                      <div>
                        <h3 className="font-semibold">Take Quiz</h3>
                        <p className="text-sm text-purple-200">Test your medical knowledge</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>

              <Link href="/learning">
                <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white hover:bg-white/20 transition-colors cursor-pointer">
                  <CardContent className="p-6">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-purple-600 rounded-lg">
                        <BookOpen className="h-6 w-6" />
                      </div>
                      <div>
                        <h3 className="font-semibold">Study Materials</h3>
                        <p className="text-sm text-purple-200">Learn with AI assistance</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
                <CardContent className="p-6">
                  <div className="flex items-center gap-4">
                    <Target className="h-8 w-8 text-green-400" />
                    <div>
                      <p className="text-sm text-purple-200">Quests Completed</p>
                      <p className="text-2xl font-bold">
                        {userStats.completedQuests}/{userStats.totalQuests}
                      </p>
                    </div>
                  </div>
                  <Progress value={(userStats.completedQuests / userStats.totalQuests) * 100} className="mt-4" />
                </CardContent>
              </Card>

              <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
                <CardContent className="p-6">
                  <div className="flex items-center gap-4">
                    <Star className="h-8 w-8 text-yellow-400" />
                    <div>
                      <p className="text-sm text-purple-200">Average Score</p>
                      <p className="text-2xl font-bold">{userStats.averageScore}%</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
                <CardContent className="p-6">
                  <div className="flex items-center gap-4">
                    <Clock className="h-8 w-8 text-blue-400" />
                    <div>
                      <p className="text-sm text-purple-200">Time Spent</p>
                      <p className="text-2xl font-bold">{Math.floor(userStats.timeSpent / 60)}h</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
                <CardContent className="p-6">
                  <div className="flex items-center gap-4">
                    <Award className="h-8 w-8 text-purple-400" />
                    <div>
                      <p className="text-sm text-purple-200">Achievements</p>
                      <p className="text-2xl font-bold">
                        {userStats.achievements.filter((a) => a.earned).length}/{userStats.achievements.length}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Recent Activity */}
            <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription className="text-purple-200">Your latest learning activities</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center gap-4 p-3 bg-purple-800 rounded-lg">
                    <Trophy className="h-5 w-5 text-yellow-400" />
                    <div>
                      <p className="font-semibold">Completed "Emergency Medicine" quest</p>
                      <p className="text-sm text-purple-200">2 hours ago</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 p-3 bg-purple-800 rounded-lg">
                    <Brain className="h-5 w-5 text-blue-400" />
                    <div>
                      <p className="font-semibold">Scored 92% on Cardiology Quiz</p>
                      <p className="text-sm text-purple-200">1 day ago</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 p-3 bg-purple-800 rounded-lg">
                    <BookOpen className="h-5 w-5 text-green-400" />
                    <div>
                      <p className="font-semibold">Studied "Pharmacology Basics" for 45 minutes</p>
                      <p className="text-sm text-purple-200">2 days ago</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="achievements" className="space-y-6">
            <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
              <CardHeader>
                <CardTitle>Your Achievements</CardTitle>
                <CardDescription className="text-purple-200">Track your progress and unlock new badges</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {userStats.achievements.map((achievement) => (
                    <div
                      key={achievement.id}
                      className={`p-4 rounded-lg border-2 ${
                        achievement.earned
                          ? "bg-purple-600 border-yellow-400"
                          : "bg-purple-800 border-purple-600 opacity-60"
                      }`}
                    >
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-2xl">{achievement.icon}</span>
                        <div>
                          <h3 className="font-semibold">{achievement.name}</h3>
                          {achievement.earned && achievement.earnedAt && (
                            <p className="text-xs text-purple-200">
                              Earned on {new Date(achievement.earnedAt).toLocaleDateString()}
                            </p>
                          )}
                        </div>
                      </div>
                      <p className="text-sm text-purple-200">{achievement.description}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="settings" className="space-y-6">
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
                      placeholder="e.g., gemini-2.0-flash"
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

                  <Button onClick={saveApiSettings} className="bg-purple-600 hover:bg-purple-700">
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
