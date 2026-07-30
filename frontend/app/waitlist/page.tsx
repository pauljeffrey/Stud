"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/app/components/ui/button"
import { Input } from "@/app/components/ui/input"
import { Label } from "@/app/components/ui/label"
import { Textarea } from "@/app/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { useToast } from "@/app/components/ui/use-toast"
import { CheckCircle2, Loader2, Rocket } from "lucide-react"
import { motion } from "framer-motion"

export default function WaitlistPage() {
  const [email, setEmail] = useState("")
  const [name, setName] = useState("")
  const [note, setNote] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [joined, setJoined] = useState(false)
  const { toast } = useToast()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setIsLoading(true)

    try {
      const response = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          name: name || undefined,
          note: note || undefined,
          source_page: "/waitlist",
        }),
      })

      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        const msg = data.message || data.detail || "Failed to join the waitlist"
        throw new Error(typeof msg === "string" ? msg : "Failed to join the waitlist")
      }

      setJoined(true)
      toast({
        title: data.already_joined ? "You're already on the list" : "You're on the list!",
        description: "We'll email you when Stud launches.",
      })
    } catch (error) {
      toast({
        title: "Something went wrong",
        description: error instanceof Error ? error.message : "Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-[#0A1128] to-[#4C1D95] flex items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          className="absolute top-20 left-10 w-72 h-72 bg-purple-900/30 rounded-full blur-3xl"
          animate={{ x: [0, 100, -50, 0], y: [0, 50, -30, 0], scale: [1, 1.3, 0.9, 1] }}
          transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute bottom-20 right-10 w-96 h-96 bg-blue-900/30 rounded-full blur-3xl"
          animate={{ x: [0, -100, 50, 0], y: [0, -50, 30, 0], scale: [1, 1.4, 0.8, 1] }}
          transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="w-full max-w-md relative z-10"
      >
        <Card className="bg-black/60 backdrop-blur-md border-purple-700/40">
          <CardHeader className="space-y-1">
            <div className="flex items-center gap-2">
              <Rocket className="h-6 w-6 text-purple-400" />
              <CardTitle className="text-2xl font-bold bg-gradient-to-r from-purple-400 via-purple-300 to-blue-400 bg-clip-text text-transparent">
                Join the Waitlist
              </CardTitle>
            </div>
            <CardDescription className="text-gray-400">
              Stud is in active development. Sign up to be notified the moment it launches — and to help
              shape early pricing.
            </CardDescription>
          </CardHeader>

          {joined ? (
            <CardContent className="space-y-4 text-center py-8">
              <CheckCircle2 className="h-12 w-12 mx-auto text-green-400" />
              <p className="text-gray-200">You're on the list. We'll be in touch when Stud is ready.</p>
            </CardContent>
          ) : (
            <form onSubmit={handleSubmit}>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="bg-black/50 border-purple-700/40 text-white"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="name">Name (optional)</Label>
                  <Input
                    id="name"
                    placeholder="Jane Doe"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="bg-black/50 border-purple-700/40 text-white"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="note">What would make Stud a must-have for you? (optional)</Label>
                  <Textarea
                    id="note"
                    placeholder="e.g. exam prep, CME credits, a specific specialty..."
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    className="bg-black/50 border-purple-700/40 text-white resize-none"
                    rows={3}
                  />
                </div>
                <Button
                  type="submit"
                  className="w-full bg-gradient-to-r from-purple-700 to-purple-900 hover:from-purple-800 hover:to-purple-950"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Joining...
                    </>
                  ) : (
                    "Join the Waitlist"
                  )}
                </Button>
              </CardContent>
            </form>
          )}
        </Card>
      </motion.div>
    </div>
  )
}
