import { NextResponse } from "next/server"
import { PYTHON_BACKEND_URL } from "@/app/lib/proxy"

export async function POST(request: Request) {
  const auth = request.headers.get("authorization")
  if (!auth) {
    return NextResponse.json({ success: false, message: "Unauthorized" }, { status: 401 })
  }
  const res = await fetch(`${PYTHON_BACKEND_URL}/api/auth/refresh`, {
    method: "POST",
    headers: { Authorization: auth },
  })
  const data = await res.json().catch(() => ({}))
  return NextResponse.json(data, { status: res.status })
}
