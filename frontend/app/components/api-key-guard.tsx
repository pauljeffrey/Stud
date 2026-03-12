"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Button } from "@/app/components/ui/button"
import { AlertCircle, Key } from "lucide-react"
import { motion } from "framer-motion"
import Link from "next/link"
import { useApiKeyRequired, hasApiKey } from "@/lib/use-api-key"

interface ApiKeyGuardProps {
  children: React.ReactNode
  allowDemo?: boolean
}

export function ApiKeyGuard({ children, allowDemo = false }: ApiKeyGuardProps) {
  const router = useRouter()
  const [isChecking, setIsChecking] = useState(true)
  const [apiKeyRequired, setApiKeyRequired] = useState(false)
  const [userHasApiKey, setUserHasApiKey] = useState(false)

  useEffect(() => {
    // Check if API key is required
    const required = useApiKeyRequired()
    const hasKey = hasApiKey()
    
    setApiKeyRequired(required)
    setUserHasApiKey(hasKey)
    setIsChecking(false)

    // If API key is required and user doesn't have one, and demo is not allowed
    if (required && !hasKey && !allowDemo) {
      // Don't redirect, just show the guard UI
    }
  }, [])

  if (isChecking) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-black via-[#0A1128] to-[#4C1D95] flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
      </div>
    )
  }

  // If API key is required but user doesn't have one (and demo is not allowed)
  if (apiKeyRequired && !userHasApiKey && !allowDemo) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-black via-[#0A1128] to-[#4C1D95] flex items-center justify-center p-4 relative overflow-hidden">
        {/* Animated Background */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <motion.div
            className="absolute top-20 left-10 w-72 h-72 bg-purple-900/30 rounded-full blur-3xl"
            animate={{
              x: [0, 100, -50, 0],
              y: [0, 50, -30, 0],
              scale: [1, 1.3, 0.9, 1],
            }}
            transition={{
              duration: 12,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-md w-full relative z-10"
        >
          <Card className="bg-black/60 backdrop-blur-md border-purple-700/40">
            <CardHeader>
              <div className="flex items-center gap-3 mb-2">
                <motion.div
                  animate={{ rotate: [0, 10, -10, 0] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <Key className="h-6 w-6 text-purple-400" />
                </motion.div>
                <CardTitle className="text-2xl font-bold bg-gradient-to-r from-purple-400 via-purple-300 to-blue-400 bg-clip-text text-transparent">
                  API Key Required
                </CardTitle>
              </div>
              <CardDescription className="text-gray-400">
                To use this feature, please configure your API key in settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start gap-3 p-4 bg-purple-900/30 rounded-lg border border-purple-700/40">
                <AlertCircle className="h-5 w-5 text-purple-400 mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-sm text-gray-300">
                    This platform requires you to provide your own API key to use AI features. 
                    Please configure your API key in your dashboard settings before continuing.
                  </p>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-3">
                <Link href="/dashboard?tab=settings" className="flex-1">
                  <Button className="w-full bg-gradient-to-r from-purple-700 to-purple-900 hover:from-purple-800 hover:to-purple-950">
                    Go to Settings
                  </Button>
                </Link>
                {allowDemo && (
                  <Link href="/demo" className="flex-1">
                    <Button variant="outline" className="w-full border-purple-700/40 text-purple-300 hover:bg-purple-900/30">
                      Try Demo Instead
                    </Button>
                  </Link>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    )
  }

  // User has API key or API key is not required
  return <>{children}</>
}
