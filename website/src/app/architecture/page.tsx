"use client";

import React, { useState, useEffect } from "react";

/* ─── Design tokens shorthand ─────────────────────────── */
const S = {
 border: "2px solid var(--border)",
 borderLight: "1px solid var(--border-light)",
 shadow: "var(--shadow)",
 shadowLg: "var(--shadow-lg)",
};

/* ─── Flow step types ─────────────────────────────────── */
type FlowKey = "idle" | "store" | "recall";

/* ─── Architecture layers data ────────────────────────── */
const LAYERS = [
 {
 id: "sdk",
 num: "01",
 color: "#3b82f6",
 colorAlpha: "rgba(59,130,246,0.12)",
 colorBorder: "rgba(59,130,246,0.35)",
 icon: "📦",
 name: "Client SDK Layer",
 tagline: "How your code talks to Kyros",
 plain: "This is the starting point. Your application uses our Python or TypeScript SDK to send and retrieve memories. Think of it like a smart HTTP client that handles retries, authentication, and error formatting so you don't have to.",
 technical: "Native SDK wrappers serialize requests into structured JSON payloads with bitemporal parameters (valid_from, valid_until, recorded_at). Implements exponential backoff (base 2, max 5 retries) with jitter for transient network failures. JWT Bearer or X-API-Key headers are injected automatically per tenant config.",
 components: [
 { name: "kyros-py", desc: "Python SDK", tech: "PyPI package" },
 { name: "kyros-ts", desc: "TypeScript SDK", tech: "npm package" },
 { name: "Retry Engine", desc: "Exponential backoff + jitter", tech: "Built-in" },
 { name: "Auth Injector", desc: "API key / JWT auto-injection", tech: "Interceptor" },
 ],
 inputs: ["Your Application Code"],
 outputs: ["Signed HTTP Request → Gateway"],
 },
 {
 id: "gateway",
 num: "02",
 color: "#f59e0b",
 colorAlpha: "rgba(245,158,11,0.12)",
 colorBorder: "rgba(245,158,11,0.35)",
 icon: "🔐",
 name: "API Gateway & Security",
 tagline: "The front door — every request is verified here",
 plain: "Before any memory is touched, every single request is authenticated and rate-limited here. This layer is like a security checkpoint at an airport — it verifies your identity, checks you're not sending too many requests at once, and routes you to the right place.",
 technical: "FastAPI router performs path matching and dispatches requests. Auth Middleware validates X-API-Key against a salted SHA-256 hash stored in Postgres, or decodes RS256-signed JWTs. Rate limiter uses a Redis sliding-window counter (per-tenant, per-endpoint). Public routes (health-check, docs) are whitelisted and bypass auth entirely.",
 components: [
 { name: "FastAPI Router", desc: "Route dispatch & OpenAPI spec", tech: "Python FastAPI" },
 { name: "Auth Middleware", desc: "API Key / JWT RS256 validation", tech: "PyJWT + bcrypt" },
 { name: "Rate Limiter", desc: "Sliding-window per-tenant throttle", tech: "Redis + Lua" },
 { name: "CORS / TLS", desc: "Origin policy + HTTPS enforcement", tech: "nginx proxy" },
 ],
 inputs: ["SDK HTTP Request"],
 outputs: ["Verified Request → Memory Engine"],
 },
 {
 id: "engine",
 num: "03",
 color: "#e8f542",
 colorAlpha: "rgba(232,245,66,0.12)",
 colorBorder: "rgba(232,245,66,0.45)",
 icon: "🧠",
 name: "Memory Intelligence Engine",
 tagline: "The brain — where all the smart work happens",
 plain: "This is the core of Kyros. Once a request passes security, this layer decides what to do with the memory: it generates a unique fingerprint (hash), adds it to a tamper-proof audit log, figures out how quickly this memory should fade over time, and checks it doesn't contradict things already stored.",
 technical: "Orchestrates four cognitive sub-services: (1) SHA-256 hasher generates deterministic content fingerprints. (2) Merkle Tree service appends leaf nodes and recalculates parent hashes to root using binary tree reduction. (3) Ebbinghaus calculator initializes retention weights using R(t) = e^(-λt) with per-type decay constants. (4) Belief Resolver runs BFS over the pgvector semantic graph to detect and resolve factual contradictions before write.",
 components: [
 { name: "SHA-256 Hasher", desc: "Deterministic content fingerprinting", tech: "hashlib / crypto" },
 { name: "Merkle Service", desc: "Append-only audit tree construction", tech: "Custom Python" },
 { name: "Ebbinghaus Calc", desc: "Forgetting curve weight computation", tech: "NumPy / math" },
 { name: "Belief Resolver", desc: "Contradiction detection via BFS graph", tech: "NetworkX" },
 { name: "Embedding Engine", desc: "Text → vector via embedding model", tech: "OpenAI / local" },
 ],
 inputs: ["Verified Memory Event"],
 outputs: ["Hashed + Weighted Record → Storage"],
 },
 {
 id: "storage",
 num: "04",
 color: "#10b981",
 colorAlpha: "rgba(16,185,129,0.12)",
 colorBorder: "rgba(16,185,129,0.35)",
 icon: "💾",
 name: "Hybrid Storage Layer",
 tagline: "Where memories live — fast cache + permanent database",
 plain: "After the engine processes a memory, it needs to be saved. We use two systems: a fast in-memory cache (Redis) for memories you'll likely need again soon, and a permanent database (PostgreSQL) for long-term storage with vector search. This dual-storage approach means fast reads without sacrificing durability.",
 technical: "PostgreSQL with pgvector extension stores raw content, SHA-256 hash, Merkle leaf position, embedding vector (1536-dim), bitemporal columns (valid_time, transaction_time), and decay weight. Row-Level Security policies enforce tenant isolation at the database level. Redis stores hot embedding indices with TTL-based eviction. Recall queries execute ANN (approximate nearest neighbor) search using HNSW index, then rerank by decayed weight × cosine similarity.",
 components: [
 { name: "PostgreSQL", desc: "Primary relational + vector store", tech: "PG 15 + pgvector" },
 { name: "HNSW Index", desc: "Approximate nearest-neighbor search", tech: "pgvector HNSW" },
 { name: "Redis Cache", desc: "Hot query result caching", tech: "Redis 7 + TTL" },
 { name: "Row-Level Security", desc: "Tenant isolation at DB level", tech: "PG RLS policies" },
 { name: "Bitemporal Cols", desc: "valid_time + transaction_time", tech: "PG timestamp cols" },
 ],
 inputs: ["Processed Memory Record"],
 outputs: ["Stored + Indexed → Query Results"],
 },
];

/* ─── Data flows ──────────────────────────────────────── */
const FLOWS: Record<
 "store" | "recall",
 { label: string; color: string; steps: { node: string; label: string; detail: string }[] }
> = {
 store: {
 label: "Store Memory",
 color: "#e8f542",
 steps: [
 { node: "sdk", label: "1. SDK Ingestion", detail: "kyros.ingest() called with content, user_id, type, tags." },
 { node: "gateway", label: "2. Auth & Rate Check", detail: "API key validated. Rate limit checked. Request admitted." },
 { node: "engine", label: "3. Processing Pipeline", detail: "Hash generated → Merkle appended → Decay initialized → Beliefs checked." },
 { node: "storage", label: "4. Persist to DB", detail: "Record written to PostgreSQL. Embedding indexed in HNSW. Hot key cached in Redis." },
 ],
 },
 recall: {
 label: "Recall Memory",
 color: "#60a5fa",
 steps: [
 { node: "sdk", label: "1. SDK Recall Query", detail: "kyros.recall() called with query text, user_id, top_k, min_weight." },
 { node: "gateway", label: "2. Auth & Routing", detail: "Token validated. Request routed to recall endpoint." },
 { node: "storage", label: "3. Vector Search", detail: "Query embedded. ANN search via HNSW. Results filtered by decay weight threshold." },
 { node: "engine", label: "4. Reranking", detail: "Scores = cosine_similarity × retention_weight. Top-k returned to SDK." },
 ],
 },
};

/* ─── Tech stack details ──────────────────────────────── */
const TECH_STACK = [
 { category: "API Framework", name: "FastAPI", reason: "Async Python, automatic OpenAPI docs, Pydantic validation", icon: "" },
 { category: "Primary Database", name: "PostgreSQL 15", reason: "ACID compliance, Row-Level Security, bitemporal columns", icon: "🗄️" },
 { category: "Vector Search", name: "pgvector HNSW", reason: "ANN search in-database, no separate vector DB needed", icon: "🔍" },
 { category: "Caching Layer", name: "Redis 7", reason: "Sub-millisecond hot key access, TTL-based eviction", icon: "" },
 { category: "Cryptography", name: "SHA-256 + Merkle", reason: "Tamper-evident audit trail, O(log n) proof verification", icon: "🔐" },
 { category: "Memory Decay", name: "Ebbinghaus Model", reason: "Psychologically grounded retention weighting", icon: "📉" },
 { category: "Client SDKs", name: "Python + TypeScript", reason: "Native language support for the most common AI stacks", icon: "📦" },
 { category: "Embeddings", name: "OpenAI / Local", reason: "Pluggable embedding provider — cloud or on-premise", icon: "🧮" },
];

/* ─── Key properties ──────────────────────────────────── */
const PROPERTIES = [
 {
 icon: "🏛️",
 title: "Tenant Isolation",
 plain: "Every user's memories are completely separated from everyone else's — like private rooms in a building.",
 technical: "PostgreSQL Row-Level Security (RLS) policies enforce tenant boundaries at the database engine level. No application-level filter can accidentally leak cross-tenant data.",
 },
 {
 icon: "🔒",
 title: "Tamper-Proof Audit",
 plain: "Every memory gets a unique fingerprint. If anyone changes a memory, the fingerprint no longer matches — exposing the tampering.",
 technical: "SHA-256 hash of each memory event is stored as a Merkle tree leaf. Any mutation invalidates all ancestor hashes to root. Root hash snapshots can be stored externally for independent verification.",
 },
 {
 icon: "⏳",
 title: "Bitemporal History",
 plain: "You can ask 'What did the system know about a user on March 1st?' — and get the exact answer, even months later.",
 technical: "Every row carries valid_time (when the fact was true in reality) and transaction_time (when it was recorded in the system). AS OF queries reconstruct any historical state without any data mutation.",
 },
 {
 icon: "📉",
 title: "Intelligent Forgetting",
 plain: "Old, irrelevant memories fade away automatically — so the AI doesn't get confused by stale information.",
 technical: "Retention weight W(t) = e^(-λt). Semantic memories: λ=0.003 (half-life ~231 days). Episodic: λ=0.04 (half-life ~17 days). Recall queries filter on min_weight threshold, pruning low-signal context automatically.",
 },
 {
 icon: "🔍",
 title: "Semantic Recall",
 plain: "You search by meaning, not keywords. Ask 'tell me about the user's job' and Kyros finds all related memories even if the word 'job' wasn't used.",
 technical: "Text is converted to high-dimensional embedding vectors. ANN search uses HNSW graph index (M=16, ef_construction=200). Results are reranked by combined score: cosine_similarity × retention_weight × recency_bonus.",
 },
 {
 icon: "🌐",
 title: "Multi-Agent Shared State",
 plain: "Multiple AI agents can share the same memory space — so they always work from the same facts without duplicating work.",
 technical: "Session-scoped memory namespaces allow agent_id-tagged reads/writes within a shared tenant space. Belief resolver prevents contradictory facts from coexisting across agent writes.",
 },
];

/* ─── Component ──────────────────────────────────────── */
export default function ArchitecturePage() {
 const [activeFlow, setActiveFlow] = useState<FlowKey>("idle");
 const [activeStep, setActiveStep] = useState(-1);
 const [activeLayerId, setActiveLayerId] = useState<string | null>(null);
 const [viewMode, setViewMode] = useState<"plain" | "technical">("plain");
 const [animating, setAnimating] = useState(false);

 useEffect(() => {
 if (activeFlow === "idle") {
 const t = setTimeout(() => { setActiveStep(-1); }, 0);
 return () => clearTimeout(t);
 }
 const tStart = setTimeout(() => {
 setActiveStep(0);
 setAnimating(true);
 }, 0);
 const flowSteps = FLOWS[activeFlow].steps;
 let step = 0;
 const interval = setInterval(() => {
 step++;
 if (step >= flowSteps.length) {
 clearInterval(interval);
 setAnimating(false);
 setTimeout(() => { setActiveStep(-1); }, 2000);
 return;
 }
 setActiveStep(step);
 }, 1400);
 return () => {
 clearTimeout(tStart);
 clearInterval(interval);
 };
 }, [activeFlow]);

 const triggerFlow = (flow: "store" | "recall") => {
 if (animating) return;
 setActiveFlow("idle");
 setTimeout(() => setActiveFlow(flow), 80);
 };

 const activeFlowData = activeFlow !== "idle" ? FLOWS[activeFlow] : null;
 const activeLayerData = activeLayerId ? LAYERS.find((l) => l.id === activeLayerId) : null;

 /* ─── Render layer box in the diagram ─────────────── */
 const renderLayerBox = (layer: typeof LAYERS[0], flowStepIndex: number) => {
 const isActiveInFlow = activeFlowData !== null && activeFlowData.steps[activeStep]?.node === layer.id;
 const isPastStep = activeFlowData !== null && activeFlowData.steps.slice(0, activeStep).some((s) => s.node === layer.id);
 const isSelected = activeLayerId === layer.id;

 return (
 <div
 key={layer.id}
 onClick={() => setActiveLayerId(isSelected ? null : layer.id)}
 style={{
 position: "relative",
 padding: "1.25rem 1.5rem 1.5rem",
 border: isActiveInFlow
 ? `2px solid ${layer.color}`
 : isSelected
 ? S.border
 : S.borderLight,
 borderRadius: 12,
 background: isActiveInFlow
 ? layer.colorAlpha
 : isSelected
 ? "var(--bg-alt)"
 : "var(--bg)",
 cursor: "pointer",
 transition: "all 0.25s ease",
 boxShadow: isActiveInFlow
 ? `0 0 24px ${layer.color}40, ${S.shadowLg}`
 : isSelected
 ? S.shadow
 : "none",
 transform: isActiveInFlow ? "translateY(-4px)" : "none",
 flex: 1,
 minWidth: 160,
 }}
 >
 {/* Active pulse ring */}
 {isActiveInFlow && (
 <div
 style={{
 position: "absolute",
 inset: -4,
 borderRadius: 15,
 border: `2px solid ${layer.color}`,
 animation: "pulse-ring 1s ease-out infinite",
 pointerEvents: "none",
 }}
 />
 )}

 {/* Step number badge */}
 <div style={{ display: "flex", alignItems: "center", gap: "0.625rem", marginBottom: "0.875rem" }}>
 <span
 style={{
 display: "flex",
 alignItems: "center",
 justifyContent: "center",
 width: 32,
 height: 32,
 borderRadius: 8,
 background: isActiveInFlow ? layer.color : "var(--bg-dark)",
 color: isActiveInFlow ? "#111" : layer.color,
 fontFamily: "var(--font-mono)",
 fontSize: "0.7rem",
 fontWeight: 900,
 border: `1.5px solid ${layer.colorBorder}`,
 flexShrink: 0,
 transition: "all 0.25s",
 }}
 >
 {isPastStep ? "" : layer.num}
 </span>
 <span style={{ fontSize: "0.6rem", fontFamily: "var(--font-mono)", fontWeight: 800, color: layer.color, textTransform: "uppercase" as const, letterSpacing: "0.08em" }}>
 Layer {layer.num}
 </span>
 </div>

 {/* Icon + name */}
 <div style={{ marginBottom: "0.5rem" }}>
 <div style={{ fontSize: "1.5rem", marginBottom: "0.35rem" }}>{layer.icon}</div>
 <h3 style={{ fontSize: "0.88rem", fontWeight: 900, letterSpacing: "-0.02em", color: "var(--text)", margin: 0, lineHeight: 1.25 }}>
 {layer.name}
 </h3>
 </div>

 <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", margin: 0, lineHeight: 1.6 }}>
 {layer.tagline}
 </p>

 {/* Click prompt */}
 <div style={{ marginTop: "0.75rem", fontSize: "0.6rem", color: isSelected ? layer.color : "var(--text-muted)", fontFamily: "var(--font-mono)", fontWeight: 700, letterSpacing: "0.06em" }}>
 {isSelected ? "▲ Collapse" : "▼ Click to inspect"}
 </div>

 {flowStepIndex > -1 && (
 <div style={{ position: "absolute", top: "0.75rem", right: "0.75rem", padding: "0.15rem 0.4rem", borderRadius: 4, background: isActiveInFlow ? layer.color : "transparent", border: isActiveInFlow ? "none" : `1px solid ${layer.colorBorder}`, fontFamily: "var(--font-mono)", fontSize: "0.55rem", fontWeight: 800, color: isActiveInFlow ? "#111" : layer.color }}>
 {isActiveInFlow ? "ACTIVE" : ""}
 </div>
 )}
 </div>
 );
 };

 return (
 <div style={{ background: "var(--bg)", color: "var(--text)", width: "100%" }}>
 {/* ─── Pulse animation keyframes (injected) ─── */}
 <style>{`
 @keyframes pulse-ring {
 0% { opacity: 1; transform: scale(1); }
 100% { opacity: 0; transform: scale(1.06); }
 }
 @keyframes flow-dot {
 0% { opacity: 0; transform: scale(0.5); }
 30% { opacity: 1; transform: scale(1); }
 70% { opacity: 1; transform: scale(1); }
 100% { opacity: 0; transform: scale(0.5); }
 }
 @keyframes slide-in-up {
 from { opacity: 0; transform: translateY(12px); }
 to { opacity: 1; transform: translateY(0); }
 }
 `}</style>

 {/* ─── Hero ──────────────────────────────────── */}
 <section
 style={{
 background: "var(--bg-dark)",
 color: "var(--text-on-dark)",
 borderBottom: S.border,
 padding: "5rem 1.5rem 4rem",
 }}
 >
 <div style={{ maxWidth: "1152px", margin: "0 auto" }}>
 <div
 style={{
 display: "inline-flex",
 alignItems: "center",
 gap: "0.5rem",
 padding: "0.3rem 0.9rem",
 borderRadius: 9999,
 border: "1.5px solid rgba(232,245,66,0.4)",
 background: "rgba(232,245,66,0.1)",
 fontFamily: "var(--font-mono)",
 fontSize: "0.65rem",
 fontWeight: 700,
 letterSpacing: "0.1em",
 textTransform: "uppercase" as const,
 color: "var(--primary)",
 marginBottom: "1.5rem",
 }}
 >
 ◆ System Architecture
 </div>
 <h1
 style={{
 fontSize: "clamp(2.25rem, 5vw, 4rem)",
 fontWeight: 900,
 letterSpacing: "-0.04em",
 color: "var(--text-on-dark)",
 margin: "0 0 1.25rem",
 lineHeight: 1.05,
 }}
 >
 How Kyros works<br />under the hood
 </h1>
 <p style={{ color: "rgba(249,247,242,0.6)", maxWidth: "58ch", fontSize: "1rem", lineHeight: 1.8, margin: "0 0 2.5rem" }}>
 A four-layer architecture purpose-built for AI memory: secure ingestion, cryptographic integrity, intelligent decay, and hybrid vector storage.
 Click anything to learn exactly what it does — in plain English or technical detail.
 </p>

 {/* Architecture summary stats */}
 <div style={{ display: "flex", gap: "2.5rem", flexWrap: "wrap" }}>
 {[
 { value: "4", label: "Architecture Layers" },
 { value: "SHA-256", label: "Hash Algorithm" },
 { value: "HNSW", label: "Vector Index" },
 { value: "RLS", label: "Tenant Isolation" },
 ].map((s) => (
 <div key={s.label}>
 <div style={{ fontSize: "1.75rem", fontWeight: 900, fontFamily: "var(--font-mono)", color: "var(--primary)", lineHeight: 1 }}>
 {s.value}
 </div>
 <div style={{ fontSize: "0.68rem", color: "rgba(249,247,242,0.45)", marginTop: "0.3rem", fontFamily: "var(--font-mono)", letterSpacing: "0.05em" }}>
 {s.label}
 </div>
 </div>
 ))}
 </div>
 </div>
 </section>

 {/* ─── View mode toggle ──────────────────────── */}
 <div style={{ borderBottom: S.borderLight, background: "var(--bg-alt)", padding: "0.875rem 1.5rem", position: "sticky", top: 64, zIndex: 15 }}>
 <div style={{ maxWidth: "1152px", margin: "0 auto", display: "flex", alignItems: "center", gap: "0.875rem", flexWrap: "wrap" }}>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.65rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" as const, letterSpacing: "0.1em" }}>
 Explanation Mode:
 </span>
 {(["plain", "technical"] as const).map((mode) => (
 <button
 key={mode}
 onClick={() => setViewMode(mode)}
 style={{
 padding: "0.35rem 1rem",
 border: viewMode === mode ? S.border : S.borderLight,
 borderRadius: 9999,
 background: viewMode === mode ? "var(--text)" : "var(--bg)",
 color: viewMode === mode ? "var(--bg)" : "var(--text-muted)",
 fontFamily: "var(--font-mono)",
 fontSize: "0.7rem",
 fontWeight: 700,
 cursor: "pointer",
 letterSpacing: "0.04em",
 transition: "all 0.15s",
 }}
 >
 {mode === "plain" ? "🗣️ Plain English" : "️ Technical Deep Dive"}
 </button>
 ))}
 <span style={{ marginLeft: "auto", fontSize: "0.68rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
 Click any layer box to inspect it
 </span>
 </div>
 </div>

 {/* ─── Interactive Architecture Diagram ──────── */}
 <section style={{ padding: "3rem 1.5rem", background: "var(--bg)", borderBottom: S.border }}>
 <div style={{ maxWidth: "1152px", margin: "0 auto" }}>

 {/* Section title */}
 <div style={{ marginBottom: "2rem" }}>
 <h2 style={{ fontSize: "1.5rem", fontWeight: 900, letterSpacing: "-0.03em", margin: "0 0 0.4rem" }}>
 System Dataflow Diagram
 </h2>
 <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", margin: 0 }}>
 Trace exactly what happens when you store or recall a memory. Click a flow button, then click any layer to inspect it.
 </p>
 </div>

 {/* Flow control buttons */}
 <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", marginBottom: "2rem", alignItems: "center" }}>
 <button
 onClick={() => triggerFlow("store")}
 disabled={animating}
 style={{
 padding: "0.625rem 1.5rem",
 border: S.border,
 borderRadius: 8,
 background: activeFlow === "store" ? "#e8f542" : "var(--bg-dark)",
 color: activeFlow === "store" ? "#111" : "var(--text-on-dark)",
 fontWeight: 800,
 fontSize: "0.82rem",
 cursor: animating ? "not-allowed" : "pointer",
 boxShadow: S.shadow,
 transition: "all 0.15s",
 display: "flex",
 alignItems: "center",
 gap: "0.5rem",
 opacity: animating ? 0.6 : 1,
 fontFamily: "var(--font-mono)",
 }}
 >
 <span style={{ fontSize: "1rem" }}>→</span>
 {animating && activeFlow === "store" ? "Animating…" : "Trace: Store Memory"}
 </button>
 <button
 onClick={() => triggerFlow("recall")}
 disabled={animating}
 style={{
 padding: "0.625rem 1.5rem",
 border: S.border,
 borderRadius: 8,
 background: activeFlow === "recall" ? "#60a5fa" : "var(--bg)",
 color: activeFlow === "recall" ? "#111" : "var(--text)",
 fontWeight: 800,
 fontSize: "0.82rem",
 cursor: animating ? "not-allowed" : "pointer",
 boxShadow: S.shadow,
 transition: "all 0.15s",
 display: "flex",
 alignItems: "center",
 gap: "0.5rem",
 opacity: animating ? 0.6 : 1,
 fontFamily: "var(--font-mono)",
 }}
 >
 <span style={{ fontSize: "1rem" }}>←</span>
 {animating && activeFlow === "recall" ? "Animating…" : "Trace: Recall Memory"}
 </button>
 {activeFlow !== "idle" && (
 <button
 onClick={() => { setActiveFlow("idle"); setActiveStep(-1); }}
 style={{
 padding: "0.625rem 1rem",
 border: S.borderLight,
 borderRadius: 8,
 background: "transparent",
 color: "var(--text-muted)",
 fontWeight: 600,
 fontSize: "0.78rem",
 cursor: "pointer",
 fontFamily: "var(--font-mono)",
 }}
 >
 Clear
 </button>
 )}
 </div>

 {/* Architecture Diagram */}
 <div
 style={{
 border: S.border,
 borderRadius: "var(--radius)",
 background: "var(--bg-dark)",
 padding: "2.5rem 2rem",
 boxShadow: S.shadowLg,
 }}
 >
 {/* Top label */}
 <div style={{ textAlign: "center", marginBottom: "2rem" }}>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.62rem", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.12em", color: "rgba(249,247,242,0.3)" }}>
 Kyros AI · System Architecture · 4-Layer Stack
 </span>
 </div>

 {/* External: Your App */}
 <div style={{ display: "flex", justifyContent: "center", marginBottom: "1.25rem" }}>
 <div style={{ padding: "0.625rem 1.75rem", border: "1.5px dashed rgba(249,247,242,0.2)", borderRadius: 8, display: "flex", alignItems: "center", gap: "0.625rem" }}>
 <span style={{ fontSize: "1.1rem" }}>🖥️</span>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", fontWeight: 700, color: "rgba(249,247,242,0.6)" }}>Your Application</span>
 </div>
 </div>

 {/* Down arrow */}
 <div style={{ display: "flex", justifyContent: "center", marginBottom: "1rem" }}>
 <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
 <div style={{ width: 2, height: 20, background: "rgba(249,247,242,0.15)" }} />
 <div style={{ width: 8, height: 8, borderRight: "2px solid rgba(249,247,242,0.3)", borderBottom: "2px solid rgba(249,247,242,0.3)", transform: "rotate(45deg)" }} />
 </div>
 </div>

 {/* 4 Layer Boxes */}
 <div style={{ display: "flex", gap: "1rem", alignItems: "stretch", flexWrap: "wrap" }}>
 {LAYERS.map((layer, idx) => (
 <React.Fragment key={layer.id}>
 {renderLayerBox(layer, idx)}
 {idx < LAYERS.length - 1 && (
 <div style={{ display: "flex", alignItems: "center", flexShrink: 0, padding: "0 0.25rem" }}>
 <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 3 }}>
 {/* animated arrow between layers */}
 <div
 style={{
 width: 32,
 height: 2,
 background: activeFlowData && activeStep > idx
 ? activeFlowData.color
 : "rgba(249,247,242,0.1)",
 transition: "background 0.4s",
 position: "relative",
 }}
 >
 {activeFlowData && activeStep === idx + 1 && (
 <div
 style={{
 position: "absolute",
 right: -4,
 top: "50%",
 transform: "translateY(-50%)",
 width: 10,
 height: 10,
 borderRadius: "50%",
 background: activeFlowData.color,
 animation: "flow-dot 1.4s ease-in-out",
 }}
 />
 )}
 </div>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.5rem", color: "rgba(249,247,242,0.15)" }}>→</span>
 </div>
 </div>
 )}
 </React.Fragment>
 ))}
 </div>

 {/* Down arrow to storage */}
 <div style={{ display: "flex", justifyContent: "center", margin: "1.25rem 0" }}>
 <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
 <div style={{ width: 2, height: 20, background: "rgba(249,247,242,0.15)" }} />
 <div style={{ width: 8, height: 8, borderRight: "2px solid rgba(249,247,242,0.3)", borderBottom: "2px solid rgba(249,247,242,0.3)", transform: "rotate(45deg)" }} />
 </div>
 </div>

 {/* Database row */}
 <div style={{ display: "flex", justifyContent: "center", gap: "1.25rem", flexWrap: "wrap" }}>
 {[
 { name: "PostgreSQL + pgvector", icon: "🗄️", color: "#60a5fa", desc: "Vector + relational storage" },
 { name: "Redis Cache", icon: "", color: "#f97316", desc: "Hot key caching layer" },
 { name: "Merkle Audit Log", icon: "🌳", color: "#a78bfa", desc: "Cryptographic audit trail" },
 ].map((db) => (
 <div
 key={db.name}
 style={{
 padding: "1rem 1.5rem",
 border: `1.5px solid ${db.color}40`,
 borderRadius: 10,
 background: `${db.color}0D`,
 display: "flex",
 alignItems: "center",
 gap: "0.75rem",
 minWidth: 200,
 }}
 >
 <span style={{ fontSize: "1.4rem" }}>{db.icon}</span>
 <div>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", fontWeight: 800, color: db.color }}>
 {db.name}
 </div>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", color: "rgba(249,247,242,0.35)", marginTop: "0.2rem" }}>
 {db.desc}
 </div>
 </div>
 </div>
 ))}
 </div>
 </div>

 {/* Active flow step indicator */}
 {activeFlowData && activeStep >= 0 && (
 <div
 style={{
 marginTop: "1.25rem",
 padding: "1.25rem 1.75rem",
 border: `2px solid ${activeFlowData.color}60`,
 borderRadius: "var(--radius)",
 background: `${activeFlowData.color}0F`,
 display: "flex",
 alignItems: "flex-start",
 gap: "1rem",
 animation: "slide-in-up 0.3s ease-out",
 }}
 >
 <div
 style={{
 width: 36,
 height: 36,
 borderRadius: 8,
 background: activeFlowData.color,
 color: "#111",
 display: "flex",
 alignItems: "center",
 justifyContent: "center",
 fontFamily: "var(--font-mono)",
 fontSize: "0.78rem",
 fontWeight: 900,
 flexShrink: 0,
 }}
 >
 {activeStep + 1}
 </div>
 <div>
 <div style={{ fontSize: "0.88rem", fontWeight: 900, color: "var(--text)", marginBottom: "0.25rem" }}>
 {activeFlowData.steps[activeStep]?.label}
 </div>
 <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", lineHeight: 1.6 }}>
 {activeFlowData.steps[activeStep]?.detail}
 </div>
 </div>
 <div style={{ marginLeft: "auto", fontFamily: "var(--font-mono)", fontSize: "0.6rem", color: "var(--text-muted)", whiteSpace: "nowrap" as const }}>
 Step {activeStep + 1} / {activeFlowData.steps.length}
 </div>
 </div>
 )}
 </div>
 </section>

 {/* ─── Layer Detail Panel (expanded when clicked) ─── */}
 {activeLayerData && (
 <section
 style={{
 padding: "0 1.5rem",
 background: "var(--bg-alt)",
 borderBottom: S.border,
 animation: "slide-in-up 0.3s ease-out",
 }}
 >
 <div style={{ maxWidth: "1152px", margin: "0 auto", padding: "2.5rem 0" }}>
 <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1.75rem", flexWrap: "wrap" }}>
 <span style={{ fontSize: "2rem" }}>{activeLayerData.icon}</span>
 <div>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", fontWeight: 800, color: activeLayerData.color, textTransform: "uppercase" as const, letterSpacing: "0.1em", marginBottom: "0.2rem" }}>
 Layer {activeLayerData.num} — Inspecting
 </div>
 <h2 style={{ fontSize: "1.4rem", fontWeight: 900, letterSpacing: "-0.03em", margin: 0, color: "var(--text)" }}>
 {activeLayerData.name}
 </h2>
 </div>
 <button
 onClick={() => setActiveLayerId(null)}
 style={{ marginLeft: "auto", padding: "0.375rem 0.875rem", border: S.borderLight, borderRadius: 6, background: "var(--bg)", color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: "0.65rem", fontWeight: 700, cursor: "pointer" }}
 >
 Close
 </button>
 </div>

 <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem", flexWrap: "wrap" }}>
 {/* Explanation */}
 <div>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.1em", color: "var(--text-muted)", marginBottom: "0.75rem" }}>
 {viewMode === "plain" ? "🗣️ In Plain English" : "️ Technical Detail"}
 </div>
 <p style={{ fontSize: "0.925rem", color: "var(--text)", lineHeight: 1.85, margin: "0 0 1.5rem" }}>
 {viewMode === "plain" ? activeLayerData.plain : activeLayerData.technical}
 </p>

 {/* Data flow */}
 <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
 <div>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.58rem", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.1em", color: "var(--text-muted)", marginBottom: "0.4rem" }}>
 Receives
 </div>
 {activeLayerData.inputs.map((inp) => (
 <div key={inp} style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.5rem 0.875rem", border: S.borderLight, borderRadius: 6, background: "var(--bg)", marginBottom: "0.375rem" }}>
 <span style={{ fontSize: "0.75rem", color: "#60a5fa" }}>↓</span>
 <span style={{ fontSize: "0.78rem", fontFamily: "var(--font-mono)", color: "var(--text)" }}>{inp}</span>
 </div>
 ))}
 </div>
 <div>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.58rem", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.1em", color: "var(--text-muted)", marginBottom: "0.4rem" }}>
 Passes On
 </div>
 {activeLayerData.outputs.map((out) => (
 <div key={out} style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.5rem 0.875rem", border: `1px solid ${activeLayerData.colorBorder}`, borderRadius: 6, background: activeLayerData.colorAlpha, marginBottom: "0.375rem" }}>
 <span style={{ fontSize: "0.75rem", color: activeLayerData.color }}>→</span>
 <span style={{ fontSize: "0.78rem", fontFamily: "var(--font-mono)", color: "var(--text)" }}>{out}</span>
 </div>
 ))}
 </div>
 </div>
 </div>

 {/* Components */}
 <div>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.1em", color: "var(--text-muted)", marginBottom: "0.75rem" }}>
 Internal Components
 </div>
 <div style={{ display: "flex", flexDirection: "column", gap: "0.625rem" }}>
 {activeLayerData.components.map((comp) => (
 <div
 key={comp.name}
 style={{
 padding: "0.875rem 1.125rem",
 border: S.borderLight,
 borderLeft: `3px solid ${activeLayerData.color}`,
 borderRadius: "0 8px 8px 0",
 background: "var(--bg)",
 display: "flex",
 justifyContent: "space-between",
 alignItems: "flex-start",
 gap: "0.75rem",
 }}
 >
 <div>
 <div style={{ fontSize: "0.82rem", fontWeight: 800, color: "var(--text)", marginBottom: "0.2rem" }}>{comp.name}</div>
 <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{comp.desc}</div>
 </div>
 <span style={{ padding: "0.18rem 0.5rem", borderRadius: 4, background: "var(--bg-dark)", color: activeLayerData.color, fontFamily: "var(--font-mono)", fontSize: "0.58rem", fontWeight: 700, whiteSpace: "nowrap" as const, flexShrink: 0 }}>
 {comp.tech}
 </span>
 </div>
 ))}
 </div>
 </div>
 </div>
 </div>
 </section>
 )}

 {/* ─── Key Architectural Properties ──────────── */}
 <section style={{ padding: "4rem 1.5rem", background: "var(--bg)", borderBottom: S.border }}>
 <div style={{ maxWidth: "1152px", margin: "0 auto" }}>
 <div style={{ marginBottom: "2.5rem" }}>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.62rem", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.12em", color: "var(--text-muted)", marginBottom: "0.625rem" }}>
 Design Principles
 </div>
 <h2 style={{ fontSize: "1.75rem", fontWeight: 900, letterSpacing: "-0.04em", margin: "0 0 0.5rem" }}>
 Six properties that make Kyros different
 </h2>
 <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", margin: 0 }}>
 {viewMode === "plain" ? "Explained simply, so anyone can understand." : "With full technical depth for engineers."}
 </p>
 </div>

 <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "1.25rem" }}>
 {PROPERTIES.map((prop) => (
 <div
 key={prop.title}
 style={{
 border: S.border,
 borderRadius: "var(--radius)",
 background: "var(--bg)",
 overflow: "hidden",
 boxShadow: S.shadow,
 transition: "box-shadow 0.2s, transform 0.2s",
 }}
 onMouseEnter={(e) => {
 (e.currentTarget as HTMLElement).style.boxShadow = S.shadowLg;
 (e.currentTarget as HTMLElement).style.transform = "translate(-2px,-2px)";
 }}
 onMouseLeave={(e) => {
 (e.currentTarget as HTMLElement).style.boxShadow = S.shadow;
 (e.currentTarget as HTMLElement).style.transform = "none";
 }}
 >
 <div style={{ padding: "1.25rem 1.5rem", borderBottom: S.border, background: "var(--bg-dark)", display: "flex", alignItems: "center", gap: "0.875rem" }}>
 <span style={{ fontSize: "1.4rem" }}>{prop.icon}</span>
 <h3 style={{ fontSize: "0.95rem", fontWeight: 900, letterSpacing: "-0.02em", color: "var(--text-on-dark)", margin: 0 }}>
 {prop.title}
 </h3>
 </div>
 <div style={{ padding: "1.25rem 1.5rem" }}>
 <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", lineHeight: 1.8, margin: 0 }}>
 {viewMode === "plain" ? prop.plain : prop.technical}
 </p>
 </div>
 </div>
 ))}
 </div>
 </div>
 </section>

 {/* ─── Technology Stack ──────────────────────── */}
 <section style={{ padding: "4rem 1.5rem", background: "var(--bg-alt)", borderBottom: S.border }}>
 <div style={{ maxWidth: "1152px", margin: "0 auto" }}>
 <div style={{ marginBottom: "2.5rem" }}>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.62rem", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.12em", color: "var(--text-muted)", marginBottom: "0.625rem" }}>
 Technology Choices
 </div>
 <h2 style={{ fontSize: "1.75rem", fontWeight: 900, letterSpacing: "-0.04em", margin: "0 0 0.5rem" }}>
 What we use and why
 </h2>
 <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", margin: 0 }}>
 Every technology choice was made deliberately — not just for what it does, but for why it&apos;s the right tool for AI memory.
 </p>
 </div>

 <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "1rem" }}>
 {TECH_STACK.map((tech) => (
 <div
 key={tech.name}
 style={{
 padding: "1.25rem 1.5rem",
 border: S.border,
 borderRadius: "var(--radius)",
 background: "var(--bg)",
 boxShadow: S.shadow,
 display: "flex",
 gap: "1rem",
 alignItems: "flex-start",
 }}
 >
 <span style={{ fontSize: "1.5rem", flexShrink: 0, marginTop: "0.1rem" }}>{tech.icon}</span>
 <div>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.08em", color: "var(--text-muted)", marginBottom: "0.3rem" }}>
 {tech.category}
 </div>
 <div style={{ fontSize: "0.92rem", fontWeight: 900, color: "var(--text)", marginBottom: "0.4rem", letterSpacing: "-0.02em" }}>
 {tech.name}
 </div>
 <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", lineHeight: 1.6 }}>
 {tech.reason}
 </div>
 </div>
 </div>
 ))}
 </div>
 </div>
 </section>

 {/* ─── Request Lifecycle (full path) ─────────── */}
 <section style={{ padding: "4rem 1.5rem 6rem", background: "var(--bg)" }}>
 <div style={{ maxWidth: "1152px", margin: "0 auto" }}>
 <div style={{ marginBottom: "2.5rem" }}>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.62rem", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.12em", color: "var(--text-muted)", marginBottom: "0.625rem" }}>
 Full Request Lifecycle
 </div>
 <h2 style={{ fontSize: "1.75rem", fontWeight: 900, letterSpacing: "-0.04em", margin: "0 0 0.5rem" }}>
 From your code to stored memory — every step
 </h2>
 <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", margin: 0 }}>
 A complete walkthrough of a single <code style={{ fontFamily: "var(--font-mono)", fontSize: "0.85em", background: "var(--bg-alt)", padding: "0.1em 0.35em", borderRadius: 4 }}>kyros.ingest()</code> call — what happens inside the system.
 </p>
 </div>

 <div style={{ display: "flex", flexDirection: "column", gap: 0, border: S.border, borderRadius: "var(--radius)", overflow: "hidden", boxShadow: S.shadowLg }}>
 {[
 {
 step: "01", label: "SDK Call Initiated",
 code: `kyros.ingest(content="User is Alex. Loves Python.", user_id="u123", type="semantic")`,
 desc: "Your application calls the SDK. The SDK serializes the request body and injects your API key into the Authorization header automatically.",
 color: "#3b82f6",
 },
 {
 step: "02", label: "Gateway Authentication",
 code: `POST /v1/memories/ingest\nAuthorization: Bearer eyJhbGci...\nX-Tenant-ID: org_kyros_abc`,
 desc: "The gateway validates your API key against its SHA-256 hash. Checks rate limit (default: 1000 req/min). Extracts tenant_id for RLS scoping.",
 color: "#f59e0b",
 },
 {
 step: "03", label: "Hashing & Merkle Append",
 code: `hash = SHA256("User is Alex. Loves Python.") → "sha256_4af1b2c..."
merkle.append(leaf=hash) # Root recalculated
new_root = "sha256_root_e9f3..."`,
 desc: "A deterministic SHA-256 hash is computed from the content. Appended as a new leaf to the Merkle tree. All parent hashes are recalculated bottom-up to produce a new root.",
 color: "#e8f542",
 },
 {
 step: "04", label: "Embedding & Decay Init",
 code: `embedding = embed_model.encode("User is Alex. Loves Python.")
# → [0.021, -0.314, 0.887, ...] (1536 dimensions)
retention_weight = 1.0 # λ=0.003 for semantic type`,
 desc: "The content is converted to a high-dimensional vector embedding. Initial retention weight is set to 1.0 (100%). The Ebbinghaus decay constant (λ) is assigned based on memory type.",
 color: "#10b981",
 },
 {
 step: "05", label: "Belief Conflict Check",
 code: `# BFS search for semantic contradictions
conflicts = belief_graph.find_contradictions(
 new_content="User is Alex",
 user_id="u123"
)
# → [] (no conflicts found — safe to commit)`,
 desc: "A BFS traversal over the semantic relationship graph checks for factual contradictions (e.g., if 'User is Bob' already exists). Conflicts are flagged or auto-resolved before write.",
 color: "#a78bfa",
 },
 {
 step: "06", label: "Database Commit",
 code: `INSERT INTO memories (
 user_id, content, hash, embedding,
 retention_weight, valid_from, recorded_at, type
) VALUES ('u123', 'User is Alex...', 'sha256_4af1b2c...', '[0.021,...]', 1.0, NOW(), NOW(), 'semantic');
-- HNSW index updated. Redis hot-key cached.`,
 desc: "The complete memory record is written to PostgreSQL. The HNSW vector index is updated for ANN search. The hot embedding is cached in Redis with a TTL for fast subsequent recall.",
 color: "#f97316",
 },
 ].map((item, idx, arr) => (
 <div
 key={item.step}
 style={{
 display: "grid",
 gridTemplateColumns: "60px 1fr",
 borderBottom: idx < arr.length - 1 ? S.borderLight : "none",
 }}
 >
 {/* Step number column */}
 <div
 style={{
 display: "flex",
 flexDirection: "column",
 alignItems: "center",
 padding: "1.5rem 0",
 borderRight: S.borderLight,
 background: "var(--bg-alt)",
 gap: 8,
 }}
 >
 <div
 style={{
 width: 32,
 height: 32,
 borderRadius: 8,
 background: `${item.color}20`,
 border: `1.5px solid ${item.color}60`,
 display: "flex",
 alignItems: "center",
 justifyContent: "center",
 fontFamily: "var(--font-mono)",
 fontSize: "0.65rem",
 fontWeight: 900,
 color: item.color,
 }}
 >
 {item.step}
 </div>
 {idx < arr.length - 1 && (
 <div style={{ flex: 1, width: 2, background: `${item.color}25`, borderRadius: 1 }} />
 )}
 </div>

 {/* Content column */}
 <div style={{ padding: "1.5rem 2rem" }}>
 <h3 style={{ fontSize: "0.95rem", fontWeight: 900, letterSpacing: "-0.02em", color: "var(--text)", margin: "0 0 0.5rem" }}>
 {item.label}
 </h3>
 <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", lineHeight: 1.75, margin: "0 0 1rem" }}>
 {item.desc}
 </p>
 <pre
 style={{
 margin: 0,
 padding: "1rem 1.25rem",
 background: "var(--bg-dark)",
 color: "#a3e635",
 fontFamily: "var(--font-mono)",
 fontSize: "0.72rem",
 lineHeight: 1.8,
 borderRadius: 8,
 border: `1px solid ${item.color}30`,
 overflowX: "auto",
 }}
 >
 <code>{item.code}</code>
 </pre>
 </div>
 </div>
 ))}
 </div>
 </div>
 </section>

 {/* ─── CTA ───────────────────────────────────── */}
 <section style={{ background: "var(--primary)", borderTop: S.border, padding: "4rem 1.5rem" }}>
 <div style={{ maxWidth: "1152px", margin: "0 auto", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "2rem" }}>
 <div>
 <h2 style={{ fontSize: "clamp(1.5rem, 3vw, 2.25rem)", fontWeight: 900, letterSpacing: "-0.04em", color: "var(--text)", margin: "0 0 0.75rem", lineHeight: 1.1 }}>
 Ready to integrate?
 </h2>
 <p style={{ fontSize: "0.9rem", color: "rgba(17,16,16,0.65)", margin: 0, maxWidth: "46ch" }}>
 The full API reference documents every endpoint, parameter, and response shape in this architecture.
 </p>
 </div>
 <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
 <a href="/docs" style={{ padding: "0.875rem 1.75rem", border: S.border, borderRadius: "var(--radius)", background: "var(--bg-dark)", color: "var(--text-on-dark)", fontWeight: 800, fontSize: "0.875rem", textDecoration: "none", boxShadow: S.shadow, display: "inline-flex", alignItems: "center", gap: "0.5rem" }}>
 API Reference →
 </a>
 <a href="/simulation" style={{ padding: "0.875rem 1.75rem", border: S.border, borderRadius: "var(--radius)", background: "var(--bg)", color: "var(--text)", fontWeight: 800, fontSize: "0.875rem", textDecoration: "none", boxShadow: S.shadow, display: "inline-flex", alignItems: "center", gap: "0.5rem" }}>
 Try the Sandbox
 </a>
 </div>
 </div>
 </section>
 </div>
 );
}
