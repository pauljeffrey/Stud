import { proxy } from "@/app/lib/proxy"

export const GET = async (
  req: Request,
  context: { params: Promise<{ gameId: string }> }
) => {
  const { gameId } = await context.params
  return proxy(req, `/api/game/${gameId}`)
}
