"use client"

import type React from "react"
import Link from "next/link"
import { useState } from "react"
import { Button } from "@/app/components/ui/button"
import { Menu, X, Gamepad2, BookOpen, Brain, Info, HelpCircle } from "lucide-react"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { motion } from "framer-motion"

export default function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const pathname = usePathname()

  // Don't show navbar on game page
  if (pathname === "/mediquest" || pathname === "/game") return null

  const isAuthPage = pathname.startsWith("/auth")
  const isHomePage = pathname === "/"

  return (
    <motion.nav
      className={cn(
        "w-full py-4 px-6 z-50 fixed top-0 left-0",
        isAuthPage ? "bg-purple-950/95 backdrop-blur-sm" : "bg-black/90 backdrop-blur-md border-b border-purple-900/30"
      )}
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="container mx-auto flex justify-between items-center">
        <motion.div
          animate={{
            scale: [1, 1.05, 1],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          <Link href="/" className="text-2xl font-bold bg-gradient-to-r from-purple-400 via-purple-300 to-blue-400 bg-clip-text text-transparent">
            <motion.span
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
              STUD
            </motion.span>
          </Link>
        </motion.div>

        {/* Mobile menu button */}
        <button
          className="md:hidden text-white"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
        >
          {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>

        {/* Desktop menu */}
        <div className="hidden md:flex items-center space-x-6">
          <NavLink href="/">Home</NavLink>
          <NavLink href="/demo">
            <span className="flex items-center gap-1">
              <Gamepad2 className="h-4 w-4" />
              Demo
            </span>
          </NavLink>
          <NavLink href="/mediquest">
            <span className="flex items-center gap-1">
              <Gamepad2 className="h-4 w-4" />
              Mediquest
            </span>
          </NavLink>
          <NavLink href="/study">
            <span className="flex items-center gap-1">
              <BookOpen className="h-4 w-4" />
              Study
            </span>
          </NavLink>
          <NavLink href="/quiz">
            <span className="flex items-center gap-1">
              <Brain className="h-4 w-4" />
              Quiz
            </span>
          </NavLink>
          <NavLink href="/about">
            <span className="flex items-center gap-1">
              <Info className="h-4 w-4" />
              About
            </span>
          </NavLink>
          <NavLink href="/how-to-use">
            <span className="flex items-center gap-1">
              <HelpCircle className="h-4 w-4" />
              How to Use
            </span>
          </NavLink>
          <div className="flex space-x-2">
            <Link href="/auth/login">
              <Button variant="ghost" className="text-white hover:bg-purple-800">
                Login
              </Button>
            </Link>
            <Link href="/auth/register">
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Button className="bg-gradient-to-r from-purple-700 to-purple-900 hover:from-purple-800 hover:to-purple-950 relative overflow-hidden">
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
                  <span className="relative z-10">Register</span>
                </Button>
              </motion.div>
            </Link>
          </div>
        </div>

        {/* Mobile menu */}
        {isMenuOpen && (
          <motion.div
            className="md:hidden absolute top-16 left-0 right-0 bg-black/95 backdrop-blur-md p-4 flex flex-col space-y-4 z-50 border-t border-purple-700/40"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <NavLink href="/" onClick={() => setIsMenuOpen(false)}>Home</NavLink>
            <NavLink href="/demo" onClick={() => setIsMenuOpen(false)}>
              <span className="flex items-center gap-1">
                <Gamepad2 className="h-4 w-4" />
                Demo
              </span>
            </NavLink>
            <NavLink href="/mediquest" onClick={() => setIsMenuOpen(false)}>
              <span className="flex items-center gap-1">
                <Gamepad2 className="h-4 w-4" />
                Mediquest
              </span>
            </NavLink>
            <NavLink href="/study" onClick={() => setIsMenuOpen(false)}>
              <span className="flex items-center gap-1">
                <BookOpen className="h-4 w-4" />
                Study
              </span>
            </NavLink>
            <NavLink href="/quiz" onClick={() => setIsMenuOpen(false)}>
              <span className="flex items-center gap-1">
                <Brain className="h-4 w-4" />
                Quiz
              </span>
            </NavLink>
            <NavLink href="/about" onClick={() => setIsMenuOpen(false)}>
              <span className="flex items-center gap-1">
                <Info className="h-4 w-4" />
                About
              </span>
            </NavLink>
            <NavLink href="/how-to-use" onClick={() => setIsMenuOpen(false)}>
              <span className="flex items-center gap-1">
                <HelpCircle className="h-4 w-4" />
                How to Use
              </span>
            </NavLink>
            <div className="flex flex-col space-y-2 pt-4 border-t border-purple-500/30">
              <Link href="/auth/login" onClick={() => setIsMenuOpen(false)}>
                <Button variant="ghost" className="w-full text-white hover:bg-purple-800">
                  Login
                </Button>
              </Link>
              <Link href="/auth/register" onClick={() => setIsMenuOpen(false)}>
                <Button className="w-full bg-gradient-to-r from-purple-700 to-purple-900 hover:from-purple-800 hover:to-purple-950">
                  Register
                </Button>
              </Link>
            </div>
          </motion.div>
        )}
      </div>
    </motion.nav>
  )
}

function NavLink({
  href,
  children,
  onClick,
}: {
  href: string
  children: React.ReactNode
  onClick?: () => void
}) {
  const pathname = usePathname()
  const isActive = pathname === href

  return (
    <Link
      href={href}
      className={cn(
        "text-white hover:text-purple-400 transition-colors text-sm relative",
        isActive && "font-semibold text-purple-400"
      )}
      onClick={onClick}
    >
      {children}
    </Link>
  )
}
