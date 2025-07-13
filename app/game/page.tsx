"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Loader2, Send, Clock, AlertCircle, Volume2, VolumeX, Users, Save } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import Image from "next/image"

export default function GamePage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "system",
      content:
        "Welcome to MediQuest! You are a cardiologist at Central Hospital. A 58-year-old patient has been admitted with chest pain that started 2 hours ago. The pain radiates to the left arm and is accompanied by shortness of breath and nausea. What would you like to do?",
    },
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [timeRemaining, setTimeRemaining] = useState(600) // 10 minutes in seconds
  const [isMuted, setIsMuted] = useState(true)
  const [showDialog, setShowDialog] = useState(false)
  const [dialogContent, setDialogContent] = useState({ title: "", content: "", image: "" })
  const [currentCase, setCurrentCase] = useState("case1")
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { toast } = useToast()
  const audioRef = useRef<HTMLAudioElement | null>(null)

  // Initialize audio
  useEffect(() => {
    audioRef.current = new Audio("/game-background.mp3")
    audioRef.current.loop = true
    return () => {
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current.src = ""
      }
    }
  }, [])

  // Handle audio mute/unmute
  useEffect(() => {
    if (audioRef.current) {
      if (!isMuted) {
        audioRef.current.play().catch((e) => console.error("Audio play failed:", e))
      } else {
        audioRef.current.pause()
      }
    }
  }, [isMuted])

  // Timer effect
  useEffect(() => {
    const timer = setInterval(() => {
      setTimeRemaining((prev) => Math.max(0, prev - 1))
    }, 1000)

    return () => clearInterval(timer)
  }, [])

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Format time remaining as MM:SS
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    // Add user message
    const userMessage = { role: "user", content: input }
    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      // In a production app, this would call the FastAPI backend
      // const response = await fetch('http://your-fastapi-url/api/generate-response', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({
      //     prompt: input,
      //     gameState: {
      //       userId: 'user123', // This would come from authentication
      //       caseId: currentCase,
      //       messages: messages,
      //       patientData: currentCase === 'case1' ? case1PatientData : case2PatientData,
      //       timeRemaining: timeRemaining
      //     }
      //   }),
      // });
      // const data = await response.json();

      // For now, simulate the response
      await new Promise((resolve) => setTimeout(resolve, 1500))

      // Simulate AI response based on keywords
      let responseContent = ""
      const lowerInput = input.toLowerCase()

      if (currentCase === "case1") {
        if (lowerInput.includes("ecg") || lowerInput.includes("ekg")) {
          responseContent =
            "The ECG shows ST-segment elevation in leads II, III, and aVF, suggesting an inferior wall myocardial infarction. What treatment would you like to administer?"

          // Show ECG image in dialog
          setDialogContent({
            title: "ECG Results",
            content: "The ECG shows ST-segment elevation in leads II, III, and aVF.",
            image: "/placeholder.svg?height=300&width=500",
          })
          setShowDialog(true)
        } else if (lowerInput.includes("blood") || lowerInput.includes("test")) {
          responseContent =
            "Blood tests reveal elevated troponin levels (2.3 ng/mL) and elevated CK-MB. These findings support the diagnosis of acute myocardial infarction."
        } else if (
          lowerInput.includes("treat") ||
          lowerInput.includes("aspirin") ||
          lowerInput.includes("medication")
        ) {
          responseContent =
            "You administer aspirin 325mg, nitroglycerin, and morphine for pain. The patient needs immediate intervention. Would you like to consult with the interventional cardiologist for a potential primary PCI?"
        } else if (
          lowerInput.includes("consult") ||
          lowerInput.includes("pci") ||
          lowerInput.includes("intervention")
        ) {
          responseContent =
            "The interventional cardiologist agrees with your assessment. The patient is rushed to the cath lab for primary PCI. The procedure successfully opens the occluded right coronary artery and a stent is placed. The patient's symptoms improve dramatically."

          // Trigger success dialog
          setTimeout(() => {
            setDialogContent({
              title: "Case Completed Successfully!",
              content:
                "You've successfully diagnosed and treated an acute inferior wall myocardial infarction. The patient is stable and will be monitored in the CCU.",
              image: "/placeholder.svg?height=300&width=500",
            })
            setShowDialog(true)

            // Move to next case
            setTimeout(() => {
              setCurrentCase("case2")
              setMessages([
                {
                  role: "system",
                  content:
                    'New case: A 42-year-old female presents with sudden onset of severe headache described as "the worst headache of my life." She also reports neck stiffness and vomiting. Her BP is 170/95. What would you like to do?',
                },
              ])
            }, 3000)
          }, 2000)
        } else {
          responseContent =
            "The patient's condition appears serious. His vital signs are: BP 150/90, HR 95, RR 22, O2 sat 94% on room air. What tests would you like to order?"
        }
      } else if (currentCase === "case2") {
        if (lowerInput.includes("ct") || lowerInput.includes("scan")) {
          responseContent =
            "The CT scan reveals subarachnoid hemorrhage, likely due to a ruptured aneurysm. This is a medical emergency requiring immediate neurosurgical consultation."

          // Show CT image in dialog
          setDialogContent({
            title: "CT Scan Results",
            content: "The CT scan shows blood in the subarachnoid space, consistent with SAH.",
            image: "/placeholder.svg?height=300&width=500",
          })
          setShowDialog(true)
        } else {
          responseContent =
            "The patient appears to be in severe distress. Given her symptoms, what imaging studies would you like to order?"
        }
      }

      // Add system response
      setMessages((prev) => [...prev, { role: "system", content: responseContent }])
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to get a response. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  function saveGameState() {
    // In a production app, this would call the FastAPI backend to save the game state
    // fetch('http://your-fastapi-url/api/save-checkpoint', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({
    //     userId: 'user123', // This would come from authentication
    //     caseId: currentCase,
    //     messages: messages,
    //     patientData: currentCase === 'case1' ? case1PatientData : case2PatientData,
    //     timeRemaining: timeRemaining
    //   }),
    // });

    toast({
      title: "Game Saved",
      description: "Your progress has been saved successfully.",
    })
  }

  // Patient data for each case
  const case1PatientData = {
    demographics: {
      age: 58,
      gender: "male",
    },
    vitalSigns: {
      bloodPressure: "150/90 mmHg",
      heartRate: 95,
      respiratoryRate: 22,
      oxygenSaturation: 94,
      temperature: 37.1,
    },
    chiefComplaint: "Chest pain radiating to left arm, shortness of breath, nausea",
    medicalHistory: ["Hypertension", "Hyperlipidemia", "Type 2 Diabetes", "Smoker (1 pack/day for 30 years)"],
  }

  const case2PatientData = {
    demographics: {
      age: 42,
      gender: "female",
    },
    vitalSigns: {
      bloodPressure: "170/95 mmHg",
      heartRate: 88,
      respiratoryRate: 18,
      oxygenSaturation: 98,
      temperature: 37.0,
    },
    chiefComplaint: '"Worst headache of my life", neck stiffness, vomiting',
    medicalHistory: ["No significant past medical history", "No known allergies", "No current medications"],
  }

  return (
    <div className="h-screen bg-gradient-to-b from-purple-900 to-purple-700 flex flex-col">
      {/* Game header */}
      <div className="bg-purple-800 p-3 text-white flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <Badge variant="outline" className="bg-purple-700 text-white border-purple-500">
            Case: {currentCase === "case1" ? "Cardiac Emergency" : "Neurological Emergency"}
          </Badge>
          <div className="flex items-center">
            <Clock className="mr-2 h-4 w-4" />
            <span>{formatTime(timeRemaining)}</span>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <Button
            variant="ghost"
            size="sm"
            className="text-white hover:bg-purple-700"
            onClick={() => setIsMuted(!isMuted)}
          >
            {isMuted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
          </Button>
          <Button variant="ghost" size="sm" className="text-white hover:bg-purple-700" onClick={saveGameState}>
            <Save className="h-5 w-5" />
          </Button>
          <Button variant="ghost" size="sm" className="text-white hover:bg-purple-700">
            <Users className="h-5 w-5" />
          </Button>
        </div>
      </div>

      <div className="flex-1 flex flex-col md:flex-row p-4 gap-4">
        {/* Game master instructions */}
        <div className="w-full md:w-1/2 flex flex-col">
          <Card className="flex-1 bg-white/10 backdrop-blur-sm border-purple-400">
            <CardHeader className="pb-2">
              <CardTitle className="text-white text-lg flex items-center">
                <AlertCircle className="h-5 w-5 mr-2 text-yellow-400" />
                Game Master
              </CardTitle>
            </CardHeader>
            <CardContent className="overflow-y-auto h-[calc(100vh-220px)]">
              <div className="space-y-4">
                {messages.map((message, index) => (
                  <div key={index} className={`${message.role === "system" ? "block" : "hidden"}`}>
                    <div className="p-3 rounded-lg bg-gray-800 text-white">{message.content}</div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* User input and game interface */}
        <div className="w-full md:w-1/2 flex flex-col">
          <Tabs defaultValue="actions" className="flex-1 flex flex-col">
            <TabsList className="bg-purple-800">
              <TabsTrigger value="actions" className="data-[state=active]:bg-purple-600">
                Actions
              </TabsTrigger>
              <TabsTrigger value="patient" className="data-[state=active]:bg-purple-600">
                Patient Data
              </TabsTrigger>
              <TabsTrigger value="team" className="data-[state=active]:bg-purple-600">
                Team
              </TabsTrigger>
            </TabsList>

            <TabsContent value="actions" className="flex-1 flex flex-col mt-0 p-0">
              <Card className="flex-1 bg-white/10 backdrop-blur-sm border-purple-400">
                <CardContent className="p-4 overflow-y-auto h-[calc(100vh-280px)]">
                  <div className="space-y-4">
                    {messages.map((message, index) => (
                      <div key={index} className={`${message.role === "user" ? "block" : "hidden"}`}>
                        <div className="p-3 rounded-lg bg-purple-600 text-white ml-auto max-w-[80%]">
                          {message.content}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
                <form onSubmit={handleSubmit} className="p-4 border-t border-purple-400">
                  <div className="flex gap-2">
                    <Input
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      placeholder="What would you like to do?"
                      className="bg-white/20 border-purple-400 text-white placeholder:text-gray-300"
                      disabled={isLoading}
                    />
                    <Button
                      type="submit"
                      disabled={isLoading || !input.trim()}
                      className="bg-purple-500 hover:bg-purple-600"
                    >
                      {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
                    </Button>
                  </div>
                </form>
              </Card>
            </TabsContent>

            <TabsContent value="patient" className="flex-1 mt-0">
              <Card className="h-full bg-white/10 backdrop-blur-sm border-purple-400">
                <CardHeader>
                  <CardTitle className="text-white">Patient Information</CardTitle>
                </CardHeader>
                <CardContent className="text-white">
                  {currentCase === "case1" ? (
                    <div className="space-y-4">
                      <div>
                        <h3 className="font-semibold">Demographics</h3>
                        <p>58-year-old male</p>
                      </div>
                      <div>
                        <h3 className="font-semibold">Vital Signs</h3>
                        <ul className="list-disc list-inside">
                          <li>BP: 150/90 mmHg</li>
                          <li>HR: 95 bpm</li>
                          <li>RR: 22/min</li>
                          <li>O2 Sat: 94% on room air</li>
                          <li>Temp: 37.1°C</li>
                        </ul>
                      </div>
                      <div>
                        <h3 className="font-semibold">Chief Complaint</h3>
                        <p>Chest pain radiating to left arm, shortness of breath, nausea</p>
                      </div>
                      <div>
                        <h3 className="font-semibold">Medical History</h3>
                        <ul className="list-disc list-inside">
                          <li>Hypertension</li>
                          <li>Hyperlipidemia</li>
                          <li>Type 2 Diabetes</li>
                          <li>Smoker (1 pack/day for 30 years)</li>
                        </ul>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div>
                        <h3 className="font-semibold">Demographics</h3>
                        <p>42-year-old female</p>
                      </div>
                      <div>
                        <h3 className="font-semibold">Vital Signs</h3>
                        <ul className="list-disc list-inside">
                          <li>BP: 170/95 mmHg</li>
                          <li>HR: 88 bpm</li>
                          <li>RR: 18/min</li>
                          <li>O2 Sat: 98% on room air</li>
                          <li>Temp: 37.0°C</li>
                        </ul>
                      </div>
                      <div>
                        <h3 className="font-semibold">Chief Complaint</h3>
                        <p>"Worst headache of my life", neck stiffness, vomiting</p>
                      </div>
                      <div>
                        <h3 className="font-semibold">Medical History</h3>
                        <ul className="list-disc list-inside">
                          <li>No significant past medical history</li>
                          <li>No known allergies</li>
                          <li>No current medications</li>
                        </ul>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="team" className="flex-1 mt-0">
              <Card className="h-full bg-white/10 backdrop-blur-sm border-purple-400">
                <CardHeader>
                  <CardTitle className="text-white">Medical Team</CardTitle>
                </CardHeader>
                <CardContent className="text-white">
                  <div className="space-y-4">
                    <div className="flex items-center space-x-4 p-3 bg-purple-800 rounded-lg">
                      <div className="h-12 w-12 rounded-full bg-purple-600 flex items-center justify-center text-xl font-bold">
                        {currentCase === "case1" ? "C" : "N"}
                      </div>
                      <div>
                        <h3 className="font-semibold">
                          {currentCase === "case1" ? "Dr. Carter (Cardiologist)" : "Dr. Neuro (Neurologist)"}
                        </h3>
                        <p className="text-sm">Available for consultation</p>
                      </div>
                      <Button size="sm" className="ml-auto bg-purple-500 hover:bg-purple-600">
                        Consult
                      </Button>
                    </div>

                    <div className="flex items-center space-x-4 p-3 bg-purple-800 rounded-lg">
                      <div className="h-12 w-12 rounded-full bg-purple-600 flex items-center justify-center text-xl font-bold">
                        N
                      </div>
                      <div>
                        <h3 className="font-semibold">Nurse Johnson</h3>
                        <p className="text-sm">Can assist with procedures</p>
                      </div>
                      <Button size="sm" className="ml-auto bg-purple-500 hover:bg-purple-600">
                        Request
                      </Button>
                    </div>

                    <div className="flex items-center space-x-4 p-3 bg-purple-800 rounded-lg">
                      <div className="h-12 w-12 rounded-full bg-purple-600 flex items-center justify-center text-xl font-bold">
                        L
                      </div>
                      <div>
                        <h3 className="font-semibold">Lab Technician</h3>
                        <p className="text-sm">Can expedite test results</p>
                      </div>
                      <Button size="sm" className="ml-auto bg-purple-500 hover:bg-purple-600">
                        Contact
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* Dialog for displaying images and important information */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="bg-purple-900 text-white border-purple-500">
          <DialogHeader>
            <DialogTitle>{dialogContent.title}</DialogTitle>
            <DialogDescription className="text-gray-300">{dialogContent.content}</DialogDescription>
          </DialogHeader>
          {dialogContent.image && (
            <div className="flex justify-center my-4">
              <Image
                src={dialogContent.image || "/placeholder.svg"}
                alt="Medical image"
                width={500}
                height={300}
                className="rounded-md"
              />
            </div>
          )}
          <Button onClick={() => setShowDialog(false)} className="bg-purple-600 hover:bg-purple-700 mt-2">
            Close
          </Button>
        </DialogContent>
      </Dialog>
    </div>
  )
}

interface Message {
  role: "user" | "system"
  content: string
}

