"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/app/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Input } from "@/app/components/ui/input"
import { Label } from "@/app/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/app/components/ui/select"
import { ArrowRight, Sparkles, AlertCircle } from "lucide-react"
import { motion } from "framer-motion"
import { useToast } from "@/app/components/ui/use-toast"

export default function DemoPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    profession: "",
    clinical_setting: "",
    model_name: "",
    api_key: "",
    provider: "google"
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      // Initialize demo game
      const response = await fetch("/api/game/initialize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          game_config: {
            profession: formData.profession || undefined,
            clinical_setting: formData.clinical_setting || undefined,
            total_cases: 3,
            max_clinical_changes: 3
          },
          is_demo: true,
          model_name: formData.model_name || undefined,
          api_key: formData.api_key || undefined,
          provider: formData.provider
        })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || "Failed to initialize demo")
      }

      const data = await response.json()
      
      // Navigate to mediquest with game state
      router.push(`/mediquest?game_id=${data.game_state.game_id}`)
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to start demo. Please try again.",
        variant: "destructive"
      })
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-[#1E3A8A] to-[#8B5CF6] text-white py-12">
      <div className="container mx-auto px-4 max-w-2xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <div className="text-center mb-8">
            <motion.div
              className="inline-block mb-4"
              animate={{ rotate: [0, 10, -10, 0] }}
              transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
            >
              <Sparkles className="h-16 w-16 text-purple-400" />
            </motion.div>
            <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              Try Stud Demo
            </h1>
            <p className="text-gray-300 text-lg">
              Experience 1 test game with 3 clinical scenarios and 3 dynamic changes each
            </p>
          </div>

          <Card className="bg-black/40 backdrop-blur-md border-purple-500/30">
            <CardHeader>
              <CardTitle className="text-2xl">Demo Configuration</CardTitle>
              <CardDescription className="text-gray-400">
                Configure your demo experience. Leave fields empty for random selection.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="profession">Profession (Optional)</Label>
                  <Select
                    value={formData.profession}
                    onValueChange={(value) => setFormData({ ...formData, profession: value })}
                  >
                    <SelectTrigger className="bg-black/50 border-purple-500/30">
                      <SelectValue placeholder="Select or leave empty for random" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="General Practitioner">General Practitioner</SelectItem>
                      <SelectItem value="Nurse">Nurse</SelectItem>
                      <SelectItem value="Emergency Medicine Physician">Emergency Medicine Physician</SelectItem>
                      <SelectItem value="Pediatrician">Pediatrician</SelectItem>
                      <SelectItem value="Surgeon">Surgeon</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="clinical_setting">Clinical Setting (Optional)</Label>
                  <Select
                    value={formData.clinical_setting}
                    onValueChange={(value) => setFormData({ ...formData, clinical_setting: value })}
                  >
                    <SelectTrigger className="bg-black/50 border-purple-500/30">
                      <SelectValue placeholder="Select or leave empty for random" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Emergency">Emergency</SelectItem>
                      <SelectItem value="ICU">ICU</SelectItem>
                      <SelectItem value="Outpatient">Outpatient</SelectItem>
                      <SelectItem value="Inpatient">Inpatient</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="bg-purple-900/30 border border-purple-500/30 rounded-lg p-4 space-y-4">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="h-5 w-5 text-purple-400 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-purple-300 mb-1">
                        Optional: Use Your Own API Key
                      </p>
                      <p className="text-xs text-gray-400">
                        For Basic tier users, provide your own API key. Leave empty to use platform defaults.
                      </p>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="provider">Model Provider</Label>
                    <Select
                      value={formData.provider}
                      onValueChange={(value) => setFormData({ ...formData, provider: value })}
                    >
                      <SelectTrigger className="bg-black/50 border-purple-500/30">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="google">Google (Gemini)</SelectItem>
                        <SelectItem value="openai">OpenAI (ChatGPT)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="model_name">Model Name (Optional)</Label>
                    <Input
                      id="model_name"
                      placeholder="e.g., gemini-2.0-flash-exp or gpt-4"
                      value={formData.model_name}
                      onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
                      className="bg-black/50 border-purple-500/30"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="api_key">API Key (Optional)</Label>
                    <Input
                      id="api_key"
                      type="password"
                      placeholder="Your API key (not saved)"
                      value={formData.api_key}
                      onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                      className="bg-black/50 border-purple-500/30"
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white text-lg py-6"
                >
                  {loading ? (
                    "Starting Demo..."
                  ) : (
                    <>
                      Start Demo Game
                      <ArrowRight className="ml-2 h-5 w-5" />
                    </>
                  )}
                </Button>
              </form>

              <div className="mt-6 text-center">
                <p className="text-sm text-gray-400">
                  After this demo,{" "}
                  <a href="/auth/register" className="text-purple-400 hover:text-purple-300 underline">
                    register for full access
                  </a>
                </p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}
