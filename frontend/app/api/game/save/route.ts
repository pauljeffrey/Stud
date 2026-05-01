import { proxy } from "@/app/lib/proxy"

export const POST = (req: Request) => proxy(req, "/api/game/save")
