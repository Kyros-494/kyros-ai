# Core Concepts

This document explains the fundamental concepts and features of Kyros.

## Memory Types

Kyros supports three types of memory, each designed for specific use cases.

### Episodic Memory

Episodic memory stores sequential experiences, conversations, and actions. It represents "what happened" in chronological order.

**Characteristics:**
- Temporal ordering
- Session grouping
- Content types (text, action, tool_call, observation)
- Role attribution (user, assistant, system)
- Importance scoring

**Use Cases:**
- Conversation history
- Action logs
- Event sequences
- User interactions

**Example:**
```python
client.remember(
    agent_id="agent-123",
    content="User asked about pricing plans",
    content_type="text",
    role="user",
    session_id="session-456",
    importance=0.7,
    metadata={"topic": "pricing"}
)
```

**Fields:**
- `memory_id`: Unique identifier
- `agent_id`: Agent identifier
- `content`: Memory content
- `content_type`: Type of content
- `role`: Speaker role
- `session_id`: Session grouping
- `importance`: Importance score (0.0-1.0)
- `metadata`: Additional key-value pairs
- `created_at`: Timestamp
- `embedding`: Vector representation

### Semantic Memory

Semantic memory stores facts and knowledge as subject-predicate-object triples with confidence scores.

**Characteristics:**
- Triple structure (subject-predicate-object)
- Confidence scores
- Contradiction detection
- Belief propagation
- Source tracking

**Use Cases:**
- Knowledge bases
- User preferences
- Entity relationships
- Factual information

**Example:**
```python
client.store_fact(
    agent_id="agent-123",
    subject="user",
    predicate="prefers",
    value="dark mode",
    confidence=0.9,
    source_type="explicit"
)
```

**Fields:**
- `fact_id`: Unique identifier
- `agent_id`: Agent identifier
- `subject`: Entity
- `predicate`: Relationship
- `object`: Value
- `confidence`: Belief strength (0.0-1.0)
- `source_type`: Source classification
- `created_at`: Timestamp
- `embedding`: Vector representation

**Contradiction Handling:**

When a new fact contradicts an existing fact:
1. Old fact is marked as replaced
2. New fact is stored with reference to old fact
3. Confidence propagates through semantic edges
4. Related facts are updated

### Procedural Memory

Procedural memory stores workflows, procedures, and skills with execution statistics.

**Characteristics:**
- Step-by-step instructions
- Task type classification
- Success rate tracking
- Execution duration
- Outcome learning

**Use Cases:**
- Workflow automation
- Skill libraries
- Process documentation
- Task execution

**Example:**
```python
client.store_procedure(
    agent_id="agent-123",
    name="Send Email",
    description="Send an email to a recipient",
    task_type="communication",
    steps=[
        {"action": "compose", "params": {"to": "user@example.com"}},
        {"action": "validate", "params": {"check_spam": True}},
        {"action": "send"}
    ],
    metadata={"priority": "high"}
)
```

**Fields:**
- `procedure_id`: Unique identifier
- `agent_id`: Agent identifier
- `name`: Procedure name
- `description`: Detailed description
- `task_type`: Task classification
- `steps`: Ordered list of steps
- `success_count`: Successful executions
- `failure_count`: Failed executions
- `success_rate`: Success percentage
- `avg_duration_ms`: Average execution time
- `created_at`: Timestamp

**Outcome Reporting:**

```python
client.report_outcome(
    procedure_id="proc-456",
    success=True,
    duration_ms=1500
)
```

## Memory Decay

Kyros implements Ebbinghaus forgetting curves to model natural memory decay over time.

### Decay Formula

```
freshness = base_retention * e^(-decay_rate * time_elapsed)
```

Where:
- `base_retention`: Initial retention (typically 1.0)
- `decay_rate`: Category-specific decay rate
- `time_elapsed`: Time since creation (in days)

### Decay Rates by Category

Different memory categories decay at different rates:

| Category | Decay Rate | Half-life |
|----------|------------|-----------|
| Conversation | 0.1 | 7 days |
| Facts | 0.05 | 14 days |
| Skills | 0.01 | 70 days |
| Preferences | 0.02 | 35 days |

### Freshness Scores

Each memory includes a freshness score:
- `freshness_score`: Current freshness (0.0-1.0)
- `freshness_warning`: Boolean flag when freshness < 0.5
- `memory_category`: Category for decay calculation

### Staleness Reports

```python
report = client.get_staleness_report(agent_id="agent-123")
```

Returns:
- Total memories
- Stale memories (freshness < 0.5)
- Very stale memories (freshness < 0.2)
- Average freshness by category

### Configuring Decay Rates

```python
# Get current rates
rates = client.get_decay_rates()

# Update rates
client.set_decay_rates({
    "conversation": 0.15,
    "facts": 0.03,
    "skills": 0.005
})
```

## Integrity Proofs

Kyros provides cryptographic integrity verification to detect tampering.

### Content Hashing

Every memory includes a SHA-256 hash:
```
content_hash = SHA256(content + metadata + timestamp)
```

### Merkle Trees

Batch verification using Merkle trees:
1. Memories are grouped into batches
2. Each memory's hash is a leaf node
3. Parent nodes are hashes of child pairs
4. Root hash represents entire batch

### Audit Logs

Immutable audit trail:
- Memory creation
- Memory updates
- Memory deletion
- Integrity verification results

### Verification

```python
# Get integrity proof for single memory
proof = client.get_memory_proof(memory_id="mem-123")

# Audit all memories for agent
audit = client.audit_integrity(agent_id="agent-123")
```

Audit results include:
- Total memories checked
- Verified memories
- Tampered memories
- Missing memories

## Causal Reasoning

Kyros tracks cause-effect relationships between memories.

### Causal Edges

Directed edges represent causation:
- Source memory (cause)
- Target memory (effect)
- Confidence score
- Explanation text

### Causal Chains

Trace causation through multiple hops:
```python
explanation = client.explain(
    agent_id="agent-123",
    memory_id="mem-456",
    max_depth=3
)
```

Returns:
- Direct causes
- Indirect causes (up to max_depth)
- Causal chain visualization
- Confidence scores

### Use Cases

- Explain agent decisions
- Debug agent behavior
- Counterfactual reasoning
- Root cause analysis

## Belief Propagation

Kyros automatically propagates confidence updates through semantic relationships.

### Semantic Edges

Edges connect related facts:
- Subject-subject relationships
- Predicate-predicate relationships
- Object-object relationships
- Confidence weights

### Propagation Algorithm

When a fact's confidence changes:
1. Identify connected facts via semantic edges
2. Calculate confidence updates
3. Propagate updates recursively
4. Log all changes

### Propagation Logs

Track confidence changes:
```python
# Logs include:
# - Source fact
# - Target fact
# - Old confidence
# - New confidence
# - Propagation path
```

### Contradiction Detection

When facts contradict:
1. Detect contradiction
2. Mark old fact as replaced
3. Store new fact
4. Propagate confidence updates
5. Log contradiction

## Vector Search

Kyros uses vector embeddings for semantic similarity search.

### Embedding Models

Default: `all-MiniLM-L6-v2` (384 dimensions)

Supported models:
- `all-MiniLM-L6-v2`: Fast, 384 dimensions
- `all-mpnet-base-v2`: High quality, 768 dimensions
- `paraphrase-multilingual-MiniLM-L12-v2`: Multilingual, 384 dimensions

### Dual Embeddings

Support for two embedding models:
- Primary embedding: Main search
- Secondary embedding: Model portability

### Search Process

1. Query is embedded using same model
2. Vector similarity search (cosine similarity)
3. Results ranked by relevance
4. Decay applied to scores
5. Top-k results returned

### Search Parameters

```python
results = client.recall(
    agent_id="agent-123",
    query="user preferences",
    k=10,                    # Number of results
    min_relevance=0.5,       # Minimum similarity score
    memory_type="episodic",  # Filter by type
    session_id="session-456" # Filter by session
)
```

## Memory Categories

Memories are automatically categorized for decay calculation.

### Categories

- **conversation**: Chat messages, dialogue
- **facts**: Factual information, knowledge
- **skills**: Procedures, workflows
- **preferences**: User preferences, settings
- **observations**: Sensor data, observations
- **actions**: Agent actions, commands

### Category Detection

Automatic categorization based on:
- Content analysis
- Metadata
- Memory type
- Context

### Custom Categories

```python
client.remember(
    agent_id="agent-123",
    content="User completed tutorial",
    metadata={"category": "achievements"}
)
```

## Importance Scoring

Importance scores influence memory retention and retrieval.

### Importance Scale

- `0.0-0.3`: Low importance (ephemeral)
- `0.3-0.7`: Medium importance (normal)
- `0.7-1.0`: High importance (critical)

### Importance Factors

Importance affects:
- Decay rate (higher importance = slower decay)
- Search ranking (higher importance = higher rank)
- Compression priority (lower importance = compressed first)
- Archival decisions (lower importance = archived sooner)

### Setting Importance

```python
client.remember(
    agent_id="agent-123",
    content="User's credit card number",
    importance=1.0  # Critical information
)
```

## Session Management

Sessions group related memories for context management.

### Session IDs

Unique identifiers for conversation sessions:
```python
client.remember(
    agent_id="agent-123",
    content="User: Hello",
    session_id="session-456"
)
```

### Session Filtering

Recall memories from specific session:
```python
results = client.recall(
    agent_id="agent-123",
    query="what did we discuss?",
    session_id="session-456"
)
```

### Session Boundaries

Sessions typically represent:
- Single conversation
- Single task execution
- Time-bounded interaction
- Context window

## Metadata

Flexible key-value metadata for all memory types.

### Common Metadata Fields

```python
metadata = {
    "category": "preferences",
    "source": "user_input",
    "language": "en",
    "sentiment": "positive",
    "tags": ["important", "urgent"],
    "user_id": "user-789"
}
```

### Metadata Search

Metadata is indexed and searchable:
- Filter by metadata fields
- Search within metadata values
- Combine with vector search

### Metadata Best Practices

- Use consistent key names
- Keep values simple (strings, numbers, booleans)
- Avoid deeply nested structures
- Use for filtering and categorization

## Advanced Features

### Memory Compression

Automatic summarization of old memories:
- Extractive compression (local)
- LLM-based compression (OpenAI, Anthropic, Gemini)
- Configurable compression strategy

### Memory Archival

Move deleted memories to S3:
- Compliance with data retention policies
- Disaster recovery
- Audit trail preservation

### Embedding Migration

Migrate between embedding models:
```python
client.migrate_embeddings(
    agent_id="agent-123",
    from_model="all-MiniLM-L6-v2",
    to_model="all-mpnet-base-v2",
    strategy="translate"  # or "re-embed"
)
```

### Multi-tenancy

Tenant isolation for SaaS applications:
- Row-level security
- Separate API keys per tenant
- Isolated data access
- Shared infrastructure

## Performance Considerations

### Latency

- Memory storage: <50ms p95
- Memory recall: <100ms p95
- Batch operations: <200ms p95

### Throughput

- Single instance: 1000+ req/s
- Scaled deployment: 10,000+ req/s

### Optimization Tips

1. Use batch operations when possible
2. Cache frequently accessed memories
3. Set appropriate k values (don't over-fetch)
4. Use session filtering to reduce search space
5. Configure connection pooling
6. Use read replicas for scaling

## Best Practices

### Memory Storage

- Set appropriate importance scores
- Use descriptive content
- Include relevant metadata
- Group related memories in sessions
- Use consistent agent_id naming

### Memory Recall

- Write specific queries
- Set reasonable k values
- Use min_relevance to filter noise
- Filter by memory_type when appropriate
- Consider freshness in results

### Production Deployment

- Configure decay rates for your use case
- Set up monitoring and alerting
- Enable integrity verification
- Configure backups
- Use connection pooling
- Scale horizontally as needed

## Conclusion

Understanding these core concepts is essential for effectively using Kyros. Each feature is designed to work together to provide a comprehensive memory management system for AI agents.

For implementation details, see the SDK documentation and API reference.
