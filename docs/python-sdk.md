# Python SDK Reference

Complete API reference for the Kyros Python SDK.

## Installation

```bash
pip install kyros-sdk
```

### Optional Dependencies

```bash
# LangChain integration
pip install kyros-sdk[langchain]

# LlamaIndex integration
pip install kyros-sdk[llama-index]

# AutoGen integration
pip install kyros-sdk[autogen]

# CrewAI integration
pip install kyros-sdk[crewai]

# All integrations
pip install kyros-sdk[all]
```

## Quick Start

```python
from kyros import KyrosClient

# Initialize client
client = KyrosClient(api_key="your-api-key")

# Store a memory
response = client.remember(
    agent_id="agent-123",
    content="User prefers dark mode",
    importance=0.8
)

# Recall memories
results = client.recall(
    agent_id="agent-123",
    query="What are the user's preferences?"
)

for memory in results.results:
    print(f"{memory.content} (score: {memory.relevance_score})")
```

## Client Initialization

### KyrosClient

```python
class KyrosClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.kyros.ai",
        timeout: float = 30.0
    )
```

Initialize the Kyros client.

**Parameters:**

- `api_key` (str, optional): API key for authentication. If not provided, reads from `KYROS_API_KEY` environment variable.
- `base_url` (str, optional): Base URL for the Kyros API. Default: `https://api.kyros.ai`
- `timeout` (float, optional): Request timeout in seconds. Default: 30.0

**Example:**

```python
# Using API key directly
client = KyrosClient(api_key="mk_live_...")

# Using environment variable
import os
os.environ["KYROS_API_KEY"] = "mk_live_..."
client = KyrosClient()

# Self-hosted instance
client = KyrosClient(
    api_key="your-key",
    base_url="https://kyros.yourcompany.com"
)
```

## Episodic Memory

Episodic memory stores conversation history, actions, observations, and tool calls.

### remember

```python
def remember(
    self,
    agent_id: str,
    content: str,
    content_type: str = "text",
    role: Optional[str] = None,
    session_id: Optional[str] = None,
    importance: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> RememberResponse
```

Store an episodic memory.

**Parameters:**

- `agent_id` (str): Unique identifier for the agent
- `content` (str): Memory content to store
- `content_type` (str, optional): Type of content. Options: `text`, `action`, `tool_call`, `observation`. Default: `text`
- `role` (str, optional): Speaker role (e.g., `user`, `assistant`, `system`)
- `session_id` (str, optional): Session identifier for grouping related memories
- `importance` (float, optional): Importance score between 0.0 and 1.0. Higher values decay slower.
- `metadata` (dict, optional): Additional metadata as key-value pairs

**Returns:** `RememberResponse` object with:
- `memory_id` (str): Unique identifier for the stored memory
- `agent_id` (str): Agent identifier
- `created_at` (datetime): Timestamp when memory was created

**Example:**

```python
# Basic usage
response = client.remember(
    agent_id="agent-123",
    content="User asked about pricing"
)

# With all options
response = client.remember(
    agent_id="agent-123",
    content="User: What are your pricing plans?",
    content_type="text",
    role="user",
    session_id="session-456",
    importance=0.8,
    metadata={
        "category": "sales",
        "language": "en",
        "sentiment": "neutral"
    }
)

print(f"Stored memory: {response.memory_id}")
```

### recall

```python
def recall(
    self,
    agent_id: str,
    query: str,
    memory_type: Optional[str] = None,
    k: int = 10,
    min_relevance: Optional[float] = None,
    session_id: Optional[str] = None,
    include_causal_ancestry: bool = False
) -> RecallResponse
```

Recall memories using semantic search.

**Parameters:**

- `agent_id` (str): Agent identifier
- `query` (str): Search query
- `memory_type` (str, optional): Filter by memory type. Options: `episodic`, `semantic`, `procedural`
- `k` (int, optional): Maximum number of results to return. Default: 10
- `min_relevance` (float, optional): Minimum relevance score (0.0-1.0). Filters out low-relevance results.
- `session_id` (str, optional): Filter by session identifier
- `include_causal_ancestry` (bool, optional): Include causal chain for each memory. Default: False

**Returns:** `RecallResponse` object with:
- `results` (List[Memory]): List of matching memories
- `total` (int): Total number of results

**Memory Object:**
- `memory_id` (str): Unique identifier
- `content` (str): Memory content
- `relevance_score` (float): Similarity score (0.0-1.0)
- `freshness_score` (float): Recency score with decay applied
- `importance` (float): Importance score
- `created_at` (datetime): Creation timestamp
- `metadata` (dict): Additional metadata

**Example:**

```python
# Basic recall
results = client.recall(
    agent_id="agent-123",
    query="What did the user ask about?"
)

for memory in results.results:
    print(f"{memory.content}")
    print(f"  Relevance: {memory.relevance_score:.2f}")
    print(f"  Freshness: {memory.freshness_score:.2f}")

# Advanced recall with filters
results = client.recall(
    agent_id="agent-123",
    query="pricing questions",
    memory_type="episodic",
    k=5,
    min_relevance=0.7,
    session_id="session-456",
    include_causal_ancestry=True
)
```

### forget

```python
def forget(
    self,
    agent_id: str,
    memory_id: str
) -> None
```

Delete a specific memory.

**Parameters:**

- `agent_id` (str): Agent identifier
- `memory_id` (str): Memory identifier to delete

**Returns:** None

**Example:**

```python
# Delete a memory
client.forget(
    agent_id="agent-123",
    memory_id="mem-456"
)
```

## Semantic Memory

Semantic memory stores facts as subject-predicate-object triples with confidence scores.

### store_fact

```python
def store_fact(
    self,
    agent_id: str,
    subject: str,
    predicate: str,
    value: str,
    confidence: float = 1.0,
    source_type: str = "explicit"
) -> FactResult
```

Store a semantic fact.

**Parameters:**

- `agent_id` (str): Agent identifier
- `subject` (str): Subject of the fact (e.g., "user", "product")
- `predicate` (str): Relationship or property (e.g., "prefers", "has_feature")
- `value` (str): Object or value (e.g., "dark mode", "true")
- `confidence` (float, optional): Confidence score (0.0-1.0). Default: 1.0
- `source_type` (str, optional): Source of the fact. Options: `explicit`, `inferred`, `observed`. Default: `explicit`

**Returns:** `FactResult` object with:
- `fact_id` (str): Unique identifier for the fact
- `subject` (str): Subject
- `predicate` (str): Predicate
- `value` (str): Value
- `confidence` (float): Confidence score

**Example:**

```python
# Store a user preference
fact = client.store_fact(
    agent_id="agent-123",
    subject="user",
    predicate="prefers",
    value="dark mode",
    confidence=0.9
)

# Store product information
fact = client.store_fact(
    agent_id="agent-123",
    subject="product_pro",
    predicate="price",
    value="$99/month",
    confidence=1.0,
    source_type="explicit"
)

# Store inferred fact
fact = client.store_fact(
    agent_id="agent-123",
    subject="user",
    predicate="skill_level",
    value="advanced",
    confidence=0.7,
    source_type="inferred"
)
```

### query_facts

```python
def query_facts(
    self,
    agent_id: str,
    query: str,
    k: int = 10
) -> RecallResponse
```

Query semantic facts using natural language.

**Parameters:**

- `agent_id` (str): Agent identifier
- `query` (str): Natural language query
- `k` (int, optional): Maximum number of results. Default: 10

**Returns:** `RecallResponse` with matching facts

**Example:**

```python
# Query facts
results = client.query_facts(
    agent_id="agent-123",
    query="user preferences",
    k=10
)

for fact in results.results:
    print(f"{fact.subject} {fact.predicate} {fact.value}")
    print(f"  Confidence: {fact.confidence:.2f}")
```

## Procedural Memory

Procedural memory stores workflows, procedures, and skills with success tracking.

### store_procedure

```python
def store_procedure(
    self,
    agent_id: str,
    name: str,
    description: str,
    task_type: str,
    steps: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None
) -> ProcedureResponse
```

Store a procedure or workflow.

**Parameters:**

- `agent_id` (str): Agent identifier
- `name` (str): Procedure name
- `description` (str): Detailed description of what the procedure does
- `task_type` (str): Category of task (e.g., "communication", "data_processing")
- `steps` (List[dict]): List of steps, each with `action` and optional `params`
- `metadata` (dict, optional): Additional metadata

**Returns:** `ProcedureResponse` object with:
- `procedure_id` (str): Unique identifier
- `name` (str): Procedure name
- `success_rate` (float): Historical success rate (0.0-1.0)

**Example:**

```python
# Store email sending procedure
procedure = client.store_procedure(
    agent_id="agent-123",
    name="Send Email",
    description="Send an email to a recipient with subject and body",
    task_type="communication",
    steps=[
        {
            "action": "validate_email",
            "params": {"field": "to"}
        },
        {
            "action": "compose_message",
            "params": {"template": "default"}
        },
        {
            "action": "send",
            "params": {"retry": 3}
        }
    ],
    metadata={
        "category": "email",
        "priority": "high"
    }
)

print(f"Stored procedure: {procedure.procedure_id}")
```

### match_procedure

```python
def match_procedure(
    self,
    agent_id: str,
    task_description: str,
    k: int = 5
) -> ProcedureMatchResponse
```

Find procedures matching a task description.

**Parameters:**

- `agent_id` (str): Agent identifier
- `task_description` (str): Natural language description of the task
- `k` (int, optional): Maximum number of results. Default: 5

**Returns:** `ProcedureMatchResponse` with:
- `matches` (List[Procedure]): List of matching procedures sorted by relevance and success rate

**Procedure Object:**
- `procedure_id` (str): Unique identifier
- `name` (str): Procedure name
- `description` (str): Description
- `steps` (List[dict]): Procedure steps
- `success_rate` (float): Historical success rate
- `relevance_score` (float): Match score for the query

**Example:**

```python
# Find matching procedures
matches = client.match_procedure(
    agent_id="agent-123",
    task_description="I need to send an email to a customer",
    k=5
)

for proc in matches.matches:
    print(f"{proc.name} (success: {proc.success_rate:.1%})")
    print(f"  Relevance: {proc.relevance_score:.2f}")
    print(f"  Steps: {len(proc.steps)}")
```

### report_outcome

```python
def report_outcome(
    self,
    procedure_id: str,
    success: bool,
    duration_ms: Optional[int] = None
) -> ProcedureOutcomeResponse
```

Report the outcome of a procedure execution.

**Parameters:**

- `procedure_id` (str): Procedure identifier
- `success` (bool): Whether the execution succeeded
- `duration_ms` (int, optional): Execution duration in milliseconds

**Returns:** `ProcedureOutcomeResponse` with:
- `procedure_id` (str): Procedure identifier
- `new_success_rate` (float): Updated success rate

**Example:**

```python
# Report successful execution
outcome = client.report_outcome(
    procedure_id="proc-456",
    success=True,
    duration_ms=1500
)

print(f"New success rate: {outcome.new_success_rate:.1%}")

# Report failure
outcome = client.report_outcome(
    procedure_id="proc-456",
    success=False,
    duration_ms=3000
)
```

## Unified Search

Search across all memory types simultaneously.

### search

```python
def search(
    self,
    agent_id: str,
    query: str,
    k: int = 10
) -> RecallResponse
```

Search across episodic, semantic, and procedural memories.

**Parameters:**

- `agent_id` (str): Agent identifier
- `query` (str): Search query
- `k` (int, optional): Maximum number of results. Default: 10

**Returns:** `RecallResponse` with mixed memory types

**Example:**

```python
# Unified search
results = client.search(
    agent_id="agent-123",
    query="email preferences",
    k=10
)

for memory in results.results:
    print(f"[{memory.memory_type}] {memory.content}")
```

## Advanced Features

### Causal Reasoning

#### explain

```python
def explain(
    self,
    agent_id: str,
    memory_id: str,
    max_depth: int = 3
) -> CausalExplanation
```

Get causal explanation for a memory.

**Parameters:**

- `agent_id` (str): Agent identifier
- `memory_id` (str): Memory identifier
- `max_depth` (int, optional): Maximum depth of causal chain. Default: 3

**Returns:** `CausalExplanation` with causal chain

**Example:**

```python
explanation = client.explain(
    agent_id="agent-123",
    memory_id="mem-456",
    max_depth=3
)

print("Causal chain:")
for step in explanation.chain:
    print(f"  {step.cause} → {step.effect}")
```

### Integrity Verification

#### get_memory_proof

```python
def get_memory_proof(
    self,
    memory_id: str
) -> MemoryProof
```

Get cryptographic proof for a memory.

**Parameters:**

- `memory_id` (str): Memory identifier

**Returns:** `MemoryProof` with:
- `memory_id` (str): Memory identifier
- `content_hash` (str): SHA-256 hash of content
- `merkle_root` (str): Merkle tree root
- `merkle_proof` (List[str]): Merkle proof path

**Example:**

```python
proof = client.get_memory_proof(memory_id="mem-456")
print(f"Content hash: {proof.content_hash}")
print(f"Merkle root: {proof.merkle_root}")
```

#### audit_integrity

```python
def audit_integrity(
    self,
    agent_id: str
) -> IntegrityAudit
```

Audit integrity of all memories for an agent.

**Parameters:**

- `agent_id` (str): Agent identifier

**Returns:** `IntegrityAudit` with:
- `total_memories` (int): Total number of memories
- `verified` (int): Number of verified memories
- `tampered` (int): Number of tampered memories
- `issues` (List[str]): List of integrity issues

**Example:**

```python
audit = client.audit_integrity(agent_id="agent-123")
print(f"Verified: {audit.verified}/{audit.total_memories}")
if audit.tampered > 0:
    print(f"WARNING: {audit.tampered} tampered memories detected!")
```

### Memory Decay

#### get_staleness_report

```python
def get_staleness_report(
    self,
    agent_id: str
) -> StalenessReport
```

Get report on memory staleness.

**Parameters:**

- `agent_id` (str): Agent identifier

**Returns:** `StalenessReport` with decay statistics

**Example:**

```python
report = client.get_staleness_report(agent_id="agent-123")
print(f"Stale memories: {report.stale_count}")
print(f"Average freshness: {report.avg_freshness:.2f}")
```

#### get_decay_rates

```python
def get_decay_rates(self) -> Dict[str, float]
```

Get current decay rates for all memory categories.

**Returns:** Dictionary mapping category names to decay rates

**Example:**

```python
rates = client.get_decay_rates()
for category, rate in rates.items():
    print(f"{category}: {rate}")
```

#### set_decay_rates

```python
def set_decay_rates(
    self,
    rates: Dict[str, float]
) -> None
```

Set decay rates for memory categories.

**Parameters:**

- `rates` (dict): Dictionary mapping category names to decay rates (0.0-1.0)

**Example:**

```python
client.set_decay_rates({
    "conversation": 0.1,
    "facts": 0.05,
    "procedures": 0.02
})
```

### Export/Import

#### export_memories

```python
def export_memories(
    self,
    agent_id: str
) -> Dict[str, Any]
```

Export all memories for an agent.

**Parameters:**

- `agent_id` (str): Agent identifier

**Returns:** Dictionary with all memories in portable format

**Example:**

```python
# Export memories
export_data = client.export_memories(agent_id="agent-123")

# Save to file
import json
with open("memories.json", "w") as f:
    json.dump(export_data, f, indent=2)
```

#### import_memories

```python
def import_memories(
    self,
    agent_id: str,
    data: Dict[str, Any]
) -> ImportResult
```

Import memories for an agent.

**Parameters:**

- `agent_id` (str): Agent identifier
- `data` (dict): Export data from `export_memories`

**Returns:** `ImportResult` with import statistics

**Example:**

```python
# Load from file
import json
with open("memories.json", "r") as f:
    export_data = json.load(f)

# Import memories
result = client.import_memories(
    agent_id="agent-456",
    data=export_data
)

print(f"Imported {result.imported_count} memories")
```

### Embedding Migration

#### migrate_embeddings

```python
def migrate_embeddings(
    self,
    agent_id: str,
    from_model: str,
    to_model: str,
    strategy: str = "translate"
) -> MigrationResult
```

Migrate embeddings to a different model.

**Parameters:**

- `agent_id` (str): Agent identifier
- `from_model` (str): Current embedding model
- `to_model` (str): Target embedding model
- `strategy` (str, optional): Migration strategy. Options: `translate`, `regenerate`. Default: `translate`

**Returns:** `MigrationResult` with migration statistics

**Example:**

```python
result = client.migrate_embeddings(
    agent_id="agent-123",
    from_model="all-MiniLM-L6-v2",
    to_model="all-mpnet-base-v2",
    strategy="translate"
)

print(f"Migrated {result.migrated_count} embeddings")
```

## Framework Integrations

### LangChain

```python
from kyros.integrations.langchain import KyrosChatMemory
from langchain.chains import ConversationChain
from langchain.llms import OpenAI

memory = KyrosChatMemory(
    agent_id="agent-123",
    api_key="your-api-key"
)

chain = ConversationChain(
    llm=OpenAI(),
    memory=memory
)

response = chain.run("Hello!")
```

### LlamaIndex

```python
from kyros.integrations.llama_index import KyrosMemory
from llama_index.core.chat_engine import SimpleChatEngine

memory = KyrosMemory(
    agent_id="agent-123",
    api_key="your-api-key"
)

engine = SimpleChatEngine.from_defaults(memory=memory)
response = engine.chat("Hello!")
```

### AutoGen

```python
from kyros.integrations.autogen import inject_kyros_memory
from autogen import AssistantAgent

agent = AssistantAgent(name="assistant")
inject_kyros_memory(
    agent,
    agent_id="agent-123",
    api_key="your-api-key"
)
```

### CrewAI

```python
from kyros.integrations.crewai import get_kyros_tools
from crewai import Agent

tools = get_kyros_tools(
    agent_id="agent-123",
    api_key="your-api-key"
)

agent = Agent(
    role="Assistant",
    goal="Help users",
    tools=tools
)
```

## Error Handling

```python
from kyros import (
    KyrosClient,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    ServerError,
    TimeoutError,
    ConnectionError
)

try:
    client = KyrosClient(api_key="invalid-key")
    client.remember(agent_id="agent-123", content="test")
    
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
    
except RateLimitError as e:
    print(f"Rate limit exceeded. Retry after {e.retry_after}s")
    
except NotFoundError as e:
    print(f"Resource not found: {e}")
    
except ValidationError as e:
    print(f"Validation error: {e}")
    
except ServerError as e:
    print(f"Server error: {e}")
    
except TimeoutError as e:
    print(f"Request timed out: {e}")
    
except ConnectionError as e:
    print(f"Connection failed: {e}")
```

## Type Definitions

### RememberResponse

```python
@dataclass
class RememberResponse:
    memory_id: str
    agent_id: str
    created_at: datetime
```

### RecallResponse

```python
@dataclass
class RecallResponse:
    results: List[Memory]
    total: int
```

### Memory

```python
@dataclass
class Memory:
    memory_id: str
    content: str
    relevance_score: float
    freshness_score: float
    importance: float
    created_at: datetime
    metadata: Dict[str, Any]
    memory_type: str
```

### FactResult

```python
@dataclass
class FactResult:
    fact_id: str
    subject: str
    predicate: str
    value: str
    confidence: float
```

### ProcedureResponse

```python
@dataclass
class ProcedureResponse:
    procedure_id: str
    name: str
    success_rate: float
```

### ProcedureMatchResponse

```python
@dataclass
class ProcedureMatchResponse:
    matches: List[Procedure]
```

### Procedure

```python
@dataclass
class Procedure:
    procedure_id: str
    name: str
    description: str
    steps: List[Dict[str, Any]]
    success_rate: float
    relevance_score: float
```

## Best Practices

### Memory Importance

Set importance scores based on content significance:

```python
# Critical information (decays slowly)
client.remember(
    agent_id="agent-123",
    content="User's API key: abc123",
    importance=1.0
)

# Normal conversation (standard decay)
client.remember(
    agent_id="agent-123",
    content="User asked about weather",
    importance=0.5
)

# Low-priority information (decays quickly)
client.remember(
    agent_id="agent-123",
    content="User said hello",
    importance=0.1
)
```

### Session Management

Group related memories with session IDs:

```python
session_id = "session-" + str(uuid.uuid4())

# Store conversation in session
client.remember(
    agent_id="agent-123",
    content="User: What's the weather?",
    session_id=session_id
)

client.remember(
    agent_id="agent-123",
    content="Assistant: It's sunny today.",
    session_id=session_id
)

# Recall from specific session
results = client.recall(
    agent_id="agent-123",
    query="weather",
    session_id=session_id
)
```

### Metadata Usage

Use metadata for filtering and organization:

```python
client.remember(
    agent_id="agent-123",
    content="User purchased Pro plan",
    metadata={
        "category": "billing",
        "event_type": "purchase",
        "plan": "pro",
        "amount": 99.00,
        "currency": "USD"
    }
)
```

### Error Handling

Always handle errors gracefully:

```python
from kyros import KyrosClient, KyrosError

client = KyrosClient(api_key="your-key")

try:
    response = client.remember(
        agent_id="agent-123",
        content="Important information"
    )
except KyrosError as e:
    # Log error and continue
    logger.error(f"Failed to store memory: {e}")
    # Implement fallback behavior
```

## Links

- [GitHub Repository](https://github.com/Kyros-494/kyros-ai)
- [PyPI Package](https://pypi.org/project/kyros-sdk/)
- [API Documentation](https://docs.kyros.ai)
- [Issue Tracker](https://github.com/Kyros-494/kyros-ai/issues)
