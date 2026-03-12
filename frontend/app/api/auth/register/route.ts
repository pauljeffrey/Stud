import { NextResponse } from "next/server"

const pythonBackendUrl = process.env.PYTHON_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export async function POST(request: Request) {
  try {
    const userData = await request.json()

    // Validate required fields
    const requiredFields = ["name", "email", "password"]
    for (const field of requiredFields) {
      if (!userData[field]) {
        return NextResponse.json({ success: false, message: `${field} is required` }, { status: 400 })
      }
    }

    // Call Python backend registration endpoint
    const response = await fetch(`${pythonBackendUrl}/api/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: userData.email,
        password: userData.password,
        name: userData.name,
        profession: userData.profession || null,
        age: userData.age ? parseInt(userData.age) : null,
      }),
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(
        { success: false, message: data.detail || "Registration failed" },
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
        message: data.message || "User registered successfully",
        user: data.user,
        token: data.token,
        session_token: data.session_token,
      },
      { headers: responseHeaders }
    )
  } catch (error) {
    console.error("Registration error:", error)
    return NextResponse.json(
      { success: false, message: error instanceof Error ? error.message : "Server error" },
      { status: 500 }
    )
  }
}
