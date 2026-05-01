import { NextResponse } from "next/server"

/** Logout proxy. Best-effort: never block the client on backend failure. */
export async function POST(request: Request) {
  const auth = request.headers.get("authorization") || ""
  const pythonBackendUrl = process.env.PYTHON_BACKEND_URL || "http://localhost:8000"
  try {
    if (auth) {
      await fetch(`${pythonBackendUrl}/api/auth/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: auth },
      }).catch(() => null)
    }
  } catch {
    /* ignore */
  }
  const headers = new Headers()
  headers.append(
    "Set-Cookie",
    "session_token=; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=0"
  )
  return NextResponse.json({ success: true }, { headers })
}
