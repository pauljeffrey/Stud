"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Loader2, Send, Clock, AlertTriangle } from "lucide-react"
import Link from "next/link"
import { useToast } from "@/components/ui/use-toast"

export default function DemoPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "system",
      content:
        "Welcome to the MediQuest demo! You are a general practitioner in a busy hospital. A patient has just arrived with symptoms that need your attention. What would you like to do?",
    },
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [timeRemaining, setTimeRemaining] = useState(300) // 5 minutes in seconds
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { toast } = useToast()

  // Timer effect
  useEffect(() => {
    if (timeRemaining <= 0) {
      toast({
        title: "Time's up!",
        description: "Your demo session has ended. Register for the full experience!",
        variant: "destructive",
      })
      return
    }

    const timer = setInterval(() => {
      setTimeRemaining((prev) => prev - 1)
    }, 1000)

    return () => clearInterval(timer)
  }, [timeRemaining, toast])

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Format time remaining as MM:SS
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    // Add user message
    const userMessage = { role: "user", content: input }
    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      // Simulate API call to AI service
      await new Promise((resolve) => setTimeout(resolve, 1500))

      // Demo responses based on keywords in user input
      let responseContent = ""
      const lowerInput = input.toLowerCase()

      if (lowerInput.includes("examine") || lowerInput.includes("check")) {
        responseContent =
          "Upon examination, you notice the patient is a 45-year-old male with pale skin, sweating profusely. His pulse is rapid at 110 BPM, and he's clutching his chest. He reports the pain started about an hour ago and radiates to his left arm."
      } else if (lowerInput.includes("test") || lowerInput.includes("ecg") || lowerInput.includes("ekg")) {
        responseContent =
          "You order an ECG which shows ST-segment elevation in leads V1-V4. Blood tests reveal elevated troponin levels. These findings are consistent with an acute myocardial infarction (heart attack)."
      } else if (lowerInput.includes("treat") || lowerInput.includes("medication")) {
        responseContent =
          "You administer aspirin 325mg and nitroglycerin. The patient needs immediate intervention. In a full game, you would coordinate with cardiology for a potential angioplasty or other interventions."
      } else {
        responseContent =
          "The patient looks at you expectantly. His condition seems serious. Would you like to examine him more closely, order tests, or begin treatment?"
      }

      // Add system response
      setMessages((prev) => [...prev, { role: "system", content: responseContent }])

      // Add demo limitation message after 3 exchanges
      if (messages.filter((m) => m.role === "user").length >= 2) {
        setTimeout(() => {
          setMessages((prev) => [
            ...prev,
            {
              role: "system",
              content:
                "This is just a limited demo of MediQuest. Register for the full experience to access complete patient cases, collaborate with specialists, and track your medical career progress!",
            },
          ])
        }, 2000)
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to get a response. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-900 to-purple-700 flex flex-col">
      {/* Timer bar */}
      <div className="bg-purple-800 p-2 text-white flex justify-between items-center">
        <div className="flex items-center">
          <Clock className="mr-2 h-5 w-5" />
          <span>Demo Time Remaining: {formatTime(timeRemaining)}</span>
        </div>
        <Link href="/auth/register">
          <Button size="sm" className="bg-purple-500 hover:bg-purple-600">
            Register for Full Access
          </Button>
        </Link>
      </div>

      <div className="flex-1 container mx-auto p-4 flex flex-col">
        <h1 className="text-2xl font-bold text-white mb-4">MediQuest Demo</h1>

        {/* Demo limitations notice */}
        <div className="bg-yellow-600 text-white p-3 rounded-md mb-4 flex items-start">
          <AlertTriangle className="h-5 w-5 mr-2 flex-shrink-0 mt-0.5" />
          <p className="text-sm">
            This is a limited demo version with preset scenarios. The full version includes AI-powered dynamic
            scenarios, multiplayer functionality, and progression tracking.
          </p>
        </div>

        {/* Chat container */}
        <Card className="flex-1 flex flex-col bg-white/10 backdrop-blur-sm border-purple-400">
          <div className="flex-1 p-4 overflow-y-auto">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`mb-4 ${message.role === "user" ? "ml-auto max-w-[80%]" : "mr-auto max-w-[80%]"}`}
              >
                <div
                  className={`p-3 rounded-lg ${
                    message.role === "user"
                      ? "bg-purple-600 text-white rounded-br-none"
                      : "bg-gray-200 text-gray-800 rounded-bl-none"
                  }`}
                >
                  {message.content}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <form onSubmit={handleSubmit} className="p-4 border-t border-purple-400">
            <div className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="What would you like to do?"
                className="bg-white/20 border-purple-400 text-white placeholder:text-gray-300"
                disabled={isLoading || timeRemaining <= 0}
              />
              <Button
                type="submit"
                disabled={isLoading || !input.trim() || timeRemaining <= 0}
                className="bg-purple-500 hover:bg-purple-600"
              >
                {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  )
}

interface Message {
  role: "user" | "system"
  content: string
}
