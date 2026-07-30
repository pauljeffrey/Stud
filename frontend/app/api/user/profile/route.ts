import { proxy } from "@/app/lib/proxy"

export const PUT = (req: Request) => proxy(req, "/api/user/profile", { method: "PUT" })
