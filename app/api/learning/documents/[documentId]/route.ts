import { type NextRequest, NextResponse } from "next/server"

export async function DELETE(request: NextRequest, { params }: { params: { documentId: string } }) {
  try {
    const pythonBackendUrl = process.env.PYTHON_BACKEND_URL || "http://localhost:8000"

    const response = await fetch(`${pythonBackendUrl}/api/learning/documents/${params.documentId}`, {
      method: "DELETE",
    })

    if (!response.ok) {
      throw new Error("Failed to delete document")
    }

    const result = await response.json()
    return NextResponse.json(result)
  } catch (error) {
    console.error("Delete document error:", error)
    return NextResponse.json({ error: "Failed to delete document" }, { status: 500 })
  }
}
