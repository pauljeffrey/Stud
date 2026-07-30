import { proxy } from "@/app/lib/proxy"

export const GET = (req: Request) => {
  const query = new URL(req.url).search.replace(/^\?/, "")
  return proxy(req, "/api/notifications", { query })
}
