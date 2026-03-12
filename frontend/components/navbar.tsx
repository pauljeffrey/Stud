"use client"

import type React from "react"

import Link from "next/link"
import { useState } from "react"
import { Button } from "@/app/components/ui/button"
import { Menu, X } from "lucide-react"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"

export default function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const pathname = usePathname()

  // Don't show navbar on game page
  if (pathname === "/game") return null

  const isAuthPage = pathname.startsWith("/auth")

  return (
    <nav className={cn("w-full py-4 px-6 z-50", isAuthPage ? "bg-purple-900" : "bg-transparent absolute top-0 left-0")}>
      <div className="container mx-auto flex justify-between items-center">
        <Link href="/" className="text-2xl font-bold text-white">
          MediQuest
        </Link>

        {/* Mobile menu button */}
        <button className="md:hidden text-white" onClick={() => setIsMenuOpen(!isMenuOpen)}>
          {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>

        {/* Desktop menu */}
        <div className="hidden md:flex items-center space-x-6">
          <NavLink href="/">Home</NavLink>
          <NavLink href="/demo">Demo</NavLink>
          <NavLink href="/dashboard">Dashboard</NavLink>
          <NavLink href="/game">Game</NavLink>
          <NavLink href="/quiz">Quiz</NavLink>
          <NavLink href="/learning">Learning</NavLink>
          <div className="flex space-x-2">
            <Link href="/auth/login">
              <Button variant="ghost" className="text-white hover:bg-purple-800">
                Login
              </Button>
            </Link>
            <Link href="/auth/register">
              <Button className="bg-purple-500 hover:bg-purple-600">Register</Button>
            </Link>
          </div>
        </div>

        {/* Mobile menu */}
        {isMenuOpen && (
          <div className="md:hidden absolute top-16 left-0 right-0 bg-purple-900 p-4 flex flex-col space-y-4 z-50">
            <NavLink href="/" onClick={() => setIsMenuOpen(false)}>
              Home
            </NavLink>
            <NavLink href="/demo" onClick={() => setIsMenuOpen(false)}>
              Demo
            </NavLink>
            <NavLink href="/dashboard" onClick={() => setIsMenuOpen(false)}>
              Dashboard
            </NavLink>
            <NavLink href="/game" onClick={() => setIsMenuOpen(false)}>
              Game
            </NavLink>
            <NavLink href="/quiz" onClick={() => setIsMenuOpen(false)}>
              Quiz
            </NavLink>
            <NavLink href="/learning" onClick={() => setIsMenuOpen(false)}>
              Learning
            </NavLink>
            <Link href="/auth/login" onClick={() => setIsMenuOpen(false)}>
              <Button variant="ghost" className="w-full text-white hover:bg-purple-800">
                Login
              </Button>
            </Link>
            <Link href="/auth/register" onClick={() => setIsMenuOpen(false)}>
              <Button className="w-full bg-purple-500 hover:bg-purple-600">Register</Button>
            </Link>
          </div>
        )}
      </div>
    </nav>
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
      className={cn("text-white hover:text-purple-300 transition-colors", isActive && "font-semibold text-purple-300")}
      onClick={onClick}
    >
      {children}
    </Link>
  )
}
