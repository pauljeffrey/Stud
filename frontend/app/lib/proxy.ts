import { NextResponse } from "next/server"

export const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || "http://localhost:8000"

/**
 * Forward a Next.js API request to the Python backend, preserving auth and
 * streaming the response back. Centralises 4xx/5xx pass-through and removes
 * boilerplate from individual route files.
 */
export async function proxy(
  req: Request,
  path: string,
  opts: {
    method?: string
    /** When true, forwards the raw body (e.g. multipart/form-data) untouched. */
    raw?: boolean
    /** Optional querystring to append (without leading `?`). */
    query?: string
    /** Stream upstream body back as text/plain (for SSE-like chat endpoints). */
    stream?: boolean
  } = {}
): Promise<Response> {
  const method = (opts.method || req.method || "GET").toUpperCase()
  const headers: Record<string, string> = {}
  const auth = req.headers.get("authorization")
  if (auth) headers.Authorization = auth

  let body: BodyInit | undefined
  if (method !== "GET" && method !== "HEAD") {
    if (opts.raw) {
      body = await req.arrayBuffer()
      const ct = req.headers.get("content-type")
      if (ct) headers["Content-Type"] = ct
    } else {
      const text = await req.text()
      body = text
      headers["Content-Type"] = req.headers.get("content-type") || "application/json"
    }
  }

  const url = `${PYTHON_BACKEND_URL}${path}${opts.query ? `?${opts.query}` : ""}`
  const upstream = await fetch(url, { method, headers, body })

  if (opts.stream) {
    return new Response(upstream.body, {
      status: upstream.status,
      headers: {
        "Content-Type": "text/plain",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    })
  }

  const contentType = upstream.headers.get("content-type") || "application/json"
  if (contentType.includes("application/json")) {
    const data = await upstream.json().catch(() => ({}))
    return NextResponse.json(data, { status: upstream.status })
  }
  return new Response(upstream.body, {
    status: upstream.status,
    headers: { "Content-Type": contentType },
  })
}
