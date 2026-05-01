import { proxy } from "@/app/lib/proxy"

export async function GET(req: Request) {
  const url = new URL(req.url)
  const userId = url.searchParams.get("user_id")
  return proxy(req, "/api/learning/enrollments", {
    query: userId ? `user_id=${encodeURIComponent(userId)}` : undefined,
  })
}
