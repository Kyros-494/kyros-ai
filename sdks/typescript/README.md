# Kyros TypeScript SDK

Official TypeScript/JavaScript SDK for Kyros — Persistent Memory for AI Agents.

The Kyros TypeScript SDK provides a type-safe, native interface to the Kyros Memory API, implemented using the standard Fetch API. It allows you to store, recall, and manage persistent episodic, semantic, and procedural memories for autonomous agents.

---

## Quick Start

### Installation

```bash
npm install @kyros.494/sdk
```

### Basic Usage

```typescript
import { KyrosClient } from '@kyros.494/sdk';

// Initialize the client
const client = new KyrosClient({
  apiKey: 'your-api-key',
  baseUrl: 'http://localhost:8000'
});

async function main() {
  // Store an episodic event
  const response = await client.remember('agent-123', 'User prefers TypeScript and dark mode', {
    importance: 0.8
  });

  // Recall memories using semantic search
  const results = await client.recall('agent-123', 'What are the user\'s preferences?');

  for (const memory of results.results) {
    console.log(`${memory.content} (score: ${memory.relevance_score})`);
  }
}

main().catch(console.error);
```

---

## Configuration

Initialize the client with configuration parameters or environment variables:

| Option | Environment Variable | Default | Description |
|--------|----------------------|---------|-------------|
| `apiKey` | `KYROS_API_KEY` | Required | API key for authentication |
| `baseUrl` | `KYROS_BASE_URL` | `https://api.kyros.ai` | Target server URL |
| `timeout` | — | `30000` (ms) | Request timeout limit |

```typescript
// Option 1: Pass config directly
const client = new KyrosClient({
  apiKey: 'your-api-key',
  baseUrl: 'http://localhost:8000',
  timeout: 15000
});

// Option 2: Fallback to environment variables
// Make sure KYROS_API_KEY is defined in process.env
const client = new KyrosClient();
```

---

## Core Features

### Episodic Memory

Episodic memory stores chronological conversation histories, actions, and observations.

```typescript
// Store a memory
const response = await client.remember('agent-123', 'User asked about corporate pricing tiers', {
  contentType: 'text',
  role: 'user',
  sessionId: 'session-456',
  importance: 0.7,
  metadata: { category: 'sales' }
});

// Recall memories
const results = await client.recall('agent-123', 'What corporate queries did we receive?', {
  k: 5,
  minRelevance: 0.5
});

// Delete a memory
await client.forget('agent-123', 'memory-uuid-here');
```

### Semantic Memory

Semantic memory stores structured facts as subject-predicate-object triples and updates confidence scores automatically when conflicts arise.

```typescript
// Store a semantic fact
const fact = await client.storeFact(
  'agent-123',
  'user',
  'prefers',
  'TypeScript',
  {
    confidence: 0.95,
    sourceType: 'explicit'
  }
);

// Query facts
const results = await client.queryFacts('agent-123', 'user language preferences', 10);
```

### Procedural Memory

Procedural memory stores agent skills, workflows, and procedures, calculating matching execution patterns based on task descriptions.

```typescript
// Store a procedure workflow
const procedure = await client.storeProcedure(
  'agent-123',
  'Deploy Web App',
  'Standard procedure to deploy static React applications',
  'deployment',
  [
    { action: 'install', params: { cmd: 'npm install' } },
    { action: 'build', params: { cmd: 'npm run build' } },
    { action: 'sync', params: { bucket: 's3://app' } }
  ]
);

// Match execution pattern
const matches = await client.matchProcedure(
  'agent-123',
  'I need to deploy our new web interface to production',
  { k: 3 }
);

// Report execution outcome
const outcome = await client.reportOutcome('proc-uuid-here', true, {
  durationMs: 42000
});
```

### Unified Search

Query across episodic, semantic, and procedural memory stores simultaneously.

```typescript
const results = await client.search('agent-123', 'deployment configurations', 10);
```

---

## Advanced Features

### Causal Reasoning

Retrieve parent-child dependency chains to audit reasoning patterns.

```typescript
const explanation = await client.explain('agent-123', 'memory-uuid-here', 3);
```

### Integrity Verification

Audit cryptographic signatures of the memory ledger.

```typescript
// Get proof block
const proof = await client.getMemoryProof('memory-uuid-here');

// Audit agent integrity tree
const audit = await client.auditIntegrity('agent-123');
```

### Temporal Memory Decay

Inspect forgetting curves and configure decay coefficients.

```typescript
// Get staleness details
const report = await client.getStalenessReport('agent-123');

// Get decay parameters
const rates = await client.getDecayRates();

// Modify decay parameters
await client.setDecayRates({ conversation: 0.15, facts: 0.02 });
```

---

## Error Handling

All client methods throw typed errors extending `KyrosError` for robust validation:

```typescript
import {
  KyrosClient,
  AuthenticationError,
  RateLimitError,
  NotFoundError,
  ValidationError,
  ServerError
} from '@kyros.494/sdk';

const client = new KyrosClient({ apiKey: 'invalid-key' });

try {
  await client.remember('agent-123', 'test');
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.error('Invalid credentials provided:', error.message);
  } else if (error instanceof RateLimitError) {
    console.error(`Rate limited. Limit: ${error.limit}, Reset: ${error.reset}`);
  } else if (error instanceof ValidationError) {
    console.error('Invalid request body:', error.message);
  } else if (error instanceof ServerError) {
    console.error('API server returned error code:', error.status);
  } else {
    console.error('Unexpected error:', error);
  }
}
```

---

## License

This SDK is licensed under the Apache License 2.0. See the root LICENSE file for details.
