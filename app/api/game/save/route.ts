import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    const pythonBackendUrl = process.env.PYTHON_BACKEND_URL || "http://localhost:8000"

    const response = await fetch(`${pythonBackendUrl}/api/game/save`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      throw new Error("Failed to save game")
    }

    const result = await response.json()
    return NextResponse.json(result)
  } catch (error) {
    console.error("Save game error:", error)
    return NextResponse.json({ error: "Failed to save game" }, { status: 500 })
  }
}
