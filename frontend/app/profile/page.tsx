"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Input } from "@/app/components/ui/input"
import { Label } from "@/app/components/ui/label"
import { Textarea } from "@/app/components/ui/textarea"
import { Button } from "@/app/components/ui/button"
import { Badge } from "@/app/components/ui/badge"
import { Skeleton } from "@/app/components/ui/skeleton"
import { Avatar, AvatarFallback, AvatarImage } from "@/app/components/ui/avatar"
import { apiFetch } from "@/app/lib/auth"
import {
  User,
  Mail,
  Calendar,
  Briefcase,
  Edit,
  Save,
  X,
  Camera,
  Shield,
  Bell,
  Globe,
  ArrowLeft,
} from "lucide-react"
import Link from "next/link"
import { useToast } from "@/app/components/ui/use-toast"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/app/components/ui/select"

interface UserProfile {
  id: string
  name: string
  email: string
  profession: string
  age: number
  avatar_url?: string
  bio: string
  created_at?: string
  level: number
  xp: number
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isEditing, setIsEditing] = useState(false)
  const [editedProfile, setEditedProfile] = useState<Partial<UserProfile>>({})
  const { toast } = useToast()

  useEffect(() => {
    loadProfile()
  }, [])

  const loadProfile = async () => {
    try {
      setIsLoading(true)
      const [meResponse, statsResponse] = await Promise.all([
        apiFetch("/api/auth/me"),
        apiFetch("/api/user/stats"),
      ])

      if (meResponse.ok) {
        const data = await meResponse.json()
        const stats = statsResponse.ok ? await statsResponse.json().catch(() => null) : null
        const merged: UserProfile = {
          ...data.user,
          level: stats?.stats?.currentLevel ?? 1,
          xp: stats?.stats?.totalXP ?? 0,
        }
        setProfile(merged)
        setEditedProfile(merged)
      } else {
        // Mock data
        setProfile({
          id: "user123",
          name: "Dr. Smith",
          email: "dr.smith@example.com",
          profession: "Cardiologist",
          age: 35,
          bio: "Passionate about medical education and patient care.",
          created_at: "2024-01-01",
          level: 5,
          xp: 2450,
        })
        setEditedProfile({
          id: "user123",
          name: "Dr. Smith",
          email: "dr.smith@example.com",
          profession: "Cardiologist",
          age: 35,
          bio: "Passionate about medical education and patient care.",
        })
      }
    } catch (error) {
      console.error("Failed to load profile:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      const response = await apiFetch("/api/user/profile", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(editedProfile),
      })

      if (response.ok) {
        const data = await response.json()
        setProfile(data.user)
        setIsEditing(false)
        toast({
          title: "Profile Updated",
          description: "Your profile has been updated successfully.",
        })
      } else {
        throw new Error("Failed to update profile")
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update profile. Please try again.",
        variant: "destructive",
      })
    }
  }

  const handleCancel = () => {
    setEditedProfile(profile || {})
    setIsEditing(false)
  }

  if (isLoading || !profile) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-purple-900 via-purple-800 to-purple-900 p-4">
        <div className="max-w-4xl mx-auto space-y-6">
          <Skeleton className="h-16 w-full bg-purple-800/50" />
          <Skeleton className="h-64 w-full bg-purple-800/50" />
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-900 via-purple-800 to-purple-900 p-4 md:p-6 lg:p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between animate-in fade-in slide-in-from-top-4 duration-700">
          <Link href="/dashboard">
            <Button variant="ghost" className="text-white hover:bg-purple-800">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          </Link>
          {!isEditing ? (
            <Button onClick={() => setIsEditing(true)} className="bg-purple-600 hover:bg-purple-700">
              <Edit className="h-4 w-4 mr-2" />
              Edit Profile
            </Button>
          ) : (
            <div className="flex gap-2">
              <Button onClick={handleCancel} variant="outline" className="border-purple-400 text-white hover:bg-purple-800">
                <X className="h-4 w-4 mr-2" />
                Cancel
              </Button>
              <Button onClick={handleSave} className="bg-purple-600 hover:bg-purple-700">
                <Save className="h-4 w-4 mr-2" />
                Save
              </Button>
            </div>
          )}
        </div>

        {/* Profile Card */}
        <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white animate-in fade-in duration-500">
          <CardContent className="p-6 md:p-8">
            <div className="flex flex-col md:flex-row items-start md:items-center gap-6">
              <div className="relative group">
                <Avatar className="h-32 w-32 border-4 border-purple-500">
                  <AvatarImage src={profile.avatar_url} />
                  <AvatarFallback className="bg-purple-600 text-2xl">
                    {profile.name.charAt(0)}
                  </AvatarFallback>
                </Avatar>
                {isEditing && (
                  <Button
                    size="sm"
                    className="absolute bottom-0 right-0 rounded-full bg-purple-600 hover:bg-purple-700 border-2 border-purple-900"
                  >
                    <Camera className="h-4 w-4" />
                  </Button>
                )}
              </div>
              <div className="flex-1">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-4">
                  <div>
                    {isEditing ? (
                      <Input
                        value={editedProfile.name || ""}
                        onChange={(e) => setEditedProfile({ ...editedProfile, name: e.target.value })}
                        className="text-3xl font-bold bg-purple-800 border-purple-600 text-white mb-2"
                      />
                    ) : (
                      <h1 className="text-3xl md:text-4xl font-bold mb-2">{profile.name}</h1>
                    )}
                    {isEditing ? (
                      <Select
                        value={editedProfile.profession || ""}
                        onValueChange={(value) => setEditedProfile({ ...editedProfile, profession: value })}
                      >
                        <SelectTrigger className="bg-purple-800 border-purple-600 text-white w-full md:w-64">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="General Practitioner">General Practitioner</SelectItem>
                          <SelectItem value="Cardiologist">Cardiologist</SelectItem>
                          <SelectItem value="Surgeon">Surgeon</SelectItem>
                          <SelectItem value="Pediatrician">Pediatrician</SelectItem>
                          <SelectItem value="Emergency Medicine">Emergency Medicine</SelectItem>
                        </SelectContent>
                      </Select>
                    ) : (
                      <Badge className="bg-purple-600 text-white text-lg px-3 py-1">{profile.profession}</Badge>
                    )}
                  </div>
                  <div className="text-right">
                    <Badge className="bg-gradient-to-r from-purple-600 to-pink-600 text-white text-lg px-4 py-2 mb-2">
                      Level {profile.level ?? 1}
                    </Badge>
                    <p className="text-sm text-purple-200">{(profile.xp ?? 0).toLocaleString()} XP</p>
                  </div>
                </div>
                {isEditing ? (
                  <Textarea
                    value={editedProfile.bio || ""}
                    onChange={(e) => setEditedProfile({ ...editedProfile, bio: e.target.value })}
                    placeholder="Tell us about yourself..."
                    className="bg-purple-800 border-purple-600 text-white placeholder-purple-300 min-h-[100px]"
                  />
                ) : (
                  <p className="text-purple-200 text-lg">{profile.bio || "No bio yet."}</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Profile Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Personal Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-purple-200">Email</Label>
                {isEditing ? (
                  <Input
                    type="email"
                    value={editedProfile.email || ""}
                    onChange={(e) => setEditedProfile({ ...editedProfile, email: e.target.value })}
                    className="bg-purple-800 border-purple-600 text-white mt-1"
                  />
                ) : (
                  <div className="flex items-center gap-2 mt-1">
                    <Mail className="h-4 w-4 text-purple-300" />
                    <p>{profile.email}</p>
                  </div>
                )}
              </div>
              <div>
                <Label className="text-purple-200">Age</Label>
                {isEditing ? (
                  <Input
                    type="number"
                    value={editedProfile.age || ""}
                    onChange={(e) => setEditedProfile({ ...editedProfile, age: parseInt(e.target.value) })}
                    className="bg-purple-800 border-purple-600 text-white mt-1"
                  />
                ) : (
                  <div className="flex items-center gap-2 mt-1">
                    <Calendar className="h-4 w-4 text-purple-300" />
                    <p>{profile.age} years old</p>
                  </div>
                )}
              </div>
              <div>
                <Label className="text-purple-200">Member Since</Label>
                <div className="flex items-center gap-2 mt-1">
                  <Calendar className="h-4 w-4 text-purple-300" />
                  <p>{profile.created_at ? new Date(profile.created_at).toLocaleDateString() : "—"}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/10 backdrop-blur-sm border-purple-400 text-white">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Account Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button variant="outline" className="w-full border-purple-400 text-white hover:bg-purple-800 justify-start">
                <Bell className="h-4 w-4 mr-2" />
                Notification Settings
              </Button>
              <Button variant="outline" className="w-full border-purple-400 text-white hover:bg-purple-800 justify-start">
                <Globe className="h-4 w-4 mr-2" />
                Privacy Settings
              </Button>
              <Button variant="outline" className="w-full border-purple-400 text-white hover:bg-purple-800 justify-start">
                <Shield className="h-4 w-4 mr-2" />
                Change Password
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}




