"use client"

import { useState, useRef, useEffect } from "react"
import dynamic from "next/dynamic"
import { Button } from "@/app/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Textarea } from "@/app/components/ui/textarea"
import { Input } from "@/app/components/ui/input"
import { Label } from "@/app/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/app/components/ui/select"
import { Upload, Send, RotateCcw, FileText, Loader2, BookOpen, MessageCircle, Trash2, Plus, Search } from "lucide-react"
import { useRouter } from "next/navigation"
import { useToast } from "@/app/components/ui/use-toast"
import { useDropzone } from "react-dropzone"
import { motion } from "framer-motion"
import {
  fetchAccountCredentials,
  resolveCredentials,
  resolveModelFields,
  toModelConfig,
} from "@/app/lib/api-credentials"
import { useAuth, apiFetch, getToken } from "@/app/lib/auth"
import { readApiError, readSseStream } from "@/app/lib/game-state"
import { DocumentPicker, type PickerDoc } from "@/app/components/document-picker"
import { FreeModelNotice } from "@/app/components/free-model-notice"

const MAX_UPLOAD_MB = 10
const ANON_ID_KEY = "stud_anon_study_id"

/** Stable per-browser id for anonymous (logged-out) study sessions, so two
 *  anonymous users never share the same uploaded documents/chat history. */
function getOrCreateAnonId(): string {
  if (typeof window === "undefined") return "anon"
  let id = localStorage.getItem(ANON_ID_KEY)
  if (!id) {
    id = `anon_${crypto.randomUUID()}`
    localStorage.setItem(ANON_ID_KEY, id)
  }
  return id
}
const StudyPdfPanel = dynamic(
  () => import("./study-pdf-panel").then((mod) => ({ default: mod.StudyPdfPanel })),
  { ssr: false, loading: () => <Loader2 className="animate-spin text-purple-400" /> }
)

interface ChatMessage {
  role: "user" | "assistant"
  content: string
  sources?: string[]
  timestamp: Date
}

export default function StudyPage() {
  const router = useRouter()
  const { user } = useAuth()
  const [document, setDocument] = useState<File | null>(null)
  const [documentId, setDocumentId] = useState<string | null>(null)
  const [processingStatus, setProcessingStatus] = useState<"queued" | "ready" | "failed" | null>(null)
  const [documentContent, setDocumentContent] = useState<string>("")
  // Set when a document is chosen via the library/own-documents picker
  // instead of dropped in as a raw File — no local bytes to preview.
  const [pickedDoc, setPickedDoc] = useState<PickerDoc | null>(null)
  const [showPicker, setShowPicker] = useState(false)
  const [isSuggesting, setIsSuggesting] = useState(false)
  const [suggested, setSuggested] = useState(false)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [userInput, setUserInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isGeneratingQuiz, setIsGeneratingQuiz] = useState(false)
  const [chatPosition, setChatPosition] = useState<"right" | "left">("right")
  const [numPages, setNumPages] = useState<number>(0)
  const [pageNumber, setPageNumber] = useState<number>(1)
  const [modelConfig, setModelConfig] = useState({
    model_name: "",
    api_key: "",
    provider: "google"
  })
  const { toast } = useToast()
  const chatEndRef = useRef<HTMLDivElement>(null)
  const documentViewerRef = useRef<HTMLDivElement>(null)
  const [hasSavedCreds, setHasSavedCreds] = useState(false)
  const [anonId] = useState(getOrCreateAnonId)

  const studyUserId = user?.id || anonId

  useEffect(() => {
    const apply = (creds: ReturnType<typeof resolveCredentials>) => {
      if (creds) {
        setModelConfig(toModelConfig(creds))
        setHasSavedCreds(true)
      }
    }
    apply(resolveCredentials())
    const token = getToken()
    if (token) fetchAccountCredentials(token).then(apply).catch(() => {})
  }, [])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [chatMessages])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      "application/pdf": [".pdf"],
      "application/msword": [".doc"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"],
      "text/plain": [".txt"],
      "image/*": [".png", ".jpg", ".jpeg"]
    },
    maxSize: MAX_UPLOAD_MB * 1024 * 1024,
    onDrop: async (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        await handleFileUpload(acceptedFiles[0])
      }
    },
    onDropRejected: (rejections) => {
      const tooLarge = rejections.some((r) => r.errors.some((e) => e.code === "file-too-large"))
      toast({
        title: tooLarge ? "File too large" : "File not accepted",
        description: tooLarge
          ? `Documents must be ${MAX_UPLOAD_MB}MB or smaller.`
          : "Please upload a PDF, DOCX, PPTX, TXT, or image file.",
        variant: "destructive"
      })
    },
    multiple: false
  })

  const handleFileUpload = async (file: File) => {
    setIsLoading(true)
    setUploadProgress(0)

    try {
      const formData = new FormData()
      formData.append("file", file)
      formData.append("document_id", `doc_${Date.now()}`)
      formData.append("user_id", studyUserId)

      const response = await apiFetch("/api/learning/upload", {
        method: "POST",
        body: formData
      })

      if (!response.ok) throw new Error(await readApiError(response))

      const data = await response.json()
      setDocumentId(data.document_id)
      setDocument(file)
      setPickedDoc(null)
      setSuggested(false)
      setProcessingStatus(data.status === "ready" ? "ready" : "queued")

      // Extract text for preview (simplified - in production use proper extraction)
      if (file.type === "text/plain") {
        const text = await file.text()
        setDocumentContent(text)
      }

      if (data.status === "ready") {
        toast({
          title: "Document ready",
          description: `Processed ${data.chunk_count ?? ""} chunks. You can start chatting now.`
        })
      } else {
        toast({
          title: "Document uploaded",
          description: "We're processing it in the background — we'll notify you when it's ready to chat with."
        })
      }
    } catch (error) {
      toast({
        title: "Upload failed",
        description: error instanceof Error ? error.message : "Failed to upload document",
        variant: "destructive"
      })
    } finally {
      setIsLoading(false)
      setUploadProgress(0)
    }
  }

  // Poll the document's processing status while it's still queued, so the
  // chat/quiz UI unlocks automatically without the user having to refresh.
  useEffect(() => {
    if (!documentId || processingStatus !== "queued") return
    const interval = setInterval(async () => {
      try {
        const res = await apiFetch("/api/learning/documents")
        if (!res.ok) return
        const data = await res.json()
        const doc = (data.documents || []).find((d: { id: string }) => d.id === documentId)
        if (!doc) return
        if (doc.processed) {
          setProcessingStatus("ready")
        } else if (doc.processing_status === "failed") {
          setProcessingStatus("failed")
        }
      } catch {
        /* keep polling */
      }
    }, 8000)
    return () => clearInterval(interval)
  }, [documentId, processingStatus])

  const handleChat = async () => {
    if (!userInput.trim() || !documentId) return

    const userMessage = userInput
    setUserInput("")
    setIsLoading(true)

    // Add user message
    setChatMessages((prev) => [
      ...prev,
      { role: "user", content: userMessage, timestamp: new Date() }
    ])

    try {
      const response = await apiFetch("/api/learning/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          document_id: documentId,
          message: userMessage,
          chat_history: chatMessages.map(m => ({ role: m.role, content: m.content })),
          ...resolveModelFields(modelConfig),
        })
      })

      if (!response.ok) throw new Error(await readApiError(response))

      let accumulatedResponse = ""
      await readSseStream(response, (data) => {
        accumulatedResponse += (data.content as string) ?? ""
        setChatMessages((prev) => {
          const newMessages = [...prev]
          const lastMsg = newMessages[newMessages.length - 1]
          if (lastMsg?.role === "assistant") {
            lastMsg.content = accumulatedResponse
            if (data.sources) lastMsg.sources = data.sources as string[]
          } else {
            newMessages.push({
              role: "assistant",
              content: accumulatedResponse,
              sources: data.sources as string[] | undefined,
              timestamp: new Date()
            })
          }
          return newMessages
        })

        if (data.complete && data.generate_quiz) {
          toast({
            title: "Ready to test yourself?",
            description: "Click \"Generate Quiz\" above to spin up a quiz from this discussion.",
          })
        }
      })
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to get response",
        variant: "destructive"
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteDocument = async () => {
    if (!documentId) return

    try {
      const response = await apiFetch(`/api/learning/documents/${documentId}`, {
        method: "DELETE"
      })

      if (!response.ok) throw new Error(await readApiError(response))

      setDocument(null)
      setDocumentId(null)
      setProcessingStatus(null)
      setDocumentContent("")
      setChatMessages([])
      setPickedDoc(null)
      setSuggested(false)

      toast({
        title: "Document deleted",
        description: "Document and its data have been removed"
      })
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to delete document",
        variant: "destructive"
      })
    }
  }

  /** Choosing a document from the central library / "your documents" picker
   *  — no local File bytes, so the viewer shows a reference card instead of
   *  a PDF preview. */
  const handleSelectLibraryDoc = (doc: PickerDoc) => {
    setDocument(null)
    setDocumentId(doc.id)
    setProcessingStatus("ready")
    setDocumentContent("")
    setChatMessages([])
    setPickedDoc(doc)
    setSuggested(false)
    setShowPicker(false)
  }

  const handleSuggestForLibrary = async () => {
    if (!documentId) return
    setIsSuggesting(true)
    try {
      const response = await apiFetch(`/api/learning/documents/${documentId}/suggest-global`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      })
      if (!response.ok) throw new Error(await readApiError(response))
      setSuggested(true)
      toast({ title: "Thanks!", description: "We'll review this for the central library." })
    } catch (error) {
      toast({
        title: "Couldn't submit suggestion",
        description: error instanceof Error ? error.message : "Please try again",
        variant: "destructive",
      })
    } finally {
      setIsSuggesting(false)
    }
  }

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
  }

  /** If a document is uploaded, generate a quiz grounded in it — and in
   *  whatever's been discussed in the chat so far, if anything — then hand
   *  off to /quiz preloaded. Falls back to the blank quiz-config page when
   *  there's no document yet. */
  const handleCreateQuizClick = async () => {
    if (!documentId) {
      router.push("/quiz")
      return
    }
    if (processingStatus !== "ready") {
      toast({
        title: "Still processing",
        description: "This document isn't ready yet — we'll notify you when it is.",
        variant: "destructive",
      })
      return
    }
    setIsGeneratingQuiz(true)
    try {
      const formData = new FormData()
      formData.append("document_id", documentId)
      formData.append("user_id", studyUserId)

      const recentDiscussion = chatMessages
        .slice(-12)
        .map((m) => `${m.role === "user" ? "Learner" : "Tutor"}: ${m.content}`)
        .join("\n")
        .slice(0, 4000)
      if (recentDiscussion) formData.append("chat_context", recentDiscussion)

      const response = await apiFetch("/api/learning/generate-quiz-from-document", {
        method: "POST",
        body: formData,
      })
      if (!response.ok) throw new Error(await readApiError(response))

      const quizData = await response.json()
      sessionStorage.setItem("quiz_pending", JSON.stringify(quizData))
      router.push("/quiz")
    } catch (error) {
      toast({
        title: "Couldn't generate quiz",
        description: error instanceof Error ? error.message : "Failed to generate quiz from this document",
        variant: "destructive"
      })
    } finally {
      setIsGeneratingQuiz(false)
    }
  }

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
      <div className="container mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between relative z-10">
          <div>
            <motion.h1 
              className="text-4xl font-bold mb-2 bg-gradient-to-r from-purple-400 via-purple-300 to-blue-400 bg-clip-text text-transparent"
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
              Study Mode
            </motion.h1>
            <motion.p 
              className="text-gray-300"
              animate={{
                y: [0, -3, 0],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            >
              Upload documents and chat with them using AI
            </motion.p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => setChatPosition(chatPosition === "right" ? "left" : "right")}
              variant="outline"
              className="border-purple-700/40"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Rotate Sections
            </Button>
            <Button
              onClick={handleCreateQuizClick}
              disabled={isGeneratingQuiz}
              variant="outline"
              className="border-purple-700/40"
            >
              {isGeneratingQuiz ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Plus className="h-4 w-4 mr-2" />
              )}
              {documentId ? "Generate Quiz" : "Create Quiz"}
            </Button>
            <Button
              onClick={() => router.push("/demo")}
              variant="outline"
              className="border-purple-700/40"
            >
              Start Quest
            </Button>
          </div>
        </div>

        <FreeModelNotice className="mb-3" />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-[calc(100vh-8rem)]">
          {/* Document Viewer - Left */}
          <div className={`${chatPosition === "left" ? "lg:order-2" : ""} relative z-10`}>
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <Card className="bg-black/60 backdrop-blur-md border-purple-700/40 h-full flex flex-col">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    Document Viewer
                  </CardTitle>
                  {(document || pickedDoc) && (
                    <Button
                      onClick={handleDeleteDocument}
                      variant="ghost"
                      size="sm"
                      className="text-red-400 hover:text-red-300"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto">
                {!document && pickedDoc ? (
                  <div className="border border-purple-700/40 rounded-lg p-12 text-center space-y-2">
                    <FileText className="h-12 w-12 mx-auto mb-2 text-purple-400" />
                    <p className="text-lg">{pickedDoc.file_name}</p>
                    <p className="text-sm text-gray-400">
                      {pickedDoc.scope === "global"
                        ? "Central library document — grounding your study session."
                        : "Your document — grounding your study session."}
                    </p>
                  </div>
                ) : !document ? (
                  <div className="space-y-3">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="w-full border-purple-700/40 text-purple-300"
                      onClick={() => setShowPicker((v) => !v)}
                    >
                      <Search className="h-4 w-4 mr-2" />
                      {showPicker ? "Hide library" : "Browse central library / your documents"}
                    </Button>
                    {showPicker && (
                      <DocumentPicker selectedId={documentId} onSelect={handleSelectLibraryDoc} />
                    )}
                    <div
                      {...getRootProps()}
                      className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
                        isDragActive
                          ? "border-purple-500 bg-purple-900/20"
                          : "border-purple-700/40 hover:border-purple-500/60"
                      }`}
                    >
                      <input {...getInputProps()} />
                      <motion.div
                        animate={{
                          scale: [1, 1.02, 1],
                        }}
                        transition={{
                          duration: 3,
                          repeat: Infinity,
                          ease: "easeInOut"
                        }}
                      >
                      <motion.div
                        animate={{
                          y: [0, -10, 0],
                          rotate: [0, 5, -5, 0],
                        }}
                        transition={{
                          duration: 3,
                          repeat: Infinity,
                          ease: "easeInOut"
                        }}
                      >
                        <Upload className="h-12 w-12 mx-auto mb-4 text-purple-400" />
                      </motion.div>
                      </motion.div>
                      <motion.p
                        className="text-lg mb-2"
                        animate={{
                          scale: [1, 1.05, 1],
                        }}
                        transition={{
                          duration: 2.5,
                          repeat: Infinity,
                          ease: "easeInOut",
                          delay: 0.5
                        }}
                      >
                        {isDragActive ? "Drop file here" : "Drag & drop document here"}
                      </motion.p>
                      <p className="text-sm text-gray-400">
                        Supports PDF, DOCX, PPT, TXT, Images
                      </p>
                      <motion.div
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        <Button className="mt-4 bg-purple-700 hover:bg-purple-800">
                          Select File
                        </Button>
                      </motion.div>
                    </div>
                  </div>
                ) : document.type === "application/pdf" ? (
                  <div ref={documentViewerRef} className="space-y-4">
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-sm text-gray-400">
                        Page {pageNumber} of {numPages}
                      </span>
                      <div className="flex gap-2">
                        <Button
                          onClick={() => setPageNumber((p) => Math.max(1, p - 1))}
                          disabled={pageNumber <= 1}
                          size="sm"
                          variant="outline"
                          className="border-purple-700/40"
                        >
                          Previous
                        </Button>
                        <Button
                          onClick={() => setPageNumber((p) => Math.min(numPages, p + 1))}
                          disabled={pageNumber >= numPages}
                          size="sm"
                          variant="outline"
                          className="border-purple-700/40"
                        >
                          Next
                        </Button>
                      </div>
                    </div>
                    <StudyPdfPanel
                      file={document}
                      pageNumber={pageNumber}
                      onLoadSuccess={onDocumentLoadSuccess}
                    />
                  </div>
                ) : (
                  <div className="prose prose-invert max-w-none">
                    <pre className="whitespace-pre-wrap text-sm bg-black/30 p-4 rounded">
                      {documentContent || "Document content will appear here"}
                    </pre>
                  </div>
                )}
                {documentId &&
                  processingStatus === "ready" &&
                  !(pickedDoc && pickedDoc.scope === "global") && (
                    <div className="mt-3 flex items-center justify-between gap-2 text-xs bg-purple-950/30 border border-purple-700/30 rounded-lg px-3 py-2">
                      <span className="text-gray-400">
                        Think this should be part of our standard central library?
                      </span>
                      {suggested ? (
                        <span className="text-green-400 shrink-0">Suggested ✓</span>
                      ) : (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          className="border-purple-700/40 shrink-0"
                          onClick={handleSuggestForLibrary}
                          disabled={isSuggesting}
                        >
                          {isSuggesting ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            "Suggest for library"
                          )}
                        </Button>
                      )}
                    </div>
                  )}
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Chat Interface - Right */}
        <div className={`${chatPosition === "left" ? "lg:order-1" : ""} relative z-10`}>
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Card className="bg-black/60 backdrop-blur-md border-purple-700/40 h-full flex flex-col">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageCircle className="h-5 w-5" />
                  Chat with Document
                </CardTitle>
                <CardDescription className="text-gray-400">
                  Ask questions about your uploaded document
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col overflow-y-auto">
                {/* Chat Messages */}
                <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                    {chatMessages.length === 0 ? (
                      <motion.div 
                        className="text-center text-gray-400 mt-8"
                        animate={{
                          opacity: [0.5, 0.8, 0.5],
                        }}
                        transition={{
                          duration: 2,
                          repeat: Infinity,
                          ease: "easeInOut"
                        }}
                      >
                        <motion.div
                          animate={{
                            y: [0, -10, 0],
                            rotate: [0, 5, -5, 0],
                          }}
                          transition={{
                            duration: 3,
                            repeat: Infinity,
                            ease: "easeInOut"
                          }}
                        >
                          <BookOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        </motion.div>
                        <motion.p
                          animate={{
                            scale: [1, 1.02, 1],
                          }}
                          transition={{
                            duration: 2.5,
                            repeat: Infinity,
                            ease: "easeInOut",
                            delay: 0.5
                          }}
                        >
                          Start a conversation about your document
                        </motion.p>
                      </motion.div>
                    ) : (
                      chatMessages.map((msg, idx) => (
                        <motion.div
                          key={idx}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: idx * 0.1 }}
                          className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                        >
                          <motion.div
                            className={`max-w-[80%] rounded-lg p-3 ${
                              msg.role === "user"
                                ? "bg-purple-700/30"
                                : "bg-blue-800/30"
                            }`}
                            animate={{
                              scale: [1, 1.01, 1],
                            }}
                            transition={{
                              duration: 3,
                              repeat: Infinity,
                              ease: "easeInOut",
                              delay: idx * 0.1
                            }}
                          >
                            <p className="text-sm">{msg.content}</p>
                            {msg.sources && msg.sources.length > 0 && (
                              <div className="mt-2 text-xs text-gray-400">
                                Sources: {msg.sources.length}
                              </div>
                            )}
                          </motion.div>
                        </motion.div>
                      ))
                    )}
                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="bg-blue-600/30 rounded-lg p-3">
                        <Loader2 className="h-4 w-4 animate-spin" />
                      </div>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>

                {/* Input Area */}
                <div className="space-y-2">
                  {documentId && processingStatus && processingStatus !== "ready" && (
                    <p className="text-xs text-purple-300 flex items-center gap-1.5">
                      {processingStatus === "queued" ? (
                        <>
                          <Loader2 className="h-3 w-3 animate-spin" />
                          Still processing this document — we'll notify you when it's ready to chat with.
                        </>
                      ) : (
                        <span className="text-red-400">
                          Processing failed for this document. Try deleting and re-uploading it.
                        </span>
                      )}
                    </p>
                  )}
                  <Textarea
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && !e.shiftKey && handleChat()}
                    placeholder="Ask a question about the document..."
                    className="bg-black/50 border-purple-700/40 resize-none"
                    rows={3}
                    disabled={!documentId || processingStatus !== "ready" || isLoading}
                  />
                  <div className="flex gap-2">
                    <Button
                      onClick={handleChat}
                      disabled={!documentId || processingStatus !== "ready" || isLoading || !userInput.trim()}
                      className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600"
                    >
                      <Send className="h-4 w-4 mr-2" />
                      Send
                    </Button>
                  </div>
                </div>

                {/* Model Configuration */}
                {!hasSavedCreds && (
                <div className="mt-4 pt-4 border-t border-purple-700/40 space-y-2">
                  <Label className="text-xs text-gray-400">Model Configuration (Optional)</Label>
                  <div className="grid grid-cols-2 gap-2">
                    <Select
                      value={modelConfig.provider}
                      onValueChange={(value) => setModelConfig({ ...modelConfig, provider: value })}
                    >
                      <SelectTrigger className="bg-black/50 border-purple-700/40 text-xs h-8">
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
                      className="bg-black/50 border-purple-700/40 text-xs h-8"
                    />
                  </div>
                </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
    </div>
  )
}
