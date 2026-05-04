# Quick Start - Use Kyros in 5 Minutes

Get Kyros running and start using it with your AI agents right now.

## Step 1: Start Kyros (30 seconds)

```bash
# Start all services
docker compose up -d

# Wait for services to start (30 seconds)
# Check status
docker compose ps
```

You should see:
- ✓ postgres (running)
- ✓ redis (running)
- ✓ kyros-server (running)

## Step 2: Create Your API Key (1 minute)

```bash
# Access the database
docker compose exec postgres psql -U kyros -d kyros

# Create your API key (copy-paste this entire block)
INSERT INTO tenants (tenant_id, name, api_key_hash, tier, created_at)
VALUES (
  'my-tenant',
  'My Organization',
  encode(digest('my_secret_api_key_12345', 'sha256'), 'hex'),
  'pro',
  NOW()
);

# Exit
\q
```

**Your API Key:** `my_secret_api_key_12345`

(Change this to something secure for production!)

## Step 3: Use Kyros

### Option A: Python (Recommended)

```bash
# Install SDK
pip install kyros-sdk
```

```python
from kyros import KyrosClient

# Initialize
client = KyrosClient(
    api_key="my_secret_api_key_12345",
    base_url="http://localhost:8000"
)

# Store a memory
client.remember(
    agent_id="my-agent",
    content="User loves Python and wants to build AI agents",
    importance=0.9
)

# Recall memories
results = client.recall(
    agent_id="my-agent",
    query="What does the user want to build?"
)

print(results.results[0].content)
# → "User loves Python and wants to build AI agents"
```

### Option B: TypeScript

```bash
# Install SDK
npm install @kyros/sdk
```

```typescript
import { KyrosClient } from '@kyros/sdk';

const client = new KyrosClient({
  apiKey: 'my_secret_api_key_12345',
  baseUrl: 'http://localhost:8000'
});

// Store a memory
await client.remember(
  'my-agent',
  'User loves TypeScript and wants to build AI agents'
);

// Recall memories
const results = await client.recall(
  'my-agent',
  'What does the user want to build?'
);

console.log(results.results[0].content);
// → "User loves TypeScript and wants to build AI agents"
```

### Option C: Direct HTTP API

```bash
# Store a memory
curl -X POST http://localhost:8000/v1/memory/episodic/remember \
  -H "Authorization: Bearer my_secret_api_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "my-agent",
    "content": "User wants to build AI agents",
    "importance": 0.9
  }'

# Recall memories
curl -X POST http://localhost:8000/v1/memory/episodic/recall \
  -H "Authorization: Bearer my_secret_api_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "my-agent",
    "query": "What does the user want?"
  }'
```

## Real-World Example: Chatbot with Memory

### Python

```python
from kyros import KyrosClient
import openai

# Initialize
kyros = KyrosClient(
    api_key="my_secret_api_key_12345",
    base_url="http://localhost:8000"
)
openai.api_key = "your-openai-key"

def chat(user_id: str, message: str) -> str:
    # Store user message
    kyros.remember(
        agent_id=user_id,
        content=f"User: {message}",
        role="user"
    )
    
    # Recall relevant context
    context = kyros.recall(
        agent_id=user_id,
        query=message,
        k=5
    )
    
    # Build context for LLM
    context_text = "\n".join([
        f"- {m.content}" 
        for m in context.results
    ])
    
    # Get LLM response
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": f"Context:\n{context_text}"},
            {"role": "user", "content": message}
        ]
    )
    
    reply = response.choices[0].message.content
    
    # Store assistant response
    kyros.remember(
        agent_id=user_id,
        content=f"Assistant: {reply}",
        role="assistant"
    )
    
    return reply

# Use it
response = chat("user-123", "What's my favorite programming language?")
print(response)
```

### TypeScript

```typescript
import { KyrosClient } from '@kyros/sdk';
import OpenAI from 'openai';

const kyros = new KyrosClient({
  apiKey: 'my_secret_api_key_12345',
  baseUrl: 'http://localhost:8000'
});

const openai = new OpenAI({ apiKey: 'your-openai-key' });

async function chat(userId: string, message: string): Promise<string> {
  // Store user message
  await kyros.remember(userId, `User: ${message}`, { role: 'user' });
  
  // Recall relevant context
  const context = await kyros.recall(userId, message, { k: 5 });
  
  // Build context for LLM
  const contextText = context.results
    .map(m => `- ${m.content}`)
    .join('\n');
  
  // Get LLM response
  const response = await openai.chat.completions.create({
    model: 'gpt-4',
    messages: [
      { role: 'system', content: `Context:\n${contextText}` },
      { role: 'user', content: message }
    ]
  });
  
  const reply = response.choices[0].message.content!;
  
  // Store assistant response
  await kyros.remember(userId, `Assistant: ${reply}`, { role: 'assistant' });
  
  return reply;
}

// Use it
const response = await chat('user-123', "What's my favorite programming language?");
console.log(response);
```

## Integration with Popular Frameworks

### LangChain

```python
from kyros.integrations.langchain import KyrosChatMemory
from langchain.chains import ConversationChain
from langchain.llms import OpenAI

memory = KyrosChatMemory(
    agent_id="my-agent",
    api_key="my_secret_api_key_12345",
    base_url="http://localhost:8000"
)

chain = ConversationChain(
    llm=OpenAI(),
    memory=memory
)

# Use it
response = chain.run("Hello! I love Python.")
print(response)

# Memory is automatically stored and recalled!
```

### Vercel AI SDK

```typescript
import { KyrosClient } from '@kyros/sdk';
import { createKyrosTools } from '@kyros/sdk/integrations/vercel';
import { generateText } from 'ai';
import { openai } from '@ai-sdk/openai';

const kyros = new KyrosClient({
  apiKey: 'my_secret_api_key_12345',
  baseUrl: 'http://localhost:8000'
});

const tools = createKyrosTools(kyros, 'my-agent');

const result = await generateText({
  model: openai('gpt-4'),
  tools,
  prompt: 'Remember that I prefer TypeScript'
});

console.log(result.text);
// Memory is automatically stored!
```

## View Your Data

### API Documentation (Interactive)

Open in browser: http://localhost:8000/docs

- Try all endpoints
- See request/response formats
- Test directly in browser

### Database

```bash
# View all memories
docker compose exec postgres psql -U kyros -d kyros -c "
  SELECT agent_id, content, created_at 
  FROM episodic_memories 
  ORDER BY created_at DESC 
  LIMIT 10;
"

# Count memories per agent
docker compose exec postgres psql -U kyros -d kyros -c "
  SELECT agent_id, COUNT(*) as memory_count
  FROM episodic_memories
  GROUP BY agent_id;
"
```

## Common Use Cases

### 1. Customer Support Agent

```python
# Store customer information
kyros.store_fact(
    agent_id="customer-123",
    subject="customer",
    predicate="subscription",
    value="Pro Plan",
    confidence=1.0
)

# Store support history
kyros.remember(
    agent_id="customer-123",
    content="Customer reported login issue, resolved by password reset",
    importance=0.8,
    metadata={"category": "support", "status": "resolved"}
)

# Recall when customer contacts again
history = kyros.recall(
    agent_id="customer-123",
    query="previous issues",
    k=5
)
```

### 2. Personal Assistant

```python
# Store preferences
kyros.store_fact("user-456", "user", "prefers", "morning meetings")
kyros.store_fact("user-456", "user", "timezone", "PST")

# Store tasks
kyros.remember(
    agent_id="user-456",
    content="User wants to schedule dentist appointment next week",
    importance=0.9,
    metadata={"type": "task", "due": "next_week"}
)

# Recall tasks
tasks = kyros.recall(
    agent_id="user-456",
    query="upcoming tasks",
    k=10
)
```

### 3. Code Assistant

```python
# Store coding preferences
kyros.store_fact("dev-789", "developer", "prefers", "TypeScript")
kyros.store_fact("dev-789", "developer", "uses", "React")

# Store procedures
kyros.store_procedure(
    agent_id="dev-789",
    name="Deploy to Production",
    description="Deploy application to production environment",
    task_type="deployment",
    steps=[
        {"action": "run_tests"},
        {"action": "build"},
        {"action": "deploy_staging"},
        {"action": "verify_staging"},
        {"action": "deploy_production"}
    ]
)

# Match procedures
matches = kyros.match_procedure(
    agent_id="dev-789",
    task_description="I need to deploy the app",
    k=5
)
```

## Production Deployment

When you're ready for production:

1. **Change API Key:**
   ```bash
   # Generate secure key
   openssl rand -hex 32
   ```

2. **Update .env:**
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

3. **Deploy:**
   - See `docs/self-hosting.md` for full deployment guide
   - Kubernetes, Docker Swarm, or cloud providers
   - SSL/TLS, monitoring, backups

## Need Help?

- **API Docs:** http://localhost:8000/docs
- **Python SDK:** `docs/python-sdk.md`
- **TypeScript SDK:** `docs/typescript-sdk.md`
- **Full Guide:** `docs/quickstart.md`
- **Architecture:** `docs/architecture.md`
- **Issues:** https://github.com/Kyros-494/kyros-ai/issues

## Stop Services

```bash
# Stop services
docker compose down

# Stop and remove data
docker compose down -v
```

---

**You're ready to build AI agents with persistent memory!** 🚀
