/** Shared AI credential validation and session-only storage. */

export interface ApiCredentials {
  provider: string
  modelName: string
  apiKey: string
}

export const SESSION_CREDS_KEY = "stud_session_api_credentials"

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/
const MODEL_HINT_RE = /(gemini|gpt|claude|openai|anthropic|llama|mistral|nemotron|\/|meta-)/i

export function looksLikeEmail(value: string): boolean {
  return EMAIL_RE.test((value || "").trim())
}

export function validateCredentials(
  creds: Partial<ApiCredentials>
): { valid: boolean; message?: string } {
  const modelName = (creds.modelName || "").trim()
  const apiKey = (creds.apiKey || "").trim()

  if (!modelName && !apiKey) {
    return { valid: false, message: "Model name and API key are required." }
  }
  if (!modelName) {
    return { valid: false, message: "Model name is required." }
  }
  if (!apiKey) {
    return { valid: false, message: "API key is required." }
  }
  if (looksLikeEmail(modelName)) {
    return {
      valid: false,
      message:
        "Model name cannot be an email address. Use a model ID such as gemini-2.0-flash or gpt-4o-mini.",
    }
  }
  if (looksLikeEmail(apiKey)) {
    return {
      valid: false,
      message: "API key cannot be an email address. Paste the key from your AI provider.",
    }
  }
  if (!MODEL_HINT_RE.test(modelName)) {
    return {
      valid: false,
      message:
        "Model name does not look valid. Examples: gemini-2.0-flash, gpt-4o-mini, anthropic/claude-3.5-sonnet.",
    }
  }
  if (apiKey.length < 8) {
    return { valid: false, message: "API key is too short." }
  }
  return { valid: true }
}

export function hasUsableCredentials(creds: Partial<ApiCredentials> | null | undefined): boolean {
  if (!creds) return false
  return validateCredentials(creds).valid
}

export function getSessionCredentials(): ApiCredentials | null {
  if (typeof window === "undefined") return null
  try {
    const raw = sessionStorage.getItem(SESSION_CREDS_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as ApiCredentials
    return hasUsableCredentials(parsed) ? parsed : null
  } catch {
    return null
  }
}

export function setSessionCredentials(creds: ApiCredentials): void {
  if (typeof window === "undefined") return
  sessionStorage.setItem(SESSION_CREDS_KEY, JSON.stringify(creds))
}

export function clearSessionCredentials(): void {
  if (typeof window === "undefined") return
  sessionStorage.removeItem(SESSION_CREDS_KEY)
}

/** Map UI credentials to backend initialize payload fields. */
export function toBackendModelFields(creds: ApiCredentials) {
  return {
    model_name: creds.modelName,
    api_key: creds.apiKey,
    provider: creds.provider || "google",
  }
}

export function parseApiErrorDetail(detail: unknown): string {
  if (!detail) return "Request failed"
  if (typeof detail === "string") return detail
  if (typeof detail === "object" && detail !== null) {
    const d = detail as { message?: string; code?: string }
    if (d.message) return d.message
  }
  return "Request failed"
}
