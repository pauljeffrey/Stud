import { NextResponse } from "next/server"
import { PYTHON_BACKEND_URL } from "@/app/lib/proxy"
import { sessionCookieSuffix } from "@/app/lib/session-cookie"

const SESSION_COOKIE_MAX_AGE = 7 * 24 * 60 * 60 // 7 days
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export async function POST(request: Request) {
  try {
    const userData = await request.json()

    for (const field of ["name", "email", "password"] as const) {
      if (!userData[field]) {
        return NextResponse.json({ success: false, message: `${field} is required` }, { status: 400 })
      }
    }
    if (!userData.user_type || !["professional", "student"].includes(userData.user_type)) {
      return NextResponse.json(
        { success: false, message: "Please select whether you are a Professional or Student" },
        { status: 400 }
      )
    }
    const professionValue = userData.profession === "other" ? userData.profession_other : userData.profession
    if (!professionValue || (typeof professionValue === "string" && !professionValue.trim())) {
      return NextResponse.json(
        { success: false, message: "Please select or enter your profession/field" },
        { status: 400 }
      )
    }
    if (!EMAIL_REGEX.test(userData.email)) {
      return NextResponse.json({ success: false, message: "Invalid email format" }, { status: 400 })
    }
    if (userData.password.length < 8) {
      return NextResponse.json(
        { success: false, message: "Password must be at least 8 characters long" },
        { status: 400 }
      )
    }

    const backendPayload = {
      email: userData.email,
      password: userData.password,
      name: userData.name,
      user_type: userData.user_type,
      profession: userData.profession,
      profession_other: userData.profession_other || undefined,
      age: userData.age ? parseInt(userData.age, 10) : undefined,
    }

    const response = await fetch(`${PYTHON_BACKEND_URL}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(backendPayload),
    })
    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      const message = typeof data.detail === "string" ? data.detail : data.message || "Registration failed"
      return NextResponse.json({ success: false, message }, { status: response.status })
    }

    const headers = new Headers()
    if (data.session_token) {
      headers.set(
        "Set-Cookie",
        `session_token=${data.session_token}; ${sessionCookieSuffix(SESSION_COOKIE_MAX_AGE)}`
      )
    }
    return NextResponse.json(
      {
        success: true,
        message: data.message || "User registered successfully",
        user: data.user,
        token: data.token,
        session_token: data.session_token,
      },
      { headers }
    )
  } catch (error) {
    console.error("Registration error:", error)
    return NextResponse.json(
      { success: false, message: error instanceof Error ? error.message : "Server error" },
      { status: 500 }
    )
  }
}
