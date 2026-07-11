"use client"

import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Button } from "@/app/components/ui/button"
import { Badge } from "@/app/components/ui/badge"
import { ExternalLink, KeyRound, Shield } from "lucide-react"

const PROVIDERS = [
  {
    id: "openai",
    name: "OpenAI",
    models: ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini"],
    steps: [
      "Sign in at platform.openai.com.",
      "Open API keys in the left sidebar (Settings → API keys).",
      "Click Create new secret key and copy it immediately — you will not see it again.",
      "Use a model name like gpt-4o-mini in Stud.",
    ],
    url: "https://platform.openai.com/api-keys",
  },
  {
    id: "google",
    name: "Google Gemini",
    models: ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-pro"],
    steps: [
      "Go to Google AI Studio (aistudio.google.com).",
      "Click Get API key in the left menu.",
      "Create a key for your Google Cloud project and copy it.",
      "Use a model name like gemini-2.0-flash in Stud.",
    ],
    url: "https://aistudio.google.com/apikey",
  },
  {
    id: "anthropic",
    name: "Anthropic",
    models: ["claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"],
    steps: [
      "Create an account at console.anthropic.com.",
      "Open API Keys and create a new key.",
      "Copy the key and store it somewhere safe.",
      "Use a model name like claude-3-5-sonnet-latest, or an OpenRouter ID anthropic/claude-3.5-sonnet.",
    ],
    url: "https://console.anthropic.com/settings/keys",
  },
  {
    id: "openrouter",
    name: "OpenRouter",
    models: [
      "meta-llama/llama-3.3-70b-instruct:free",
      "nvidia/nemotron-3-nano-30b-a3b:free",
      "anthropic/claude-3.5-sonnet",
    ],
    steps: [
      "Sign up at openrouter.ai.",
      "Open Keys and create an API key.",
      "Copy the key — it starts with sk-or-.",
      "Use the full model slug from openrouter.ai/models (provider/model-name).",
    ],
    url: "https://openrouter.ai/keys",
  },
]

export default function ApiKeysGuidePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-[#0A1128] to-[#4C1D95] text-white py-12">
      <div className="container mx-auto px-4 max-w-4xl space-y-8">
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 text-purple-300">
            <KeyRound className="h-6 w-6" />
            <span className="text-sm font-medium uppercase tracking-wide">Stud setup guide</span>
          </div>
          <h1 className="text-4xl font-bold">How to get a model name &amp; API key</h1>
          <p className="text-gray-300 max-w-2xl mx-auto">
            Registered accounts need your own AI provider credentials. Use a{" "}
            <strong className="text-purple-200">model ID</strong> (not your email) and a secret{" "}
            <strong className="text-purple-200">API key</strong> from one of the providers below.
          </p>
        </div>

        <Card className="bg-black/50 border-purple-700/40">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-purple-200">
              <Shield className="h-5 w-5" />
              How Stud stores your key
            </CardTitle>
            <CardDescription className="text-gray-400">
              If you choose to save your API key, it is encrypted on our server before storage. You
              can also use a key for one session only without saving it.
            </CardDescription>
          </CardHeader>
        </Card>

        <div className="grid gap-6">
          {PROVIDERS.map((p) => (
            <Card key={p.id} className="bg-black/60 border-purple-700/40">
              <CardHeader>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <CardTitle>{p.name}</CardTitle>
                  <Button variant="outline" size="sm" asChild className="border-purple-600">
                    <a href={p.url} target="_blank" rel="noopener noreferrer">
                      Open console <ExternalLink className="ml-1 h-3 w-3" />
                    </a>
                  </Button>
                </div>
                <CardDescription className="text-gray-400">Example model names</CardDescription>
                <div className="flex flex-wrap gap-2 pt-1">
                  {p.models.map((m) => (
                    <Badge key={m} variant="secondary" className="bg-purple-900/50 text-purple-100">
                      {m}
                    </Badge>
                  ))}
                </div>
              </CardHeader>
              <CardContent>
                <ol className="list-decimal list-inside space-y-2 text-sm text-gray-300">
                  {p.steps.map((step, i) => (
                    <li key={i}>{step}</li>
                  ))}
                </ol>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="flex flex-wrap gap-3 justify-center pt-4">
          <Button asChild className="bg-purple-700 hover:bg-purple-800">
            <Link href="/demo">Back to Mediquest</Link>
          </Button>
          <Button asChild variant="outline" className="border-purple-600">
            <Link href="/dashboard">Open dashboard settings</Link>
          </Button>
        </div>
      </div>
    </div>
  )
}
