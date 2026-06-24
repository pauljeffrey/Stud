import { proxy } from "@/app/lib/proxy"

export async function GET(request: Request) {
  return proxy(request, "/api/auth/me", { method: "GET" })
}
