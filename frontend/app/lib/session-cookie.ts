/** Build Set-Cookie flags: Secure only when explicitly enabled or in production. */
export function sessionCookieSuffix(maxAgeSec: number): string {
  const secure =
    process.env.COOKIE_SECURE === "true" ||
    process.env.COOKIE_SECURE === "1" ||
    process.env.NODE_ENV === "production"
  const securePart = secure ? "Secure; " : ""
  return `HttpOnly; ${securePart}SameSite=Strict; Path=/; Max-Age=${maxAgeSec}`
}
