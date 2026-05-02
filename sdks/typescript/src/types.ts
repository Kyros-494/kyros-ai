/** Kyros SDK type definitions — mirrors the server API schemas. */

export type MemoryType = 'episodic' | 'semantic' | 'procedural';
export type ContentType = 'text' | 'action' | 'tool_call' | 'observation';

// ─── Episodic Memory ──────────────────────────

export interface RememberResponse {
  memory_id: string;
  agent_id: string;
  memory_type: MemoryType;
  created_at: string;
}

export interface MemoryResult {
  memory_id: string;
  content: string;
  memory_type: MemoryType;
  relevance_score: number;
  importance: number;
  created_at: string;
  metadata: Record<string, unknown>;
  // Ebbinghaus decay fields (always present in server response)
  freshness_score: number;
  freshness_warning: boolean;
  memory_category: string | null;
  // Causal ancestry (present when include_causal_ancestry=true)
  causal_ancestry: Record<string, unknown>[];
}

export interface RecallResponse {
  agent_id: string;
  query: string;
  results: MemoryResult[];
  total_searched: number;
  latency_ms: number;
}

// ─── Semantic Memory ──────────────────────────

export interface FactResult {
  fact_id: string;
  subject: string;
  predicate: string;
  object: string;
  confidence: number;
  created_at: string;
  was_contradiction: boolean;
  replaced_fact_id: string | null;
  // Belief propagation updates triggered by this fact (empty array if none)
  propagated_updates: Record<string, unknown>[];
}

// ─── Procedural Memory ────────────────────────

export interface ProcedureResponse {
  procedure_id: string;
  agent_id: string;
  name: string;
  task_type: string;
  created_at: string;
}

export interface ProcedureResult {
  procedure_id: string;
  name: string;
  description: string;
  task_type: string;
  steps: Record<string, unknown>[];
  success_rate: number;
  total_executions: number;
  relevance_score: number;
  avg_duration_ms: number | null;
  created_at: string;
}

export interface ProcedureMatchResponse {
  agent_id: string;
  task_description: string;
  results: ProcedureResult[];
  latency_ms: number;
}

export interface ProcedureOutcomeResponse {
  procedure_id: string;
  success_count: number;
  failure_count: number;
  success_rate: number;
  avg_duration_ms: number | null;
}

// ─── Admin ────────────────────────────────────

export interface SummaryResponse {
  agent_id: string;
  summary: string;
  memory_count: number;
  compression_ratio: number;
}

export interface ExportData {
  agent_id: string;
  episodic: Record<string, unknown>[];
  semantic: Record<string, unknown>[];
  procedural: Record<string, unknown>[];
  total_memories: number;
  exported_at: string;
}
