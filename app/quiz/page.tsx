"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Clock, Brain, CheckCircle, XCircle, Trophy, Star, Upload, FileText } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"

interface Question {
  id: string
  question: string
  type: "multiple_choice" | "true_false" | "open_ended"
  options?: string[]
  correct_answer: string
  explanation: string
}

interface Quiz {
  id: string
  title: string
  questions: Question[]
  timeLimit: number
  totalQuestions: number
}

export default function QuizPage() {
  const [quizMode, setQuizMode] = useState<"create" | "take" | null>(null)
  const [quizType, setQuizType] = useState<"multiple_choice" | "true_false" | "open_ended">("multiple_choice")
  const [numQuestions, setNumQuestions] = useState(10)
  const [timeLimit, setTimeLimit] = useState(600) // 10 minutes
  const [currentQuiz, setCurrentQuiz] = useState<Quiz | null>(null)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [userAnswers, setUserAnswers] = useState<Record<string, string>>({})
  const [timeRemaining, setTimeRemaining] = useState(0)
  const [quizStarted, setQuizStarted] = useState(false)
  const [quizCompleted, setQuizCompleted] = useState(false)
  const [score, setScore] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const { toast } = useToast()

  // Timer effect
  useEffect(() => {
    if (quizStarted && timeRemaining > 0 && !quizCompleted) {
      const timer = setInterval(() => {
        setTimeRemaining((prev) => {
          if (prev <= 1) {
            completeQuiz()
            return 0
          }
          return prev - 1
        })
      }, 1000)

      return () => clearInterval(timer)
    }
  }, [quizStarted, timeRemaining, quizCompleted])

  const generateQuiz = async () => {
    setIsLoading(true)
    try {
      const formData = new FormData()
      formData.append("quiz_type", quizType)
      formData.append("num_questions", numQuestions.toString())
      formData.append("time_limit", timeLimit.toString())

      if (uploadedFile) {
        formData.append("file", uploadedFile)
      }

      const response = await fetch("/api/quiz/generate", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        throw new Error("Failed to generate quiz")
      }

      const quiz = await response.json()
      setCurrentQuiz(quiz)
      setQuizMode("take")

      toast({
        title: "Quiz Generated",
        description: `Created a ${numQuestions}-question ${quizType.replace("_", " ")} quiz.`,
      })
    } catch (error) {
      console.error("Quiz generation error:", error)
      toast({
        title: "Error",
        description: "Failed to generate quiz. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const startQuiz = () => {
    if (!currentQuiz) return

    setQuizStarted(true)
    setTimeRemaining(currentQuiz.timeLimit)
    setCurrentQuestionIndex(0)
    setUserAnswers({})
    setQuizCompleted(false)
    setScore(0)
  }

  const answerQuestion = (questionId: string, answer: string) => {
    setUserAnswers((prev) => ({
      ...prev,
      [questionId]: answer,
    }))
  }

  const nextQuestion = () => {
    if (currentQuiz && currentQuestionIndex < currentQuiz.questions.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1)
    } else {
      completeQuiz()
    }
  }

  const previousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex((prev) => prev - 1)
    }
  }

  const completeQuiz = async () => {
    if (!currentQuiz) return

    setQuizCompleted(true)
    setQuizStarted(false)

    // Calculate score
    let correctAnswers = 0
    currentQuiz.questions.forEach((question) => {
      const userAnswer = userAnswers[question.id]
      if (userAnswer && userAnswer.toLowerCase().trim() === question.correct_answer.toLowerCase().trim()) {
        correctAnswers++
      }
    })

    const finalScore = Math.round((correctAnswers / currentQuiz.questions.length) * 100)
    setScore(finalScore)

    // Save quiz result
    try {
      await fetch("/api/quiz/submit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          quizId: currentQuiz.id,
          answers: userAnswers,
          score: finalScore,
          timeSpent: currentQuiz.timeLimit - timeRemaining,
        }),
      })
    } catch (error) {
      console.error("Failed to save quiz result:", error)
    }

    toast({
      title: "Quiz Completed!",
      description: `You scored ${finalScore}% (${correctAnswers}/${currentQuiz.questions.length} correct)`,
    })
  }

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }

  const resetQuiz = () => {
    setQuizMode(null)
    setCurrentQuiz(null)
    setQuizStarted(false)
    setQuizCompleted(false)
    setCurrentQuestionIndex(0)
    setUserAnswers({})
    setTimeRemaining(0)
    setScore(0)
    setUploadedFile(null)
  }

  if (quizCompleted && currentQuiz) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-purple-900 to-purple-700 p-4">
        <div className="max-w-4xl mx-auto">
          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
            <CardHeader className="text-center">
              <CardTitle className="text-3xl mb-4">Quiz Completed!</CardTitle>
              <div className="flex justify-center mb-4">
                <Trophy className="h-16 w-16 text-yellow-400" />
              </div>
            </CardHeader>
            <CardContent className="text-center space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-purple-800 p-6 rounded-lg">
                  <Star className="h-8 w-8 mx-auto mb-2 text-yellow-400" />
                  <p className="text-2xl font-bold">{score}%</p>
                  <p className="text-purple-200">Final Score</p>
                </div>
                <div className="bg-purple-800 p-6 rounded-lg">
                  <CheckCircle className="h-8 w-8 mx-auto mb-2 text-green-400" />
                  <p className="text-2xl font-bold">
                    {
                      currentQuiz.questions.filter(
                        (q) => userAnswers[q.id]?.toLowerCase().trim() === q.correct_answer.toLowerCase().trim(),
                      ).length
                    }
                  </p>
                  <p className="text-purple-200">Correct Answers</p>
                </div>
                <div className="bg-purple-800 p-6 rounded-lg">
                  <Clock className="h-8 w-8 mx-auto mb-2 text-blue-400" />
                  <p className="text-2xl font-bold">{formatTime(currentQuiz.timeLimit - timeRemaining)}</p>
                  <p className="text-purple-200">Time Taken</p>
                </div>
              </div>

              {/* Review Answers */}
              <div className="text-left">
                <h3 className="text-xl font-semibold mb-4">Review Your Answers</h3>
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {currentQuiz.questions.map((question, index) => {
                    const userAnswer = userAnswers[question.id]
                    const isCorrect = userAnswer?.toLowerCase().trim() === question.correct_answer.toLowerCase().trim()

                    return (
                      <div key={question.id} className="bg-purple-800 p-4 rounded-lg">
                        <div className="flex items-start gap-3">
                          {isCorrect ? (
                            <CheckCircle className="h-5 w-5 text-green-400 mt-1 flex-shrink-0" />
                          ) : (
                            <XCircle className="h-5 w-5 text-red-400 mt-1 flex-shrink-0" />
                          )}
                          <div className="flex-1">
                            <p className="font-semibold mb-2">
                              Q{index + 1}: {question.question}
                            </p>
                            <p className="text-sm text-purple-200 mb-1">
                              Your answer:{" "}
                              <span className={isCorrect ? "text-green-400" : "text-red-400"}>
                                {userAnswer || "No answer"}
                              </span>
                            </p>
                            <p className="text-sm text-purple-200 mb-2">
                              Correct answer: <span className="text-green-400">{question.correct_answer}</span>
                            </p>
                            <p className="text-sm text-purple-300">{question.explanation}</p>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              <div className="flex gap-4 justify-center">
                <Button onClick={resetQuiz} className="bg-purple-600 hover:bg-purple-700">
                  Take Another Quiz
                </Button>
                <Button variant="outline" className="border-purple-400 text-white hover:bg-purple-800 bg-transparent">
                  View Dashboard
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  if (quizStarted && currentQuiz) {
    const currentQuestion = currentQuiz.questions[currentQuestionIndex]
    const progress = ((currentQuestionIndex + 1) / currentQuiz.questions.length) * 100

    return (
      <div className="min-h-screen bg-gradient-to-b from-purple-900 to-purple-700 p-4">
        <div className="max-w-4xl mx-auto">
          {/* Quiz Header */}
          <div className="flex justify-between items-center mb-6">
            <div>
              <h1 className="text-2xl font-bold text-white">Medical Quiz</h1>
              <p className="text-purple-200">
                Question {currentQuestionIndex + 1} of {currentQuiz.questions.length}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-white text-right">
                <p className="text-sm text-purple-200">Time Remaining</p>
                <p className="text-xl font-bold">{formatTime(timeRemaining)}</p>
              </div>
              <Button
                onClick={completeQuiz}
                variant="outline"
                className="border-purple-400 text-white hover:bg-purple-800 bg-transparent"
              >
                Submit Quiz
              </Button>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mb-6">
            <Progress value={progress} className="h-2" />
          </div>

          {/* Question Card */}
          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
            <CardHeader>
              <CardTitle className="text-xl">{currentQuestion.question}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {currentQuestion.type === "multiple_choice" && currentQuestion.options && (
                <div className="space-y-3">
                  {currentQuestion.options.map((option, index) => (
                    <div
                      key={index}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        userAnswers[currentQuestion.id] === option
                          ? "bg-purple-600 border-purple-400"
                          : "bg-purple-800 border-purple-600 hover:bg-purple-700"
                      }`}
                      onClick={() => answerQuestion(currentQuestion.id, option)}
                    >
                      <p>{option}</p>
                    </div>
                  ))}
                </div>
              )}

              {currentQuestion.type === "true_false" && (
                <div className="space-y-3">
                  {["True", "False"].map((option) => (
                    <div
                      key={option}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        userAnswers[currentQuestion.id] === option
                          ? "bg-purple-600 border-purple-400"
                          : "bg-purple-800 border-purple-600 hover:bg-purple-700"
                      }`}
                      onClick={() => answerQuestion(currentQuestion.id, option)}
                    >
                      <p>{option}</p>
                    </div>
                  ))}
                </div>
              )}

              {currentQuestion.type === "open_ended" && (
                <Textarea
                  value={userAnswers[currentQuestion.id] || ""}
                  onChange={(e) => answerQuestion(currentQuestion.id, e.target.value)}
                  placeholder="Type your answer here..."
                  className="bg-purple-800 border-purple-600 text-white placeholder-purple-300"
                  rows={4}
                />
              )}

              {/* Navigation */}
              <div className="flex justify-between pt-4">
                <Button
                  onClick={previousQuestion}
                  disabled={currentQuestionIndex === 0}
                  variant="outline"
                  className="border-purple-400 text-white hover:bg-purple-800 bg-transparent"
                >
                  Previous
                </Button>
                <Button
                  onClick={nextQuestion}
                  className="bg-purple-600 hover:bg-purple-700"
                  disabled={!userAnswers[currentQuestion.id]}
                >
                  {currentQuestionIndex === currentQuiz.questions.length - 1 ? "Finish" : "Next"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-900 to-purple-700 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Medical Quiz</h1>
          <p className="text-purple-200">Test your medical knowledge with AI-generated quizzes</p>
        </div>

        {!quizMode && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card
              className="bg-white/10 backdrop-blur-sm border-purple-400 text-white cursor-pointer hover:bg-white/20 transition-colors"
              onClick={() => setQuizMode("create")}
            >
              <CardContent className="p-8 text-center">
                <Brain className="h-16 w-16 mx-auto mb-4 text-purple-400" />
                <h3 className="text-2xl font-bold mb-2">Generate New Quiz</h3>
                <p className="text-purple-200">Create a custom quiz with AI-generated questions</p>
              </CardContent>
            </Card>

            <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white opacity-60">
              <CardContent className="p-8 text-center">
                <Trophy className="h-16 w-16 mx-auto mb-4 text-purple-400" />
                <h3 className="text-2xl font-bold mb-2">Saved Quizzes</h3>
                <p className="text-purple-200">Access your previously taken quizzes</p>
                <Badge className="mt-2 bg-yellow-600">Coming Soon</Badge>
              </CardContent>
            </Card>
          </div>
        )}

        {quizMode === "create" && (
          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
            <CardHeader>
              <CardTitle>Create New Quiz</CardTitle>
              <CardDescription className="text-purple-200">
                Configure your quiz settings and generate questions
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <Label htmlFor="quizType">Quiz Type</Label>
                  <Select value={quizType} onValueChange={(value: any) => setQuizType(value)}>
                    <SelectTrigger className="bg-purple-800 border-purple-600 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="multiple_choice">Multiple Choice</SelectItem>
                      <SelectItem value="true_false">True/False</SelectItem>
                      <SelectItem value="open_ended">Open Ended</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="numQuestions">Number of Questions</Label>
                  <Input
                    id="numQuestions"
                    type="number"
                    min="5"
                    max="50"
                    value={numQuestions}
                    onChange={(e) => setNumQuestions(Number.parseInt(e.target.value))}
                    className="bg-purple-800 border-purple-600 text-white"
                  />
                </div>

                <div>
                  <Label htmlFor="timeLimit">Time Limit (minutes)</Label>
                  <Input
                    id="timeLimit"
                    type="number"
                    min="5"
                    max="120"
                    value={timeLimit / 60}
                    onChange={(e) => setTimeLimit(Number.parseInt(e.target.value) * 60)}
                    className="bg-purple-800 border-purple-600 text-white"
                  />
                </div>

                <div>
                  <Label htmlFor="difficulty">Difficulty Level</Label>
                  <Select defaultValue="intermediate">
                    <SelectTrigger className="bg-purple-800 border-purple-600 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="beginner">Beginner</SelectItem>
                      <SelectItem value="intermediate">Intermediate</SelectItem>
                      <SelectItem value="advanced">Advanced</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Optional File Upload */}
              <div>
                <Label>Upload Study Material (Optional)</Label>
                <div className="mt-2">
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx,.txt"
                    onChange={(e) => setUploadedFile(e.target.files?.[0] || null)}
                    className="hidden"
                    id="file-upload"
                  />
                  <label
                    htmlFor="file-upload"
                    className="flex items-center gap-2 p-3 border-2 border-dashed border-purple-600 rounded-lg cursor-pointer hover:border-purple-400 transition-colors"
                  >
                    <Upload className="h-5 w-5" />
                    <span>{uploadedFile ? uploadedFile.name : "Choose file to generate questions from"}</span>
                  </label>
                </div>
              </div>

              <div className="flex gap-4">
                <Button onClick={generateQuiz} disabled={isLoading} className="bg-purple-600 hover:bg-purple-700">
                  {isLoading ? "Generating..." : "Generate Quiz"}
                </Button>
                <Button
                  onClick={() => setQuizMode(null)}
                  variant="outline"
                  className="border-purple-400 text-white hover:bg-purple-800"
                >
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {quizMode === "take" && currentQuiz && !quizStarted && (
          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
            <CardHeader>
              <CardTitle>Quiz Ready!</CardTitle>
              <CardDescription className="text-purple-200">Review the quiz details before starting</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-purple-800 p-4 rounded-lg text-center">
                  <Brain className="h-8 w-8 mx-auto mb-2 text-purple-400" />
                  <p className="text-lg font-bold">{currentQuiz.questions.length}</p>
                  <p className="text-sm text-purple-200">Questions</p>
                </div>
                <div className="bg-purple-800 p-4 rounded-lg text-center">
                  <Clock className="h-8 w-8 mx-auto mb-2 text-blue-400" />
                  <p className="text-lg font-bold">{currentQuiz.timeLimit / 60} min</p>
                  <p className="text-sm text-purple-200">Time Limit</p>
                </div>
                <div className="bg-purple-800 p-4 rounded-lg text-center">
                  <FileText className="h-8 w-8 mx-auto mb-2 text-green-400" />
                  <p className="text-lg font-bold">{quizType.replace("_", " ")}</p>
                  <p className="text-sm text-purple-200">Question Type</p>
                </div>
              </div>

              <div className="bg-purple-800 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">Instructions:</h4>
                <ul className="text-sm text-purple-200 space-y-1">
                  <li>• Answer all questions to the best of your ability</li>
                  <li>• You can navigate between questions using Previous/Next buttons</li>
                  <li>• Your progress is automatically saved</li>
                  <li>• The quiz will auto-submit when time runs out</li>
                </ul>
              </div>

              <div className="flex gap-4">
                <Button onClick={startQuiz} className="bg-green-600 hover:bg-green-700">
                  Start Quiz
                </Button>
                <Button
                  onClick={() => setQuizMode("create")}
                  variant="outline"
                  className="border-purple-400 text-white hover:bg-purple-800"
                >
                  Modify Settings
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
