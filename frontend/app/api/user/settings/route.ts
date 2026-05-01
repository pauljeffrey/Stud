import { proxy } from "@/app/lib/proxy"

export const GET = (req: Request) => proxy(req, "/api/user/settings")
export const PUT = (req: Request) => proxy(req, "/api/user/settings")
