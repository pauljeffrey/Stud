import { proxy } from "@/app/lib/proxy"

export const GET = (req: Request, { params }: { params: { gameId: string } }) =>
  proxy(req, `/api/game/${params.gameId}`)
