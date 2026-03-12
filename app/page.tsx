"use client"

import type React from "react"
import Link from "next/link"
import { Button } from "@/app/components/ui/button"
import { ArrowRight, Stethoscope, BookOpen, Brain, Sparkles, Zap, Shield } from "lucide-react"
import { motion } from "framer-motion"

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-[#1E3A8A] to-[#8B5CF6] text-white overflow-hidden relative">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <motion.div
          className="absolute top-20 left-10 w-72 h-72 bg-purple-500/20 rounded-full blur-3xl"
          animate={{
            x: [0, 100, 0],
            y: [0, 50, 0],
            scale: [1, 1.2, 1],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <motion.div
          className="absolute bottom-20 right-10 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl"
          animate={{
            x: [0, -100, 0],
            y: [0, -50, 0],
            scale: [1, 1.3, 1],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut"
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
            className="text-6xl md:text-8xl font-bold mb-6 bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400 bg-clip-text text-transparent"
            animate={{
              backgroundPosition: ["0%", "100%", "0%"],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: "linear"
            }}
            style={{
              backgroundSize: "200% auto"
            }}
          >
            STUD
          </motion.h1>
          
          <motion.p
            className="text-xl md:text-3xl mb-4 font-light"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.8 }}
          >
            Master Medicine Through Adventure
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
              <Button
                size="lg"
                className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white border-0 shadow-lg shadow-purple-500/50 text-lg px-8 py-6 group"
              >
                <Sparkles className="mr-2 h-5 w-5 group-hover:rotate-12 transition-transform" />
                Try Demo
                <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Button>
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
        className="bg-black/40 backdrop-blur-sm py-16 relative z-10"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
      >
        <div className="container mx-auto px-4">
          <motion.h2
            className="text-4xl md:text-5xl font-bold mb-12 text-center bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent"
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
              icon={<BookOpen className="h-16 w-16 mb-4 text-blue-400" />}
              title="Study"
              description="Upload documents and chat with them using AI. Learn from your own materials with intelligent Q&A and document analysis."
              link="/study"
              delay={0.2}
            />
            <FeatureCard
              icon={<Brain className="h-16 w-16 mb-4 text-pink-400" />}
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
          className="text-4xl md:text-5xl font-bold mb-12 text-center bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          Why Choose Stud?
        </motion.h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <KeyFeature
            icon={<Zap className="h-8 w-8" />}
            title="AI-Powered"
            description="Advanced AI agents create dynamic, personalized learning experiences"
          />
          <KeyFeature
            icon={<Shield className="h-8 w-8" />}
            title="Gamified"
            description="Earn achievements, progress through levels, and track your career growth"
          />
          <KeyFeature
            icon={<Sparkles className="h-8 w-8" />}
            title="Immersive"
            description="Futuristic design with animations and interactive elements"
          />
          <KeyFeature
            icon={<Brain className="h-8 w-8" />}
            title="Educational"
            description="Medically accurate content designed by healthcare professionals"
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
          className="text-4xl md:text-5xl font-bold mb-6"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          Ready to Start Your Medical Adventure?
        </motion.h2>
        <motion.p
          className="text-xl mb-8 text-gray-300"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2, duration: 0.8 }}
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
            <Button
              size="lg"
              className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white border-0 shadow-lg shadow-purple-500/50 text-xl px-12 py-8"
            >
              Start Free Demo
              <ArrowRight className="ml-2 h-6 w-6" />
            </Button>
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
      className="bg-black/40 backdrop-blur-md p-8 rounded-xl border border-purple-500/30 hover:border-purple-500/60 transition-all group cursor-pointer"
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay, duration: 0.8 }}
      whileHover={{ scale: 1.05, y: -5 }}
    >
      <Link href={link}>
        <div className="flex justify-center mb-4">{icon}</div>
        <h3 className="text-2xl font-bold mb-3 text-center group-hover:text-purple-400 transition-colors">
          {title}
        </h3>
        <p className="text-gray-300 text-center">{description}</p>
      </Link>
    </motion.div>
  )
}

function KeyFeature({
  icon,
  title,
  description
}: {
  icon: React.ReactNode
  title: string
  description: string
}) {
  return (
    <motion.div
      className="bg-black/40 backdrop-blur-md p-6 rounded-lg border border-blue-500/30"
      initial={{ opacity: 0, scale: 0.9 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
      whileHover={{ scale: 1.05 }}
    >
      <div className="flex justify-center mb-3 text-blue-400">{icon}</div>
      <h3 className="text-xl font-bold mb-2 text-center">{title}</h3>
      <p className="text-gray-300 text-center text-sm">{description}</p>
    </motion.div>
  )
}
