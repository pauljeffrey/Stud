import { NextResponse } from "next/server"

const pythonBackendUrl = process.env.PYTHON_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export async function POST(request: Request) {
  try {
    const { email, password } = await request.json()

    if (!email || !password) {
      return NextResponse.json({ success: false, message: "Email and password are required" }, { status: 400 })
    }

    // Call Python backend authentication endpoint
    const response = await fetch(`${pythonBackendUrl}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(
        { success: false, message: data.detail || "Login failed" },
        { status: response.status }
      )
    }

    // Store token in response headers for client to read
    const responseHeaders = new Headers()
    if (data.token) {
      responseHeaders.set("X-Auth-Token", data.token)
    }
    if (data.session_token) {
      responseHeaders.set("X-Session-Token", data.session_token)
    }

    return NextResponse.json(
      {
        success: true,
        user: data.user,
        token: data.token,
        session_token: data.session_token,
      },
      { headers: responseHeaders }
    )
  } catch (error) {
    console.error("Login error:", error)
    return NextResponse.json(
      { success: false, message: error instanceof Error ? error.message : "Server error" },
      { status: 500 }
    )
  }
}
