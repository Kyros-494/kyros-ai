# @kyros/sdk

> TypeScript SDK for Kyros — persistent memory for AI agents.

## Install

```bash
npm install @kyros/sdk
```

## Quickstart

```typescript
import { KyrosClient } from '@kyros/sdk';

const client = new KyrosClient({ apiKey: 'mk_live_...' });

// Store a memory
await client.remember('my-agent', 'User prefers TypeScript and dark mode');

// Recall by meaning
const results = await client.recall('my-agent', 'What does the user prefer?');
console.log(results.results[0].content);
// → "User prefers TypeScript and dark mode"

// Store a fact (auto-resolves contradictions)
await client.storeFact('my-agent', 'user', 'language', 'TypeScript');
```

## Configuration

| Option | Env Variable | Default |
|--------|-------------|---------|
| `apiKey` | `KYROS_API_KEY` | Required |
| `baseUrl` | `KYROS_BASE_URL` | `https://api.kyros.ai` |
| `timeout` | — | `30000` ms |

## Full Documentation

See [docs/typescript-sdk.md](../../docs/typescript-sdk.md) for the complete API reference.

## License

Apache 2.0
