import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()

    const pythonBackendUrl = process.env.PYTHON_BACKEND_URL || "http://localhost:8000"

    const response = await fetch(`${pythonBackendUrl}/api/quiz/generate`, {
      method: "POST",
      body: formData,
    })

    if (!response.ok) {
      throw new Error("Failed to generate quiz")
    }

    const result = await response.json()
    return NextResponse.json(result)
  } catch (error) {
    console.error("Quiz generation error:", error)
    return NextResponse.json({ error: "Failed to generate quiz" }, { status: 500 })
  }
}
