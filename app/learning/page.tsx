"use client"

import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Upload, FileText, Send, Loader2, BookOpen, MessageCircle, Trash2 } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { useDropzone } from "react-dropzone"

interface Document {
  id: string
  name: string
  type: string
  size: number
  uploadedAt: string
  processed: boolean
}

interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: string
  sources?: string[]
}

export default function LearningPage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [userInput, setUserInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const { toast } = useToast()
  const chatEndRef = useRef<HTMLDivElement>(null)

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      "application/pdf": [".pdf"],
      "application/msword": [".doc"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    onDrop: handleFileUpload,
  })

  async function handleFileUpload(acceptedFiles: File[]) {
    for (const file of acceptedFiles) {
      const documentId = `doc_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

      const newDocument: Document = {
        id: documentId,
        name: file.name,
        type: file.type,
        size: file.size,
        uploadedAt: new Date().toISOString(),
        processed: false,
      }

      setDocuments((prev) => [...prev, newDocument])

      try {
        // Simulate upload progress
        for (let i = 0; i <= 100; i += 10) {
          setUploadProgress(i)
          await new Promise((resolve) => setTimeout(resolve, 100))
        }

        // Upload and process document
        const formData = new FormData()
        formData.append("file", file)
        formData.append("documentId", documentId)

        const response = await fetch("/api/learning/upload", {
          method: "POST",
          body: formData,
        })

        if (!response.ok) {
          throw new Error("Upload failed")
        }

        // Update document as processed
        setDocuments((prev) => prev.map((doc) => (doc.id === documentId ? { ...doc, processed: true } : doc)))

        toast({
          title: "Document Uploaded",
          description: `${file.name} has been processed and is ready for chat.`,
        })
      } catch (error) {
        console.error("Upload error:", error)
        toast({
          title: "Upload Failed",
          description: `Failed to upload ${file.name}. Please try again.`,
          variant: "destructive",
        })

        // Remove failed document
        setDocuments((prev) => prev.filter((doc) => doc.id !== documentId))
      } finally {
        setUploadProgress(0)
      }
    }
  }

  const selectDocument = (document: Document) => {
    if (!document.processed) {
      toast({
        title: "Document Not Ready",
        description: "Please wait for the document to finish processing.",
        variant: "destructive",
      })
      return
    }

    setSelectedDocument(document)
    setChatMessages([
      {
        id: `msg_${Date.now()}`,
        role: "assistant",
        content: `Hello! I'm ready to help you learn from "${document.name}". You can ask me questions about the content, request summaries, or explore specific topics. What would you like to know?`,
        timestamp: new Date().toISOString(),
      },
    ])
  }

  const sendMessage = async () => {
    if (!userInput.trim() || !selectedDocument) return

    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: "user",
      content: userInput,
      timestamp: new Date().toISOString(),
    }

    setChatMessages((prev) => [...prev, userMessage])
    setUserInput("")
    setIsLoading(true)

    try {
      const response = await fetch("/api/learning/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          documentId: selectedDocument.id,
          message: userInput,
          chatHistory: chatMessages,
        }),
      })

      if (!response.ok) {
        throw new Error("Failed to get response")
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error("No response body")

      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now()}`,
        role: "assistant",
        content: "",
        timestamp: new Date().toISOString(),
        sources: [],
      }

      setChatMessages((prev) => [...prev, assistantMessage])

      // Stream the response
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = new TextDecoder().decode(value)
        const lines = chunk.split("\n")

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.content) {
                setChatMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessage.id ? { ...msg, content: msg.content + data.content } : msg,
                  ),
                )
              }
              if (data.sources) {
                setChatMessages((prev) =>
                  prev.map((msg) => (msg.id === assistantMessage.id ? { ...msg, sources: data.sources } : msg)),
                )
              }
            } catch (e) {
              // Ignore parsing errors for incomplete chunks
            }
          }
        }
      }
    } catch (error) {
      console.error("Chat error:", error)
      toast({
        title: "Error",
        description: "Failed to get response. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const deleteDocument = async (documentId: string) => {
    try {
      await fetch(`/api/learning/documents/${documentId}`, {
        method: "DELETE",
      })

      setDocuments((prev) => prev.filter((doc) => doc.id !== documentId))

      if (selectedDocument?.id === documentId) {
        setSelectedDocument(null)
        setChatMessages([])
      }

      toast({
        title: "Document Deleted",
        description: "Document has been removed successfully.",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete document.",
        variant: "destructive",
      })
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-900 to-purple-700 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Learning Center</h1>
          <p className="text-purple-200">Upload documents and chat with AI to enhance your learning</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Document Management */}
          <div className="lg:col-span-1">
            <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white mb-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5" />
                  Upload Documents
                </CardTitle>
                <CardDescription className="text-purple-200">
                  Upload PDF, Word, or text files to start learning
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                    isDragActive ? "border-purple-400 bg-purple-800/50" : "border-purple-600 hover:border-purple-400"
                  }`}
                >
                  <input {...getInputProps()} />
                  <Upload className="h-8 w-8 mx-auto mb-2 text-purple-300" />
                  {isDragActive ? (
                    <p className="text-purple-200">Drop files here...</p>
                  ) : (
                    <div>
                      <p className="text-purple-200 mb-1">Drag & drop files here</p>
                      <p className="text-sm text-purple-300">or click to browse</p>
                      <p className="text-xs text-purple-400 mt-2">Supports PDF, DOC, DOCX, TXT (max 10MB)</p>
                    </div>
                  )}
                </div>

                {uploadProgress > 0 && (
                  <div className="mt-4">
                    <div className="flex justify-between text-sm mb-1">
                      <span>Uploading...</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <Progress value={uploadProgress} />
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Document List */}
            <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Your Documents
                </CardTitle>
              </CardHeader>
              <CardContent>
                {documents.length === 0 ? (
                  <p className="text-purple-200 text-center py-4">No documents uploaded yet</p>
                ) : (
                  <div className="space-y-2">
                    {documents.map((doc) => (
                      <div
                        key={doc.id}
                        className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                          selectedDocument?.id === doc.id
                            ? "bg-purple-600 border-purple-400"
                            : "bg-purple-800 border-purple-600 hover:bg-purple-700"
                        }`}
                        onClick={() => selectDocument(doc)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1 min-w-0">
                            <p className="font-medium truncate">{doc.name}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-xs text-purple-200">{formatFileSize(doc.size)}</span>
                              {doc.processed ? (
                                <Badge variant="secondary" className="bg-green-600 text-white text-xs">
                                  Ready
                                </Badge>
                              ) : (
                                <Badge variant="secondary" className="bg-yellow-600 text-white text-xs">
                                  Processing...
                                </Badge>
                              )}
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              deleteDocument(doc.id)
                            }}
                            className="text-red-400 hover:text-red-300 hover:bg-red-900/20"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Chat Interface */}
          <div className="lg:col-span-2">
            <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white h-[700px] flex flex-col">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageCircle className="h-5 w-5" />
                  {selectedDocument ? `Chat with ${selectedDocument.name}` : "Select a document to start chatting"}
                </CardTitle>
              </CardHeader>

              {selectedDocument ? (
                <>
                  <CardContent className="flex-1 overflow-y-auto">
                    <div className="space-y-4">
                      {chatMessages.map((message) => (
                        <div
                          key={message.id}
                          className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                        >
                          <div
                            className={`max-w-[80%] p-3 rounded-lg ${
                              message.role === "user" ? "bg-purple-600 text-white" : "bg-purple-800 text-white"
                            }`}
                          >
                            <p className="whitespace-pre-wrap">{message.content}</p>
                            {message.sources && message.sources.length > 0 && (
                              <div className="mt-2 pt-2 border-t border-purple-600">
                                <p className="text-xs text-purple-200 mb-1">Sources:</p>
                                {message.sources.map((source, index) => (
                                  <p key={index} className="text-xs text-purple-300">
                                    • {source}
                                  </p>
                                ))}
                              </div>
                            )}
                            <p className="text-xs text-purple-300 mt-1">
                              {new Date(message.timestamp).toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                      ))}
                      {isLoading && (
                        <div className="flex justify-start">
                          <div className="bg-purple-800 p-3 rounded-lg">
                            <Loader2 className="h-4 w-4 animate-spin" />
                          </div>
                        </div>
                      )}
                      <div ref={chatEndRef} />
                    </div>
                  </CardContent>

                  <div className="p-4 border-t border-purple-600">
                    <div className="flex gap-2">
                      <Textarea
                        value={userInput}
                        onChange={(e) => setUserInput(e.target.value)}
                        placeholder="Ask questions about the document..."
                        className="flex-1 bg-purple-800 border-purple-600 text-white placeholder-purple-300 resize-none"
                        rows={2}
                        onKeyPress={(e) => {
                          if (e.key === "Enter" && !e.shiftKey) {
                            e.preventDefault()
                            sendMessage()
                          }
                        }}
                      />
                      <Button
                        onClick={sendMessage}
                        disabled={isLoading || !userInput.trim()}
                        className="bg-purple-600 hover:bg-purple-700"
                      >
                        {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                </>
              ) : (
                <CardContent className="flex-1 flex items-center justify-center">
                  <div className="text-center">
                    <BookOpen className="h-16 w-16 mx-auto mb-4 text-purple-400" />
                    <h3 className="text-xl font-semibold mb-2">No Document Selected</h3>
                    <p className="text-purple-200">
                      Upload and select a document to start an AI-powered learning session
                    </p>
                  </div>
                </CardContent>
              )}
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
