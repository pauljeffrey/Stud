import { proxy } from "@/app/lib/proxy"

export const GET = (req: Request) => proxy(req, "/api/quiz/saved")
export const POST = (req: Request) => proxy(req, "/api/quiz/saved")
