"use client"

import { motion } from "framer-motion"
import type React from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Button } from "@/app/components/ui/button"
import { Badge } from "@/app/components/ui/badge"
import {
  BookOpen,
  Gamepad2,
  Brain,
  Key,
  Settings,
  ArrowRight,
  ExternalLink,
  CheckCircle2,
} from "lucide-react"

export default function HowToUsePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-[#0A1128] to-[#4C1D95] text-white py-12 relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          className="absolute top-20 left-10 w-72 h-72 bg-purple-900/30 rounded-full blur-3xl"
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
          className="absolute bottom-20 right-10 w-96 h-96 bg-blue-900/30 rounded-full blur-3xl"
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
      <div className="container mx-auto px-4 max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-5xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              How to Use Stud
            </h1>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              A comprehensive guide to getting started with Stud
            </p>
          </div>

          {/* Quick Start */}
          <Card className="bg-black/60 backdrop-blur-md border-purple-700/40 mb-8">
            <CardHeader>
              <CardTitle className="text-3xl">Quick Start</CardTitle>
              <CardDescription className="text-gray-400">
                Get started in minutes
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <Step number={1} title="Try the Demo">
                  Click the "Try Demo" button on the homepage to experience Stud without registration.
                  You'll get 1 test game with 3 clinical scenarios.
                </Step>
                <Step number={2} title="Register for Full Access">
                  After trying the demo, register for full access to all features including unlimited
                  games, quizzes, and document uploads.
                </Step>
                <Step number={3} title="Choose Your Mode">
                  Select from Mediquest (game), Study (document chat), or Quiz mode based on your learning needs.
                </Step>
                <Step number={4} title="Start Learning">
                  Begin your medical education adventure! Track your progress, earn achievements, and master medicine.
                </Step>
              </div>
            </CardContent>
          </Card>

          {/* Mode Guides */}
          <div className="space-y-6 mb-8">
            <Card className="bg-black/60 backdrop-blur-md border-purple-700/40">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Gamepad2 className="h-6 w-6 text-purple-400" />
                  Mediquest Mode
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-gray-300">
                <p>
                  Mediquest is an immersive clinical role-playing game where you diagnose patients, make decisions,
                  and advance your career.
                </p>
                <div className="space-y-2">
                  <h4 className="font-semibold text-white">How it works:</h4>
                  <ul className="list-disc list-inside space-y-1 ml-4">
                    <li>Configure your game world (profession, setting, era, etc.) or use random settings</li>
                    <li>Face 20-50 unique clinical cases per adventure</li>
                    <li>Each case can dynamically change 5-15 times based on your decisions</li>
                    <li>Chat with Game Master for guidance</li>
                    <li>Interact with NPCs (patients, nurses, specialists) for clues</li>
                    <li>Use clues (with penalties) when stuck</li>
                    <li>Earn achievements and track your performance</li>
                  </ul>
                </div>
                <motion.div 
                  className="bg-purple-900/30 border border-purple-700/40 rounded-lg p-4"
                  animate={{
                    borderColor: ["rgba(139, 92, 246, 0.4)", "rgba(139, 92, 246, 0.6)", "rgba(139, 92, 246, 0.4)"],
                  }}
                  transition={{
                    duration: 3,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                >
                  <p className="text-sm">
                    <strong>Tip:</strong> Each clinical case has a time limit. Answer questions accurately and quickly
                    to maximize your score. Using clues will increase case difficulty.
                  </p>
                </motion.div>
              </CardContent>
            </Card>

            <Card className="bg-black/60 backdrop-blur-md border-purple-700/40">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BookOpen className="h-6 w-6 text-blue-400" />
                  Study Mode
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-gray-300">
                <p>
                  Upload your medical documents and chat with them using AI. Perfect for studying from your own materials.
                </p>
                <div className="space-y-2">
                  <h4 className="font-semibold text-white">How it works:</h4>
                  <ul className="list-disc list-inside space-y-1 ml-4">
                    <li>Upload documents (PDF, DOCX, PPT, TXT, Images)</li>
                    <li>Documents are processed and stored temporarily (2-hour expiry)</li>
                    <li>View your document on one side, chat on the other</li>
                    <li>Ask questions about the document content</li>
                    <li>Get AI-powered answers with source references</li>
                    <li>Create quizzes from your document</li>
                    <li>Start a Mediquest adventure based on your document</li>
                  </ul>
                </div>
                <div className="bg-blue-900/30 border border-blue-400/30 rounded-lg p-4">
                  <p className="text-sm">
                    <strong>Note:</strong> Documents are automatically deleted after 2 hours to save storage.
                    You can rotate sections to switch document and chat positions.
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-black/60 backdrop-blur-md border-purple-700/40">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-6 w-6 text-pink-400" />
                  Quiz Mode
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-gray-300">
                <p>
                  Generate AI-powered quizzes from knowledge or your uploaded documents. Multiple choice and open-ended questions available.
                </p>
                <div className="space-y-2">
                  <h4 className="font-semibold text-white">How it works:</h4>
                  <ul className="list-disc list-inside space-y-1 ml-4">
                    <li>Configure quiz settings (type, number of questions, time limit)</li>
                    <li>Choose source: AI knowledge or uploaded document</li>
                    <li>Select mix of multiple choice and open-ended questions</li>
                    <li>Answer questions within time limits</li>
                    <li>Get instant feedback and scores</li>
                    <li>Open-ended answers are scored by AI</li>
                  </ul>
                </div>
                <div className="bg-pink-900/30 border border-pink-500/30 rounded-lg p-4">
                  <p className="text-sm">
                    <strong>Tip:</strong> Open-ended questions allow you to demonstrate deeper understanding.
                    AI scoring evaluates completeness, accuracy, and reasoning.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* API Key Guide */}
          <Card className="bg-black/60 backdrop-blur-md border-purple-700/40 mb-8">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="h-6 w-6 text-yellow-400" />
                Getting API Keys
              </CardTitle>
              <CardDescription className="text-gray-400">
                Required for Basic tier, optional for others
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Google API Key */}
              <div className="border border-purple-700/40 rounded-lg p-4">
                <h3 className="text-xl font-semibold mb-3 flex items-center gap-2">
                  <Badge className="bg-blue-800">Google (Gemini)</Badge>
                </h3>
                <ol className="list-decimal list-inside space-y-2 text-gray-300">
                  <li>Visit{" "}
                    <a
                      href="https://makersuite.google.com/app/apikey"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-purple-400 hover:text-purple-300 underline inline-flex items-center gap-1"
                    >
                      Google AI Studio
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </li>
                  <li>Sign in with your Google account</li>
                  <li>Click "Create API Key"</li>
                  <li>Copy your API key</li>
                  <li>Enter it in Stud's model configuration (not saved on backend)</li>
                </ol>
                <div className="mt-4 bg-blue-900/30 border border-blue-400/30 rounded p-3">
                  <p className="text-sm">
                    <strong>Model Names:</strong> gemini-2.0-flash-exp, gemini-1.5-pro, gemini-1.5-flash
                  </p>
                </div>
              </div>

              {/* OpenAI API Key */}
              <div className="border border-purple-700/40 rounded-lg p-4">
                <h3 className="text-xl font-semibold mb-3 flex items-center gap-2">
                  <Badge className="bg-purple-700">OpenAI (ChatGPT)</Badge>
                </h3>
                <ol className="list-decimal list-inside space-y-2 text-gray-300">
                  <li>Visit{" "}
                    <a
                      href="https://platform.openai.com/api-keys"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-purple-400 hover:text-purple-300 underline inline-flex items-center gap-1"
                    >
                      OpenAI Platform
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </li>
                  <li>Sign in or create an account</li>
                  <li>Navigate to API Keys section</li>
                  <li>Click "Create new secret key"</li>
                  <li>Copy your API key (shown only once!)</li>
                  <li>Enter it in Stud's model configuration (not saved on backend)</li>
                </ol>
                <div className="mt-4 bg-purple-900/30 border border-purple-700/40 rounded p-3">
                  <p className="text-sm">
                    <strong>Model Names:</strong> gpt-4, gpt-4-turbo, gpt-3.5-turbo
                  </p>
                </div>
              </div>

              <div className="bg-purple-900/30 border border-purple-700/40 rounded-lg p-4">
                <p className="text-sm">
                  <strong>Security Note:</strong> API keys are never saved on our backend. They're only used
                  for the current session. For Basic tier users, providing your own API key is required.
                  Professional and Enterprise tiers can use platform defaults.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Model Selection Guide */}
          <Card className="bg-black/60 backdrop-blur-md border-purple-700/40 mb-8">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-6 w-6 text-purple-400" />
                Model Selection Guide
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-gray-300">
              <div>
                <h4 className="font-semibold text-white mb-2">Google Models:</h4>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li><strong>gemini-2.0-flash-exp:</strong> Latest experimental model, fast and capable</li>
                  <li><strong>gemini-1.5-pro:</strong> Most capable model, best for complex reasoning</li>
                  <li><strong>gemini-1.5-flash:</strong> Fast and efficient, good for quick responses</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold text-white mb-2">OpenAI Models:</h4>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li><strong>gpt-4:</strong> Most capable, best for complex tasks</li>
                  <li><strong>gpt-4-turbo:</strong> Faster version of GPT-4</li>
                  <li><strong>gpt-3.5-turbo:</strong> Fast and cost-effective</li>
                </ul>
              </div>
              <div className="bg-purple-900/30 border border-purple-700/40 rounded-lg p-4">
                <p className="text-sm">
                  <strong>Recommendation:</strong> Start with gemini-2.0-flash-exp or gpt-4-turbo for best balance
                  of speed and capability. Leave model name empty to use platform defaults.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Tips & Best Practices */}
          <Card className="bg-black/60 backdrop-blur-md border-purple-700/40">
            <CardHeader>
              <CardTitle>Tips & Best Practices</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="h-5 w-5 text-purple-400 mt-0.5" />
                    <div>
                      <p className="font-semibold">Use Demo First</p>
                      <p className="text-sm text-gray-400">
                        Try the demo to understand how Stud works before registering
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="h-5 w-5 text-purple-400 mt-0.5" />
                    <div>
                      <p className="font-semibold">Start Simple</p>
                      <p className="text-sm text-gray-400">
                        Begin with easier cases and gradually increase difficulty
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="h-5 w-5 text-purple-400 mt-0.5" />
                    <div>
                      <p className="font-semibold">Track Performance</p>
                      <p className="text-sm text-gray-400">
                        Review your performance analysis to identify strengths and weaknesses
                      </p>
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="h-5 w-5 text-purple-400 mt-0.5" />
                    <div>
                      <p className="font-semibold">Use NPCs Wisely</p>
                      <p className="text-sm text-gray-400">
                        NPCs provide valuable clues but use them strategically
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="h-5 w-5 text-purple-400 mt-0.5" />
                    <div>
                      <p className="font-semibold">Upload Quality Documents</p>
                      <p className="text-sm text-gray-400">
                        Better quality documents lead to better quiz and game generation
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="h-5 w-5 text-purple-400 mt-0.5" />
                    <div>
                      <p className="font-semibold">Regular Practice</p>
                      <p className="text-sm text-gray-400">
                        Consistent practice improves performance and unlocks achievements
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* CTA */}
          <div className="text-center mt-12 relative z-10">
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Button
                size="lg"
                className="bg-gradient-to-r from-purple-700 to-purple-900 hover:from-purple-800 hover:to-purple-950 text-white text-lg px-8 py-6 relative overflow-hidden"
                onClick={() => window.location.href = "/demo"}
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
                <span className="relative z-10">Start Your Journey</span>
                <motion.span
                  animate={{
                    x: [0, 5, 0],
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                  className="relative z-10 inline-block ml-2"
                >
                  <ArrowRight className="h-5 w-5" />
                </motion.span>
              </Button>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

function Step({ number, title, children }: { number: number; title: string; children: React.ReactNode }) {
  return (
    <div className="flex gap-4">
      <div className="bg-gradient-to-br from-purple-600 to-pink-600 rounded-full h-10 w-10 flex items-center justify-center flex-shrink-0 font-bold">
        {number}
      </div>
      <div className="flex-1">
        <h3 className="text-lg font-semibold mb-1">{title}</h3>
        <p className="text-gray-300">{children}</p>
      </div>
    </div>
  )
}
