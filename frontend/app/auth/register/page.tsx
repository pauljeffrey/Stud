"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/app/components/ui/button"
import { Input } from "@/app/components/ui/input"
import { Label } from "@/app/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/app/components/ui/card"
import { useToast } from "@/app/components/ui/use-toast"
import { Loader2 } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/app/components/ui/select"
import { motion } from "framer-motion"
import { saveAuth } from "@/app/lib/auth"

// Exhaustive list of health/biological professions
const PROFESSION_OPTIONS = [
  "Physician (MD/DO)",
  "Surgeon",
  "Anesthesiologist",
  "Radiologist",
  "Pathologist",
  "Psychiatrist",
  "Pediatrician",
  "Obstetrician/Gynecologist",
  "Cardiologist",
  "Neurologist",
  "Orthopedic Surgeon",
  "Emergency Medicine Physician",
  "Family Medicine Physician",
  "Internal Medicine Physician",
  "Dermatologist",
  "Ophthalmologist",
  "Otolaryngologist (ENT)",
  "Urologist",
  "Pulmonologist",
  "Gastroenterologist",
  "Nephrologist",
  "Endocrinologist",
  "Rheumatologist",
  "Oncologist",
  "Infectious Disease Specialist",
  "Registered Nurse (RN)",
  "Licensed Practical Nurse (LPN)",
  "Nurse Practitioner (NP)",
  "Nurse Anesthetist (CRNA)",
  "Nurse Midwife (CNM)",
  "Physician Assistant (PA)",
  "Medical Assistant",
  "Pharmacist",
  "Pharmacy Technician",
  "Physical Therapist (PT)",
  "Occupational Therapist (OT)",
  "Speech-Language Pathologist",
  "Respiratory Therapist",
  "Radiologic Technologist",
  "Medical Laboratory Scientist",
  "Phlebotomist",
  "Paramedic",
  "Emergency Medical Technician (EMT)",
  "Dental Hygienist",
  "Dentist",
  "Veterinarian",
  "Biomedical Scientist",
  "Clinical Research Associate",
  "Healthcare Administrator",
  "Medical Coder",
  "Other",
]

// Exhaustive list of student fields
const STUDENT_FIELD_OPTIONS = [
  "Medical Student (MD/DO)",
  "Nursing Student (BSN)",
  "Nursing Student (ADN)",
  "Physician Assistant Student",
  "Pharmacy Student",
  "Dental Student",
  "Veterinary Student",
  "Physical Therapy Student",
  "Occupational Therapy Student",
  "Speech Pathology Student",
  "Respiratory Therapy Student",
  "Radiology Technology Student",
  "Medical Laboratory Science Student",
  "Public Health Student",
  "Biomedical Sciences Student",
  "Pre-Med",
  "Pre-Nursing",
  "Pre-Pharmacy",
  "Pre-Dental",
  "Pre-Veterinary",
  "Biology Student",
  "Biochemistry Student",
  "Neuroscience Student",
  "Health Sciences Student",
  "Other",
]

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    userType: "" as "" | "professional" | "student",
    profession: "",
    professionOther: "",
    age: "",
  })
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()
  const { toast } = useToast()

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  function handleUserTypeChange(value: string) {
    setFormData((prev) => ({
      ...prev,
      userType: value as "professional" | "student",
      profession: "",
      professionOther: "",
    }))
  }

  function handleProfessionChange(value: string) {
    setFormData((prev) => ({
      ...prev,
      profession: value,
      professionOther: value === "Other" ? prev.professionOther : "",
    }))
  }

  function getProfessionValue(): string {
    if (formData.profession === "Other") {
      return formData.professionOther.trim() || "Other"
    }
    return formData.profession
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    if (formData.password !== formData.confirmPassword) {
      toast({
        title: "Passwords do not match",
        description: "Please make sure your passwords match.",
        variant: "destructive",
      })
      return
    }

    if (!formData.userType) {
      toast({
        title: "Select your role",
        description: "Please select whether you are a Professional or Student.",
        variant: "destructive",
      })
      return
    }

    const professionValue = getProfessionValue()
    if (!professionValue) {
      toast({
        title: "Select your field",
        description: "Please select your profession or field of study.",
        variant: "destructive",
      })
      return
    }

    setIsLoading(true)

    try {
      const payload = {
        name: formData.name,
        email: formData.email,
        password: formData.password,
        user_type: formData.userType,
        profession: formData.profession === "Other" ? "other" : professionValue,
        profession_other: formData.profession === "Other" ? formData.professionOther.trim() || undefined : undefined,
        age: formData.age ? parseInt(formData.age, 10) : undefined,
      }

      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })

      const data = await response.json().catch(() => ({}))
      if (!response.ok) {
        const msg = data.message || data.detail || "Registration failed"
        throw new Error(msg)
      }

      if (data.token && data.user) {
        saveAuth(data.token, data.user)
      }
      if (data.session_token) {
        localStorage.setItem("session_token", data.session_token)
      }

      toast({
        title: "Registration successful",
        description: "Your account has been created. Redirecting to dashboard...",
      })

      router.push("/dashboard")
    } catch (error) {
      toast({
        title: "Registration failed",
        description: error instanceof Error ? error.message : "There was an error creating your account. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const options = formData.userType === "student" ? STUDENT_FIELD_OPTIONS : PROFESSION_OPTIONS
  const showOtherInput = formData.profession === "Other"

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
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="w-full max-w-md relative z-10"
      >
        <Card className="bg-black/60 backdrop-blur-md border-purple-700/40">
          <CardHeader className="space-y-1">
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
              <CardTitle className="text-2xl font-bold bg-gradient-to-r from-purple-400 via-purple-300 to-blue-400 bg-clip-text text-transparent">
                Create an account
              </CardTitle>
            </motion.div>
            <CardDescription className="text-gray-400">Enter your information to join Stud</CardDescription>
          </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Full Name</Label>
              <Input
                id="name"
                name="name"
                placeholder="Dr. Jane Smith"
                value={formData.name}
                onChange={handleChange}
                className="bg-black/50 border-purple-700/40 text-white"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="doctor@example.com"
                value={formData.email}
                onChange={handleChange}
                className="bg-black/50 border-purple-700/40 text-white"
                required
              />
            </div>

            <div className="space-y-2">
              <Label>I am a...</Label>
              <Select value={formData.userType} onValueChange={handleUserTypeChange} required>
                <SelectTrigger className="bg-black/50 border-purple-700/40 text-white">
                  <SelectValue placeholder="Select your role" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="professional">Professional</SelectItem>
                  <SelectItem value="student">Student</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {formData.userType && (
              <div className="space-y-2">
                <Label>
                  {formData.userType === "professional" ? "Profession" : "Field of study"}
                </Label>
                <Select value={formData.profession} onValueChange={handleProfessionChange}>
                  <SelectTrigger className="bg-black/50 border-purple-700/40 text-white">
                    <SelectValue
                      placeholder={
                        formData.userType === "professional"
                          ? "Select your profession"
                          : "Select your field"
                      }
                    />
                  </SelectTrigger>
                  <SelectContent>
                    {options.map((opt) => (
                      <SelectItem key={opt} value={opt}>
                        {opt}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {showOtherInput && (
                  <Input
                    placeholder="Enter your profession or field"
                    value={formData.professionOther}
                    onChange={(e) =>
                      setFormData((prev) => ({ ...prev, professionOther: e.target.value }))
                    }
                    className="mt-2 bg-black/50 border-purple-700/40 text-white"
                  />
                )}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="age">Age</Label>
              <Input
                id="age"
                name="age"
                type="number"
                placeholder="30"
                min="18"
                max="100"
                value={formData.age}
                onChange={handleChange}
                className="bg-black/50 border-purple-700/40 text-white"
              />
              <p className="text-xs text-gray-500">Optional</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                className="bg-black/50 border-purple-700/40 text-white"
                required
                minLength={8}
              />
              <p className="text-xs text-gray-500">Minimum 8 characters</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                value={formData.confirmPassword}
                onChange={handleChange}
                className="bg-black/50 border-purple-700/40 text-white"
                required
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <motion.div
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full"
            >
              <Button 
                type="submit" 
                className="w-full bg-gradient-to-r from-purple-700 to-purple-900 hover:from-purple-800 hover:to-purple-950 relative overflow-hidden" 
                disabled={isLoading}
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
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin relative z-10" />
                    <span className="relative z-10">Creating account...</span>
                  </>
                ) : (
                  <span className="relative z-10">Register</span>
                )}
              </Button>
            </motion.div>
            <div className="text-center text-sm text-gray-400">
              Already have an account?{" "}
              <Link href="/auth/login" className="text-purple-400 hover:text-purple-300 font-medium">
                Login
              </Link>
            </div>
          </CardFooter>
        </form>
        </Card>
      </motion.div>
    </div>
  )
}
