/** Shared AI credential validation and storage (session + saved account). */

export interface ApiCredentials {
  provider: string
  modelName: string
  apiKey: string
}

export const SESSION_CREDS_KEY = "stud_session_api_credentials"
export const ACCOUNT_CREDS_KEY = "stud_account_api_credentials"

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/
const MODEL_HINT_RE = /(gemini|gpt|claude|openai|anthropic|llama|mistral|nemotron|qwen|\/|meta-)/i

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
        "Model name does not look valid. Examples: gemini-2.0-flash, gpt-4o-mini, meta-llama/llama-3.3-70b-instruct:free.",
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

/** Normalize API settings from backend or legacy localStorage shapes. */
export function normalizeStoredSettings(
  raw: Partial<ApiCredentials> & { model_name?: string; api_key?: string } | null | undefined
): ApiCredentials | null {
  if (!raw) return null
  const creds: ApiCredentials = {
    provider: String(raw.provider || "google"),
    modelName: String(raw.modelName || raw.model_name || "").trim(),
    apiKey: String(raw.apiKey || raw.api_key || "").trim(),
  }
  return hasUsableCredentials(creds) ? creds : null
}

export function getSessionCredentials(): ApiCredentials | null {
  if (typeof window === "undefined") return null
  try {
    const raw = sessionStorage.getItem(SESSION_CREDS_KEY)
    if (!raw) return null
    return normalizeStoredSettings(JSON.parse(raw) as ApiCredentials)
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

/** Cached account credentials (survives refresh; synced after secure save). */
export function getAccountCredentials(): ApiCredentials | null {
  if (typeof window === "undefined") return null
  try {
    const raw =
      localStorage.getItem(ACCOUNT_CREDS_KEY) ||
      localStorage.getItem("apiSettings") ||
      localStorage.getItem("api_settings")
    if (!raw) return null
    return normalizeStoredSettings(JSON.parse(raw))
  } catch {
    return null
  }
}

export function persistAccountCredentials(creds: ApiCredentials): void {
  if (typeof window === "undefined") return
  localStorage.setItem(ACCOUNT_CREDS_KEY, JSON.stringify(creds))
  localStorage.setItem(
    "apiSettings",
    JSON.stringify({
      provider: creds.provider,
      modelName: creds.modelName,
      apiKey: creds.apiKey,
    })
  )
}

export function clearAccountCredentials(): void {
  if (typeof window === "undefined") return
  localStorage.removeItem(ACCOUNT_CREDS_KEY)
  localStorage.removeItem("apiSettings")
  localStorage.removeItem("api_settings")
}

/** Best available credentials without a network call. */
export function resolveCredentials(): ApiCredentials | null {
  return getSessionCredentials() || getAccountCredentials()
}

/**
 * Backend request fields for AI calls: prefers live session/account
 * credentials (re-checked at call time, since a user may add/change creds
 * mid-session), falling back to whatever the caller's own model-config state
 * has typed in — even if it doesn't pass full validation, so the backend can
 * still try it. Shared by demo/mediquest/quiz/study instead of each page
 * re-implementing its own precedence order.
 */
export function resolveModelFields(
  fallback: { model_name: string; api_key: string; provider: string }
): Record<string, string> {
  const creds = getSessionCredentials() || getAccountCredentials()
  const fields: Record<string, string> = { provider: creds?.provider || fallback.provider }
  const modelName = creds?.modelName || fallback.model_name
  const apiKey = creds?.apiKey || fallback.api_key
  if (modelName && apiKey && hasUsableCredentials({ provider: fields.provider, modelName, apiKey })) {
    return toBackendModelFields({ provider: fields.provider, modelName, apiKey })
  }
  if (fallback.model_name) fields.model_name = fallback.model_name
  if (fallback.api_key) fields.api_key = fallback.api_key
  return fields
}

export async function fetchAccountCredentials(token: string): Promise<ApiCredentials | null> {
  const res = await fetch("/api/user/settings", {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) return getAccountCredentials()
  const data = await res.json()
  const creds = normalizeStoredSettings(data.settings)
  if (creds) persistAccountCredentials(creds)
  return creds
}

export async function saveAccountCredentials(
  creds: ApiCredentials,
  token: string
): Promise<ApiCredentials> {
  const res = await fetch("/api/user/settings", {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(creds),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(parseApiErrorDetail(err.detail) || "Failed to save API settings")
  }
  const data = await res.json()
  const saved = normalizeStoredSettings(data.settings) || creds
  persistAccountCredentials(saved)
  return saved
}

/** Map UI credentials to backend payload fields. */
export function toBackendModelFields(creds: ApiCredentials) {
  return {
    model_name: creds.modelName,
    api_key: creds.apiKey,
    provider: creds.provider || "google",
  }
}

export function toModelConfig(creds: ApiCredentials) {
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
