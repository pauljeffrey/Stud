import { NextResponse } from "next/server"
import { PYTHON_BACKEND_URL } from "@/app/lib/proxy"

const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10MB
const MAX_IMAGE_SIZE = 5 * 1024 * 1024 // 5MB

export const maxDuration = 300

export async function POST(req: Request) {
  try {
    const formData = await req.formData()
    const file = formData.get("file") as File | null
    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 })
    }
    const maxSize = file.type.startsWith("image/") ? MAX_IMAGE_SIZE : MAX_FILE_SIZE
    if (file.size > maxSize) {
      const fileMB = (file.size / 1048576).toFixed(2)
      const maxMB = (maxSize / 1048576).toFixed(0)
      return NextResponse.json(
        { error: `File size (${fileMB}MB) exceeds maximum (${maxMB}MB)` },
        { status: 400 }
      )
    }

    const headers: Record<string, string> = {}
    const auth = req.headers.get("authorization")
    if (auth) headers.Authorization = auth

    const upstream = await fetch(`${PYTHON_BACKEND_URL}/api/learning/upload`, {
      method: "POST",
      headers,
      body: formData,
    })
    const data = await upstream.json().catch(() => ({}))
    return NextResponse.json(data, { status: upstream.status })
  } catch (error: any) {
    console.error("Upload error:", error)
    return NextResponse.json(
      { error: error?.message || "Failed to upload document" },
      { status: 500 }
    )
  }
}
