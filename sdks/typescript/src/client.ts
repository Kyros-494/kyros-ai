/**
 * Kyros TypeScript SDK Client.
 *
 * Mirrors the Python SDK API surface using native fetch().
 */

import type {
  RememberResponse,
  RecallResponse,
  FactResult,
  ProcedureResponse,
  ProcedureMatchResponse,
  ProcedureOutcomeResponse,
  SummaryResponse,
  ExportData,
  ContentType,
  MemoryType,
} from './types';
import {
  KyrosError,
  AuthenticationError,
  RateLimitError,
  NotFoundError,
  ValidationError,
  ServerError,
} from './errors';

// ─── Config ───────────────────────────────────

export interface KyrosConfig {
  apiKey?: string;
  baseUrl?: string;
  timeout?: number;
}

export interface RememberOptions {
  contentType?: ContentType;
  role?: string;
  sessionId?: string;
  importance?: number;
  metadata?: Record<string, unknown>;
}

export interface RecallOptions {
  memoryType?: MemoryType;
  k?: number;
  minRelevance?: number;
  sessionId?: string;
  /** If true, each result includes its causal ancestry chain. Adds latency. */
  includeCausalAncestry?: boolean;
}

export interface StoreFactOptions {
  confidence?: number;
  sourceType?: string;
}

export interface StoreProcedureOptions {
  metadata?: Record<string, unknown>;
}

export interface MatchProcedureOptions {
  k?: number;
}

export interface OutcomeOptions {
  durationMs?: number;
}

// ─── Client ───────────────────────────────────

export class KyrosClient {
  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly timeout: number;

  constructor(config: KyrosConfig = {}) {
    this.apiKey = config.apiKey || process.env.KYROS_API_KEY || '';
    if (!this.apiKey) {
      throw new AuthenticationError(
        'No API key provided. Pass apiKey in config or set KYROS_API_KEY env variable.',
      );
    }
    this.baseUrl = (config.baseUrl || process.env.KYROS_BASE_URL || 'https://api.kyros.ai').replace(/\/$/, '');
    this.timeout = config.timeout || 30000;
  }

  // ─── HTTP helpers ─────────────────────────

  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        method,
        headers: {
          'X-API-Key': this.apiKey,
          'Content-Type': 'application/json',
          'User-Agent': 'kyros-sdk-typescript/0.1.0',
        },
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      if (!response.ok) {
        await this.handleError(response);
      }

      if (response.status === 204) return undefined as T;
      return (await response.json()) as T;
    } finally {
      clearTimeout(timer);
    }
  }

  private async handleError(response: Response): Promise<never> {
    let body: Record<string, unknown> = {};
    try {
      body = (await response.json()) as Record<string, unknown>;
    } catch {
      body = { message: await response.text() };
    }

    const message = (body.message || body.detail || `HTTP ${response.status}`) as string;
    const errorCode = body.error as string | undefined;

    switch (response.status) {
      case 401:
      case 403:
        throw new AuthenticationError(message, response.status, errorCode);
      case 404:
        throw new NotFoundError(message, errorCode);
      case 422:
        throw new ValidationError(message, errorCode);
      case 429:
        throw new RateLimitError(
          message,
          parseInt(response.headers.get('X-RateLimit-Limit') || '0'),
          parseInt(response.headers.get('X-RateLimit-Remaining') || '0'),
          parseInt(response.headers.get('X-RateLimit-Reset') || '0'),
          errorCode,
        );
      default:
        if (response.status >= 500) {
          throw new ServerError(message, response.status, errorCode);
        }
        throw new KyrosError(message, response.status, errorCode);
    }
  }

  // ─── Episodic Memory ──────────────────────

  async remember(agentId: string, content: string, options: RememberOptions = {}): Promise<RememberResponse> {
    return this.request<RememberResponse>('POST', '/v1/memory/episodic/remember', {
      agent_id: agentId,
      content,
      content_type: options.contentType || 'text',
      role: options.role,
      session_id: options.sessionId,
      importance: options.importance ?? 0.5,
      metadata: options.metadata || {},
    });
  }

  async recall(agentId: string, query: string, options: RecallOptions = {}): Promise<RecallResponse> {
    return this.request<RecallResponse>('POST', '/v1/memory/episodic/recall', {
      agent_id: agentId,
      query,
      memory_type: options.memoryType,
      k: options.k ?? 10,
      min_relevance: options.minRelevance ?? 0.0,
      session_id: options.sessionId,
      include_causal_ancestry: options.includeCausalAncestry ?? false,
    });
  }

  async forget(agentId: string, memoryId: string): Promise<void> {
    // agentId is accepted for API symmetry; the server scopes deletion by memory_id + auth tenant
    await this.request<void>('DELETE', `/v1/memory/episodic/${memoryId}`);
  }

  // ─── Semantic Memory ──────────────────────

  async storeFact(
    agentId: string,
    subject: string,
    predicate: string,
    value: string,
    options: StoreFactOptions = {},
  ): Promise<FactResult> {
    return this.request<FactResult>('POST', '/v1/memory/semantic/facts', {
      agent_id: agentId,
      subject,
      predicate,
      object: value,
      confidence: options.confidence ?? 1.0,
      source_type: options.sourceType || 'explicit',
    });
  }

  async queryFacts(agentId: string, query: string, k = 10): Promise<RecallResponse> {
    return this.request<RecallResponse>('POST', '/v1/memory/semantic/query', {
      agent_id: agentId,
      query,
      k,
    });
  }

  // ─── Procedural Memory ────────────────────

  async storeProcedure(
    agentId: string,
    name: string,
    description: string,
    taskType: string,
    steps: Record<string, unknown>[],
    options: StoreProcedureOptions = {},
  ): Promise<ProcedureResponse> {
    return this.request<ProcedureResponse>('POST', '/v1/memory/procedural/store', {
      agent_id: agentId,
      name,
      description,
      task_type: taskType,
      steps,
      metadata: options.metadata || {},
    });
  }

  async matchProcedure(
    agentId: string,
    taskDescription: string,
    options: MatchProcedureOptions = {},
  ): Promise<ProcedureMatchResponse> {
    return this.request<ProcedureMatchResponse>('POST', '/v1/memory/procedural/match', {
      agent_id: agentId,
      task_description: taskDescription,
      k: options.k ?? 5,
    });
  }

  async reportOutcome(
    procedureId: string,
    success: boolean,
    options: OutcomeOptions = {},
  ): Promise<ProcedureOutcomeResponse> {
    return this.request<ProcedureOutcomeResponse>('POST', '/v1/memory/procedural/outcome', {
      procedure_id: procedureId,
      success,
      duration_ms: options.durationMs,
    });
  }

  // ─── Admin ────────────────────────────────

  async summarise(agentId: string): Promise<SummaryResponse> {
    return this.request<SummaryResponse>('GET', `/v1/admin/summarise/${agentId}`);
  }

  async exportMemories(agentId: string): Promise<ExportData> {
    return this.request<ExportData>('GET', `/v1/admin/export/${agentId}`);
  }

  async importMemories(agentId: string, data: ExportData): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>('POST', `/v1/admin/import/${agentId}`, data);
  }

  // ─── Unified Search ───────────────────────

  async search(agentId: string, query: string, k = 10): Promise<RecallResponse> {
    return this.request<RecallResponse>('POST', '/v1/search/unified', {
      agent_id: agentId,
      query,
      k,
    });
  }

  // ─── Staleness & Decay ────────────────────

  async getStalenessReport(agentId: string): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>('GET', `/v1/admin/staleness-report/${agentId}`);
  }

  async getDecayRates(): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>('GET', '/v1/admin/decay-rates');
  }

  async setDecayRates(rates: Record<string, number>): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>('PUT', '/v1/admin/decay-rates', { rates });
  }

  // ─── Integrity ────────────────────────────

  async getMemoryProof(memoryId: string): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>('GET', `/v1/admin/memory/${memoryId}/proof`);
  }

  async auditIntegrity(agentId: string): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>('POST', `/v1/admin/agent/${agentId}/audit`);
  }

  // ─── Causal Graph ─────────────────────────

  async explain(agentId: string, memoryId: string, maxDepth = 3): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>('POST', '/v1/memory/causal/explain', {
      agent_id: agentId,
      memory_id: memoryId,
      max_depth: maxDepth,
      direction: 'causes',
    });
  }

  // ─── Embeddings Migration ─────────────────

  async migrateEmbeddings(
    agentId: string,
    fromModel: string,
    toModel: string,
    strategy: 'translate' | 're-embed' = 'translate',
  ): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>(
      'POST',
      `/v1/admin/agent/${agentId}/migrate-embeddings`,
      { from_model: fromModel, to_model: toModel, strategy },
    );
  }
}
