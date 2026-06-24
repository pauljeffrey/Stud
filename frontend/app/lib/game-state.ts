/** Shared Mediquest game-state helpers (display + API payload). */

export interface GameNpc {
  npc_id: string
  name: string
  role: string
  personality_description: string
}

export interface GameCaseState {
  case_state_id: string
  clinical_case_scenario_description: string
  question: string
  diagnosis?: string
  examination_findings: Record<string, unknown>
  investigation_results: Record<string, unknown>
  options?: string[]
  answer?: string
  reason_for_answer?: string
  clue?: string
  time_limit_seconds: number
  time_remaining_seconds: number
  n_changes: number
  max_clinical_changes: number
  clue_used: boolean
  npc_states?: GameNpc[]
}

export interface GameState {
  game_id: string
  user_id: string
  game_world: {
    world_description: string
    hospital_name?: string
    department?: string
  }
  case_state: GameCaseState
  npc_states: GameNpc[]
  current_case_number: number
  total_cases: number
  user_performance: Array<{
    score: number
    analysis: string
    strengths: string[]
    weaknesses: string[]
  }>
  achievements: Array<{ type: string; title: string; description: string }>
  game_master_chat_history: Array<{ role: string; content: string }>
}

export function mergeInitToBackend(data: Record<string, unknown>): Record<string, unknown> {
  const gs = { ...(data.game_state as Record<string, unknown>) }
  if (data.game_world) gs.game_world = data.game_world
  if (data.npc_states) gs.npc_states = data.npc_states
  if (data.case_state) {
    gs.case_state = {
      ...(data.case_state as Record<string, unknown>),
      npc_states:
        data.npc_states ??
        (data.case_state as Record<string, unknown>).npc_states,
    }
  }
  return gs
}

function normalizeCaseState(raw: Record<string, unknown> | null | undefined): GameCaseState {
  const cs = raw ?? {}
  const investigations = (cs.investigations as Record<string, unknown>) ?? {}
  return {
    case_state_id: String(cs.case_state_id ?? ""),
    clinical_case_scenario_description: String(cs.clinical_case_scenario_description ?? ""),
    question: String(cs.question ?? ""),
    diagnosis: cs.diagnosis as string | undefined,
    examination_findings:
      (cs.examination_findings as Record<string, unknown>) ?? investigations ?? {},
    investigation_results:
      (cs.investigation_results as Record<string, unknown>) ??
      investigations ??
      (cs.scan_images as Record<string, unknown>) ??
      {},
    options: cs.options as string[] | undefined,
    answer: cs.answer as string | undefined,
    reason_for_answer: cs.reason_for_answer as string | undefined,
    clue: cs.clue as string | undefined,
    time_limit_seconds: Number(cs.time_limit_seconds ?? 300),
    time_remaining_seconds: Number(cs.time_remaining_seconds ?? cs.time_limit_seconds ?? 300),
    n_changes: Number(cs.n_changes ?? 0),
    max_clinical_changes: Number(cs.max_clinical_changes ?? 10),
    clue_used: Boolean(cs.clue_used ?? false),
    npc_states: cs.npc_states as GameNpc[] | undefined,
  }
}

export function normalizeGameState(
  raw: Record<string, unknown> | null | undefined,
  extras?: {
    game_world?: Record<string, unknown>
    case_state?: Record<string, unknown>
    npc_states?: GameNpc[]
  },
  prev?: GameState | null
): GameState {
  const gs = { ...(prev ?? {}), ...(raw ?? {}) } as Record<string, unknown>
  const caseState = normalizeCaseState(
    (extras?.case_state ?? gs.case_state) as Record<string, unknown> | undefined
  )
  const npcStates =
    extras?.npc_states ??
    (gs.npc_states as GameNpc[]) ??
    caseState.npc_states ??
    prev?.npc_states ??
    []

  return {
    game_id: String(gs.game_id ?? prev?.game_id ?? ""),
    user_id: String(gs.user_id ?? prev?.user_id ?? ""),
    game_world: (extras?.game_world ??
      gs.game_world ??
      prev?.game_world ?? { world_description: "" }) as GameState["game_world"],
    case_state: caseState,
    npc_states: npcStates,
    current_case_number: Number(gs.current_case_number ?? prev?.current_case_number ?? 1),
    total_cases: Number(gs.total_cases ?? prev?.total_cases ?? 1),
    user_performance:
      (gs.user_performance as GameState["user_performance"]) ?? prev?.user_performance ?? [],
    achievements: (gs.achievements as GameState["achievements"]) ?? prev?.achievements ?? [],
    game_master_chat_history:
      (gs.game_master_chat_history as GameState["game_master_chat_history"]) ??
      prev?.game_master_chat_history ??
      [],
  }
}

export function normalizeFromInitResponse(data: Record<string, unknown>): GameState {
  return normalizeGameState(data.game_state as Record<string, unknown>, {
    game_world: data.game_world as Record<string, unknown> | undefined,
    case_state: data.case_state as Record<string, unknown> | undefined,
    npc_states: data.npc_states as GameNpc[] | undefined,
  })
}

export function mergeBackendFromResponse(
  prev: Record<string, unknown>,
  response: Record<string, unknown>
): Record<string, unknown> {
  const merged = { ...prev, ...response }
  if (prev.game_world && response.game_world) {
    merged.game_world = {
      ...(prev.game_world as Record<string, unknown>),
      ...(response.game_world as Record<string, unknown>),
    }
  }
  if (prev.case_state && response.case_state) {
    merged.case_state = {
      ...(prev.case_state as Record<string, unknown>),
      ...(response.case_state as Record<string, unknown>),
    }
  }
  return merged
}

/** Merge UI edits into the canonical backend payload (keeps game_config, etc.). */
export function toBackendPayload(
  backend: Record<string, unknown>,
  ui: GameState
): Record<string, unknown> {
  const prevCs = (backend.case_state ?? {}) as Record<string, unknown>
  const prevGw = (backend.game_world ?? {}) as Record<string, unknown>
  return {
    ...backend,
    current_case_number: ui.current_case_number,
    total_cases: ui.total_cases,
    user_performance: ui.user_performance,
    achievements: ui.achievements,
    npc_states: ui.npc_states ?? backend.npc_states,
    game_world: {
      ...prevGw,
      world_description: ui.game_world.world_description,
      hospital_name: ui.game_world.hospital_name ?? prevGw.hospital_name,
      department: ui.game_world.department ?? prevGw.department,
    },
    case_state: {
      ...prevCs,
      clinical_case_scenario_description: ui.case_state.clinical_case_scenario_description,
      question: ui.case_state.question,
      diagnosis: ui.case_state.diagnosis,
      time_limit_seconds: ui.case_state.time_limit_seconds,
      time_remaining_seconds: ui.case_state.time_remaining_seconds,
      n_changes: ui.case_state.n_changes,
      max_clinical_changes: ui.case_state.max_clinical_changes,
      clue_used: ui.case_state.clue_used,
      options: ui.case_state.options,
      answer: ui.case_state.answer,
      reason_for_answer: ui.case_state.reason_for_answer,
      clue: ui.case_state.clue,
      investigations:
        ui.case_state.investigation_results ?? prevCs.investigations ?? {},
      scan_images: prevCs.scan_images ?? {},
      npc_states: ui.npc_states ?? prevCs.npc_states,
    },
  }
}

export async function readApiError(response: Response): Promise<string> {
  try {
    const data = await response.clone().json()
    if (typeof data.detail === "string") return data.detail
    if (Array.isArray(data.detail)) {
      return data.detail
        .map((item: { msg?: string }) => item.msg ?? JSON.stringify(item))
        .join("; ")
    }
    return String(data.error ?? data.message ?? `Request failed (${response.status})`)
  } catch {
    return `Request failed (${response.status})`
  }
}

export async function readSseStream(
  response: Response,
  onEvent: (data: Record<string, unknown>) => void
): Promise<void> {
  const reader = response.body?.getReader()
  if (!reader) return

  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split("\n")
    buffer = lines.pop() ?? ""

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue
      try {
        onEvent(JSON.parse(line.slice(6)))
      } catch {
        // skip malformed SSE chunks
      }
    }
  }
}
