"use client"

import { motion, AnimatePresence } from "framer-motion"
import { Loader2, Brain, Swords } from "lucide-react"

interface ProgressModalProps {
  isOpen: boolean
  mode: "quiz" | "quest"
  message?: string
}

export function ProgressModal({ isOpen, mode, message }: ProgressModalProps) {
  const config = {
    quiz: {
      icon: Brain,
      title: "Generating Your Quiz",
      subtitle: "Creating personalized questions from your study material...",
      gradient: "from-violet-600 via-purple-600 to-fuchsia-600",
      ringColor: "ring-violet-400/50",
      iconBg: "bg-violet-500/20",
    },
    quest: {
      icon: Swords,
      title: "Launching Mediquest",
      subtitle: "Preparing your clinical adventure...",
      gradient: "from-amber-600 via-orange-600 to-rose-600",
      ringColor: "ring-amber-400/50",
      iconBg: "bg-amber-500/20",
    },
  }

  const { icon: Icon, title, subtitle, gradient, ringColor, iconBg } = config[mode]

  return (
    <AnimatePresence>
      {isOpen && (
    <motion.div
      key="progress-modal"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", damping: 25, stiffness: 300 }}
        className={`relative overflow-hidden rounded-2xl bg-slate-900/95 p-8 shadow-2xl ring-2 ${ringColor}`}
      >
        <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-10`} />
        <div className="relative flex flex-col items-center gap-6">
          <div className={`rounded-full p-4 ${iconBg}`}>
            <Icon className="h-12 w-12 text-white" />
          </div>
          <Loader2 className="h-8 w-8 animate-spin text-white" />
          <div className="text-center">
            <h3 className="text-xl font-semibold text-white">{title}</h3>
            <p className="mt-1 text-sm text-slate-300">
              {message || subtitle}
            </p>
          </div>
          <div className="flex gap-1">
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="h-2 w-2 rounded-full bg-white/60"
                animate={{ opacity: [0.4, 1, 0.4] }}
                transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
              />
            ))}
          </div>
        </div>
      </motion.div>
    </motion.div>
      )}
    </AnimatePresence>
  )
}

