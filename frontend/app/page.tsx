"use client"

import type React from "react"
import Link from "next/link"
import { Button } from "@/app/components/ui/button"
import { ArrowRight, Stethoscope, BookOpen, Brain, Sparkles, Zap, Shield } from "lucide-react"
import { motion } from "framer-motion"

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-[#0A1128] to-[#4C1D95] text-white overflow-hidden relative">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <motion.div
          className="absolute top-20 left-10 w-72 h-72 bg-purple-900/30 rounded-full blur-3xl"
          animate={{
            x: [0, 100, -50, 0],
            y: [0, 50, -30, 0],
            scale: [1, 1.3, 0.9, 1],
            rotate: [0, 90, 180, 360],
          }}
          transition={{
            duration: 12,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <motion.div
          className="absolute bottom-20 right-10 w-96 h-96 bg-blue-900/30 rounded-full blur-3xl"
          animate={{
            x: [0, -100, 50, 0],
            y: [0, -50, 30, 0],
            scale: [1, 1.4, 0.8, 1],
            rotate: [360, 270, 180, 0],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <motion.div
          className="absolute top-1/2 left-1/2 w-64 h-64 bg-purple-800/20 rounded-full blur-3xl"
          animate={{
            x: [0, 80, -80, 0],
            y: [0, -60, 60, 0],
            scale: [1, 1.2, 1.1, 1],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 2
          }}
        />
      </div>

      {/* Hero Section */}
      <div className="container mx-auto px-4 py-20 relative z-10">
        <motion.div
          className="flex flex-col items-center text-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <motion.h1
            className="text-6xl md:text-8xl font-bold mb-6 bg-gradient-to-r from-purple-500 via-purple-400 to-blue-400 bg-clip-text text-transparent"
            animate={{
              backgroundPosition: ["0%", "100%", "0%"],
              scale: [1, 1.05, 1],
            }}
            transition={{
              duration: 4,
              repeat: Infinity,
              ease: "easeInOut"
            }}
            style={{
              backgroundSize: "200% auto"
            }}
          >
            <motion.span
              animate={{
                y: [0, -10, 0],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            >
              S
            </motion.span>
            <motion.span
              animate={{
                y: [0, 10, 0],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 0.2
              }}
            >
              T
            </motion.span>
            <motion.span
              animate={{
                y: [0, -10, 0],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 0.4
              }}
            >
              U
            </motion.span>
            <motion.span
              animate={{
                y: [0, 10, 0],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 0.6
              }}
            >
              D
            </motion.span>
          </motion.h1>
          
          <motion.p
            className="text-xl md:text-3xl mb-4 font-light"
            initial={{ opacity: 0, y: 20 }}
            animate={{ 
              opacity: 1, 
              y: 0,
              scale: [1, 1.02, 1]
            }}
            transition={{ 
              delay: 0.3, 
              duration: 0.8,
              scale: {
                duration: 3,
                repeat: Infinity,
                ease: "easeInOut"
              }
            }}
          >
            <motion.span
              className="inline-block"
              animate={{
                y: [0, -5, 0],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            >
              Master Medicine Through Adventure
            </motion.span>
          </motion.p>
          
          <motion.p
            className="text-lg md:text-xl mb-10 max-w-3xl text-gray-300"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5, duration: 0.8 }}
          >
            An immersive, gamified medical education platform where healthcare professionals
            embark on clinical adventures, master medical knowledge, and advance their careers.
          </motion.p>
          
          <motion.div
            className="flex flex-col sm:flex-row gap-4 mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7, duration: 0.8 }}
          >
            <Link href="/demo">
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-purple-700 to-purple-900 hover:from-purple-800 hover:to-purple-950 text-white border-0 shadow-lg shadow-purple-900/50 text-lg px-8 py-6 group relative overflow-hidden"
                >
                  <motion.div
                    className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
                    animate={{
                      x: ["-100%", "100%"],
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: "linear"
                    }}
                  />
                  <motion.div
                    animate={{
                      rotate: [0, 360],
                    }}
                    transition={{
                      duration: 3,
                      repeat: Infinity,
                      ease: "linear"
                    }}
                  >
                    <Sparkles className="mr-2 h-5 w-5 relative z-10" />
                  </motion.div>
                  <span className="relative z-10">Try Demo</span>
                  <motion.div
                    animate={{
                      x: [0, 5, 0],
                    }}
                    transition={{
                      duration: 1.5,
                      repeat: Infinity,
                      ease: "easeInOut"
                    }}
                  >
                    <ArrowRight className="ml-2 h-5 w-5 relative z-10" />
                  </motion.div>
                </Button>
              </motion.div>
            </Link>
            <Link href="/auth/register">
              <Button
                size="lg"
                variant="outline"
                className="border-2 border-purple-400 text-white hover:bg-purple-800/50 text-lg px-8 py-6 backdrop-blur-sm"
              >
                Register Now
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </motion.div>

          {/* Feedback Link */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1, duration: 0.8 }}
            className="mt-8"
          >
            <a
              href="https://docs.google.com/forms/d/e/1FAIpQLSc3HzuhjIMtNv8cpjnnkhxrQV_A_q1iQ7s4HO7AzreBWY5Ljw/viewform?usp=header"
              target="_blank"
              rel="noopener noreferrer"
              className="text-purple-300 hover:text-purple-200 underline text-sm md:text-base transition-colors"
            >
              Share your feedback and help us improve Stud →
            </a>
          </motion.div>
        </motion.div>
      </div>

      {/* Features Section */}
      <motion.div
        className="bg-black/60 backdrop-blur-sm py-16 relative z-10"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
      >
        <div className="container mx-auto px-4">
          <motion.h2
            className="text-4xl md:text-5xl font-bold mb-12 text-center bg-gradient-to-r from-purple-400 via-purple-300 to-blue-400 bg-clip-text text-transparent"
            animate={{
              backgroundPosition: ["0%", "100%", "0%"],
            }}
            transition={{
              duration: 5,
              repeat: Infinity,
              ease: "linear"
            }}
            style={{
              backgroundSize: "200% auto"
            }}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            Three Powerful Modes
          </motion.h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <FeatureCard
              icon={<Stethoscope className="h-16 w-16 mb-4 text-purple-400" />}
              title="Mediquest"
              description="Immersive clinical role-playing game with dynamic cases, NPCs, and achievements. Master medicine through interactive scenarios."
              link="/mediquest"
              delay={0.1}
            />
            <FeatureCard
              icon={<BookOpen className="h-16 w-16 mb-4 text-blue-300" />}
              title="Study"
              description="Upload documents and chat with them using AI. Learn from your own materials with intelligent Q&A and document analysis."
              link="/study"
              delay={0.2}
            />
            <FeatureCard
              icon={<Brain className="h-16 w-16 mb-4 text-purple-400" />}
              title="Quiz"
              description="AI-generated quizzes from knowledge or documents. Multiple choice and open-ended questions with intelligent scoring."
              link="/quiz"
              delay={0.3}
            />
          </div>
        </div>
      </motion.div>

      {/* Key Features */}
      <motion.div
        className="container mx-auto px-4 py-16 relative z-10"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
      >
        <motion.h2
          className="text-4xl md:text-5xl font-bold mb-12 text-center bg-gradient-to-r from-purple-400 via-purple-300 to-blue-400 bg-clip-text text-transparent"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          animate={{
            backgroundPosition: ["0%", "100%", "0%"],
          }}
          style={{
            backgroundSize: "200% auto"
          }}
        >
          Why Choose Stud?
        </motion.h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <KeyFeature
            icon={<Zap className="h-8 w-8" />}
            title="AI-Powered"
            description="Advanced AI agents create dynamic, personalized learning experiences"
            delay={0}
          />
          <KeyFeature
            icon={<Shield className="h-8 w-8" />}
            title="Gamified"
            description="Earn achievements, progress through levels, and track your career growth"
            delay={0.1}
          />
          <KeyFeature
            icon={<Sparkles className="h-8 w-8" />}
            title="Immersive"
            description="Futuristic design with animations and interactive elements"
            delay={0.2}
          />
          <KeyFeature
            icon={<Brain className="h-8 w-8" />}
            title="Educational"
            description="Medically accurate content designed by healthcare professionals"
            delay={0.3}
          />
        </div>
      </motion.div>

      {/* CTA Section */}
      <motion.div
        className="container mx-auto px-4 py-20 text-center relative z-10"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
      >
        <motion.h2
          className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-purple-400 via-purple-300 to-blue-400 bg-clip-text text-transparent"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          animate={{
            backgroundPosition: ["0%", "100%", "0%"],
            scale: [1, 1.02, 1],
          }}
          style={{
            backgroundSize: "200% auto"
          }}
        >
          Ready to Start Your Medical Adventure?
        </motion.h2>
        <motion.p
          className="text-xl mb-8 text-gray-300"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2, duration: 0.8 }}
          animate={{
            y: [0, -5, 0],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 0.5
          }}
        >
          Join healthcare professionals worldwide in mastering medicine through gamified learning
        </motion.p>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.4, duration: 0.8 }}
        >
          <Link href="/demo">
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Button
                size="lg"
                className="bg-gradient-to-r from-purple-700 to-purple-900 hover:from-purple-800 hover:to-purple-950 text-white border-0 shadow-lg shadow-purple-900/50 text-xl px-12 py-8 relative overflow-hidden"
              >
                <motion.div
                  className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
                  animate={{
                    x: ["-100%", "100%"],
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "linear"
                  }}
                />
                <motion.span
                  className="relative z-10"
                  animate={{
                    scale: [1, 1.05, 1],
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                >
                  Start Free Demo
                </motion.span>
                <motion.div
                  animate={{
                    x: [0, 8, 0],
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                >
                  <ArrowRight className="ml-2 h-6 w-6 relative z-10 inline-block" />
                </motion.div>
              </Button>
            </motion.div>
          </Link>
        </motion.div>
      </motion.div>
    </div>
  )
}

function FeatureCard({
  icon,
  title,
  description,
  link,
  delay
}: {
  icon: React.ReactNode
  title: string
  description: string
  link: string
  delay: number
}) {
  return (
    <motion.div
      className="bg-black/60 backdrop-blur-md p-8 rounded-xl border border-purple-700/40 hover:border-purple-500/80 transition-all group cursor-pointer relative overflow-hidden"
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay, duration: 0.8 }}
      whileHover={{ scale: 1.05, y: -5 }}
    >
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-purple-900/20 via-transparent to-blue-900/20"
        animate={{
          x: ["-100%", "100%"],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "linear"
        }}
      />
      <Link href={link}>
        <motion.div 
          className="flex justify-center mb-4 relative z-10"
          animate={{
            y: [0, -10, 0],
            rotate: [0, 5, -5, 0],
          }}
          transition={{
            duration: 4,
            repeat: Infinity,
            ease: "easeInOut",
            delay: delay
          }}
        >
          {icon}
        </motion.div>
        <motion.h3 
          className="text-2xl font-bold mb-3 text-center group-hover:text-purple-400 transition-colors relative z-10"
          animate={{
            scale: [1, 1.02, 1],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "easeInOut",
            delay: delay + 0.5
          }}
        >
          {title}
        </motion.h3>
        <p className="text-gray-300 text-center relative z-10">{description}</p>
      </Link>
    </motion.div>
  )
}

function KeyFeature({
  icon,
  title,
  description,
  delay = 0
}: {
  icon: React.ReactNode
  title: string
  description: string
  delay?: number
}) {
  return (
    <motion.div
      className="bg-black/60 backdrop-blur-md p-6 rounded-lg border border-purple-700/40 hover:border-purple-500/80 relative overflow-hidden"
      initial={{ opacity: 0, scale: 0.9 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay }}
      whileHover={{ scale: 1.05, y: -5 }}
    >
      <motion.div
        className="absolute inset-0 bg-gradient-to-br from-purple-900/20 to-blue-900/20"
        animate={{
          opacity: [0.3, 0.6, 0.3],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "easeInOut",
          delay
        }}
      />
      <motion.div 
        className="flex justify-center mb-3 text-purple-400 relative z-10"
        animate={{
          y: [0, -8, 0],
          rotate: [0, 5, -5, 0],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "easeInOut",
          delay
        }}
      >
        {icon}
      </motion.div>
      <motion.h3 
        className="text-xl font-bold mb-2 text-center relative z-10"
        animate={{
          scale: [1, 1.02, 1],
        }}
        transition={{
          duration: 2.5,
          repeat: Infinity,
          ease: "easeInOut",
          delay: delay + 0.5
        }}
      >
        {title}
      </motion.h3>
      <p className="text-gray-300 text-center text-sm relative z-10">{description}</p>
    </motion.div>
  )
}
