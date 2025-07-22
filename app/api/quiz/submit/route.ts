import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    const pythonBackendUrl = process.env.PYTHON_BACKEND_URL || "http://localhost:8000"

    const response = await fetch(`${pythonBackendUrl}/api/quiz/submit`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      throw new Error("Failed to submit quiz")
    }

    const result = await response.json()
    return NextResponse.json(result)
  } catch (error) {
    console.error("Quiz submission error:", error)
    return NextResponse.json({ error: "Failed to submit quiz" }, { status: 500 })
  }
}
