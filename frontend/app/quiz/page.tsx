"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/app/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Input } from "@/app/components/ui/input"
import { Label } from "@/app/components/ui/label"
import { Textarea } from "@/app/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/app/components/ui/select"
import { Progress } from "@/app/components/ui/progress"
import { Badge } from "@/app/components/ui/badge"
import {
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  ArrowRight,
  ArrowLeft,
  Trophy,
  Brain,
  FileText,
  Upload,
} from "lucide-react"
import { useToast } from "@/app/components/ui/use-toast"
import { motion, AnimatePresence } from "framer-motion"

interface QuizQuestion {
  question_id: string
  question: string
  type: "multiple_choice" | "open_ended"
  options?: string[]
  correct_answer: string
  explanation: string
}

interface Quiz {
  id: string
  title: string
  questions: QuizQuestion[]
  timeLimit: number
  totalQuestions: number
  source: string
}

export default function QuizPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [quiz, setQuiz] = useState<Quiz | null>(null)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [timeRemaining, setTimeRemaining] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [showResults, setShowResults] = useState(false)
  const [scores, setScores] = useState<Record<string, number>>({})
  const [modelConfig, setModelConfig] = useState({
    model_name: "",
    api_key: "",
    provider: "google"
  })
  const [quizConfig, setQuizConfig] = useState({
    quiz_type: "general",
    num_questions: 10,
    num_multiple_choice: 7,
    num_open_ended: 3,
    time_limit: 300,
    source: "ai_knowledge" as "ai_knowledge" | "document",
    document_id: ""
  })
  const [documents, setDocuments] = useState<{ id: string; file_name: string; processed?: boolean }[]>([])
  const [documentsLoading, setDocumentsLoading] = useState(false)
  const [uploadingDoc, setUploadingDoc] = useState(false)

  useEffect(() => {
    if (quizConfig.source === "document") {
      setDocumentsLoading(true)
      const token = typeof window !== "undefined" ? localStorage.getItem("token") : null
      if (token) {
        fetch("/api/learning/documents", {
          headers: { Authorization: `Bearer ${token}` },
        })
          .then((r) => r.json())
          .then((data) => {
            if (data.success && data.documents) {
              setDocuments(data.documents)
            }
          })
          .catch(() => setDocuments([]))
          .finally(() => setDocumentsLoading(false))
      } else {
        setDocuments([])
        setDocumentsLoading(false)
      }
    } else {
      setDocuments([])
    }
  }, [quizConfig.source])

  useEffect(() => {
    if (quiz && quiz.timeLimit > 0) {
      setTimeRemaining(quiz.timeLimit)
    }
  }, [quiz])

  useEffect(() => {
    if (timeRemaining > 0 && quiz && !showResults) {
      const timer = setInterval(() => {
        setTimeRemaining((prev) => {
          if (prev <= 1) {
            handleTimeUp()
            return 0
          }
          return prev - 1
        })
      }, 1000)
      return () => clearInterval(timer)
    }
  }, [timeRemaining, quiz, showResults])

  const handleDocumentUpload = async (file: File) => {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null
    const userStr = typeof window !== "undefined" ? localStorage.getItem("user") : null
    const user = userStr ? JSON.parse(userStr) : null
    const userId = user?.id || "user_123"
    if (!token) {
      toast({ title: "Login required", description: "Please log in to upload documents", variant: "destructive" })
      return
    }
    setUploadingDoc(true)
    try {
      const formData = new FormData()
      formData.append("file", file)
      formData.append("document_id", `doc_${Date.now()}_${Math.random().toString(36).slice(2)}`)
      formData.append("user_id", userId)
      const res = await fetch("/api/learning/upload", { method: "POST", body: formData })
      const data = await res.json()
      if (data.document_id) {
        setDocuments((prev) => [{ id: data.document_id, file_name: file.name, processed: true }, ...prev])
        setQuizConfig((c) => ({ ...c, document_id: data.document_id }))
        toast({ title: "Document uploaded", description: `Processed ${data.chunk_count || 0} chunks` })
      } else throw new Error(data.message || "Upload failed")
    } catch (e: any) {
      toast({ title: "Upload failed", description: e.message || "Failed to upload", variant: "destructive" })
    } finally {
      setUploadingDoc(false)
    }
  }

  const handleGenerateQuiz = async () => {
    if (quizConfig.source === "document" && !quizConfig.document_id) {
      toast({ title: "Select a document", description: "Choose a document or upload one first", variant: "destructive" })
      return
    }
    setIsGenerating(true)
    try {
      const userStr = typeof window !== "undefined" ? localStorage.getItem("user") : null
      const user = userStr ? JSON.parse(userStr) : null
      const userId = user?.id || undefined
      const response = await fetch("/api/quiz/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          quiz_type: quizConfig.quiz_type,
          num_questions: quizConfig.num_questions,
          time_limit: quizConfig.time_limit,
          num_multiple_choice: quizConfig.num_multiple_choice,
          num_open_ended: quizConfig.num_open_ended,
          source: quizConfig.source,
          document_id: quizConfig.document_id || undefined,
          model_name: modelConfig.model_name || undefined,
          api_key: modelConfig.api_key || undefined,
          provider: modelConfig.provider,
          use_internet: true,
          user_id: userId,
        })
      })

      if (!response.ok) throw new Error("Failed to generate quiz")

      const data = await response.json()
      setQuiz(data)
      setCurrentQuestionIndex(0)
      setAnswers({})
      setShowResults(false)
      setScores({})

      toast({
        title: "Quiz Generated",
        description: `Created ${data.totalQuestions} questions`
      })
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to generate quiz",
        variant: "destructive"
      })
    } finally {
      setIsGenerating(false)
    }
  }

  const handleTimeUp = () => {
    toast({
      title: "Time's Up!",
      description: "Moving to next question",
      variant: "destructive"
    })
    handleNext()
  }

  const handleAnswerChange = (questionId: string, answer: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: answer }))
  }

  const handleNext = () => {
    if (quiz && currentQuestionIndex < quiz.questions.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1)
      setTimeRemaining(quiz.timeLimit)
    }
  }

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex((prev) => prev - 1)
      setTimeRemaining(quiz?.timeLimit || 300)
    }
  }

  const handleSubmitQuiz = async () => {
    if (!quiz) return

    setIsLoading(true)
    try {
      // Score answers
      const scoredAnswers: Record<string, any> = {}
      const newScores: Record<string, number> = {}

      for (const question of quiz.questions) {
        const userAnswer = answers[question.question_id] || ""
        scoredAnswers[question.question_id] = userAnswer

        if (question.type === "multiple_choice") {
          // Simple scoring for multiple choice
          newScores[question.question_id] = userAnswer === question.correct_answer ? 10 : 0
        } else {
          // Score open-ended using AI
          try {
            const scoreResponse = await fetch("/api/quiz/score-open", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                question: question.question,
                correct_answer: question.correct_answer,
                user_answer: userAnswer,
                model_name: modelConfig.model_name || undefined,
                api_key: modelConfig.api_key || undefined,
                provider: modelConfig.provider
              })
            })

            if (scoreResponse.ok) {
              const scoreData = await scoreResponse.json()
              newScores[question.question_id] = scoreData.score
            } else {
              newScores[question.question_id] = 5 // Default score
            }
          } catch {
            newScores[question.question_id] = 5
          }
        }
      }

      setScores(newScores)

      // Submit to backend
      const totalScore = Object.values(newScores).reduce((a, b) => a + b, 0) / quiz.questions.length

      await fetch("/api/quiz/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          quiz_id: quiz.id,
          answers: scoredAnswers,
          scores: newScores,
          total_score: totalScore,
          time_spent: quiz.timeLimit - timeRemaining
        })
      })

      setShowResults(true)
      toast({
        title: "Quiz Submitted",
        description: `Your score: ${totalScore.toFixed(1)}/10`
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to submit quiz",
        variant: "destructive"
      })
    } finally {
      setIsLoading(false)
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }

  const currentQuestion = quiz?.questions[currentQuestionIndex]
  const progress = quiz ? ((currentQuestionIndex + 1) / quiz.questions.length) * 100 : 0

  if (!quiz) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-black via-[#0A1128] to-[#4C1D95] text-white p-4 relative overflow-hidden">
        {/* Animated Background */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <motion.div
            className="absolute top-10 left-10 w-64 h-64 bg-purple-900/20 rounded-full blur-3xl"
            animate={{
              x: [0, 50, 0],
              y: [0, 30, 0],
              scale: [1, 1.2, 1],
            }}
            transition={{
              duration: 8,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
          <motion.div
            className="absolute bottom-10 right-10 w-80 h-80 bg-blue-900/20 rounded-full blur-3xl"
            animate={{
              x: [0, -50, 0],
              y: [0, -30, 0],
              scale: [1, 1.3, 1],
            }}
            transition={{
              duration: 10,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
        </div>
        <div className="container mx-auto max-w-2xl py-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div className="text-center mb-8 relative z-10">
              <motion.div
                animate={{
                  rotate: [0, 360],
                  scale: [1, 1.1, 1],
                }}
                transition={{
                  duration: 4,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              >
                <Brain className="h-16 w-16 mx-auto mb-4 text-purple-400" />
              </motion.div>
              <motion.h1 
                className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-purple-400 via-purple-300 to-blue-400 bg-clip-text text-transparent"
                animate={{
                  backgroundPosition: ["0%", "100%", "0%"],
                  scale: [1, 1.02, 1],
                }}
                transition={{
                  backgroundPosition: {
                    duration: 5,
                    repeat: Infinity,
                    ease: "linear"
                  },
                  scale: {
                    duration: 3,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }
                }}
                style={{
                  backgroundSize: "200% auto"
                }}
              >
                Quiz Mode
              </motion.h1>
              <p className="text-gray-300 text-lg">
                Generate AI-powered quizzes from knowledge or documents
              </p>
            </div>

            <Card className="bg-black/60 backdrop-blur-md border-purple-700/40">
              <CardHeader>
                <CardTitle>Quiz Configuration</CardTitle>
                <CardDescription className="text-gray-400">
                  Configure your quiz settings
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Quiz Type</Label>
                    <Input
                      value={quizConfig.quiz_type}
                      onChange={(e) => setQuizConfig({ ...quizConfig, quiz_type: e.target.value })}
                      placeholder="e.g., anatomy, pharmacology"
                      className="bg-black/50 border-purple-700/40"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Total Questions</Label>
                    <Input
                      type="number"
                      value={quizConfig.num_questions}
                      onChange={(e) => setQuizConfig({ ...quizConfig, num_questions: parseInt(e.target.value) })}
                      className="bg-black/50 border-purple-700/40"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Multiple Choice</Label>
                    <Input
                      type="number"
                      value={quizConfig.num_multiple_choice}
                      onChange={(e) => setQuizConfig({ ...quizConfig, num_multiple_choice: parseInt(e.target.value) })}
                      className="bg-black/50 border-purple-700/40"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Open-ended</Label>
                    <Input
                      type="number"
                      value={quizConfig.num_open_ended}
                      onChange={(e) => setQuizConfig({ ...quizConfig, num_open_ended: parseInt(e.target.value) })}
                      className="bg-black/50 border-purple-700/40"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Time Limit (seconds per question)</Label>
                  <Input
                    type="number"
                    value={quizConfig.time_limit}
                    onChange={(e) => setQuizConfig({ ...quizConfig, time_limit: parseInt(e.target.value) })}
                    className="bg-black/50 border-purple-700/40"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Source</Label>
                  <Select
                    value={quizConfig.source}
                    onValueChange={(value: "ai_knowledge" | "document") => setQuizConfig({ ...quizConfig, source: value })}
                  >
                    <SelectTrigger className="bg-black/50 border-purple-700/40">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ai_knowledge">AI Knowledge</SelectItem>
                      <SelectItem value="document">From Document</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {quizConfig.source === "document" && (
                  <div className="space-y-2">
                    <Label>Select Document</Label>
                    <div className="flex gap-2">
                      <div className="flex-1 min-h-0 flex flex-col gap-2">
                        <div className="border border-purple-700/40 rounded-lg bg-black/50 max-h-32 overflow-y-auto p-2 space-y-1">
                          {documentsLoading ? (
                            <div className="flex items-center gap-2 text-gray-400 py-2">
                              <Loader2 className="h-4 w-4 animate-spin" />
                              <span className="text-sm">Loading documents...</span>
                            </div>
                          ) : documents.length === 0 ? (
                            <p className="text-sm text-gray-400 py-2">No documents yet. Upload one below.</p>
                          ) : (
                            documents.map((doc) => (
                              <button
                                key={doc.id}
                                type="button"
                                onClick={() => setQuizConfig((c) => ({ ...c, document_id: doc.id }))}
                                className={`w-full text-left px-3 py-2 rounded-md text-sm truncate transition-colors ${
                                  quizConfig.document_id === doc.id
                                    ? "bg-purple-700/50 border border-purple-500"
                                    : "hover:bg-purple-900/30 border border-transparent"
                                }`}
                              >
                                <FileText className="h-4 w-4 inline mr-2 text-purple-400" />
                                {doc.file_name}
                              </button>
                            ))
                          )}
                        </div>
                        <label className="flex items-center justify-center gap-2 px-3 py-2 border border-dashed border-purple-700/40 rounded-lg cursor-pointer hover:bg-purple-900/20 transition-colors">
                          <Upload className="h-4 w-4" />
                          <span className="text-sm">
                            {uploadingDoc ? "Uploading..." : "Upload new document"}
                          </span>
                          <input
                            type="file"
                            className="hidden"
                            accept=".pdf,.doc,.docx,.pptx,.txt,image/*"
                            disabled={uploadingDoc}
                            onChange={(e) => {
                              const f = e.target.files?.[0]
                              if (f) handleDocumentUpload(f)
                              e.target.value = ""
                            }}
                          />
                        </label>
                      </div>
                    </div>
                  </div>
                )}

                <div className="bg-purple-900/30 border border-purple-700/40 rounded-lg p-4 space-y-2">
                  <Label className="text-sm text-purple-300">Model Configuration (Optional)</Label>
                  <div className="grid grid-cols-2 gap-2">
                    <Select
                      value={modelConfig.provider}
                      onValueChange={(value) => setModelConfig({ ...modelConfig, provider: value })}
                    >
                    <SelectTrigger className="bg-black/50 border-purple-700/40 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="google">Google</SelectItem>
                        <SelectItem value="openai">OpenAI</SelectItem>
                      </SelectContent>
                    </Select>
                    <Input
                      placeholder="API key"
                      type="password"
                      value={modelConfig.api_key}
                      onChange={(e) => setModelConfig({ ...modelConfig, api_key: e.target.value })}
                      className="bg-black/50 border-purple-700/40 text-xs"
                    />
                  </div>
                </div>

                <motion.div
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full"
                >
                  <Button
                    onClick={handleGenerateQuiz}
                    disabled={isGenerating}
                    className="w-full bg-gradient-to-r from-purple-700 to-purple-900 hover:from-purple-800 hover:to-purple-950 text-white text-lg py-6 relative overflow-hidden"
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
                    {isGenerating ? (
                      <>
                        <Loader2 className="h-5 w-5 mr-2 animate-spin relative z-10" />
                        <span className="relative z-10">Generating Quiz...</span>
                      </>
                    ) : (
                      <>
                        <motion.div
                          animate={{
                            rotate: [0, 360],
                          }}
                          transition={{
                            duration: 3,
                            repeat: Infinity,
                            ease: "linear"
                          }}
                          className="relative z-10 inline-block"
                        >
                          <Brain className="h-5 w-5 mr-2" />
                        </motion.div>
                        <span className="relative z-10">Generate Quiz</span>
                      </>
                    )}
                  </Button>
                </motion.div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-[#1E3A8A] to-[#8B5CF6] text-white p-4">
      <div className="container mx-auto max-w-4xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">{quiz.title}</h1>
            <div className="flex items-center gap-4 text-sm text-gray-300">
              <span>Question {currentQuestionIndex + 1} of {quiz.questions.length}</span>
              <Badge className="bg-purple-600">{quiz.source === "ai_knowledge" ? "AI Knowledge" : "Document"}</Badge>
            </div>
          </div>
          <div className="flex items-center gap-2 text-red-400">
            <Clock className="h-5 w-5" />
            <span className="font-mono text-xl">{formatTime(timeRemaining)}</span>
          </div>
        </div>

        {/* Progress Bar */}
        <Progress value={progress} className="mb-6 h-2 bg-black/30" />

        {showResults ? (
          /* Results View */
          <Card className="bg-black/60 backdrop-blur-md border-purple-700/40">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="h-6 w-6 text-yellow-400" />
                Quiz Results
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {quiz.questions.map((question, idx) => {
                const userAnswer = answers[question.question_id] || "No answer"
                const score = scores[question.question_id] || 0
                const isCorrect = question.type === "multiple_choice" && userAnswer === question.correct_answer

                return (
                  <div
                    key={question.question_id}
                    className="border border-purple-700/40 rounded-lg p-4 bg-black/30"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-semibold">Question {idx + 1}</h3>
                      <div className="flex items-center gap-2">
                        <motion.div
                          animate={{
                            rotate: [0, 360],
                            scale: [1, 1.2, 1],
                          }}
                          transition={{
                            duration: 2,
                            repeat: Infinity,
                            ease: "easeInOut"
                          }}
                        >
                          {isCorrect ? (
                            <CheckCircle2 className="h-5 w-5 text-purple-400" />
                          ) : (
                            <XCircle className="h-5 w-5 text-purple-500" />
                          )}
                        </motion.div>
                        <Badge className={score >= 7 ? "bg-purple-700" : score >= 5 ? "bg-purple-600" : "bg-purple-800"}>
                          {score.toFixed(1)}/10
                        </Badge>
                      </div>
                    </div>
                    <p className="mb-2">{question.question}</p>
                    <div className="space-y-1 text-sm">
                    <p className="text-gray-400">Your answer: {userAnswer}</p>
                    <p className="text-purple-400">Correct: {question.correct_answer}</p>
                    <p className="text-blue-300 mt-2">{question.explanation}</p>
                    </div>
                  </div>
                )
              })}

              <div className="mt-6 pt-6 border-t border-purple-700/40">
                <div className="text-center">
                  <p className="text-2xl font-bold mb-2">
                    Total Score: {(Object.values(scores).reduce((a, b) => a + b, 0) / quiz.questions.length).toFixed(1)}/10
                  </p>
                  <div className="flex gap-2 justify-center mt-4">
                    <Button
                      onClick={() => {
                        setQuiz(null)
                        setShowResults(false)
                        setAnswers({})
                        setScores({})
                      }}
                      variant="outline"
                      className="border-purple-700/40"
                    >
                      New Quiz
                    </Button>
                    <motion.div
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      <Button
                        onClick={() => router.push("/dashboard")}
                        className="bg-gradient-to-r from-purple-700 to-purple-900 hover:from-purple-800 hover:to-purple-950"
                      >
                        View Dashboard
                      </Button>
                    </motion.div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ) : (
          /* Question View */
          <AnimatePresence mode="wait">
            <motion.div
              key={currentQuestionIndex}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              <Card className="bg-black/60 backdrop-blur-md border-purple-700/40">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>Question {currentQuestionIndex + 1}</span>
                    <motion.div
                      animate={{
                        scale: [1, 1.05, 1],
                      }}
                      transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: "easeInOut"
                      }}
                    >
                      <Badge className={currentQuestion?.type === "multiple_choice" ? "bg-blue-800" : "bg-purple-700"}>
                        {currentQuestion?.type === "multiple_choice" ? "Multiple Choice" : "Open-ended"}
                      </Badge>
                    </motion.div>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <p className="text-lg">{currentQuestion?.question}</p>

                  {currentQuestion?.type === "multiple_choice" && currentQuestion.options ? (
                    <div className="space-y-2">
                      {currentQuestion.options.map((option, idx) => (
                        <Button
                          key={idx}
                          variant={
                            answers[currentQuestion.question_id] === option ? "default" : "outline"
                          }
                          className="w-full justify-start text-left bg-black/50 border-purple-700/40 hover:bg-purple-700/30"
                          onClick={() => handleAnswerChange(currentQuestion.question_id, option)}
                        >
                          {String.fromCharCode(65 + idx)}. {option}
                        </Button>
                      ))}
                    </div>
                  ) : (
                    <Textarea
                      value={answers[currentQuestion?.question_id || ""] || ""}
                      onChange={(e) => handleAnswerChange(currentQuestion?.question_id || "", e.target.value)}
                      placeholder="Type your answer here..."
                      className="bg-black/50 border-purple-700/40 min-h-[200px]"
                    />
                  )}

                  <div className="flex justify-between">
                    <Button
                      onClick={handlePrevious}
                      disabled={currentQuestionIndex === 0}
                      variant="outline"
                      className="border-purple-700/40"
                    >
                      <motion.span
                        animate={{
                          x: currentQuestionIndex === 0 ? 0 : [0, -5, 0],
                        }}
                        transition={{
                          duration: 1.5,
                          repeat: Infinity,
                          ease: "easeInOut"
                        }}
                        className="inline-block mr-2"
                      >
                        <ArrowLeft className="h-4 w-4" />
                      </motion.span>
                      Previous
                    </Button>
                    {currentQuestionIndex === quiz.questions.length - 1 ? (
                    <motion.div
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      <Button
                        onClick={handleSubmitQuiz}
                        disabled={isLoading}
                        className="bg-gradient-to-r from-purple-700 to-purple-900 hover:from-purple-800 hover:to-purple-950 relative overflow-hidden"
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
                        {isLoading ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin relative z-10" />
                            <span className="relative z-10">Submitting...</span>
                          </>
                        ) : (
                          <>
                            <span className="relative z-10">Submit Quiz</span>
                            <motion.div
                              animate={{
                                rotate: [0, 15, -15, 0],
                              }}
                              transition={{
                                duration: 2,
                                repeat: Infinity,
                                ease: "easeInOut"
                              }}
                              className="relative z-10 inline-block ml-2"
                            >
                              <Trophy className="h-4 w-4" />
                            </motion.div>
                          </>
                        )}
                      </Button>
                    </motion.div>
                    ) : (
                      <Button
                        onClick={handleNext}
                      className="bg-gradient-to-r from-purple-700 to-purple-900 hover:from-purple-800 hover:to-purple-950"
                    >
                      Next
                      <motion.span
                        animate={{
                          x: [0, 5, 0],
                        }}
                        transition={{
                          duration: 1.5,
                          repeat: Infinity,
                          ease: "easeInOut"
                        }}
                        className="inline-block ml-2"
                      >
                        <ArrowRight className="h-4 w-4" />
                      </motion.span>
                    </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </AnimatePresence>
        )}
      </div>
    </div>
  )
}
