# Kyros AI Quick Start Guide

This guide describes how to start the Kyros Persistent Memory engine, verify service health, and perform core memory operations (episodic, semantic, and procedural) using our SDKs and REST APIs.

---

## 1. Initializing Services

Start the core infrastructure services (PostgreSQL with pgvector, Redis, and the FastAPI server) using Docker Compose:

```bash
# Initialize and launch all containers
docker compose up -d

# Verify container health status
docker compose ps
```

Expected status output:
*   `postgres` (Healthy - Port 5433)
*   `redis` (Healthy - Port 6379)
*   `kyros-server` (Healthy - Port 8000)

---

## 2. Developer Dashboard and Default Credentials

Kyros implements zero-configuration auto-bootstrapping during development mode:
*   **Default API Key:** `mk_live_default_dev_key_123456`
*   **Developer Dashboard:** [http://localhost:8000/dashboard](http://localhost:8000/dashboard)

Access the dashboard settings page (via the gear icon) and supply the default development API key to view episodic memory listings, semantic belief networks, and audit logs.

---

## 3. Basic SDK Usage

### Python

Install the official Python SDK:
```bash
pip install kyros-sdk
```

Configure a client and execute basic operations:
```python
from kyros import KyrosClient

# Configure the client
client = KyrosClient(
    api_key="mk_live_default_dev_key_123456",
    base_url="http://localhost:8000"
)

# Store an episodic memory turn
client.remember(
    agent_id="finance-bot",
    content="User requested a summary of Q3 financial assets",
    importance=0.8
)

# Retrieve semantically related memories
results = client.recall(
    agent_id="finance-bot",
    query="What does the user want to see?"
)

print(results.results[0].content)
```

### TypeScript

Install the official TypeScript SDK:
```bash
npm install @kyros/sdk
```

Configure and initialize the client:
```typescript
import { KyrosClient } from '@kyros/sdk';

const client = new KyrosClient({
  apiKey: 'mk_live_default_dev_key_123456',
  baseUrl: 'http://localhost:8000'
});

// Commit experience to memory
await client.remember('finance-bot', 'User requested a summary of Q3 financial assets');

// Recall context
const results = await client.recall('finance-bot', 'What does the user want to see?');
console.log(results.results[0].content);
```

### Direct REST HTTP API

```bash
# Write episodic memory
curl -X POST http://localhost:8000/v1/memory/episodic/remember \
  -H "Authorization: Bearer mk_live_default_dev_key_123456" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "support-agent",
    "content": "User reported billing anomaly with invoice #1204",
    "importance": 0.9
  }'

# Recall episodic memories
curl -X POST http://localhost:8000/v1/memory/episodic/recall \
  -H "Authorization: Bearer mk_live_default_dev_key_123456" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "support-agent",
    "query": "billing issues"
  }'
```

---

## 4. Framework Integrations

### LangChain (Python)

```python
from kyros.integrations.langchain import KyrosChatMemory
from langchain.chains import ConversationChain
from langchain.llms import OpenAI

# Initialize Kyros memory component with automatic environment discovery
memory = KyrosChatMemory(
    agent_id="langchain-chat-agent",
    api_key="mk_live_default_dev_key_123456",
    base_url="http://localhost:8000"
)

chain = ConversationChain(
    llm=OpenAI(),
    memory=memory
)

response = chain.run("Hello, my billing email is test@company.com")
```

### Vercel AI SDK (TypeScript)

```typescript
import { KyrosClient } from '@kyros/sdk';
import { createKyrosTools } from '@kyros/sdk/integrations/vercel';
import { generateText } from 'ai';
import { openai } from '@ai-sdk/openai';

const kyros = new KyrosClient({
  apiKey: 'mk_live_default_dev_key_123456',
  baseUrl: 'http://localhost:8000'
});

const tools = createKyrosTools(kyros, 'vercel-agent');

const result = await generateText({
  model: openai('gpt-4'),
  tools,
  prompt: 'Record that the user prefers typescript code generation'
});
```

---

## 5. Model Context Protocol (MCP) Server Setup

Integrate Kyros memory tools directly into AI IDE workspaces (Cursor, Windsurf, Cline) by launching the built-in MCP server:

```bash
# Start the stdio Model Context Protocol (MCP) server
kyros mcp start
```

Once running, the IDE agent can query tools like `remember`, `recall`, and `store_fact` to persist context across development sessions.

---

## 6. Dynamic Embedding Model Overrides

Specify target embedding models on a per-request basis by sending the `X-Embedding-Model` header:

```bash
# Recall using OpenAI text-embedding-3-small
curl -X POST http://localhost:8000/v1/memory/episodic/recall \
  -H "Authorization: Bearer mk_live_default_dev_key_123456" \
  -H "X-Embedding-Model: openai/text-embedding-3-small" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "support-agent",
    "query": "billing issues"
  }'
```

---

## 7. Administrative CLI Commands

Install the command line interface locally:
```bash
pip install -e sdks/python
```

Execute management operations:
```bash
# Verify system liveness
kyros status

# Perform a cryptographic Merkle tree audit on memories
kyros audit --agent support-agent

# Export data for compliance or migration
kyros summarize --agent support-agent
```
