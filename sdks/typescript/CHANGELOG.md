# Changelog

All notable changes to `@kyros/sdk` are documented here.

## [Unreleased]

## [0.1.0] — 2026-04-27

### Added
- `KyrosClient` with full episodic, semantic, and procedural memory support
- `remember()`, `recall()`, `forget()` — episodic memory lifecycle
- `storeFact()`, `queryFacts()` — semantic knowledge graph
- `storeProcedure()`, `matchProcedure()`, `reportOutcome()` — procedural memory
- `search()` — unified search across all memory types
- `summarise()`, `exportMemories()`, `importMemories()` — admin operations
- `getStalenessReport()`, `getDecayRates()`, `setDecayRates()` — Ebbinghaus decay
- `getMemoryProof()`, `auditIntegrity()` — Merkle integrity verification
- `explain()` — causal graph traversal
- `migrateEmbeddings()` — cross-model embedding migration
- Vercel AI SDK integration (`withKyrosMemory`)
- Full TypeScript types with strict null checks
- Typed error classes: `AuthenticationError`, `RateLimitError`, `NotFoundError`, `ValidationError`, `ServerError`

[Unreleased]: https://github.com/Kyros-494/kyros-ai/compare/sdk-v0.1.0...HEAD
[0.1.0]: https://github.com/Kyros-494/kyros-ai/releases/tag/sdk-v0.1.0
