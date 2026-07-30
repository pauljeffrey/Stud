import { proxy } from "@/app/lib/proxy"

export const maxDuration = 300

export const POST = (req: Request) =>
  proxy(req, "/api/game/npc-chat", { stream: true })
