# TypeScript SDK Reference

Complete API reference for the Kyros TypeScript SDK.

## Installation

```bash
npm install @kyros/sdk
```

Or with other package managers:

```bash
# Yarn
yarn add @kyros/sdk

# pnpm
pnpm add @kyros/sdk

# Bun
bun add @kyros/sdk
```

## Quick Start

```typescript
import { KyrosClient } from '@kyros/sdk';

// Initialize client
const client = new KyrosClient({ apiKey: 'mk_live_...' });

// Store a memory
await client.remember('my-agent', 'User prefers TypeScript and dark mode');

// Recall by meaning
const results = await client.recall('my-agent', 'What does the user prefer?');
console.log(results.results[0].content);
// → "User prefers TypeScript and dark mode"

// Store a fact
await client.storeFact('my-agent', 'user', 'language', 'TypeScript');
```

## Client Initialization

### KyrosClient

```typescript
class KyrosClient {
  constructor(options?: KyrosClientOptions)
}
```

Initialize the Kyros client.

**Options:**

```typescript
interface KyrosClientOptions {
  apiKey?: string;        // API key (or use KYROS_API_KEY env var)
  baseUrl?: string;       // Base URL (default: https://api.kyros.ai)
  timeout?: number;       // Request timeout in ms (default: 30000)
}
```

**Example:**

```typescript
// Using API key directly
const client = new KyrosClient({ apiKey: 'mk_live_...' });

// Using environment variable
process.env.KYROS_API_KEY = 'mk_live_...';
const client = new KyrosClient();

// Self-hosted instance
const client = new KyrosClient({
  apiKey: 'your-key',
  baseUrl: 'https://kyros.yourcompany.com'
});

// Custom timeout
const client = new KyrosClient({
  apiKey: 'your-key',
  timeout: 60000  // 60 seconds
});
```

## Episodic Memory

Episodic memory stores conversation history, actions, observations, and tool calls.

### remember

```typescript
async remember(
  agentId: string,
  content: string,
  options?: RememberOptions
): Promise<RememberResponse>
```

Store an episodic memory.

**Parameters:**

- `agentId` (string): Unique identifier for the agent
- `content` (string): Memory content to store
- `options` (RememberOptions, optional): Additional options

**Options:**

```typescript
interface RememberOptions {
  contentType?: 'text' | 'action' | 'tool_call' | 'observation';
  role?: string;
  sessionId?: string;
  importance?: number;  // 0.0 to 1.0
  metadata?: Record<string, any>;
}
```

**Returns:**

```typescript
interface RememberResponse {
  memoryId: string;
  agentId: string;
  createdAt: Date;
}
```

**Example:**

```typescript
// Basic usage
const response = await client.remember(
  'agent-123',
  'User asked about pricing'
);

// With all options
const response = await client.remember(
  'agent-123',
  'User: What are your pricing plans?',
  {
    contentType: 'text',
    role: 'user',
    sessionId: 'session-456',
    importance: 0.8,
    metadata: {
      category: 'sales',
      language: 'en',
      sentiment: 'neutral'
    }
  }
);

console.log(`Stored memory: ${response.memoryId}`);
```

### recall

```typescript
async recall(
  agentId: string,
  query: string,
  options?: RecallOptions
): Promise<RecallResponse>
```

Recall memories using semantic search.

**Parameters:**

- `agentId` (string): Agent identifier
- `query` (string): Search query
- `options` (RecallOptions, optional): Search options

**Options:**

```typescript
interface RecallOptions {
  memoryType?: 'episodic' | 'semantic' | 'procedural';
  k?: number;              // Max results (default: 10)
  minRelevance?: number;   // Min relevance score (0.0-1.0)
  sessionId?: string;
  includeCausalAncestry?: boolean;
}
```

**Returns:**

```typescript
interface RecallResponse {
  results: Memory[];
  total: number;
}

interface Memory {
  memoryId: string;
  content: string;
  relevanceScore: number;
  freshnessScore: number;
  importance: number;
  createdAt: Date;
  metadata: Record<string, any>;
  memoryType: string;
}
```

**Example:**

```typescript
// Basic recall
const results = await client.recall(
  'agent-123',
  'What did the user ask about?'
);

for (const memory of results.results) {
  console.log(memory.content);
  console.log(`  Relevance: ${memory.relevanceScore.toFixed(2)}`);
  console.log(`  Freshness: ${memory.freshnessScore.toFixed(2)}`);
}

// Advanced recall with filters
const results = await client.recall(
  'agent-123',
  'pricing questions',
  {
    memoryType: 'episodic',
    k: 5,
    minRelevance: 0.7,
    sessionId: 'session-456',
    includeCausalAncestry: true
  }
);
```

### forget

```typescript
async forget(
  agentId: string,
  memoryId: string
): Promise<void>
```

Delete a specific memory.

**Parameters:**

- `agentId` (string): Agent identifier
- `memoryId` (string): Memory identifier to delete

**Returns:** Promise<void>

**Example:**

```typescript
// Delete a memory
await client.forget('agent-123', 'mem-456');
```

## Semantic Memory

Semantic memory stores facts as subject-predicate-object triples with confidence scores.

### storeFact

```typescript
async storeFact(
  agentId: string,
  subject: string,
  predicate: string,
  value: string,
  options?: StoreFactOptions
): Promise<FactResult>
```

Store a semantic fact.

**Parameters:**

- `agentId` (string): Agent identifier
- `subject` (string): Subject of the fact
- `predicate` (string): Relationship or property
- `value` (string): Object or value
- `options` (StoreFactOptions, optional): Additional options

**Options:**

```typescript
interface StoreFactOptions {
  confidence?: number;     // 0.0 to 1.0 (default: 1.0)
  sourceType?: 'explicit' | 'inferred' | 'observed';
}
```

**Returns:**

```typescript
interface FactResult {
  factId: string;
  subject: string;
  predicate: string;
  value: string;
  confidence: number;
}
```

**Example:**

```typescript
// Store a user preference
const fact = await client.storeFact(
  'agent-123',
  'user',
  'prefers',
  'dark mode',
  { confidence: 0.9 }
);

// Store product information
const fact = await client.storeFact(
  'agent-123',
  'product_pro',
  'price',
  '$99/month',
  {
    confidence: 1.0,
    sourceType: 'explicit'
  }
);

// Store inferred fact
const fact = await client.storeFact(
  'agent-123',
  'user',
  'skill_level',
  'advanced',
  {
    confidence: 0.7,
    sourceType: 'inferred'
  }
);
```

### queryFacts

```typescript
async queryFacts(
  agentId: string,
  query: string,
  k?: number
): Promise<RecallResponse>
```

Query semantic facts using natural language.

**Parameters:**

- `agentId` (string): Agent identifier
- `query` (string): Natural language query
- `k` (number, optional): Maximum number of results (default: 10)

**Returns:** RecallResponse with matching facts

**Example:**

```typescript
// Query facts
const results = await client.queryFacts(
  'agent-123',
  'user preferences',
  10
);

for (const fact of results.results) {
  console.log(`${fact.subject} ${fact.predicate} ${fact.value}`);
  console.log(`  Confidence: ${fact.confidence.toFixed(2)}`);
}
```

## Procedural Memory

Procedural memory stores workflows, procedures, and skills with success tracking.

### storeProcedure

```typescript
async storeProcedure(
  agentId: string,
  name: string,
  description: string,
  taskType: string,
  steps: ProcedureStep[],
  metadata?: Record<string, any>
): Promise<ProcedureResponse>
```

Store a procedure or workflow.

**Parameters:**

- `agentId` (string): Agent identifier
- `name` (string): Procedure name
- `description` (string): Detailed description
- `taskType` (string): Category of task
- `steps` (ProcedureStep[]): List of steps
- `metadata` (object, optional): Additional metadata

**Types:**

```typescript
interface ProcedureStep {
  action: string;
  params?: Record<string, any>;
}

interface ProcedureResponse {
  procedureId: string;
  name: string;
  successRate: number;
}
```

**Example:**

```typescript
// Store email sending procedure
const procedure = await client.storeProcedure(
  'agent-123',
  'Send Email',
  'Send an email to a recipient with subject and body',
  'communication',
  [
    {
      action: 'validate_email',
      params: { field: 'to' }
    },
    {
      action: 'compose_message',
      params: { template: 'default' }
    },
    {
      action: 'send',
      params: { retry: 3 }
    }
  ],
  {
    category: 'email',
    priority: 'high'
  }
);

console.log(`Stored procedure: ${procedure.procedureId}`);
```

### matchProcedure

```typescript
async matchProcedure(
  agentId: string,
  taskDescription: string,
  k?: number
): Promise<ProcedureMatchResponse>
```

Find procedures matching a task description.

**Parameters:**

- `agentId` (string): Agent identifier
- `taskDescription` (string): Natural language description
- `k` (number, optional): Maximum number of results (default: 5)

**Returns:**

```typescript
interface ProcedureMatchResponse {
  matches: Procedure[];
}

interface Procedure {
  procedureId: string;
  name: string;
  description: string;
  steps: ProcedureStep[];
  successRate: number;
  relevanceScore: number;
}
```

**Example:**

```typescript
// Find matching procedures
const matches = await client.matchProcedure(
  'agent-123',
  'I need to send an email to a customer',
  5
);

for (const proc of matches.matches) {
  console.log(`${proc.name} (success: ${(proc.successRate * 100).toFixed(0)}%)`);
  console.log(`  Relevance: ${proc.relevanceScore.toFixed(2)}`);
  console.log(`  Steps: ${proc.steps.length}`);
}
```

### reportOutcome

```typescript
async reportOutcome(
  procedureId: string,
  success: boolean,
  durationMs?: number
): Promise<ProcedureOutcomeResponse>
```

Report the outcome of a procedure execution.

**Parameters:**

- `procedureId` (string): Procedure identifier
- `success` (boolean): Whether execution succeeded
- `durationMs` (number, optional): Execution duration in milliseconds

**Returns:**

```typescript
interface ProcedureOutcomeResponse {
  procedureId: string;
  newSuccessRate: number;
}
```

**Example:**

```typescript
// Report successful execution
const outcome = await client.reportOutcome(
  'proc-456',
  true,
  1500
);

console.log(`New success rate: ${(outcome.newSuccessRate * 100).toFixed(0)}%`);

// Report failure
const outcome = await client.reportOutcome(
  'proc-456',
  false,
  3000
);
```

## Unified Search

Search across all memory types simultaneously.

### search

```typescript
async search(
  agentId: string,
  query: string,
  k?: number
): Promise<RecallResponse>
```

Search across episodic, semantic, and procedural memories.

**Parameters:**

- `agentId` (string): Agent identifier
- `query` (string): Search query
- `k` (number, optional): Maximum number of results (default: 10)

**Returns:** RecallResponse with mixed memory types

**Example:**

```typescript
// Unified search
const results = await client.search(
  'agent-123',
  'email preferences',
  10
);

for (const memory of results.results) {
  console.log(`[${memory.memoryType}] ${memory.content}`);
}
```

## Advanced Features

### Causal Reasoning

#### explain

```typescript
async explain(
  agentId: string,
  memoryId: string,
  maxDepth?: number
): Promise<CausalExplanation>
```

Get causal explanation for a memory.

**Parameters:**

- `agentId` (string): Agent identifier
- `memoryId` (string): Memory identifier
- `maxDepth` (number, optional): Maximum depth of causal chain (default: 3)

**Returns:**

```typescript
interface CausalExplanation {
  chain: CausalStep[];
}

interface CausalStep {
  cause: string;
  effect: string;
}
```

**Example:**

```typescript
const explanation = await client.explain(
  'agent-123',
  'mem-456',
  3
);

console.log('Causal chain:');
for (const step of explanation.chain) {
  console.log(`  ${step.cause} → ${step.effect}`);
}
```

### Integrity Verification

#### getMemoryProof

```typescript
async getMemoryProof(
  memoryId: string
): Promise<MemoryProof>
```

Get cryptographic proof for a memory.

**Parameters:**

- `memoryId` (string): Memory identifier

**Returns:**

```typescript
interface MemoryProof {
  memoryId: string;
  contentHash: string;
  merkleRoot: string;
  merkleProof: string[];
}
```

**Example:**

```typescript
const proof = await client.getMemoryProof('mem-456');
console.log(`Content hash: ${proof.contentHash}`);
console.log(`Merkle root: ${proof.merkleRoot}`);
```

#### auditIntegrity

```typescript
async auditIntegrity(
  agentId: string
): Promise<IntegrityAudit>
```

Audit integrity of all memories for an agent.

**Parameters:**

- `agentId` (string): Agent identifier

**Returns:**

```typescript
interface IntegrityAudit {
  totalMemories: number;
  verified: number;
  tampered: number;
  issues: string[];
}
```

**Example:**

```typescript
const audit = await client.auditIntegrity('agent-123');
console.log(`Verified: ${audit.verified}/${audit.totalMemories}`);
if (audit.tampered > 0) {
  console.log(`WARNING: ${audit.tampered} tampered memories detected!`);
}
```

### Memory Decay

#### getStalenessReport

```typescript
async getStalenessReport(
  agentId: string
): Promise<StalenessReport>
```

Get report on memory staleness.

**Parameters:**

- `agentId` (string): Agent identifier

**Returns:**

```typescript
interface StalenessReport {
  staleCount: number;
  avgFreshness: number;
}
```

**Example:**

```typescript
const report = await client.getStalenessReport('agent-123');
console.log(`Stale memories: ${report.staleCount}`);
console.log(`Average freshness: ${report.avgFreshness.toFixed(2)}`);
```

#### getDecayRates

```typescript
async getDecayRates(): Promise<Record<string, number>>
```

Get current decay rates for all memory categories.

**Returns:** Object mapping category names to decay rates

**Example:**

```typescript
const rates = await client.getDecayRates();
for (const [category, rate] of Object.entries(rates)) {
  console.log(`${category}: ${rate}`);
}
```

#### setDecayRates

```typescript
async setDecayRates(
  rates: Record<string, number>
): Promise<void>
```

Set decay rates for memory categories.

**Parameters:**

- `rates` (object): Object mapping category names to decay rates (0.0-1.0)

**Example:**

```typescript
await client.setDecayRates({
  conversation: 0.1,
  facts: 0.05,
  procedures: 0.02
});
```

### Export/Import

#### exportMemories

```typescript
async exportMemories(
  agentId: string
): Promise<ExportData>
```

Export all memories for an agent.

**Parameters:**

- `agentId` (string): Agent identifier

**Returns:** Object with all memories in portable format

**Example:**

```typescript
// Export memories
const exportData = await client.exportMemories('agent-123');

// Save to file
import fs from 'fs';
fs.writeFileSync(
  'memories.json',
  JSON.stringify(exportData, null, 2)
);
```

#### importMemories

```typescript
async importMemories(
  agentId: string,
  data: ExportData
): Promise<ImportResult>
```

Import memories for an agent.

**Parameters:**

- `agentId` (string): Agent identifier
- `data` (ExportData): Export data from exportMemories

**Returns:**

```typescript
interface ImportResult {
  importedCount: number;
}
```

**Example:**

```typescript
// Load from file
import fs from 'fs';
const exportData = JSON.parse(
  fs.readFileSync('memories.json', 'utf-8')
);

// Import memories
const result = await client.importMemories(
  'agent-456',
  exportData
);

console.log(`Imported ${result.importedCount} memories`);
```

### Embedding Migration

#### migrateEmbeddings

```typescript
async migrateEmbeddings(
  agentId: string,
  fromModel: string,
  toModel: string,
  strategy?: 'translate' | 'regenerate'
): Promise<MigrationResult>
```

Migrate embeddings to a different model.

**Parameters:**

- `agentId` (string): Agent identifier
- `fromModel` (string): Current embedding model
- `toModel` (string): Target embedding model
- `strategy` (string, optional): Migration strategy (default: 'translate')

**Returns:**

```typescript
interface MigrationResult {
  migratedCount: number;
}
```

**Example:**

```typescript
const result = await client.migrateEmbeddings(
  'agent-123',
  'all-MiniLM-L6-v2',
  'all-mpnet-base-v2',
  'translate'
);

console.log(`Migrated ${result.migratedCount} embeddings`);
```

## Vercel AI SDK Integration

The Kyros SDK integrates seamlessly with the Vercel AI SDK.

```typescript
import { KyrosClient } from '@kyros/sdk';
import { createKyrosTools } from '@kyros/sdk/integrations/vercel';
import { generateText } from 'ai';
import { openai } from '@ai-sdk/openai';

const kyros = new KyrosClient({ apiKey: 'mk_live_...' });
const tools = createKyrosTools(kyros, 'my-agent');

const result = await generateText({
  model: openai('gpt-4'),
  tools,
  prompt: 'Remember that the user prefers dark mode'
});
```

### createKyrosTools

```typescript
function createKyrosTools(
  client: KyrosClient,
  agentId: string
): Record<string, Tool>
```

Create Vercel AI SDK tools for Kyros operations.

**Parameters:**

- `client` (KyrosClient): Kyros client instance
- `agentId` (string): Agent identifier

**Returns:** Object with tools:
- `remember`: Store a memory
- `recall`: Search memories
- `storeFact`: Store a fact
- `queryFacts`: Query facts

**Example:**

```typescript
import { KyrosClient } from '@kyros/sdk';
import { createKyrosTools } from '@kyros/sdk/integrations/vercel';
import { generateText } from 'ai';
import { anthropic } from '@ai-sdk/anthropic';

const kyros = new KyrosClient({ apiKey: process.env.KYROS_API_KEY });
const tools = createKyrosTools(kyros, 'agent-123');

const result = await generateText({
  model: anthropic('claude-3-5-sonnet-20241022'),
  tools,
  maxSteps: 5,
  prompt: 'What do you remember about my preferences?'
});

console.log(result.text);
```

## Error Handling

```typescript
import {
  KyrosClient,
  KyrosError,
  AuthenticationError,
  RateLimitError,
  NotFoundError,
  ValidationError,
  ServerError,
  TimeoutError,
  ConnectionError
} from '@kyros/sdk';

const client = new KyrosClient({ apiKey: 'invalid-key' });

try {
  await client.remember('agent-123', 'test');
  
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.error('Authentication failed:', error.message);
    
  } else if (error instanceof RateLimitError) {
    console.error(`Rate limit exceeded. Retry after ${error.retryAfter}s`);
    
  } else if (error instanceof NotFoundError) {
    console.error('Resource not found:', error.message);
    
  } else if (error instanceof ValidationError) {
    console.error('Validation error:', error.message);
    
  } else if (error instanceof ServerError) {
    console.error('Server error:', error.message);
    
  } else if (error instanceof TimeoutError) {
    console.error('Request timed out:', error.message);
    
  } else if (error instanceof ConnectionError) {
    console.error('Connection failed:', error.message);
    
  } else if (error instanceof KyrosError) {
    console.error('Kyros error:', error.message);
    
  } else {
    console.error('Unknown error:', error);
  }
}
```

## Best Practices

### Memory Importance

Set importance scores based on content significance:

```typescript
// Critical information (decays slowly)
await client.remember(
  'agent-123',
  "User's API key: abc123",
  { importance: 1.0 }
);

// Normal conversation (standard decay)
await client.remember(
  'agent-123',
  'User asked about weather',
  { importance: 0.5 }
);

// Low-priority information (decays quickly)
await client.remember(
  'agent-123',
  'User said hello',
  { importance: 0.1 }
);
```

### Session Management

Group related memories with session IDs:

```typescript
import { randomUUID } from 'crypto';

const sessionId = `session-${randomUUID()}`;

// Store conversation in session
await client.remember(
  'agent-123',
  'User: What is the weather?',
  { sessionId }
);

await client.remember(
  'agent-123',
  'Assistant: It is sunny today.',
  { sessionId }
);

// Recall from specific session
const results = await client.recall(
  'agent-123',
  'weather',
  { sessionId }
);
```

### Metadata Usage

Use metadata for filtering and organization:

```typescript
await client.remember(
  'agent-123',
  'User purchased Pro plan',
  {
    metadata: {
      category: 'billing',
      eventType: 'purchase',
      plan: 'pro',
      amount: 99.00,
      currency: 'USD'
    }
  }
);
```

### Error Handling

Always handle errors gracefully:

```typescript
import { KyrosClient, KyrosError } from '@kyros/sdk';

const client = new KyrosClient({ apiKey: 'your-key' });

try {
  const response = await client.remember(
    'agent-123',
    'Important information'
  );
} catch (error) {
  if (error instanceof KyrosError) {
    // Log error and continue
    console.error('Failed to store memory:', error.message);
    // Implement fallback behavior
  } else {
    throw error;
  }
}
```

### TypeScript Types

The SDK is fully typed for excellent IDE support:

```typescript
import type {
  RememberOptions,
  RememberResponse,
  RecallOptions,
  RecallResponse,
  Memory,
  FactResult,
  ProcedureResponse,
  Procedure
} from '@kyros/sdk';

// Type-safe options
const options: RememberOptions = {
  contentType: 'text',
  importance: 0.8,
  metadata: {
    category: 'sales'
  }
};

// Type-safe response handling
const response: RememberResponse = await client.remember(
  'agent-123',
  'content',
  options
);
```

## Links

- [GitHub Repository](https://github.com/Kyros-494/kyros-ai)
- [npm Package](https://www.npmjs.com/package/@kyros/sdk)
- [API Documentation](https://docs.kyros.ai)
- [Issue Tracker](https://github.com/Kyros-494/kyros-ai/issues)
