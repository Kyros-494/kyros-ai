# Kyros API Testing Guide

Complete guide to testing the Kyros Memory API with real requests.

## Quick Start

### Step 1: Start the Server

```bash
# Start all services (PostgreSQL, Redis, Kyros server)
docker compose up -d

# Check if services are running
docker compose ps

# View server logs
docker compose logs -f kyros-server
```

### Step 2: Verify Server is Running

```bash
# Health check
curl http://localhost:8000/health

# Readiness check (DB + Redis)
curl http://localhost:8000/health/ready

# View API documentation
open http://localhost:8000/docs
```

### Step 3: Create API Key

You need to create a tenant and API key in the database:

```bash
# Access PostgreSQL
docker compose exec postgres psql -U kyros -d kyros

# Create tenant with API key
INSERT INTO tenants (tenant_id, name, api_key_hash, tier, created_at)
VALUES (
  'tenant-001',
  'Test Organization',
  encode(digest('test_key_12345', 'sha256'), 'hex'),
  'pro',
  NOW()
);

# Verify tenant was created
SELECT tenant_id, name, tier FROM tenants;

# Exit psql
\q
```

**Your API Key:** `test_key_12345`

## Testing with cURL

### 1. Store an Episodic Memory

```bash
curl -X POST http://localhost:8000/v1/memory/episodic/remember \
  -H "Authorization: Bearer test_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-001",
    "content": "User prefers dark mode and TypeScript",
    "importance": 0.8,
    "metadata": {
      "category": "preferences",
      "language": "en"
    }
  }'
```

### 2. Recall Memories

```bash
curl -X POST http://localhost:8000/v1/memory/episodic/recall \
  -H "Authorization: Bearer test_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-001",
    "query": "What does the user prefer?",
    "k": 5
  }'
```

### 3. Store a Semantic Fact

```bash
curl -X POST http://localhost:8000/v1/memory/semantic/facts \
  -H "Authorization: Bearer test_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-001",
    "subject": "user",
    "predicate": "prefers",
    "value": "dark mode",
    "confidence": 0.9
  }'
```

### 4. Query Semantic Facts

```bash
curl -X POST http://localhost:8000/v1/memory/semantic/query \
  -H "Authorization: Bearer test_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-001",
    "query": "user preferences",
    "k": 10
  }'
```

### 5. Store a Procedure

```bash
curl -X POST http://localhost:8000/v1/memory/procedural/store \
  -H "Authorization: Bearer test_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-001",
    "name": "Send Email",
    "description": "Send an email to a recipient",
    "task_type": "communication",
    "steps": [
      {"action": "validate_email", "params": {"field": "to"}},
      {"action": "compose_message"},
      {"action": "send"}
    ]
  }'
```

### 6. Match Procedures

```bash
curl -X POST http://localhost:8000/v1/memory/procedural/match \
  -H "Authorization: Bearer test_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-001",
    "task_description": "I need to send an email",
    "k": 5
  }'
```

### 7. Unified Search

```bash
curl -X POST http://localhost:8000/v1/search/unified \
  -H "Authorization: Bearer test_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-001",
    "query": "email preferences",
    "k": 10
  }'
```

## Testing with Python SDK

### Install SDK

```bash
pip install kyros-sdk
```

### Test Script

Create `test_api.py`:

```python
from kyros import KyrosClient

# Initialize client
client = KyrosClient(
    api_key="test_key_12345",
    base_url="http://localhost:8000"
)

# Test 1: Store a memory
print("Test 1: Storing memory...")
response = client.remember(
    agent_id="agent-001",
    content="User loves Python and AI",
    importance=0.9,
    metadata={"category": "interests"}
)
print(f"✓ Memory stored: {response.memory_id}")

# Test 2: Recall memories
print("\nTest 2: Recalling memories...")
results = client.recall(
    agent_id="agent-001",
    query="What does the user love?",
    k=5
)
print(f"✓ Found {len(results.results)} memories:")
for memory in results.results:
    print(f"  - {memory.content} (score: {memory.relevance_score:.2f})")

# Test 3: Store a fact
print("\nTest 3: Storing fact...")
fact = client.store_fact(
    agent_id="agent-001",
    subject="user",
    predicate="loves",
    value="Python",
    confidence=0.95
)
print(f"✓ Fact stored: {fact.fact_id}")

# Test 4: Query facts
print("\nTest 4: Querying facts...")
facts = client.query_facts(
    agent_id="agent-001",
    query="user interests",
    k=10
)
print(f"✓ Found {len(facts.results)} facts:")
for fact in facts.results:
    print(f"  - {fact.subject} {fact.predicate} {fact.value}")

# Test 5: Store procedure
print("\nTest 5: Storing procedure...")
procedure = client.store_procedure(
    agent_id="agent-001",
    name="Code Review",
    description="Review code for quality and security",
    task_type="development",
    steps=[
        {"action": "check_syntax"},
        {"action": "check_security"},
        {"action": "check_performance"},
        {"action": "provide_feedback"}
    ]
)
print(f"✓ Procedure stored: {procedure.procedure_id}")

# Test 6: Search everything
print("\nTest 6: Unified search...")
results = client.search(
    agent_id="agent-001",
    query="Python development",
    k=10
)
print(f"✓ Found {len(results.results)} results across all memory types")

print("\n✅ All tests passed!")
```

Run the test:

```bash
python test_api.py
```

## Testing with TypeScript SDK

### Install SDK

```bash
npm install @kyros/sdk
```

### Test Script

Create `test-api.ts`:

```typescript
import { KyrosClient } from '@kyros/sdk';

async function testAPI() {
  // Initialize client
  const client = new KyrosClient({
    apiKey: 'test_key_12345',
    baseUrl: 'http://localhost:8000'
  });

  // Test 1: Store a memory
  console.log('Test 1: Storing memory...');
  const memory = await client.remember(
    'agent-001',
    'User loves TypeScript and React',
    {
      importance: 0.9,
      metadata: { category: 'interests' }
    }
  );
  console.log(`✓ Memory stored: ${memory.memoryId}`);

  // Test 2: Recall memories
  console.log('\nTest 2: Recalling memories...');
  const results = await client.recall(
    'agent-001',
    'What does the user love?',
    { k: 5 }
  );
  console.log(`✓ Found ${results.results.length} memories:`);
  for (const mem of results.results) {
    console.log(`  - ${mem.content} (score: ${mem.relevanceScore.toFixed(2)})`);
  }

  // Test 3: Store a fact
  console.log('\nTest 3: Storing fact...');
  const fact = await client.storeFact(
    'agent-001',
    'user',
    'loves',
    'TypeScript',
    { confidence: 0.95 }
  );
  console.log(`✓ Fact stored: ${fact.factId}`);

  // Test 4: Query facts
  console.log('\nTest 4: Querying facts...');
  const facts = await client.queryFacts(
    'agent-001',
    'user interests',
    10
  );
  console.log(`✓ Found ${facts.results.length} facts:`);
  for (const f of facts.results) {
    console.log(`  - ${f.subject} ${f.predicate} ${f.value}`);
  }

  // Test 5: Store procedure
  console.log('\nTest 5: Storing procedure...');
  const procedure = await client.storeProcedure(
    'agent-001',
    'Deploy App',
    'Deploy application to production',
    'deployment',
    [
      { action: 'run_tests' },
      { action: 'build' },
      { action: 'deploy' },
      { action: 'verify' }
    ]
  );
  console.log(`✓ Procedure stored: ${procedure.procedureId}`);

  // Test 6: Search everything
  console.log('\nTest 6: Unified search...');
  const searchResults = await client.search(
    'agent-001',
    'TypeScript development',
    10
  );
  console.log(`✓ Found ${searchResults.results.length} results across all memory types`);

  console.log('\n✅ All tests passed!');
}

testAPI().catch(console.error);
```

Run the test:

```bash
npx tsx test-api.ts
```

## Testing with Postman

### Import Collection

1. Open Postman
2. Click "Import"
3. Create a new collection called "Kyros API"
4. Add these requests:

#### Environment Variables

Create environment with:
- `base_url`: `http://localhost:8000`
- `api_key`: `test_key_12345`
- `agent_id`: `agent-001`

#### Request 1: Store Memory

```
POST {{base_url}}/v1/memory/episodic/remember
Headers:
  Authorization: Bearer {{api_key}}
  Content-Type: application/json
Body:
{
  "agent_id": "{{agent_id}}",
  "content": "User prefers dark mode",
  "importance": 0.8
}
```

#### Request 2: Recall Memories

```
POST {{base_url}}/v1/memory/episodic/recall
Headers:
  Authorization: Bearer {{api_key}}
  Content-Type: application/json
Body:
{
  "agent_id": "{{agent_id}}",
  "query": "What does the user prefer?",
  "k": 5
}
```

## Interactive API Documentation

The easiest way to test the API is using the built-in Swagger UI:

1. Start the server: `docker compose up -d`
2. Open browser: http://localhost:8000/docs
3. Click "Authorize" button
4. Enter API key: `test_key_12345`
5. Try any endpoint directly in the browser!

## Common Issues

### Issue 1: Connection Refused

**Problem:** `curl: (7) Failed to connect to localhost port 8000`

**Solution:**
```bash
# Check if server is running
docker compose ps

# Start server if not running
docker compose up -d

# Check logs for errors
docker compose logs kyros-server
```

### Issue 2: Authentication Failed

**Problem:** `401 Unauthorized`

**Solution:**
```bash
# Verify API key exists in database
docker compose exec postgres psql -U kyros -d kyros -c "SELECT tenant_id, name FROM tenants;"

# Create API key if missing (see Step 3 above)
```

### Issue 3: Database Not Ready

**Problem:** `500 Internal Server Error` or connection errors

**Solution:**
```bash
# Check database is running
docker compose ps postgres

# Check database logs
docker compose logs postgres

# Restart services
docker compose restart
```

### Issue 4: Embedding Model Download

**Problem:** First request is slow (downloading model)

**Solution:**
- First request takes 30-60 seconds to download embedding model
- Subsequent requests are fast (<100ms)
- Model is cached after first download

## Performance Testing

### Load Test with Apache Bench

```bash
# Install Apache Bench
sudo apt-get install apache2-utils  # Ubuntu/Debian
brew install httpd  # macOS

# Test memory storage (100 requests, 10 concurrent)
ab -n 100 -c 10 -T 'application/json' \
  -H 'Authorization: Bearer test_key_12345' \
  -p memory.json \
  http://localhost:8000/v1/memory/episodic/remember
```

Create `memory.json`:
```json
{
  "agent_id": "agent-001",
  "content": "Test memory for load testing",
  "importance": 0.5
}
```

### Load Test with Locust

```bash
# Run load test
make load-test

# Or manually
cd server
uv run locust -f tests/load/locustfile.py --host=http://localhost:8000
```

Open http://localhost:8089 to configure and run load tests.

## Monitoring

### View Logs

```bash
# All services
docker compose logs -f

# Server only
docker compose logs -f kyros-server

# Database only
docker compose logs -f postgres

# Redis only
docker compose logs -f redis
```

### Check Resource Usage

```bash
# Docker stats
docker stats

# Database size
docker compose exec postgres psql -U kyros -d kyros -c "
  SELECT pg_size_pretty(pg_database_size('kyros')) as size;
"

# Memory count
docker compose exec postgres psql -U kyros -d kyros -c "
  SELECT COUNT(*) FROM episodic_memories;
"
```

## Cleanup

### Reset Database

```bash
# Stop services
docker compose down

# Remove volumes (deletes all data)
docker compose down -v

# Start fresh
docker compose up -d
```

### Clear Specific Agent Data

```bash
docker compose exec postgres psql -U kyros -d kyros

-- Delete all memories for an agent
DELETE FROM episodic_memories WHERE agent_id = 'agent-001';
DELETE FROM semantic_memories WHERE agent_id = 'agent-001';
DELETE FROM procedural_memories WHERE agent_id = 'agent-001';

-- Delete agent
DELETE FROM agents WHERE agent_id = 'agent-001';
```

## Next Steps

1. **Explore API Documentation:** http://localhost:8000/docs
2. **Read SDK Documentation:** 
   - Python: `docs/python-sdk.md`
   - TypeScript: `docs/typescript-sdk.md`
3. **Try Examples:** Check `docs/quickstart.md` for more examples
4. **Build Your Application:** Integrate Kyros into your AI agent

## Support

- **Documentation:** https://docs.kyros.ai
- **GitHub Issues:** https://github.com/Kyros-494/kyros-ai/issues
- **API Reference:** http://localhost:8000/docs (when server is running)
