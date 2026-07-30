import { NextResponse } from "next/server"
import { proxy } from "@/app/lib/proxy"

/** Logout proxy. Best-effort: never block the client on backend failure. */
export async function POST(req: Request) {
  try {
    return await proxy(req, "/api/auth/logout")
  } catch {
    return NextResponse.json({ success: true })
  }
}
