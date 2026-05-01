import { NextResponse } from "next/server"

/**
 * Login API Route Handler
 * Proxies authentication requests to the Python backend
 * This route is automatically deployed as a serverless function on Vercel
 */
export async function POST(request: Request) {
  try {
    const { email, password } = await request.json()

    if (!email || !password) {
      return NextResponse.json(
        { success: false, message: "Email and password are required" },
        { status: 400 }
      )
    }

    // Call Python backend authentication endpoint
    const pythonBackendUrl = process.env.PYTHON_BACKEND_URL || "http://localhost:8000"

    const response = await fetch(`${pythonBackendUrl}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      const message = typeof errorData.detail === "string"
        ? errorData.detail
        : Array.isArray(errorData.detail)
          ? errorData.detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(", ") || "Invalid credentials"
          : errorData.message || "Invalid credentials"
      return NextResponse.json(
        { success: false, message },
        { status: response.status }
      )
    }

    const data = await response.json()

    // Set HTTP-only cookie for session token if provided
    const responseHeaders = new Headers()
    if (data.session_token) {
      responseHeaders.set(
        "Set-Cookie",
        `session_token=${data.session_token}; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=${7 * 24 * 60 * 60}` // 7 days
      )
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
      { success: false, message: "Server error. Please try again later." },
      { status: 500 }
    )
  }
}
