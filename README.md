<div align="center">
  <img src="https://raw.githubusercontent.com/Kyros-494/kyros-ai/master/docs/assets/kyros-logo.png" alt="Kyros Logo" width="120" />
</div>

<h1 align="center">Kyros</h1>

<p align="center">
  <strong>Persistent Memory System for AI Agents</strong>
</p>

<p align="center">
  Give your AI agents secure, self-correcting, persistent memory with cryptographic integrity and natural forgetting curves.
</p>

<p align="center">
  <a href="https://pypi.org/project/kyros-sdk/"><img src="https://img.shields.io/pypi/v/kyros-sdk?color=blue&label=PyPI" alt="PyPI version" /></a>
  <a href="https://www.npmjs.com/package/@kyros/sdk"><img src="https://img.shields.io/npm/v/@kyros/sdk?color=blue&label=npm" alt="npm version" /></a>
  <a href="https://github.com/Kyros-494/kyros-ai/actions"><img src="https://img.shields.io/github/actions/workflow/status/Kyros-494/kyros-ai/ci.yml?branch=main&label=CI" alt="CI Status" /></a>
  <a href="https://github.com/Kyros-494/kyros-ai/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License" /></a>
  <a href="https://github.com/Kyros-494/kyros-ai/stargazers"><img src="https://img.shields.io/github/stars/Kyros-494/kyros-ai?style=social" alt="GitHub Stars" /></a>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#examples">Examples</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#license">License</a>
</p>

---

## Overview

Kyros is an open-source memory operating system designed specifically for AI agents. It provides three biologically-inspired memory types (episodic, semantic, and procedural) with built-in features like cryptographic integrity proofs, Ebbinghaus decay curves, and belief propagation.

### The Problem

Modern AI agents are **stateless** — they forget everything between sessions. Developers manually implement memory using:
- Vector databases for semantic search
- Key-value stores for facts
- Custom logic for memory management
- Ad-hoc solutions for data integrity

This approach is **fragile, insecure, and doesn't scale**.

### The Solution

Kyros provides a **complete memory system** in a single SDK:

```python
import kyros

client = kyros.Client(api_key="your_api_key")

# Store a memory
client.remember("agent-1", "User prefers Python for backend development")

# Recall relevant memories
results = client.recall("agent-1", "What language does the user prefer?")
print(results.results[0].content)
# → "User prefers Python for backend development"
```

---

## Features

### Three Memory Types

Based on cognitive science research, Kyros implements three distinct memory systems:

- **Episodic Memory**: Events and experiences (conversations, actions, observations)
- **Semantic Memory**: Facts and knowledge (user preferences, domain knowledge)
- **Procedural Memory**: Skills and workflows (how to perform tasks)

### Cryptographic Integrity

Every memory is protected with SHA-256 hashing and Merkle tree proofs:
- Detect tampering and poisoning attacks
- Verify memory authenticity
- Audit trail for all changes
- Immutable memory history

### Ebbinghaus Decay

Memories naturally fade over time based on category-specific decay rates:
- Market data: 1.4 days half-life
- User identity: 693 days half-life
- Prevents memory bloat
- Keeps context relevant

### Belief Propagation

When facts conflict, confidence updates ripple through the semantic graph:
- Automatic conflict resolution
- Confidence scoring
- Relationship tracking
- Self-correcting knowledge base

### High Performance

- **<20ms** average recall latency
- **<50ms** memory storage
- **pgvector** for semantic search
- **Redis** caching layer
- Horizontal scaling support

### Framework Integrations

Works seamlessly with popular AI frameworks:
- **LangChain**: Memory integration
- **LlamaIndex**: Data connector
- **AutoGen**: Multi-agent memory
- **CrewAI**: Crew memory
- **Vercel AI SDK**: Streaming support

### Model Agnostic

Compatible with any LLM provider:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)
- Open source models (Llama, Mistral)
- Custom models

---

## Quick Start

### Prerequisites

- **Docker** and **Docker Compose** (for self-hosting)
- **Python 3.11+** or **Node.js 18+** (for SDK)

### Installation

#### Option 1: Self-Hosted (Recommended)

```bash
# Clone the repository
git clone https://github.com/Kyros-494/kyros-ai.git
cd kyros-ai

# Start the server
docker compose up -d

# Server runs at http://localhost:8000
```

#### Option 2: Cloud Hosted

Coming soon!!!

### SDK Installation

**Python:**
```bash
pip install kyros-sdk
```

**TypeScript:**
```bash
npm install @kyros/sdk
```

### Basic Usage

**Python:**
```python
import kyros

# Initialize client
client = kyros.Client(
    base_url="http://localhost:8000",  # or https://api.kyros.ai
    api_key="your_api_key"
)

# Store episodic memory (what happened)
client.store_episode(
    agent_id="agent-1",
    content="User asked about pricing plans",
    metadata={"timestamp": "2026-05-03T10:30:00Z"}
)

# Store semantic memory (what is true)
client.store_fact(
    agent_id="agent-1",
    subject="user_123",
    predicate="subscription_plan",
    value="Pro"
)

# Store procedural memory (how to do things)
client.store_procedure(
    agent_id="agent-1",
    name="handle_refund_request",
    steps=["Verify purchase", "Check refund policy", "Process refund"]
)

# Query memories
results = client.query(
    agent_id="agent-1",
    query="What plan is the user on?",
    memory_types=["semantic"]
)

for memory in results.results:
    print(f"{memory.content} (confidence: {memory.confidence})")
```

**TypeScript:**
```typescript
import { KyrosClient } from '@kyros/sdk';

// Initialize client
const client = new KyrosClient({
  baseUrl: 'http://localhost:8000',  // or https://api.kyros.ai
  apiKey: 'your_api_key'
});

// Store and query memories
await client.storeEpisode({
  agentId: 'agent-1',
  content: 'User asked about pricing plans',
  metadata: { timestamp: '2026-05-03T10:30:00Z' }
});

const results = await client.query({
  agentId: 'agent-1',
  query: 'What plan is the user on?',
  memoryTypes: ['semantic']
});

results.results.forEach(memory => {
  console.log(`${memory.content} (confidence: ${memory.confidence})`);
});
```

---

## Examples

### LangChain Integration

```python
from langchain.memory import KyrosMemory
from langchain.chains import ConversationChain
from langchain.llms import OpenAI

# Initialize Kyros memory
memory = KyrosMemory(
    agent_id="chatbot-1",
    api_key="your_api_key"
)

# Create conversation chain
conversation = ConversationChain(
    llm=OpenAI(),
    memory=memory
)

# Chat with persistent memory
response = conversation.predict(input="My name is Alice")
# Memory automatically stored

response = conversation.predict(input="What's my name?")
# → "Your name is Alice"
```

### Multi-Agent System

```python
import kyros

client = kyros.Client(api_key="your_api_key")

# Agent 1: Research agent
client.remember("researcher", "Found 3 relevant papers on neural networks")

# Agent 2: Writer agent queries researcher's findings
results = client.recall("researcher", "What papers did you find?")
papers = results.results[0].content

# Writer uses the information
client.remember("writer", f"Writing article based on: {papers}")
```

### Causal Reasoning

```python
# Store causal relationships
client.store_causal_edge(
    agent_id="agent-1",
    cause_memory_id="mem_abc123",
    effect_memory_id="mem_def456",
    confidence=0.95
)

# Query causal chains
chain = client.get_causal_chain(
    agent_id="agent-1",
    memory_id="mem_def456"
)

# Understand why something happened
for link in chain:
    print(f"{link.cause} → {link.effect} (confidence: {link.confidence})")
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Your Application                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Kyros SDK (Python/TS)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Kyros API Server (FastAPI)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Episodic   │  │   Semantic   │  │  Procedural  │      │
│  │    Memory    │  │    Memory    │  │    Memory    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Integrity  │  │    Decay     │  │    Belief    │      │
│  │    Proofs    │  │    Engine    │  │ Propagation  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Storage Layer (PostgreSQL + Redis)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PostgreSQL  │  │    Redis     │  │   pgvector   │      │
│  │  (Memories)  │  │   (Cache)    │  │ (Embeddings) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## Documentation

### Getting Started
- [Introduction](./docs/introduction.md) - Learn about Kyros and its architecture
- [Quick Start Guide](./docs/quickstart.md) - Get up and running in 5 minutes
- [Core Concepts](./docs/concepts.md) - Understand memory types and features

### SDK References
- [Python SDK](./docs/python-sdk.md) - Complete Python API reference
- [TypeScript SDK](./docs/typescript-sdk.md) - Complete TypeScript API reference

### Deployment
- [Self-Hosting Guide](./docs/self-hosting.md) - Deploy Kyros on your infrastructure
- [Configuration](./docs/configuration.md) - Environment variables and settings
- [Security Best Practices](./SECURITY.md) - Secure your deployment

### Advanced Topics
- [Architecture Deep Dive](./docs/architecture.md) - System design and internals

---


## Community

### Get Help

- **Documentation**: [docs.kyros.ai](https://docs.kyros.ai)
- **GitHub Discussions**: [Ask questions](https://github.com/Kyros-494/kyros-ai/discussions)
- **GitHub Issues**: [Report bugs](https://github.com/Kyros-494/kyros-ai/issues)
- **Email**: [kyros.494@gmail.com](mailto:kyros.494@gmail.com)

### Stay Updated

- **Star this repo** to follow development
- **Watch releases** for new versions

### Contributing

We welcome contributions from the community! See our [Contributing Guide](./CONTRIBUTING.md) for:
- Code of Conduct
- Development setup
- Commit conventions
- Pull request process
- Testing requirements

**Good First Issues**: [View beginner-friendly tasks →](https://github.com/Kyros-494/kyros-ai/labels/good%20first%20issue)

---

## License

Kyros uses an **Open Core** licensing model:

- **Server Core**: [Apache 2.0 License](./LICENSE) - Free to self-host and modify
- **SDKs & Integrations**: [MIT License](./LICENSE-MIT) - Free to use in any project
- **Enterprise Modules**: Commercial License - [Contact us](mailto:kyros.494@gmail.com)

This means you can:
- ✅ Use Kyros for free in commercial projects
- ✅ Self-host on your own infrastructure
- ✅ Modify the source code
- ✅ Distribute your modifications
- ❌ Use the "Kyros" trademark without permission

See [LICENSE](./LICENSE) and [LICENSE-MIT](./LICENSE-MIT) for full terms.

---

## Security

We take security seriously. If you discover a security vulnerability, please email [kyros.494@gmail.com](mailto:kyros.494@gmail.com) instead of using the issue tracker.

- **Response Time**: Within 48 hours
- **Patch Timeline**: 7 days for critical issues
- **Disclosure**: Coordinated disclosure policy

See [SECURITY.md](./SECURITY.md) for our full security policy.

---

## Acknowledgments

Kyros is built on the shoulders of giants:

- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Reliable database
- **pgvector** - Vector similarity search
- **Redis** - High-performance caching
- **Sentence Transformers** - Embedding models
- **LangChain** - LLM application framework

Special thanks to all our [contributors](https://github.com/Kyros-494/kyros-ai/graphs/contributors) who make this project possible.

---

<div align="center">
  <p>
    <strong>Built with ❤️ by the Kyros team</strong>
  </p>
  <p>
    <a href="https://kyros.ai">Website</a> •
    <a href="https://docs.kyros.ai">Documentation</a> •
    <a href="https://github.com/Kyros-494/kyros-ai">GitHub</a> •
  </p>
  <p>
    <sub>Copyright © 2026 Kyros. All rights reserved.</sub>
  </p>
</div>
