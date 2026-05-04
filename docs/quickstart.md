# Quickstart Guide

Get up and running with Kyros in 5 minutes.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker**: 20.10+ and Docker Compose 2.0+
- **Python**: 3.11+ (for Python SDK) OR
- **Node.js**: 20+ (for TypeScript SDK)
- **Git**: For cloning the repository (optional)

## Step 1: Start Kyros Server (2 minutes)

### Option A: Using Docker Compose (Recommended)

1. Clone the repository or download docker-compose.yml:

```bash
git clone https://github.com/Kyros-494/kyros-ai.git
cd kyros-ai
```

2. Create environment file:

```bash
cp .env.example .env
```

3. Start the services:

```bash
docker compose up -d
```

4. Verify the server is running:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

### Option B: Using Pre-built Docker Image

```bash
docker run -d \
  --name kyros-server \
  -p 8000:8000 \
  -e KYROS_DATABASE_URL=postgresql://... \
  -e KYROS_REDIS_URL=redis://... \
  kyros/kyros-server:latest
```

## Step 2: Install SDK (1 minute)

Choose your preferred language:

### Python

```bash
pip install kyros-sdk
```

### TypeScript

```bash
npm install kyros-sdk
```

## Step 3: Initialize Client (1 minute)

### Python

Create a file `example.py`:

```python
from kyros import KyrosClient

# Initialize client
client = KyrosClient(
    api_key="test-api-key",  # Use your API key
    base_url="http://localhost:8000"
)

print("Kyros client initialized successfully!")
```

### TypeScript

Create a file `example.ts`:

```typescript
import { KyrosClient } from 'kyros-sdk';

// Initialize client
const client = new KyrosClient({
  apiKey: 'test-api-key',  // Use your API key
  baseUrl: 'http://localhost:8000'
});

console.log('Kyros client initialized successfully!');
```

## Step 4: Store Your First Memory (1 minute)

### Python

```python
from kyros import KyrosClient

client = KyrosClient(
    api_key="test-api-key",
    base_url="http://localhost:8000"
)

# Store a memory
response = client.remember(
    agent_id="my-agent",
    content="User prefers dark mode and wants email notifications",
    importance=0.8,
    metadata={"category": "preferences"}
)

print(f"Memory stored with ID: {response.memory_id}")
```

### TypeScript

```typescript
import { KyrosClient } from 'kyros-sdk';

const client = new KyrosClient({
  apiKey: 'test-api-key',
  baseUrl: 'http://localhost:8000'
});

// Store a memory
const response = await client.remember(
  'my-agent',
  'User prefers dark mode and wants email notifications',
  {
    importance: 0.8,
    metadata: { category: 'preferences' }
  }
);

console.log(`Memory stored with ID: ${response.memory_id}`);
```

## Step 5: Recall Memories (1 minute)

### Python

```python
# Recall memories
results = client.recall(
    agent_id="my-agent",
    query="What are the user's preferences?",
    k=5
)

print(f"Found {len(results.results)} memories:")
for memory in results.results:
    print(f"- {memory.content} (score: {memory.relevance_score:.2f})")
```

### TypeScript

```typescript
// Recall memories
const results = await client.recall(
  'my-agent',
  "What are the user's preferences?",
  { k: 5 }
);

console.log(`Found ${results.results.length} memories:`);
results.results.forEach(memory => {
  console.log(`- ${memory.content} (score: ${memory.relevance_score.toFixed(2)})`);
});
```

## Complete Example

### Python

```python
from kyros import KyrosClient

# Initialize client
client = KyrosClient(
    api_key="test-api-key",
    base_url="http://localhost:8000"
)

# Store multiple memories
memories = [
    "User prefers dark mode",
    "User wants email notifications",
    "User is interested in AI and machine learning",
    "User's timezone is UTC-5"
]

for content in memories:
    response = client.remember(
        agent_id="my-agent",
        content=content,
        importance=0.7
    )
    print(f"Stored: {content}")

# Recall relevant memories
queries = [
    "What are the user's preferences?",
    "What is the user interested in?",
    "What is the user's timezone?"
]

for query in queries:
    print(f"\nQuery: {query}")
    results = client.recall(
        agent_id="my-agent",
        query=query,
        k=3
    )
    for memory in results.results:
        print(f"  - {memory.content} (score: {memory.relevance_score:.2f})")
```

### TypeScript

```typescript
import { KyrosClient } from 'kyros-sdk';

async function main() {
  // Initialize client
  const client = new KyrosClient({
    apiKey: 'test-api-key',
    baseUrl: 'http://localhost:8000'
  });

  // Store multiple memories
  const memories = [
    'User prefers dark mode',
    'User wants email notifications',
    'User is interested in AI and machine learning',
    "User's timezone is UTC-5"
  ];

  for (const content of memories) {
    const response = await client.remember('my-agent', content, {
      importance: 0.7
    });
    console.log(`Stored: ${content}`);
  }

  // Recall relevant memories
  const queries = [
    "What are the user's preferences?",
    'What is the user interested in?',
    "What is the user's timezone?"
  ];

  for (const query of queries) {
    console.log(`\nQuery: ${query}`);
    const results = await client.recall('my-agent', query, { k: 3 });
    results.results.forEach(memory => {
      console.log(`  - ${memory.content} (score: ${memory.relevance_score.toFixed(2)})`);
    });
  }
}

main();
```

## Next Steps

### Explore Memory Types

**Episodic Memory** (Conversations)
```python
# Store conversation
client.remember(
    agent_id="my-agent",
    content="User: How do I reset my password?",
    role="user",
    session_id="session-123"
)
```

**Semantic Memory** (Facts)
```python
# Store fact
client.store_fact(
    agent_id="my-agent",
    subject="user",
    predicate="email",
    value="user@example.com",
    confidence=1.0
)
```

**Procedural Memory** (Workflows)
```python
# Store procedure
client.store_procedure(
    agent_id="my-agent",
    name="Send Email",
    description="Send an email to a recipient",
    task_type="communication",
    steps=[
        {"action": "compose", "params": {"to": "user@example.com"}},
        {"action": "send"}
    ]
)
```

### Framework Integration

**LangChain**
```python
from kyros.integrations.langchain import KyrosChatMemory
from langchain.chains import ConversationChain
from langchain.llms import OpenAI

memory = KyrosChatMemory(agent_id="my-agent", api_key="test-api-key")
chain = ConversationChain(llm=OpenAI(), memory=memory)
response = chain.run("Hello!")
```

**LlamaIndex**
```python
from kyros.integrations.llama_index import KyrosMemory
from llama_index.core.chat_engine import SimpleChatEngine

memory = KyrosMemory(agent_id="my-agent", api_key="test-api-key")
engine = SimpleChatEngine.from_defaults(memory=memory)
response = engine.chat("Hello!")
```

### Advanced Features

**Causal Reasoning**
```python
# Get causal explanation
explanation = client.explain(
    agent_id="my-agent",
    memory_id="mem-123",
    max_depth=3
)
```

**Integrity Verification**
```python
# Verify memory integrity
proof = client.get_memory_proof(memory_id="mem-123")
audit = client.audit_integrity(agent_id="my-agent")
```

**Memory Decay**
```python
# Get staleness report
report = client.get_staleness_report(agent_id="my-agent")
```

## Troubleshooting

### Server Not Starting

**Problem**: Docker Compose fails to start

**Solution**:
1. Check Docker is running: `docker ps`
2. Check logs: `docker compose logs kyros-server`
3. Verify .env file exists and is configured
4. Ensure ports 8000, 5433, 6379 are available

### Connection Refused

**Problem**: Cannot connect to server

**Solution**:
1. Verify server is running: `curl http://localhost:8000/health`
2. Check firewall settings
3. Verify base_url in client configuration
4. Check Docker network: `docker network ls`

### Authentication Failed

**Problem**: API key authentication fails

**Solution**:
1. Verify API key is correct
2. Check server logs for authentication errors
3. Ensure API key is not expired
4. For testing, use "test-api-key"

### Import Errors

**Problem**: Cannot import kyros module

**Solution**:
1. Verify SDK is installed: `pip list | grep kyros` or `npm list kyros-sdk`
2. Check Python/Node version compatibility
3. Reinstall SDK: `pip install --upgrade kyros-sdk`
4. Check virtual environment is activated

### Memory Not Found

**Problem**: Recall returns no results

**Solution**:
1. Verify memories were stored successfully
2. Check agent_id matches
3. Try broader query
4. Reduce min_relevance threshold
5. Increase k (number of results)

## Common Issues

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
docker compose -f docker-compose.yml -e KYROS_PORT=8001 up -d
```

### Database Connection Failed

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Check connection string
echo $KYROS_DATABASE_URL

# Test connection
psql $KYROS_DATABASE_URL -c "SELECT 1;"
```

### Redis Connection Failed

```bash
# Check Redis is running
docker compose ps redis

# Test connection
redis-cli -u $KYROS_REDIS_URL ping
```

## API Documentation

For complete API documentation, visit:
- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc
- OpenAPI spec: http://localhost:8000/openapi.json

## Additional Resources

- **Concepts**: Learn about memory types and features
- **Python SDK**: Complete Python API reference
- **TypeScript SDK**: Complete TypeScript API reference
- **Self-Hosting**: Deploy Kyros on your infrastructure
- **Configuration**: Environment variables and settings
- **Architecture**: System design and internals

## Getting Help

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **Documentation**: Browse complete documentation
- **Examples**: View sample applications

## Conclusion

You now have Kyros running and have stored and recalled your first memories. Explore the documentation to learn about advanced features like semantic memory, procedural memory, causal reasoning, and framework integrations.

Happy building!
