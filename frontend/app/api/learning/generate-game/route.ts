import { NextResponse } from "next/server"
import { PYTHON_BACKEND_URL } from "@/app/lib/proxy"

export const maxDuration = 300

export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => ({}))
    const documentId = body?.document_id
    if (!documentId) {
      return NextResponse.json({ error: "document_id required" }, { status: 400 })
    }

    const formData = new FormData()
    formData.append("document_id", documentId)

    const headers: Record<string, string> = {}
    const auth = req.headers.get("authorization")
    if (auth) headers.Authorization = auth

    const response = await fetch(
      `${PYTHON_BACKEND_URL}/api/learning/generate-game-from-document`,
      { method: "POST", headers, body: formData },
    )
    const data = await response.json().catch(() => ({}))
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("Generate game error:", error)
    return NextResponse.json({ error: "Failed to generate game" }, { status: 500 })
  }
}
