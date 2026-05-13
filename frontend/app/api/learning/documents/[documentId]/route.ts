import type { NextRequest } from "next/server"
import { proxy } from "@/app/lib/proxy"

export async function DELETE(
  request: NextRequest,
  context: { params: Promise<{ documentId: string }> }
) {
  const { documentId } = await context.params
  return proxy(request, `/api/learning/documents/${documentId}`, { method: "DELETE" })
}
