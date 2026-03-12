// User types
export interface User {
    id: string
    name: string
    email: string
    profession: string
    age?: number
  }
  
  // Game types
  export interface GameState {
    userId: string
    caseId: string
    messages: Message[]
    patientData: PatientData
    checkpoint?: string
    timeRemaining: number
  }
  
  export interface Message {
    role: "user" | "system"
    content: string
    timestamp?: string
  }
  
  export interface PatientData {
    demographics: {
      age: number
      gender: string
    }
    vitalSigns: {
      bloodPressure: string
      heartRate: number
      respiratoryRate: number
      oxygenSaturation: number
      temperature: number
    }
    chiefComplaint: string
    medicalHistory: string[]
    medications?: string[]
    allergies?: string[]
    labResults?: Record<string, any>
    imagingResults?: Record<string, any>
  }
  
  // AI Service types
  export interface AIRequest {
    prompt: string
    gameState: GameState
    context?: string[]
  }
  
  export interface AIResponse {
    text: string
    image?: string
    actions?: string[]
    patientUpdate?: Partial<PatientData>
  }
