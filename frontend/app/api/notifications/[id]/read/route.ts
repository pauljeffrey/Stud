import { proxy } from "@/app/lib/proxy"

export const POST = async (
  req: Request,
  context: { params: Promise<{ id: string }> }
) => {
  const { id } = await context.params
  return proxy(req, `/api/notifications/${id}/read`)
}
