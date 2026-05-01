import { proxy } from "@/app/lib/proxy"

export const GET = (req: Request) => proxy(req, "/api/game/settings")
