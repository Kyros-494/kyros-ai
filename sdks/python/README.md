# Kyros Python SDK

> **Official Python SDK for Kyros — Persistent Memory for AI Agents**

[![PyPI version](https://badge.fury.io/py/kyros-sdk.svg)](https://badge.fury.io/py/kyros-sdk)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The Kyros Python SDK provides a simple, type-safe interface to the Kyros Memory API. Store and recall memories for your AI agents with just a few lines of code.

---

## 🚀 Quick Start

### Installation

```bash
pip install kyros-sdk
```

### Basic Usage

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

---

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install kyros-sdk
```

### With Framework Integrations

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

### From Source

```bash
git clone https://github.com/Kyros-494/kyros-ai.git
cd kyros-ai/sdks/python
pip install -e .
```

---

## 🔑 Authentication

### API Key

Get your API key from the [Kyros Dashboard](https://kyros.ai/dashboard) or self-hosted instance.

### Configuration

```python
# Option 1: Pass API key directly
client = KyrosClient(api_key="your-api-key")

# Option 2: Use environment variable
import os
os.environ["KYROS_API_KEY"] = "your-api-key"
client = KyrosClient()

# Option 3: Custom base URL (for self-hosted)
client = KyrosClient(
    api_key="your-api-key",
    base_url="https://your-kyros-instance.com"
)
```

---

## 📚 Core Features

### Episodic Memory

Store and recall conversation history, actions, and observations.

```python
# Store a memory
response = client.remember(
    agent_id="agent-123",
    content="User asked about pricing",
    content_type="text",
    role="user",
    session_id="session-456",
    importance=0.7,
    metadata={"category": "sales"}
)

# Recall memories
results = client.recall(
    agent_id="agent-123",
    query="What did the user ask about?",
    k=5,
    min_relevance=0.5
)

# Delete a memory
client.forget(agent_id="agent-123", memory_id="mem-789")
```

### Semantic Memory

Store and query facts as subject-predicate-object triples.

```python
# Store a fact
fact = client.store_fact(
    agent_id="agent-123",
    subject="user",
    predicate="prefers",
    value="dark mode",
    confidence=0.9
)

# Query facts
results = client.query_facts(
    agent_id="agent-123",
    query="user preferences",
    k=10
)
```

### Procedural Memory

Store and match workflows, skills, and procedures.

```python
# Store a procedure
procedure = client.store_procedure(
    agent_id="agent-123",
    name="Send Email",
    description="Send an email to a recipient",
    task_type="communication",
    steps=[
        {"action": "compose", "params": {"to": "user@example.com"}},
        {"action": "send"}
    ]
)

# Match procedures
matches = client.match_procedure(
    agent_id="agent-123",
    task_description="I need to send an email",
    k=5
)

# Report outcome
outcome = client.report_outcome(
    procedure_id="proc-456",
    success=True,
    duration_ms=1500
)
```

### Unified Search

Search across all memory types.

```python
results = client.search(
    agent_id="agent-123",
    query="email preferences",
    k=10
)
```

---

## 🔌 Framework Integrations

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
inject_kyros_memory(agent, agent_id="agent-123", api_key="your-api-key")

# Agent now automatically stores and recalls memories
```

### CrewAI

```python
from kyros.integrations.crewai import get_kyros_tools
from crewai import Agent, Task, Crew

tools = get_kyros_tools(agent_id="agent-123", api_key="your-api-key")

agent = Agent(
    role="Assistant",
    goal="Help users",
    tools=tools
)

# Agent can now use Kyros memory tools
```

---

## 🎯 Advanced Features

### Causal Reasoning

```python
# Get causal explanation
explanation = client.explain(
    agent_id="agent-123",
    memory_id="mem-456",
    max_depth=3
)
```

### Integrity Verification

```python
# Get memory proof
proof = client.get_memory_proof(memory_id="mem-456")

# Audit agent integrity
audit = client.audit_integrity(agent_id="agent-123")
```

### Memory Decay

```python
# Get staleness report
report = client.get_staleness_report(agent_id="agent-123")

# Get decay rates
rates = client.get_decay_rates()

# Set decay rates
client.set_decay_rates({"conversation": 0.1, "facts": 0.05})
```

### Export/Import

```python
# Export memories
export = client.export_memories(agent_id="agent-123")

# Import memories
client.import_memories(agent_id="agent-456", data=export)
```

### Embedding Migration

```python
# Migrate embeddings
result = client.migrate_embeddings(
    agent_id="agent-123",
    from_model="all-MiniLM-L6-v2",
    to_model="all-mpnet-base-v2",
    strategy="translate"
)
```

---

## 🛠️ Development

### Setup

```bash
# Clone repository
git clone https://github.com/Kyros-494/kyros-ai.git
cd kyros-ai/sdks/python

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .

# Run type checking
mypy kyros
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=kyros --cov-report=html

# Run specific test file
pytest tests/test_client.py -v
```

---

## 📖 API Reference

### Client

#### `KyrosClient(api_key, base_url, timeout)`

Initialize Kyros client.

**Parameters:**
- `api_key` (str, optional): API key for authentication
- `base_url` (str, optional): Base URL for Kyros API
- `timeout` (float, optional): Request timeout in seconds (default: 30.0)

### Episodic Memory

#### `remember(agent_id, content, **options)`

Store an episodic memory.

**Parameters:**
- `agent_id` (str): Agent identifier
- `content` (str): Memory content
- `content_type` (str, optional): Content type (text, action, tool_call, observation)
- `role` (str, optional): Speaker role
- `session_id` (str, optional): Session identifier
- `importance` (float, optional): Importance score (0.0-1.0)
- `metadata` (dict, optional): Additional metadata

**Returns:** `RememberResponse`

#### `recall(agent_id, query, **options)`

Recall memories using semantic search.

**Parameters:**
- `agent_id` (str): Agent identifier
- `query` (str): Search query
- `memory_type` (str, optional): Filter by memory type
- `k` (int, optional): Number of results (default: 10)
- `min_relevance` (float, optional): Minimum relevance score
- `session_id` (str, optional): Filter by session
- `include_causal_ancestry` (bool, optional): Include causal chain

**Returns:** `RecallResponse`

#### `forget(agent_id, memory_id)`

Delete a memory.

**Parameters:**
- `agent_id` (str): Agent identifier
- `memory_id` (str): Memory identifier

**Returns:** None

### Semantic Memory

#### `store_fact(agent_id, subject, predicate, value, **options)`

Store a semantic fact.

**Parameters:**
- `agent_id` (str): Agent identifier
- `subject` (str): Subject
- `predicate` (str): Predicate (relationship)
- `value` (str): Object (value)
- `confidence` (float, optional): Confidence score (default: 1.0)
- `source_type` (str, optional): Source type (default: "explicit")

**Returns:** `FactResult`

#### `query_facts(agent_id, query, k)`

Query semantic facts.

**Parameters:**
- `agent_id` (str): Agent identifier
- `query` (str): Search query
- `k` (int, optional): Number of results (default: 10)

**Returns:** `RecallResponse`

### Procedural Memory

#### `store_procedure(agent_id, name, description, task_type, steps, **options)`

Store a procedure.

**Parameters:**
- `agent_id` (str): Agent identifier
- `name` (str): Procedure name
- `description` (str): Procedure description
- `task_type` (str): Task type
- `steps` (list): List of steps
- `metadata` (dict, optional): Additional metadata

**Returns:** `ProcedureResponse`

#### `match_procedure(agent_id, task_description, k)`

Find matching procedures.

**Parameters:**
- `agent_id` (str): Agent identifier
- `task_description` (str): Task description
- `k` (int, optional): Number of results (default: 5)

**Returns:** `ProcedureMatchResponse`

#### `report_outcome(procedure_id, success, duration_ms)`

Report procedure execution outcome.

**Parameters:**
- `procedure_id` (str): Procedure identifier
- `success` (bool): Success status
- `duration_ms` (int, optional): Execution duration

**Returns:** `ProcedureOutcomeResponse`

---

## 🐛 Error Handling

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

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](../../CONTRIBUTING.md) for details.

---

## 📄 License

This SDK is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

The Kyros server is licensed under the **Apache License 2.0**.

---

## 🔗 Links

- **Homepage**: https://kyros.ai
- **Documentation**: https://docs.kyros.ai
- **GitHub**: https://github.com/Kyros-494/kyros-ai
- **PyPI**: https://pypi.org/project/kyros-sdk/
- **Issues**: https://github.com/Kyros-494/kyros-ai/issues

---

## 🙏 Acknowledgments

Built with:
- [httpx](https://www.python-httpx.org/) - Modern HTTP client
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation

---

**Made with ❤️ by the Kyros team**
