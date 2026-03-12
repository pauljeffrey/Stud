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
import "react-pdf/dist/esm/Page/AnnotationLayer.css"
import "react-pdf/dist/esm/Page/TextLayer.css"

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
    <div className="min-h-screen bg-gradient-to-b from-black via-[#1E3A8A] to-[#8B5CF6] text-white p-4">
      <div className="container mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              Study Mode
            </h1>
            <p className="text-gray-300">Upload documents and chat with them using AI</p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => setChatPosition(chatPosition === "right" ? "left" : "right")}
              variant="outline"
              className="border-purple-500/30"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Rotate Sections
            </Button>
            <Button
              onClick={() => router.push("/quiz")}
              variant="outline"
              className="border-purple-500/30"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create Quiz
            </Button>
            <Button
              onClick={() => router.push("/demo")}
              variant="outline"
              className="border-purple-500/30"
            >
              Start Quest
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-[calc(100vh-8rem)]">
          {/* Document Viewer - Left */}
          <div className={`${chatPosition === "left" ? "lg:order-2" : ""}`}>
            <Card className="bg-black/40 backdrop-blur-md border-purple-500/30 h-full flex flex-col">
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
                  <div
                    {...getRootProps()}
                    className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
                      isDragActive
                        ? "border-purple-500 bg-purple-900/20"
                        : "border-purple-500/30 hover:border-purple-500/60"
                    }`}
                  >
                    <input {...getInputProps()} />
                    <Upload className="h-12 w-12 mx-auto mb-4 text-purple-400" />
                    <p className="text-lg mb-2">
                      {isDragActive ? "Drop file here" : "Drag & drop document here"}
                    </p>
                    <p className="text-sm text-gray-400">
                      Supports PDF, DOCX, PPT, TXT, Images
                    </p>
                    <Button className="mt-4 bg-purple-600 hover:bg-purple-700">
                      Select File
                    </Button>
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
                          className="border-purple-500/30"
                        >
                          Previous
                        </Button>
                        <Button
                          onClick={() => setPageNumber((p) => Math.min(numPages, p + 1))}
                          disabled={pageNumber >= numPages}
                          size="sm"
                          variant="outline"
                          className="border-purple-500/30"
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
                        className="border border-purple-500/30 rounded"
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
          </div>

          {/* Chat Interface - Right */}
          <div className={`${chatPosition === "left" ? "lg:order-1" : ""}`}>
            <Card className="bg-black/40 backdrop-blur-md border-purple-500/30 h-full flex flex-col">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageCircle className="h-5 w-5" />
                  Chat with Document
                </CardTitle>
                <CardDescription className="text-gray-400">
                  Ask questions about your uploaded document
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col">
                {/* Chat Messages */}
                <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                  {chatMessages.length === 0 ? (
                    <div className="text-center text-gray-400 mt-8">
                      <BookOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>Start a conversation about your document</p>
                    </div>
                  ) : (
                    chatMessages.map((msg, idx) => (
                      <motion.div
                        key={idx}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                      >
                        <div
                          className={`max-w-[80%] rounded-lg p-3 ${
                            msg.role === "user"
                              ? "bg-purple-600/30"
                              : "bg-blue-600/30"
                          }`}
                        >
                          <p className="text-sm">{msg.content}</p>
                          {msg.sources && msg.sources.length > 0 && (
                            <div className="mt-2 text-xs text-gray-400">
                              Sources: {msg.sources.length}
                            </div>
                          )}
                        </div>
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
                    className="bg-black/50 border-purple-500/30 resize-none"
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
                <div className="mt-4 pt-4 border-t border-purple-500/30 space-y-2">
                  <Label className="text-xs text-gray-400">Model Configuration (Optional)</Label>
                  <div className="grid grid-cols-2 gap-2">
                    <Select
                      value={modelConfig.provider}
                      onValueChange={(value) => setModelConfig({ ...modelConfig, provider: value })}
                    >
                      <SelectTrigger className="bg-black/50 border-purple-500/30 text-xs h-8">
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
                      className="bg-black/50 border-purple-500/30 text-xs h-8"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
