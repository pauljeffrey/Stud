"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/app/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Textarea } from "@/app/components/ui/textarea"
import { Input } from "@/app/components/ui/input"
import { Label } from "@/app/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/app/components/ui/select"
import { Upload, Send, RotateCcw, FileText, Loader2, BookOpen, MessageCircle, Trash2, Plus } from "lucide-react"
import { useRouter } from "next/navigation"
import { useToast } from "@/app/components/ui/use-toast"
import { useDropzone } from "react-dropzone"
import { motion } from "framer-motion"
import { Document, Page, pdfjs } from "react-pdf"
import "react-pdf/dist/Page/AnnotationLayer.css"
import "react-pdf/dist/Page/TextLayer.css"

pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`

interface ChatMessage {
  role: "user" | "assistant"
  content: string
  sources?: string[]
  timestamp: Date
}

export default function StudyPage() {
  const router = useRouter()
  const [document, setDocument] = useState<File | null>(null)
  const [documentId, setDocumentId] = useState<string | null>(null)
  const [documentContent, setDocumentContent] = useState<string>("")
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [userInput, setUserInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
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
    onDrop: async (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        await handleFileUpload(acceptedFiles[0])
      }
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
      formData.append("user_id", "user_123") // TODO: Get from auth

      const response = await fetch("/api/learning/upload", {
        method: "POST",
        body: formData
      })

      if (!response.ok) throw new Error("Upload failed")

      const data = await response.json()
      setDocumentId(data.document_id)
      setDocument(file)

      // Extract text for preview (simplified - in production use proper extraction)
      if (file.type === "text/plain") {
        const text = await file.text()
        setDocumentContent(text)
      }

      toast({
        title: "Document uploaded",
        description: `Processed ${data.chunk_count} chunks. Expires in 2 hours.`
      })
    } catch (error) {
      toast({
        title: "Upload failed",
        description: "Failed to upload document",
        variant: "destructive"
      })
    } finally {
      setIsLoading(false)
      setUploadProgress(0)
    }
  }

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
      const response = await fetch("/api/learning/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          document_id: documentId,
          message: userMessage,
          chat_history: chatMessages.map(m => ({ role: m.role, content: m.content }))
        })
      })

      if (!response.ok) throw new Error("Chat failed")

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let accumulatedResponse = ""

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split("\n")

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = JSON.parse(line.slice(6))
              accumulatedResponse += data.content

              // Update last message or add new one
              setChatMessages((prev) => {
                const newMessages = [...prev]
                const lastMsg = newMessages[newMessages.length - 1]
                if (lastMsg?.role === "assistant") {
                  lastMsg.content = accumulatedResponse
                  if (data.sources) lastMsg.sources = data.sources
                } else {
                  newMessages.push({
                    role: "assistant",
                    content: accumulatedResponse,
                    sources: data.sources,
                    timestamp: new Date()
                  })
                }
                return newMessages
              })
            }
          }
        }
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to get response",
        variant: "destructive"
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteDocument = async () => {
    if (!documentId) return

    try {
      const response = await fetch(`/api/learning/documents/${documentId}`, {
        method: "DELETE"
      })

      if (!response.ok) throw new Error("Delete failed")

      setDocument(null)
      setDocumentId(null)
      setDocumentContent("")
      setChatMessages([])

      toast({
        title: "Document deleted",
        description: "Document and its data have been removed"
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete document",
        variant: "destructive"
      })
    }
  }

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
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
              onClick={() => router.push("/quiz")}
              variant="outline"
              className="border-purple-700/40"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create Quiz
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
                  {document && (
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
                {!document ? (
                  <motion.div
                    {...getRootProps()}
                    className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
                      isDragActive
                        ? "border-purple-500 bg-purple-900/20"
                        : "border-purple-700/40 hover:border-purple-500/60"
                    }`}
                    animate={{
                      scale: [1, 1.02, 1],
                    }}
                    transition={{
                      duration: 3,
                      repeat: Infinity,
                      ease: "easeInOut"
                    }}
                  >
                    <input {...getInputProps()} />
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
                  </motion.div>
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
                    <Document
                      file={document}
                      onLoadSuccess={onDocumentLoadSuccess}
                      loading={<Loader2 className="animate-spin text-purple-400" />}
                    >
                      <Page
                        pageNumber={pageNumber}
                        renderTextLayer={true}
                        renderAnnotationLayer={true}
                        className="border border-purple-700/40 rounded"
                      />
                    </Document>
                  </div>
                ) : (
                  <div className="prose prose-invert max-w-none">
                    <pre className="whitespace-pre-wrap text-sm bg-black/30 p-4 rounded">
                      {documentContent || "Document content will appear here"}
                    </pre>
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
                  <Textarea
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && !e.shiftKey && handleChat()}
                    placeholder="Ask a question about the document..."
                    className="bg-black/50 border-purple-700/40 resize-none"
                    rows={3}
                    disabled={!documentId || isLoading}
                  />
                  <div className="flex gap-2">
                    <Button
                      onClick={handleChat}
                      disabled={!documentId || isLoading || !userInput.trim()}
                      className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600"
                    >
                      <Send className="h-4 w-4 mr-2" />
                      Send
                    </Button>
                  </div>
                </div>

                {/* Model Configuration */}
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
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
    </div>
  )
}
