import { proxy } from "@/app/lib/proxy"

export const POST = async (
  req: Request,
  context: { params: Promise<{ documentId: string }> }
) => {
  const { documentId } = await context.params
  return proxy(req, `/api/learning/documents/${documentId}/suggest-global`)
}
