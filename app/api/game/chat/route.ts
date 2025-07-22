import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // Forward request to Python backend
    const pythonBackendUrl = process.env.PYTHON_BACKEND_URL || "http://localhost:8000"

    const response = await fetch(`${pythonBackendUrl}/api/game/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      throw new Error("Failed to get response from AI service")
    }

    // Return the streaming response
    return new Response(response.body, {
      headers: {
        "Content-Type": "text/plain",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    })
  } catch (error) {
    console.error("Game chat error:", error)
    return NextResponse.json({ error: "Failed to process game chat" }, { status: 500 })
  }
}
