import { proxy } from "@/app/lib/proxy"

export const DELETE = async (
  req: Request,
  context: { params: Promise<{ checkpointId: string }> }
) => {
  const { checkpointId } = await context.params
  return proxy(req, `/api/game/checkpoints/${checkpointId}`, { method: "DELETE" })
}
