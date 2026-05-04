# Changelog

All notable changes to the Kyros Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-05-03

### Added

#### Core Features
- **KyrosClient**: Main client class for interacting with Kyros API
- **Episodic Memory**: Store and recall conversation history, actions, observations
  - `remember()` - Store episodic memories
  - `recall()` - Search memories with semantic similarity
  - `forget()` - Delete memories (soft delete)
- **Semantic Memory**: Store and query facts as subject-predicate-object triples
  - `store_fact()` - Store semantic facts
  - `query_facts()` - Query facts with semantic search
- **Procedural Memory**: Store and match workflows, skills, procedures
  - `store_procedure()` - Store procedures
  - `match_procedure()` - Find matching procedures for tasks
  - `report_outcome()` - Report execution outcomes
- **Unified Search**: Search across all memory types
  - `search()` - Unified semantic search

#### Advanced Features
- **Causal Reasoning**: Get causal explanations for memories
  - `explain()` - Get causal ancestry chain
- **Integrity Verification**: Cryptographic integrity proofs
  - `get_memory_proof()` - Get integrity proof for memory
  - `audit_integrity()` - Audit all memories for agent
- **Memory Decay**: Ebbinghaus forgetting curves
  - `get_staleness_report()` - Get decay statistics
  - `get_decay_rates()` - Get decay rate configuration
  - `set_decay_rates()` - Update decay rates
- **Export/Import**: Backup and restore memories
  - `export_memories()` - Export all memories
  - `import_memories()` - Import memories
- **Embedding Migration**: Migrate between embedding models
  - `migrate_embeddings()` - Migrate embeddings

#### Framework Integrations
- **LangChain**: `KyrosChatMemory` for LangChain chains
- **LlamaIndex**: `KyrosMemory` for LlamaIndex chat engines
- **AutoGen**: `inject_kyros_memory()` for AutoGen agents
- **CrewAI**: `get_kyros_tools()` for CrewAI agents

#### Error Handling
- `KyrosError` - Base exception class
- `AuthenticationError` - 401/403 errors
- `RateLimitError` - 429 errors with retry metadata
- `NotFoundError` - 404 errors
- `ValidationError` - 422 errors
- `ServerError` - 5xx errors
- `TimeoutError` - Request timeout errors
- `ConnectionError` - Connection failure errors

#### Type Safety
- Full Pydantic models for all request/response types
- Type hints throughout the codebase
- Strict MyPy type checking

#### Developer Experience
- Comprehensive documentation
- Code examples for all features
- Context manager support (`with` statement)
- Environment variable configuration
- Custom base URL support (for self-hosted)
- Configurable timeout

### Technical Details

- **Python Version**: 3.11+
- **Dependencies**: httpx, pydantic
- **HTTP Client**: httpx (modern, async-capable)
- **Data Validation**: Pydantic v2
- **Type Checking**: MyPy strict mode
- **Code Quality**: Ruff linting and formatting

### Documentation

- Comprehensive README with examples
- API reference documentation
- Framework integration guides
- Error handling guide
- Development setup guide

### Testing

- Unit tests for core functionality
- Integration tests for API endpoints
- Test fixtures and utilities
- pytest configuration

---

## [Unreleased]

### Planned Features

- Async client support (`AsyncKyrosClient`)
- Batch operations for bulk memory storage
- Streaming responses for large exports
- Retry logic with exponential backoff
- Request/response logging
- Metrics collection
- Connection pooling
- More framework integrations (Haystack, Semantic Kernel, etc.)

---

[0.1.0]: https://github.com/Kyros-494/kyros-ai/releases/tag/sdk-v0.1.0
