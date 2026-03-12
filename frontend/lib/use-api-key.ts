/**
 * Hook to check if API key is required based on USE_API_KEY env variable
 * Returns true if API key is NOT required (i.e., USE_API_KEY=true means platform can be used without user's API key)
 */
export function useApiKeyRequired(): boolean {
  if (typeof window === "undefined") {
    // Server-side: read from env
    const useApiKey = process.env.USE_API_KEY || process.env.NEXT_PUBLIC_USE_API_KEY
    return useApiKey?.toLowerCase() !== "true"
  }
  
  // Client-side: read from env (NEXT_PUBLIC_ prefixed vars are available)
  const useApiKey = process.env.NEXT_PUBLIC_USE_API_KEY
  return useApiKey?.toLowerCase() !== "true"
}

/**
 * Check if user has provided API key
 */
export function hasApiKey(): boolean {
  if (typeof window === "undefined") return false
  
  const apiSettings = localStorage.getItem("apiSettings")
  if (!apiSettings) return false
  
  try {
    const settings = JSON.parse(apiSettings)
    return !!(settings.apiKey && settings.apiKey.trim() !== "")
  } catch {
    return false
  }
}

/**
 * Check if user can access platform (has API key or USE_API_KEY is true)
 */
export function canAccessPlatform(): boolean {
  const apiKeyRequired = useApiKeyRequired()
  if (!apiKeyRequired) return true // Platform allows use without API key
  
  return hasApiKey() // User must provide API key
}
