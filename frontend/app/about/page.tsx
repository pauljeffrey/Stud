"use client"

import { motion } from "framer-motion"
import type React from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Badge } from "@/app/components/ui/badge"
import { Stethoscope, GraduationCap, Award, Heart } from "lucide-react"

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-[#0A1128] to-[#4C1D95] text-white py-12 relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
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
      </div>
      <div className="container mx-auto px-4 max-w-4xl relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          {/* Header */}
          <div className="text-center mb-12">
            <motion.h1 
              className="text-5xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-purple-400 via-purple-300 to-blue-400 bg-clip-text text-transparent"
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
              About Stud
            </motion.h1>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Revolutionizing medical education through gamification and AI-powered learning
            </p>
          </div>

          {/* What is Stud */}
          <Card className="bg-black/60 backdrop-blur-md border-purple-700/40 mb-8">
            <CardHeader>
              <CardTitle className="text-3xl">What is Stud?</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-gray-300">
              <p className="text-lg">
                Stud is a futuristic, gamified medical education platform designed to transform how healthcare
                professionals learn and master medical knowledge. Combining cutting-edge AI technology with
                immersive role-playing game mechanics, Stud makes medical education engaging, interactive, and effective.
              </p>
              <p>
                Our platform offers three powerful modes:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li><strong>Mediquest:</strong> Immersive clinical role-playing game with dynamic cases, NPCs, and achievements</li>
                <li><strong>Study:</strong> Document-based learning with AI-powered chat and analysis</li>
                <li><strong>Quiz:</strong> AI-generated quizzes from knowledge or documents with intelligent scoring</li>
              </ul>
            </CardContent>
          </Card>

          {/* Creator Section */}
          <Card className="bg-black/60 backdrop-blur-md border-purple-700/40 mb-8">
            <CardHeader>
              <CardTitle className="text-3xl flex items-center gap-3">
                <Stethoscope className="h-8 w-8 text-purple-400" />
                Creator
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <motion.div 
                className="flex items-start gap-4"
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
                  className="bg-gradient-to-br from-purple-700 to-purple-900 rounded-full p-4"
                  animate={{
                    rotate: [0, 360],
                    scale: [1, 1.1, 1],
                  }}
                  transition={{
                    rotate: {
                      duration: 4,
                      repeat: Infinity,
                      ease: "linear"
                    },
                    scale: {
                      duration: 2,
                      repeat: Infinity,
                      ease: "easeInOut"
                    }
                  }}
                >
                  <Heart className="h-8 w-8" />
                </motion.div>
                <div className="flex-1">
                  <motion.h3 
                    className="text-2xl font-bold mb-2 bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent"
                    animate={{
                      backgroundPosition: ["0%", "100%", "0%"],
                    }}
                    transition={{
                      duration: 4,
                      repeat: Infinity,
                      ease: "linear"
                    }}
                    style={{
                      backgroundSize: "200% auto"
                    }}
                  >
                    Dr. Jeffrey Otoibhi
                  </motion.h3>
                  <motion.p 
                    className="text-gray-300 mb-4"
                    animate={{
                      y: [0, -3, 0],
                    }}
                    transition={{
                      duration: 3,
                      repeat: Infinity,
                      ease: "easeInOut"
                    }}
                  >
                    Stud is created by Dr. Jeffrey Otoibhi, a medical professional passionate about revolutionizing
                    healthcare education through technology and gamification. With a vision to make medical learning
                    accessible, engaging, and effective, Dr. Otoibhi has developed Stud as a comprehensive platform
                    for healthcare professionals worldwide.
                  </motion.p>
                </div>
              </motion.div>

              {/* Accomplishments */}
              <div className="mt-6">
                <h4 className="text-xl font-semibold mb-4 flex items-center gap-2">
                  <Award className="h-5 w-5 text-yellow-400" />
                  Accomplishments
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <motion.div 
                    className="bg-purple-900/30 border border-purple-700/40 rounded-lg p-4"
                    animate={{
                      scale: [1, 1.02, 1],
                      borderColor: ["rgba(139, 92, 246, 0.4)", "rgba(139, 92, 246, 0.6)", "rgba(139, 92, 246, 0.4)"],
                    }}
                    transition={{
                      scale: {
                        duration: 3,
                        repeat: Infinity,
                        ease: "easeInOut"
                      },
                      borderColor: {
                        duration: 3,
                        repeat: Infinity,
                        ease: "easeInOut"
                      }
                    }}
                  >
                    <motion.div
                      animate={{
                        rotate: [0, 15, -15, 0],
                      }}
                      transition={{
                        duration: 3,
                        repeat: Infinity,
                        ease: "easeInOut"
                      }}
                    >
                      <GraduationCap className="h-6 w-6 text-purple-400 mb-2" />
                    </motion.div>
                    <h5 className="font-semibold mb-1">Medical Education Innovation</h5>
                    <p className="text-sm text-gray-400">
                      Pioneering gamified medical education platforms
                    </p>
                  </motion.div>
                  <motion.div 
                    className="bg-purple-900/30 border border-purple-700/40 rounded-lg p-4"
                    animate={{
                      scale: [1, 1.02, 1],
                      borderColor: ["rgba(139, 92, 246, 0.4)", "rgba(139, 92, 246, 0.6)", "rgba(139, 92, 246, 0.4)"],
                    }}
                    transition={{
                      scale: {
                        duration: 3,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: 0.2
                      },
                      borderColor: {
                        duration: 3,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: 0.2
                      }
                    }}
                  >
                    <motion.div
                      animate={{
                        rotate: [0, -15, 15, 0],
                      }}
                      transition={{
                        duration: 3,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: 0.2
                      }}
                    >
                      <Heart className="h-6 w-6 text-purple-400 mb-2" />
                    </motion.div>
                    <h5 className="font-semibold mb-1">Healthcare Technology</h5>
                    <p className="text-sm text-gray-400">
                      Developing AI-powered solutions for medical training
                    </p>
                  </motion.div>
                  <motion.div 
                    className="bg-purple-900/30 border border-purple-700/40 rounded-lg p-4"
                    animate={{
                      scale: [1, 1.02, 1],
                      borderColor: ["rgba(139, 92, 246, 0.4)", "rgba(139, 92, 246, 0.6)", "rgba(139, 92, 246, 0.4)"],
                    }}
                    transition={{
                      scale: {
                        duration: 3,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: 0.4
                      },
                      borderColor: {
                        duration: 3,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: 0.4
                      }
                    }}
                  >
                    <motion.div
                      animate={{
                        rotate: [0, 15, -15, 0],
                      }}
                      transition={{
                        duration: 3,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: 0.4
                      }}
                    >
                      <Stethoscope className="h-6 w-6 text-blue-300 mb-2" />
                    </motion.div>
                    <h5 className="font-semibold mb-1">Clinical Excellence</h5>
                    <p className="text-sm text-gray-400">
                      Dedicated to improving healthcare outcomes through education
                    </p>
                  </motion.div>
                  <motion.div 
                    className="bg-purple-900/30 border border-purple-700/40 rounded-lg p-4"
                    animate={{
                      scale: [1, 1.02, 1],
                      borderColor: ["rgba(139, 92, 246, 0.4)", "rgba(139, 92, 246, 0.6)", "rgba(139, 92, 246, 0.4)"],
                    }}
                    transition={{
                      scale: {
                        duration: 3,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: 0.6
                      },
                      borderColor: {
                        duration: 3,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: 0.6
                      }
                    }}
                  >
                    <motion.div
                      animate={{
                        rotate: [0, -15, 15, 0],
                      }}
                      transition={{
                        duration: 3,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: 0.6
                      }}
                    >
                      <Award className="h-6 w-6 text-purple-400 mb-2" />
                    </motion.div>
                    <h5 className="font-semibold mb-1">Platform Development</h5>
                    <p className="text-sm text-gray-400">
                      Creating comprehensive medical education ecosystems
                    </p>
                  </motion.div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Mission */}
          <Card className="bg-black/60 backdrop-blur-md border-purple-700/40 mb-8">
            <CardHeader>
              <CardTitle className="text-3xl">Our Mission</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-gray-300">
              <p>
                To make medical education accessible, engaging, and effective for healthcare professionals worldwide.
                We believe that learning should be immersive, interactive, and fun, while maintaining the highest
                standards of medical accuracy and educational value.
              </p>
              <p>
                Through gamification, AI technology, and innovative design, Stud transforms traditional medical
                education into an adventure that healthcare professionals actually want to engage with.
              </p>
            </CardContent>
          </Card>

          {/* Features Highlight */}
          <Card className="bg-black/40 backdrop-blur-md border-purple-500/30">
            <CardHeader>
              <CardTitle className="text-3xl">Why Stud?</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <motion.div 
                  className="space-y-2"
                  animate={{
                    scale: [1, 1.02, 1],
                  }}
                  transition={{
                    duration: 3,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                >
                  <Badge className="bg-purple-700 mb-2">AI-Powered</Badge>
                  <p className="text-sm text-gray-300">
                    Advanced AI agents create dynamic, personalized learning experiences
                  </p>
                </motion.div>
                <motion.div 
                  className="space-y-2"
                  animate={{
                    scale: [1, 1.02, 1],
                  }}
                  transition={{
                    duration: 3,
                    repeat: Infinity,
                    ease: "easeInOut",
                    delay: 0.2
                  }}
                >
                  <Badge className="bg-blue-800 mb-2">Gamified</Badge>
                  <p className="text-sm text-gray-300">
                    Earn achievements, progress through levels, track career growth
                  </p>
                </motion.div>
                <motion.div 
                  className="space-y-2"
                  animate={{
                    scale: [1, 1.02, 1],
                  }}
                  transition={{
                    duration: 3,
                    repeat: Infinity,
                    ease: "easeInOut",
                    delay: 0.4
                  }}
                >
                  <Badge className="bg-purple-600 mb-2">Immersive</Badge>
                  <p className="text-sm text-gray-300">
                    Futuristic design with animations and interactive elements
                  </p>
                </motion.div>
                <motion.div 
                  className="space-y-2"
                  animate={{
                    scale: [1, 1.02, 1],
                  }}
                  transition={{
                    duration: 3,
                    repeat: Infinity,
                    ease: "easeInOut",
                    delay: 0.6
                  }}
                >
                  <Badge className="bg-purple-700 mb-2">Educational</Badge>
                  <p className="text-sm text-gray-300">
                    Medically accurate content designed by healthcare professionals
                  </p>
                </motion.div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}
