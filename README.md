<div align="center">
  <img src="https://raw.githubusercontent.com/Kyros-494/kyros-ai/master/docs/assets/kyros-logo.png" alt="Kyros Logo" width="120" />
</div>

<h1 align="center">Kyros — The Memory OS for AI Agents</h1>

<div align="center">
  <p><strong>Give your AI agents secure, self-correcting, persistent memory in 3 lines of code.</strong></p>

  [![PyPI](https://img.shields.io/pypi/v/kyros-sdk?color=blue)](https://pypi.org/project/kyros-sdk/)
  [![npm](https://img.shields.io/npm/v/@kyros/sdk?color=blue)](https://www.npmjs.com/package/@kyros/sdk)
  [![GitHub Stars](https://img.shields.io/github/stars/Kyros-494/kyros-ai?style=social)](https://github.com/Kyros-494/kyros-ai)
  [![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
</div>

<br/>

Every AI agent today is **amnesiac**. It forgets everything between sessions — user preferences, past actions, and learned behaviors. Developers duct-tape memory together with Redis, Postgres, and custom logic, rebuilding the same fragile wheel on every project.

**Kyros fixes this.** One SDK call. Three memory types. Works with any model, any framework.

```python
import kyros

client = kyros.Client(api_key="mk_live_...")

# Your agent remembers
client.remember("my-agent", "User prefers Python and dark mode")

# Your agent recalls
results = client.recall("my-agent", "What does the user prefer?")
print(results.results[0].content)
# → "User prefers Python and dark mode"
```

---

## ✨ Features

Kyros goes far beyond a simple vector database by adding biological memory mechanics.

| Feature | Description |
|---------|-------------|
| 🧠 **Three Memory Types** | Stores **Episodic** (what happened), **Semantic** (what is true), and **Procedural** (how to do things). |
| 🛡️ **Poisoning Defense** | Merkle-tree cryptographic proofs ensure that an agent's memory cannot be maliciously altered or tampered with. |
| 📉 **Ebbinghaus Decay** | Built-in forgetting curves. Stale, unused information decays out of context naturally, preventing memory bloat. |
| 🕸️ **Belief Propagation** | When a fact is contradicted (e.g., a user changes jobs), Kyros automatically ripples confidence updates through the semantic graph. |
| 🤖 **Model-Agnostic** | Works with OpenAI, Anthropic, Gemini, Llama, Mistral — any LLM, any framework. |
| ⚡ **<20ms Recall** | pgvector-powered semantic search with Redis caching. Fast enough for real-time streaming agents. |

---

## 🚀 Quickstart (Self-Hosted)

Kyros Community Edition is 100% open source and self-hostable.

### 1. Start the Server

```bash
git clone https://github.com/Kyros-494/kyros-ai.git
cd kyros-ai
docker compose up -d
```
*The server runs locally at `http://localhost:8000` with an embedded PostgreSQL + Redis stack.*

### 2. Install the SDK

**Python:**
```bash
pip install kyros-sdk
```

**TypeScript:**
```bash
npm install @kyros/sdk
```

### 3. Connect and Remember

```python
import kyros

# Connect to your local self-hosted instance
client = kyros.Client(base_url="http://localhost:8000", api_key="mk_test_your_api_key_here")

# Store semantic memory (what is true)
client.store_fact("support-agent", subject="user_123", predicate="plan", value="Pro")

# Query by meaning
results = client.query_facts("support-agent", "What plan is the user on?")
print(results.results[0].content)
```

---

## 📚 Documentation

Dive into our comprehensive guides to master Kyros:

- 📖 [**Introduction**](./docs/introduction.md)
- 🚀 [**Quickstart**](./docs/quickstart.md)
- 🏛️ [**Core Concepts**](./docs/concepts.md)
- 🧰 [**Python SDK Reference**](./docs/python-sdk.md)
- 🛠️ [**Self-Hosting Guide**](./docs/self-hosting.md)
- 📊 [**Benchmarking Standard**](./docs/benchmarking/README.md)

---

## 🏢 Kyros Enterprise

While the Kyros Community Edition provides a complete, self-contained memory engine, **Kyros Enterprise** is designed for organizations that need multi-agent coordination, strict compliance, and managed infrastructure.

Enterprise Features include:
- **Federated Intelligence**: Agents learn from a global network of anonymized procedure outcomes.
- **SOC2 Type II & HIPAA**: Full compliance coverage and audit streaming.
- **Customer-Managed Encryption Keys (CMEK)**: Bring your own AWS/GCP KMS.
- **Role-Based Access Control & SSO**: Secure your agent infrastructure.

[**Learn more about Kyros Enterprise →**](https://kyros.ai/enterprise)

---

## 🤝 Contributing

We welcome contributions from the community! Please read our [**Contributing Guidelines**](./CONTRIBUTING.md) to get started.

- 🐛 [Report a bug](https://github.com/Kyros-494/kyros-ai/issues/new?template=bug_report.md)
- 💡 [Request a feature](https://github.com/Kyros-494/kyros-ai/issues/new?template=feature_request.md)

---

## 📜 License

Kyros operates under an Open Core model:
- **SDKs & Integrations**: [MIT License](./LICENSE-MIT) — Free to use in any project.
- **Kyros Server Core**: [Apache 2.0](./LICENSE) — Free to self-host and modify.
- **Enterprise Modules**: Commercial License.

*For more details on how the system works, read the [Introduction](./docs/introduction.md).*
