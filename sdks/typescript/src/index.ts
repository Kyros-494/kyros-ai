/**
 * Kyros TypeScript SDK — persistent memory for AI agents.
 *
 * @example
 * ```typescript
 * import { KyrosClient } from '@kyros/sdk';
 *
 * const client = new KyrosClient({ apiKey: 'mk_live_...' });
 * await client.remember('my-agent', 'User prefers dark mode');
 * const results = await client.recall('my-agent', 'What theme?');
 * ```
 */

export { KyrosClient } from './client';
export type {
  KyrosConfig,
  RememberOptions,
  RecallOptions,
  StoreFactOptions,
  StoreProcedureOptions,
  MatchProcedureOptions,
  OutcomeOptions,
} from './client';
export type {
  RememberResponse,
  RecallResponse,
  MemoryResult,
  FactResult,
  ProcedureResponse,
  ProcedureMatchResponse,
  ProcedureResult,
  ProcedureOutcomeResponse,
  ExportData,
  SummaryResponse,
  MemoryType,
  ContentType,
} from './types';
export {
  KyrosError,
  AuthenticationError,
  RateLimitError,
  NotFoundError,
  ValidationError,
  ServerError,
} from './errors';
