"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";

const procedureSteps = [
 { name: "Query context", desc: "Retrieve active task context & state" },
 { name: "Verify signatures", desc: "Validate Merkle tree cryptographic integrity" },
 { name: "Apply decay", desc: "Calculate forgetting curve coefficients" },
 { name: "Propagate beliefs", desc: "Resolve graph contradictions" },
];

/* ─── Shared inline-style helpers ─── */
const S = {
 border: "2px solid var(--border)",
 borderLight: "1px solid var(--border-light)",
 shadow: "var(--shadow)",
 shadowLg: "var(--shadow-lg)",
 radius: "var(--radius)",
};

export default function Home() {
 // Playground State
 const [activePlaygroundTab, setActivePlaygroundTab] = useState<"episodic" | "semantic" | "procedural">("episodic");

 // Code Tab state
 const [activeCodeTab, setActiveCodeTab] = useState<"docker" | "python" | "typescript">("docker");

 // Integration Showcase state
 const [activeIntegration, setActiveIntegration] = useState<"crewai" | "langchain" | "llamaindex">("crewai");

 // Episodic Memory Simulator State
 const [episodicInput, setEpisodicInput] = useState("");
 const [episodicMemories, setEpisodicMemories] = useState([
 {
 id: "mem-1",
 timestamp: "10 mins ago",
 content: "User mentioned their name is Alice and they are building a fintech application.",
 decay: 99.8,
 hash: "sha256_e7f3a2b1c09d8e7f",
 },
 {
 id: "mem-2",
 timestamp: "5 mins ago",
 content: "User prefers Python for backend services and PostgreSQL for data storage.",
 decay: 99.5,
 hash: "sha256_a1b2c3d4e5f60718",
 },
 ]);

 // Semantic Memory Simulator State
 const [semanticFacts, setSemanticFacts] = useState([
 { id: "fact-1", subject: "user_1", predicate: "name", object: "Alice", confidence: 0.98, status: "stable" },
 { id: "fact-2", subject: "user_1", predicate: "prefers_backend", object: "Python", confidence: 0.95, status: "stable" },
 { id: "fact-3", subject: "user_1", predicate: "prefers_db", object: "PostgreSQL", confidence: 0.92, status: "stable" },
 ]);
 const [conflictTriggered, setConflictTriggered] = useState(false);

 // Procedural Memory Simulator State
 const [runningProcedure, setRunningProcedure] = useState(false);
 const [currentProcedureStep, setCurrentProcedureStep] = useState(-1);

 // Architecture hover state
 const [hoveredArchNode, setHoveredArchNode] = useState<string | null>(null);

 // Handle Episodic Add
 const handleAddEpisodic = (e: React.FormEvent) => {
 e.preventDefault();
 if (!episodicInput.trim()) return;
 const newMem = {
 id: `mem-${Date.now()}`,
 timestamp: "Just now",
 content: episodicInput.trim(),
 decay: 100.0,
 hash: "sha256_" + Math.random().toString(16).substring(2, 10) + Math.random().toString(16).substring(2, 10),
 };
 setEpisodicMemories([newMem, ...episodicMemories]);
 setEpisodicInput("");
 };

 // Handle Semantic Conflict Simulation
 const handleTriggerConflict = () => {
 setConflictTriggered(true);
 setSemanticFacts((prev) =>
 prev.map((fact) => {
 if (fact.predicate === "name") return { ...fact, confidence: 0.12, status: "conflict" };
 if (fact.predicate === "prefers_backend") return { ...fact, confidence: 0.22, status: "conflict" };
 return fact;
 })
 );
 setTimeout(() => {
 setSemanticFacts((prev) => [
 ...prev,
 { id: "fact-4", subject: "user_1", predicate: "name", object: "Bob", confidence: 0.99, status: "resolved" },
 { id: "fact-5", subject: "user_1", predicate: "prefers_backend", object: "Go", confidence: 0.97, status: "resolved" },
 ]);
 }, 800);
 };

 const handleResetSemantic = () => {
 setConflictTriggered(false);
 setSemanticFacts([
 { id: "fact-1", subject: "user_1", predicate: "name", object: "Alice", confidence: 0.98, status: "stable" },
 { id: "fact-2", subject: "user_1", predicate: "prefers_backend", object: "Python", confidence: 0.95, status: "stable" },
 { id: "fact-3", subject: "user_1", predicate: "prefers_db", object: "PostgreSQL", confidence: 0.92, status: "stable" },
 ]);
 };

 // Handle Procedural execution simulation
 useEffect(() => {
 let timer: NodeJS.Timeout;
 if (runningProcedure) {
 if (currentProcedureStep < procedureSteps.length - 1) {
 timer = setTimeout(() => {
 setCurrentProcedureStep((prev) => prev + 1);
 }, 1000);
 } else {
 timer = setTimeout(() => {
 setRunningProcedure(false);
 setCurrentProcedureStep(-1);
 }, 1200);
 }
 }
 return () => clearTimeout(timer);
 }, [runningProcedure, currentProcedureStep]);

 const handleRunProcedure = () => {
 if (runningProcedure) return;
 setRunningProcedure(true);
 setCurrentProcedureStep(0);
 };

 return (
 <div style={{ background: "var(--bg)", color: "var(--text)", width: "100%" }}>

 {/* ══════════════════════════════════════════
 HERO SECTION — Dark background
 ══════════════════════════════════════════ */}
 <section
 style={{
 background: "var(--bg-dark)",
 color: "var(--text-on-dark)",
 borderBottom: S.border,
 paddingTop: "5rem",
 paddingBottom: "5rem",
 }}
 >
 <div
 style={{ maxWidth: "1152px", margin: "0 auto", padding: "0 1.5rem" }}
 className="flex flex-col items-center text-center"
 >
 {/* Monospace tag pill */}
 <div
 style={{
 display: "inline-flex",
 alignItems: "center",
 gap: "0.5rem",
 padding: "0.3rem 0.9rem",
 borderRadius: 9999,
 border: "1.5px solid rgba(232,245,66,0.6)",
 background: "rgba(232,245,66,0.12)",
 fontFamily: "var(--font-mono)",
 fontSize: "0.65rem",
 fontWeight: 700,
 letterSpacing: "0.1em",
 textTransform: "uppercase" as const,
 color: "var(--primary)",
 marginBottom: "1.75rem",
 }}
 >
 <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--primary)", display: "inline-block" }} />
 Open-Source · Apache 2.0
 </div>

 <h1
 style={{
 fontSize: "clamp(2.5rem, 7vw, 5.5rem)",
 fontWeight: 900,
 letterSpacing: "-0.04em",
 lineHeight: 1.05,
 color: "var(--text-on-dark)",
 maxWidth: "18ch",
 margin: "0 0 1.5rem",
 }}
 >
 Persistent memory for{" "}
 <span style={{ color: "var(--primary)" }}>autonomous AI agents</span>
 </h1>

 <p
 style={{
 fontSize: "1.05rem",
 color: "rgba(249,247,242,0.65)",
 maxWidth: "52ch",
 lineHeight: 1.75,
 margin: "0 0 2.5rem",
 fontWeight: 400,
 }}
 >
 Provide your agents with biological-inspired memory structures: Episodic log streams,
 semantic graphs, and procedural workflows. Audited with cryptographic integrity and
 structured with natural temporal decay.
 </p>

 <div className="flex flex-col sm:flex-row gap-3 items-center justify-center w-full sm:w-auto">
 {/* Primary CTA: View Documentation */}
 <Link
 href="/docs"
 style={{
 display: "inline-flex",
 alignItems: "center",
 justifyContent: "center",
 gap: "0.5rem",
 padding: "0.875rem 2rem",
 borderRadius: 10,
 background: "var(--primary)",
 color: "var(--text)",
 border: S.border,
 fontWeight: 800,
 fontSize: "0.875rem",
 letterSpacing: "-0.01em",
 textDecoration: "none",
 boxShadow: S.shadowLg,
 transition: "transform 0.15s, box-shadow 0.15s",
 width: "100%",
 }}
 className="sm:w-auto hover:[transform:translate(-2px,-2px)] hover:[box-shadow:9px_9px_0_var(--border)]"
 >
 <svg style={{ width: 16, height: 16 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
 </svg>
 View Documentation
 </Link>

 {/* Secondary CTA: GitHub Repository */}
 <a
 href="https://github.com/Kyros-494/kyros-ai"
 target="_blank"
 rel="noopener noreferrer"
 style={{
 display: "inline-flex",
 alignItems: "center",
 justifyContent: "center",
 gap: "0.5rem",
 padding: "0.875rem 2rem",
 borderRadius: 10,
 background: "transparent",
 color: "var(--text-on-dark)",
 border: "2px solid rgba(249,247,242,0.35)",
 fontWeight: 700,
 fontSize: "0.875rem",
 letterSpacing: "-0.01em",
 textDecoration: "none",
 boxShadow: "4px 4px 0 rgba(249,247,242,0.2)",
 transition: "border-color 0.15s, box-shadow 0.15s",
 width: "100%",
 }}
 className="sm:w-auto hover:border-[rgba(249,247,242,0.6)] hover:[box-shadow:4px_4px_0_rgba(249,247,242,0.35)]"
 >
 <svg style={{ width: 16, height: 16, fill: "currentColor" }} viewBox="0 0 24 24">
 <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.646.64.699 1.026 1.592 1.026 2.683 0 3.842-2.337 4.687-4.565 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.577.688.479C19.138 20.162 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
 </svg>
 GitHub Repository
 </a>
 </div>
 </div>
 </section>

 {/* ══════════════════════════════════════════
 FEATURE BAR — Capabilities Stats
 Light cream bg, bold numbers, monospace labels
 ══════════════════════════════════════════ */}
 <section
 style={{
 background: "var(--bg)",
 borderBottom: S.border,
 }}
 >
 <div
 style={{ maxWidth: "1152px", margin: "0 auto" }}
 className="grid grid-cols-2 md:grid-cols-4"
 >
 {[
 { value: "3", label: "Memory Types", sub: "Episodic · Semantic · Procedural" },
 { value: "0-Config", label: "Auto-Migration", sub: "Schema migrations on startup" },
 { value: "Apache 2.0", label: "Open Source", sub: "Permissive commercial use" },
 { value: "Py + TS", label: "Native SDKs", sub: "Framework-ready integrations" },
 ].map((stat, i) => (
 <div
 key={stat.label}
 style={{
 padding: "2.25rem 1.75rem",
 borderRight: i < 3 ? S.border : "none",
 borderBottom: "none",
 }}
 className={`flex flex-col gap-2 ${i === 1 || i === 3 ? "border-r-0 md:border-r-[2px] md:border-r-[var(--border)]" : ""}`}
 >
 <div
 style={{
 fontSize: "clamp(1.5rem, 3vw, 2.5rem)",
 fontWeight: 900,
 letterSpacing: "-0.04em",
 color: "var(--text)",
 lineHeight: 1,
 }}
 >
 {stat.value}
 </div>
 <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--text)", marginTop: "0.25rem" }}>
 {stat.label}
 </div>
 <div
 style={{
 fontSize: "0.65rem",
 fontFamily: "var(--font-mono)",
 color: "var(--text-muted)",
 letterSpacing: "0.02em",
 }}
 >
 {stat.sub}
 </div>
 </div>
 ))}
 </div>
 </section>

 {/* ══════════════════════════════════════════
 SYSTEM ARCHITECTURE DIAGRAM
 Light gray background, bordered card
 ══════════════════════════════════════════ */}
 <section
 style={{
 background: "var(--bg-alt)",
 borderBottom: S.border,
 padding: "5rem 1.5rem",
 }}
 >
 <div style={{ maxWidth: "1024px", margin: "0 auto" }}>
 {/* Section header */}
 <div style={{ textAlign: "center", marginBottom: "3rem" }}>
 <div
 style={{
 display: "inline-flex",
 alignItems: "center",
 gap: "0.5rem",
 padding: "0.25rem 0.75rem",
 borderRadius: 9999,
 border: S.border,
 background: "var(--bg)",
 fontFamily: "var(--font-mono)",
 fontSize: "0.6rem",
 fontWeight: 700,
 letterSpacing: "0.1em",
 textTransform: "uppercase" as const,
 color: "var(--text)",
 marginBottom: "1rem",
 }}
 >
 Technical Overview
 </div>
 <h2
 style={{
 fontSize: "clamp(1.75rem, 4vw, 2.75rem)",
 fontWeight: 900,
 letterSpacing: "-0.04em",
 color: "var(--text)",
 margin: "0 0 1rem",
 }}
 >
 System Architecture
 </h2>
 <p
 style={{
 color: "var(--text-muted)",
 maxWidth: "52ch",
 margin: "0 auto",
 lineHeight: 1.7,
 fontSize: "0.9rem",
 }}
 >
 Kyros acts as a secure mediation layer between your autonomous agents and the
 underlying persistent vector and graph database instances. Hover any node to inspect it.
 </p>
 </div>

 {/* Architecture card */}
 <div
 style={{
 border: S.border,
 borderRadius: S.radius,
 background: "var(--bg)",
 boxShadow: S.shadowLg,
 padding: "2rem",
 overflow: "hidden",
 display: "flex",
 flexDirection: "column",
 alignItems: "center",
 }}
 >
 <div style={{ width: "100%", maxWidth: "56rem" }}>
 <svg viewBox="0 0 900 520" className="w-full h-full select-none" style={{ color: "#888" }}>
 <defs>
 <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
 <path d="M 0 0 L 10 5 L 0 10 z" fill="#888" />
 </marker>
 <marker id="arrowCyan" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
 <path d="M 0 0 L 10 5 L 0 10 z" fill="#22d3ee" />
 </marker>
 <marker id="arrowViolet" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
 <path d="M 0 0 L 10 5 L 0 10 z" fill="#a78bfa" />
 </marker>
 <marker id="arrowDark" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
 <path d="M 0 0 L 10 5 L 0 10 z" fill="#111010" />
 </marker>
 </defs>

 {/* Layer labels */}
 <text x="80" y="28" fill="#6b6560" textAnchor="middle" fontSize="9" fontFamily="monospace" fontWeight="600" letterSpacing="2">CLIENT LAYER</text>
 <text x="390" y="28" fill="#6b6560" textAnchor="middle" fontSize="9" fontFamily="monospace" fontWeight="600" letterSpacing="2">ENGINE LAYER</text>
 <text x="730" y="28" fill="#6b6560" textAnchor="middle" fontSize="9" fontFamily="monospace" fontWeight="600" letterSpacing="2">STORAGE LAYER</text>

 {/* Layer separators */}
 <line x1="210" y1="18" x2="210" y2="500" stroke="#d4cfc8" strokeWidth="1" strokeDasharray="4,4" />
 <line x1="570" y1="18" x2="570" y2="500" stroke="#d4cfc8" strokeWidth="1" strokeDasharray="4,4" />

 {/* SDK / Agent Node */}
 <g className="cursor-pointer" onMouseEnter={() => setHoveredArchNode("sdk")} onMouseLeave={() => setHoveredArchNode(null)}>
 <rect x="20" y="80" width="160" height="70" rx="8"
 fill={hoveredArchNode === "sdk" ? "#f0ede6" : "#f9f7f2"}
 stroke={hoveredArchNode === "sdk" ? "#22d3ee" : "#111010"}
 strokeWidth="1.5" className="transition-all duration-300"
 />
 <text x="100" y="112" fill="#111010" textAnchor="middle" fontWeight="700" fontSize="12">Python / TS SDK</text>
 <text x="100" y="130" fill="#6b6560" textAnchor="middle" fontSize="9" fontFamily="monospace">KyrosClient.remember()</text>
 </g>

 {/* Proxy Node */}
 <g className="cursor-pointer" onMouseEnter={() => setHoveredArchNode("proxy")} onMouseLeave={() => setHoveredArchNode(null)}>
 <rect x="20" y="200" width="160" height="70" rx="8"
 fill={hoveredArchNode === "proxy" ? "#f0ede6" : "#f9f7f2"}
 stroke={hoveredArchNode === "proxy" ? "#f59e0b" : "#111010"}
 strokeWidth="1.5" className="transition-all duration-300"
 />
 <text x="100" y="232" fill="#111010" textAnchor="middle" fontWeight="700" fontSize="12">LLM Proxy Mode</text>
 <text x="100" y="250" fill="#6b6560" textAnchor="middle" fontSize="9" fontFamily="monospace">openai base_url redirect</text>
 </g>

 {/* MCP Node */}
 <g className="cursor-pointer" onMouseEnter={() => setHoveredArchNode("mcp")} onMouseLeave={() => setHoveredArchNode(null)}>
 <rect x="20" y="320" width="160" height="70" rx="8"
 fill={hoveredArchNode === "mcp" ? "#f0ede6" : "#f9f7f2"}
 stroke={hoveredArchNode === "mcp" ? "#a78bfa" : "#111010"}
 strokeWidth="1.5" className="transition-all duration-300"
 />
 <text x="100" y="352" fill="#111010" textAnchor="middle" fontWeight="700" fontSize="12">MCP Server</text>
 <text x="100" y="370" fill="#6b6560" textAnchor="middle" fontSize="9" fontFamily="monospace">Stdio JSON-RPC tools</text>
 </g>

 {/* Arrows: Client → Engine */}
 <path d="M 180 115 L 228 115" stroke={hoveredArchNode === "sdk" || hoveredArchNode === "engine" ? "#22d3ee" : "#888"} strokeWidth="1.5" markerEnd={hoveredArchNode === "sdk" || hoveredArchNode === "engine" ? "url(#arrowCyan)" : "url(#arrow)"} className="transition-all duration-300" />
 <text x="204" y="108" fill="#6b6560" textAnchor="middle" fontSize="8" fontFamily="monospace">REST/HTTP</text>

 <path d="M 180 235 L 228 235" stroke={hoveredArchNode === "proxy" || hoveredArchNode === "engine" ? "#f59e0b" : "#888"} strokeWidth="1.5" markerEnd="url(#arrow)" className="transition-all duration-300" />
 <text x="204" y="228" fill="#6b6560" textAnchor="middle" fontSize="8" fontFamily="monospace">intercept</text>

 <path d="M 180 355 L 228 355" stroke={hoveredArchNode === "mcp" || hoveredArchNode === "engine" ? "#a78bfa" : "#888"} strokeWidth="1.5" markerEnd={hoveredArchNode === "mcp" || hoveredArchNode === "engine" ? "url(#arrowViolet)" : "url(#arrow)"} className="transition-all duration-300" />
 <text x="204" y="348" fill="#6b6560" textAnchor="middle" fontSize="8" fontFamily="monospace">stdio RPC</text>

 {/* Kyros Engine Core */}
 <g className="cursor-pointer" onMouseEnter={() => setHoveredArchNode("engine")} onMouseLeave={() => setHoveredArchNode(null)}>
 <rect x="228" y="50" width="200" height="420" rx="10"
 fill={hoveredArchNode === "engine" ? "#f0ede6" : "#f9f7f2"}
 stroke={hoveredArchNode === "engine" ? "#22d3ee" : "#111010"}
 strokeWidth="2" className="transition-all duration-300"
 />
 <text x="328" y="84" fill="#111010" textAnchor="middle" fontWeight="800" fontSize="13" letterSpacing="0.5">Kyros Memory Engine</text>

 {/* Episodic sub-module */}
 <rect x="248" y="100" width="160" height="50" rx="5" fill="#f9f7f2" stroke="#22d3ee" strokeWidth="1.5" />
 <text x="328" y="122" fill="#22d3ee" textAnchor="middle" fontSize="11" fontWeight="600">Episodic Logger</text>
 <text x="328" y="139" fill="#6b6560" textAnchor="middle" fontSize="9" fontFamily="monospace">Ebbinghaus decay · SHA-256</text>

 {/* Semantic sub-module */}
 <rect x="248" y="170" width="160" height="50" rx="5" fill="#f9f7f2" stroke="#a78bfa" strokeWidth="1.5" />
 <text x="328" y="192" fill="#a78bfa" textAnchor="middle" fontSize="11" fontWeight="600">Semantic Graph</text>
 <text x="328" y="209" fill="#6b6560" textAnchor="middle" fontSize="9" fontFamily="monospace">Belief propagation · Triples</text>

 {/* Procedural sub-module */}
 <rect x="248" y="240" width="160" height="50" rx="5" fill="#f9f7f2" stroke="#34d399" strokeWidth="1.5" />
 <text x="328" y="262" fill="#34d399" textAnchor="middle" fontSize="11" fontWeight="600">Procedural Skills</text>
 <text x="328" y="279" fill="#6b6560" textAnchor="middle" fontSize="9" fontFamily="monospace">Workflow state · Task chains</text>

 {/* Merkle Auditor */}
 <rect x="248" y="310" width="160" height="40" rx="5" fill="#f9f7f2" stroke="#f59e0b" strokeWidth="1.5" />
 <text x="328" y="334" fill="#f59e0b" textAnchor="middle" fontSize="10" fontWeight="600">Merkle Integrity Auditor</text>

 {/* Context Injector */}
 <rect x="248" y="365" width="160" height="40" rx="5" fill="#f9f7f2" stroke="#f87171" strokeWidth="1.5" />
 <text x="328" y="389" fill="#f87171" textAnchor="middle" fontSize="10" fontWeight="600">Context Injection Engine</text>

 <text x="328" y="450" fill="#6b6560" textAnchor="middle" fontSize="8" fontFamily="monospace">REST API · Port 8000</text>
 </g>

 {/* Arrows: Engine → Storage */}
 <path d="M 428 125 L 593 160" stroke={hoveredArchNode === "engine" || hoveredArchNode === "vector" ? "#22d3ee" : "#888"} strokeWidth="1.5" markerEnd={hoveredArchNode === "engine" || hoveredArchNode === "vector" ? "url(#arrowCyan)" : "url(#arrow)"} className="transition-all duration-300" />
 <text x="510" y="140" fill="#6b6560" textAnchor="middle" fontSize="8" fontFamily="monospace">Vector Query</text>

 <path d="M 428 195 L 593 290" stroke={hoveredArchNode === "engine" || hoveredArchNode === "graph" ? "#a78bfa" : "#888"} strokeWidth="1.5" markerEnd={hoveredArchNode === "engine" || hoveredArchNode === "graph" ? "url(#arrowViolet)" : "url(#arrow)"} className="transition-all duration-300" />
 <text x="510" y="248" fill="#6b6560" textAnchor="middle" fontSize="8" fontFamily="monospace">Graph Query</text>

 <path d="M 428 335 L 593 400" stroke={hoveredArchNode === "engine" || hoveredArchNode === "cache" ? "#f59e0b" : "#888"} strokeWidth="1.5" markerEnd="url(#arrow)" className="transition-all duration-300" />
 <text x="510" y="370" fill="#6b6560" textAnchor="middle" fontSize="8" fontFamily="monospace">Cache R/W</text>

 {/* pgvector Storage */}
 <g className="cursor-pointer" onMouseEnter={() => setHoveredArchNode("vector")} onMouseLeave={() => setHoveredArchNode(null)}>
 <rect x="595" y="120" width="170" height="80" rx="8"
 fill={hoveredArchNode === "vector" ? "#f0ede6" : "#f9f7f2"}
 stroke={hoveredArchNode === "vector" ? "#22d3ee" : "#111010"}
 strokeWidth="1.5" className="transition-all duration-300"
 />
 <text x="680" y="155" fill="#111010" textAnchor="middle" fontWeight="700" fontSize="12">pgvector / PostgreSQL</text>
 <text x="680" y="173" fill="#6b6560" textAnchor="middle" fontSize="9" fontFamily="monospace">Dense embeddings · HNSW index</text>
 </g>

 {/* Semantic Facts Store */}
 <g className="cursor-pointer" onMouseEnter={() => setHoveredArchNode("graph")} onMouseLeave={() => setHoveredArchNode(null)}>
 <rect x="595" y="250" width="170" height="80" rx="8"
 fill={hoveredArchNode === "graph" ? "#f0ede6" : "#f9f7f2"}
 stroke={hoveredArchNode === "graph" ? "#a78bfa" : "#111010"}
 strokeWidth="1.5" className="transition-all duration-300"
 />
 <text x="680" y="285" fill="#111010" textAnchor="middle" fontWeight="700" fontSize="12">Semantic Facts Store</text>
 <text x="680" y="303" fill="#6b6560" textAnchor="middle" fontSize="9" fontFamily="monospace">Belief graph · Triple store</text>
 </g>

 {/* Redis Cache */}
 <g className="cursor-pointer" onMouseEnter={() => setHoveredArchNode("cache")} onMouseLeave={() => setHoveredArchNode(null)}>
 <rect x="595" y="375" width="170" height="70" rx="8"
 fill={hoveredArchNode === "cache" ? "#f0ede6" : "#f9f7f2"}
 stroke={hoveredArchNode === "cache" ? "#f59e0b" : "#111010"}
 strokeWidth="1.5" className="transition-all duration-300"
 />
 <text x="680" y="406" fill="#111010" textAnchor="middle" fontWeight="700" fontSize="12">Redis Cache</text>
 <text x="680" y="424" fill="#6b6560" textAnchor="middle" fontSize="9" fontFamily="monospace">Context window · TTL decay</text>
 </g>
 </svg>
 </div>

 {/* Dynamic explanation block */}
 <div
 style={{
 width: "100%",
 marginTop: "1.5rem",
 padding: "1rem 1.25rem",
 borderRadius: 10,
 background: "var(--bg-alt)",
 border: S.border,
 minHeight: 72,
 display: "flex",
 alignItems: "center",
 justifyContent: "center",
 textAlign: "center",
 transition: "all 0.2s",
 }}
 >
 {hoveredArchNode === "sdk" && (
 <p style={{ fontSize: "0.85rem", color: "var(--text)", margin: 0 }}>
 <strong style={{ color: "#22d3ee" }}>Python / TS SDK:</strong> The official client libraries call the Kyros REST API directly. Use{" "}
 <code style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", background: "var(--bg)", padding: "0.125rem 0.375rem", borderRadius: 4, border: S.borderLight }}>KyrosClient.remember()</code>,{" "}
 <code style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", background: "var(--bg)", padding: "0.125rem 0.375rem", borderRadius: 4, border: S.borderLight }}>recall()</code>, and{" "}
 <code style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", background: "var(--bg)", padding: "0.125rem 0.375rem", borderRadius: 4, border: S.borderLight }}>store_fact()</code> from any Python or TypeScript app.
 </p>
 )}
 {hoveredArchNode === "proxy" && (
 <p style={{ fontSize: "0.85rem", color: "var(--text)", margin: 0 }}>
 <strong style={{ color: "#f59e0b" }}>LLM Proxy Mode:</strong> Redirect any LLM client (OpenAI, Gemini, Mistral, Anthropic) by pointing its{" "}
 <code style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", background: "var(--bg)", padding: "0.125rem 0.375rem", borderRadius: 4, border: S.borderLight }}>base_url</code> to{" "}
 <code style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", background: "var(--bg)", padding: "0.125rem 0.375rem", borderRadius: 4, border: S.borderLight }}>http://localhost:8000/v1/proxy</code>. Kyros intercepts requests, injects relevant memories, and routes to the real provider.
 </p>
 )}
 {hoveredArchNode === "mcp" && (
 <p style={{ fontSize: "0.85rem", color: "var(--text)", margin: 0 }}>
 <strong style={{ color: "#a78bfa" }}>MCP Server:</strong> A built-in Model Context Protocol server exposes{" "}
 <code style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", background: "var(--bg)", padding: "0.125rem 0.375rem", borderRadius: 4, border: S.borderLight }}>remember</code>,{" "}
 <code style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", background: "var(--bg)", padding: "0.125rem 0.375rem", borderRadius: 4, border: S.borderLight }}>recall</code>, and{" "}
 <code style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", background: "var(--bg)", padding: "0.125rem 0.375rem", borderRadius: 4, border: S.borderLight }}>store_fact</code> tools over stdio JSON-RPC. Compatible with Cursor, Windsurf, Antigravity, Zed, and any MCP-enabled IDE.
 </p>
 )}
 {hoveredArchNode === "engine" && (
 <p style={{ fontSize: "0.85rem", color: "var(--text)", margin: 0 }}>
 <strong style={{ color: "#22d3ee" }}>Memory Consolidation Engine:</strong> The core of Kyros. Ingested events flow into the Episodic Logger (time-ordered log with SHA-256 hash chains), the Semantic Graph (triple-store belief propagation), and the Procedural Skills registry. All writes are Merkle-audited.
 </p>
 )}
 {hoveredArchNode === "vector" && (
 <p style={{ fontSize: "0.85rem", color: "var(--text)", margin: 0 }}>
 <strong style={{ color: "#22d3ee" }}>pgvector / PostgreSQL:</strong> Stores high-dimensional dense embeddings using HNSW indexing for sub-millisecond semantic search. Episodic log entries and semantic facts are both vectorized and queryable by cosine similarity.
 </p>
 )}
 {hoveredArchNode === "graph" && (
 <p style={{ fontSize: "0.85rem", color: "var(--text)", margin: 0 }}>
 <strong style={{ color: "#a78bfa" }}>Semantic Facts Store:</strong> A graph of subject–predicate–object triples representing persistent beliefs about agents and their environments. Confidence scores propagate via breadth-first traversal when contradictions are detected.
 </p>
 )}
 {hoveredArchNode === "cache" && (
 <p style={{ fontSize: "0.85rem", color: "var(--text)", margin: 0 }}>
 <strong style={{ color: "#f59e0b" }}>Redis Cache:</strong> Short-term context window storage with configurable TTL. Caches recent episodic recall results to avoid redundant DB queries and applies real-time Ebbinghaus decay coefficients before serving context.
 </p>
 )}
 {!hoveredArchNode && (
 <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)", margin: 0 }}>
 ↑ Hover any node to inspect how data flows through the system.
 </p>
 )}
 </div>
 </div>
 </div>
 </section>

 {/* ══════════════════════════════════════════
 HOW IT WORKS — 3 clear steps
 ══════════════════════════════════════════ */}
 <section
 style={{
 background: "var(--bg)",
 borderBottom: S.border,
 padding: "5rem 1.5rem",
 }}
 >
 <div style={{ maxWidth: "1152px", margin: "0 auto" }}>
 {/* Section header */}
 <div style={{ marginBottom: "3.5rem" }}>
 <div
 style={{
 display: "inline-flex",
 alignItems: "center",
 gap: "0.5rem",
 padding: "0.3rem 0.9rem",
 borderRadius: 9999,
 border: "1.5px solid var(--border)",
 background: "var(--primary)",
 fontFamily: "var(--font-mono)",
 fontSize: "0.65rem",
 fontWeight: 700,
 letterSpacing: "0.1em",
 textTransform: "uppercase" as const,
 color: "var(--text)",
 marginBottom: "1.25rem",
 }}
 >
 How It Works
 </div>
 <h2
 style={{
 fontSize: "clamp(1.75rem, 4vw, 2.75rem)",
 fontWeight: 900,
 letterSpacing: "-0.04em",
 color: "var(--text)",
 margin: "0 0 1rem",
 lineHeight: 1.1,
 }}
 >
 Three lines of code.<br />Infinite memory.
 </h2>
 <p style={{ color: "var(--text-muted)", maxWidth: "52ch", fontSize: "0.95rem", lineHeight: 1.75, margin: 0 }}>
 Kyros slots into your existing AI stack without changing how you write agents. Add memory in minutes, not days.
 </p>
 </div>

 <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "3rem", alignItems: "start" }}>

 {/* Left: 3 steps */}
 <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
 {[
 {
 num: "01",
 icon: "",
 title: "Store a memory",
 plain: "Your agent captures something important — a user's name, preference, or decision. One call persists it forever.",
 detail: "Kyros hashes the content with SHA-256, assigns an Ebbinghaus decay weight, appends it to the Merkle audit tree, converts it to a vector embedding, and writes it to PostgreSQL — all in a single API call.",
 color: "#3b82f6",
 },
 {
 num: "02",
 icon: "",
 title: "Recall what's relevant",
 plain: "Ask Kyros for context before your agent responds. It returns only the most relevant, highest-weight memories — no noise, no stale data.",
 detail: "HNSW approximate nearest-neighbor search finds semantically similar records. Results are reranked by cosine_similarity × retention_weight, filtered by your min_weight threshold.",
 color: "#e8f542",
 },
 {
 num: "03",
 icon: "",
 title: "Agent responds with context",
 plain: "Inject the retrieved memories into your LLM prompt. Your agent now responds as if it remembers everything — because it does.",
 detail: "Retrieved memories are returned as structured JSON with content, hash, weight, and tags. Inject directly into your system prompt or use our context builder helper.",
 color: "#10b981",
 },
 ].map((step, idx, arr) => (
 <div
 key={step.num}
 style={{
 display: "flex",
 gap: "1.25rem",
 paddingBottom: idx < arr.length - 1 ? "2rem" : 0,
 position: "relative",
 }}
 >
 {/* Connector line */}
 {idx < arr.length - 1 && (
 <div style={{ position: "absolute", left: 19, top: 48, width: 2, height: "calc(100% - 24px)", background: "var(--border-light)" }} />
 )}

 {/* Step circle */}
 <div
 style={{
 width: 40,
 height: 40,
 borderRadius: "50%",
 border: `2px solid ${step.color}`,
 background: `${step.color}15`,
 display: "flex",
 alignItems: "center",
 justifyContent: "center",
 fontSize: "1.1rem",
 flexShrink: 0,
 zIndex: 1,
 }}
 >
 {step.icon}
 </div>

 {/* Content */}
 <div style={{ paddingTop: "0.125rem", flex: 1 }}>
 <div style={{ display: "flex", alignItems: "center", gap: "0.625rem", marginBottom: "0.5rem" }}>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", fontWeight: 800, color: step.color, letterSpacing: "0.08em" }}>
 STEP {step.num}
 </span>
 </div>
 <h3 style={{ fontSize: "1.05rem", fontWeight: 900, letterSpacing: "-0.025em", color: "var(--text)", margin: "0 0 0.5rem", lineHeight: 1.2 }}>
 {step.title}
 </h3>
 <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", lineHeight: 1.75, margin: "0 0 0.625rem" }}>
 {step.plain}
 </p>
 <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", lineHeight: 1.65, margin: 0, fontFamily: "var(--font-mono)", opacity: 0.75, borderLeft: `2px solid ${step.color}40`, paddingLeft: "0.75rem" }}>
 {step.detail}
 </p>
 </div>
 </div>
 ))}
 </div>

 {/* Right: Real code example */}
 <div style={{ display: "flex", flexDirection: "column", gap: "1rem", position: "sticky", top: 80 }}>
 <div
 style={{
 border: S.border,
 borderRadius: "var(--radius)",
 background: "var(--bg-dark)",
 overflow: "hidden",
 boxShadow: S.shadowLg,
 }}
 >
 {/* Code file tabs */}
 <div style={{ display: "flex", borderBottom: S.border }}>
 {["Python", "TypeScript"].map((lang, i) => (
 <div
 key={lang}
 style={{
 padding: "0.625rem 1.25rem",
 fontFamily: "var(--font-mono)",
 fontSize: "0.65rem",
 fontWeight: 700,
 color: i === 0 ? "var(--primary)" : "rgba(249,247,242,0.3)",
 borderRight: "1px solid rgba(249,247,242,0.08)",
 background: i === 0 ? "rgba(232,245,66,0.06)" : "transparent",
 letterSpacing: "0.04em",
 }}
 >
 {lang}
 </div>
 ))}
 <div style={{ marginLeft: "auto", padding: "0.625rem 1rem", display: "flex", alignItems: "center", gap: "0.375rem" }}>
 <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#ef4444", display: "inline-block" }} />
 <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#f59e0b", display: "inline-block" }} />
 <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#22c55e", display: "inline-block" }} />
 </div>
 </div>

 {/* Code block */}
 <pre style={{ margin: 0, padding: "1.75rem 1.5rem", fontFamily: "var(--font-mono)", fontSize: "0.78rem", lineHeight: 2, overflowX: "auto", color: "#e2e8f0" }}>
 <code>{`import kyros

client = kyros.Client(api_key="ky_...")

# ① Store a memory
client.ingest(
 content="User prefers Python, dark mode.",
 user_id="user_123",
 type="semantic"
)

# ② Recall relevant context
memories = client.recall(
 query="User tech preferences",
 user_id="user_123",
 top_k=3
)

# ③ Build your prompt with context
context = "\\n".join(m.content for m in memories)
prompt = f"Context: {context}\\n\\nUser: {query}"
response = llm.complete(prompt)`}</code>
 </pre>

 {/* Footer bar */}
 <div style={{ padding: "0.875rem 1.5rem", borderTop: "1px solid rgba(249,247,242,0.08)", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "0.5rem" }}>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.62rem", color: "rgba(249,247,242,0.3)" }}>
 kyros-py v1.x · Apache 2.0
 </span>
 <div style={{ display: "flex", gap: "0.625rem" }}>
 <a
 href="/docs"
 style={{ padding: "0.35rem 0.875rem", border: "1px solid rgba(249,247,242,0.15)", borderRadius: 6, background: "transparent", color: "rgba(249,247,242,0.6)", fontFamily: "var(--font-mono)", fontSize: "0.62rem", fontWeight: 700, textDecoration: "none", transition: "all 0.15s" }}
 >
 API Docs →
 </a>
 <a
 href="/simulation"
 style={{ padding: "0.35rem 0.875rem", border: "1px solid var(--primary)", borderRadius: 6, background: "rgba(232,245,66,0.12)", color: "var(--primary)", fontFamily: "var(--font-mono)", fontSize: "0.62rem", fontWeight: 700, textDecoration: "none", transition: "all 0.15s" }}
 >
 Try Live Sandbox
 </a>
 </div>
 </div>
 </div>

 {/* What happens under the hood */}
 <div style={{ border: S.border, borderRadius: "var(--radius)", background: "var(--bg-alt)", padding: "1.25rem 1.5rem", boxShadow: S.shadow }}>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.1em", color: "var(--text-muted)", marginBottom: "0.875rem" }}>
 Under the hood — every ingest() call does:
 </div>
 <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
 {[
 { icon: "", text: "Merkle tree append for audit trail" },
 { icon: "", text: "Ebbinghaus decay weight initialized" },
 { icon: "", text: "Vector embedding for semantic search" },
 { icon: "", text: "Persisted to PostgreSQL + Redis cache" },
 ].map((item) => (
 <div key={item.text} style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
 <span style={{ fontSize: "0.875rem", flexShrink: 0 }}>{item.icon}</span>
 <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", lineHeight: 1.5 }}>{item.text}</span>
 </div>
 ))}
 </div>
 </div>

 {/* CTA */}
 <a
 href="/simulation"
 style={{
 display: "flex",
 alignItems: "center",
 justifyContent: "space-between",
 padding: "1.125rem 1.5rem",
 border: S.border,
 borderRadius: "var(--radius)",
 background: "var(--text)",
 color: "var(--bg)",
 textDecoration: "none",
 boxShadow: S.shadowLg,
 transition: "transform 0.15s, box-shadow 0.15s",
 gap: "1rem",
 }}
 onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.transform = "translate(-2px,-2px)"; (e.currentTarget as HTMLElement).style.boxShadow = "9px 9px 0 var(--border)"; }}
 onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.transform = "none"; (e.currentTarget as HTMLElement).style.boxShadow = S.shadowLg; }}
 >
 <div>
 <div style={{ fontSize: "0.88rem", fontWeight: 900, letterSpacing: "-0.02em", marginBottom: "0.2rem" }}>
 See it in action →
 </div>
 <div style={{ fontSize: "0.72rem", opacity: 0.6, fontFamily: "var(--font-mono)" }}>
 Interactive sandbox · No signup needed
 </div>
 </div>
 <span style={{ fontSize: "1.5rem" }}>→</span>
 </a>
 </div>
 </div>
 </div>
 </section>

 {/* ══════════════════════════════════════════
 MCP PROTOCOL SECTION — Dark background
 ══════════════════════════════════════════ */}
 <section
 style={{
 background: "var(--bg-dark)",
 color: "var(--text-on-dark)",
 borderBottom: S.border,
 padding: "5rem 1.5rem",
 }}
 >
 <div style={{ maxWidth: "1152px", margin: "0 auto" }}>
 <div className="grid lg:grid-cols-12 gap-10 items-center">
 <div className="lg:col-span-5 space-y-5">
 {/* Badge */}
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
 }}
 >
 Protocol Ready
 </div>

 <h2
 style={{
 fontSize: "clamp(1.75rem, 3.5vw, 2.5rem)",
 fontWeight: 900,
 letterSpacing: "-0.04em",
 color: "var(--text-on-dark)",
 lineHeight: 1.1,
 margin: 0,
 }}
 >
 Connect memory to Cursor, Cline, Windsurf, Antigravity, and more
 </h2>

 <p style={{ color: "rgba(249,247,242,0.6)", fontSize: "0.9rem", lineHeight: 1.75, margin: 0 }}>
 Kyros ships with a built-in Model Context Protocol (MCP) server. Run a single command to register Kyros as a local workspace toolset, allowing your agentic IDE to recall context across development cycles.
 </p>

 {/* IDE chips */}
 <div style={{ display: "flex", flexWrap: "wrap" as const, gap: "0.5rem" }}>
 {[
 { name: "Cursor" },
 { name: "Windsurf" },
 { name: "Cline" },
 { name: "Antigravity" },
 { name: "Zed" },
 { name: "Continue" },
 ].map((ide) => (
 <span
 key={ide.name}
 style={{
 display: "inline-flex",
 alignItems: "center",
 gap: "0.375rem",
 padding: "0.3rem 0.75rem",
 borderRadius: 9999,
 border: "1.5px solid rgba(249,247,242,0.2)",
 background: "rgba(249,247,242,0.06)",
 fontSize: "0.65rem",
 fontFamily: "var(--font-mono)",
 fontWeight: 700,
 color: "var(--text-on-dark)",
 }}
 >
 <span style={{ width: 5, height: 5, borderRadius: "50%", background: "var(--primary)", display: "inline-block" }} />
 {ide.name}
 </span>
 ))}
 </div>

 <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.625rem" }}>
 {["Zero external dependencies", "Exposes remember, recall, and store_fact tools", "Works via stdio JSON-RPC channels"].map((item) => (
 <li key={item} style={{ display: "flex", alignItems: "center", gap: "0.625rem", fontSize: "0.82rem", color: "rgba(249,247,242,0.65)" }}>
 <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--primary)", display: "inline-block", flexShrink: 0 }} />
 {item}
 </li>
 ))}
 </ul>
 </div>

 {/* Terminal Mockup */}
 <div className="lg:col-span-7">
 <div
 style={{
 borderRadius: 10,
 border: "2px solid rgba(249,247,242,0.15)",
 overflow: "hidden",
 boxShadow: "7px 7px 0 rgba(249,247,242,0.1)",
 }}
 >
 {/* Terminal header */}
 <div
 style={{
 display: "flex",
 alignItems: "center",
 justifyContent: "space-between",
 padding: "0.75rem 1rem",
 background: "rgba(249,247,242,0.06)",
 borderBottom: "1px solid rgba(249,247,242,0.1)",
 }}
 >
 <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
 <span style={{ width: 10, height: 10, borderRadius: "50%", background: "rgba(249,247,242,0.2)" }} />
 <span style={{ width: 10, height: 10, borderRadius: "50%", background: "rgba(249,247,242,0.2)" }} />
 <span style={{ width: 10, height: 10, borderRadius: "50%", background: "rgba(249,247,242,0.2)" }} />
 </div>
 <span style={{ fontSize: "0.65rem", fontFamily: "var(--font-mono)", color: "rgba(249,247,242,0.4)" }}>terminal — kyros mcp</span>
 <span style={{ width: 40 }} />
 </div>

 {/* Terminal body */}
 <div
 style={{
 padding: "1.5rem",
 fontFamily: "var(--font-mono)",
 fontSize: "0.72rem",
 color: "rgba(249,247,242,0.75)",
 lineHeight: 1.8,
 background: "#0a0908",
 minHeight: 220,
 }}
 >
 <div style={{ color: "rgba(249,247,242,0.35)", marginBottom: "0.5rem" }}># Boot the built-in MCP server locally</div>
 <div style={{ color: "var(--primary)", marginBottom: "1rem", fontWeight: 700 }}>$ kyros mcp start</div>
 <div>[info] Initializing Stdio MCP host</div>
 <div>[info] Registered tool: remember (Store episodic memories)</div>
 <div>[info] Registered tool: recall (Semantic memory queries)</div>
 <div>[info] Registered tool: store_fact (Record triple facts)</div>
 <div style={{ color: "#4ade80", fontWeight: 700, marginBottom: "1rem" }}>[ready] MCP server listening on stdio JSON-RPC</div>
 <div style={{ color: "rgba(249,247,242,0.35)", marginBottom: "0.5rem" }}>&lt;IDE Agent connected &gt;</div>
 <div style={{ color: "#60a5fa" }}>[mcp] Calling tool &quot;recall&quot; — agent_id: cursor-env</div>
 <div>[mcp] Found 3 matching episodic memories (Confidence: 0.96)</div>
 </div>
 </div>
 </div>
 </div>
 </div>
 </section>

 {/* ══════════════════════════════════════════
 INTEGRATION CODE TABS
 Cream background, bordered code window
 ══════════════════════════════════════════ */}
 <section
 id="quickstart"
 style={{
 background: "var(--bg-alt)",
 borderBottom: S.border,
 padding: "5rem 1.5rem",
 }}
 >
 <div style={{ maxWidth: "1152px", margin: "0 auto" }}>
 <div style={{ textAlign: "center", marginBottom: "3.5rem" }}>
 <h2
 style={{
 fontSize: "clamp(1.75rem, 4vw, 2.75rem)",
 fontWeight: 900,
 letterSpacing: "-0.04em",
 color: "var(--text)",
 margin: "0 0 1rem",
 }}
 >
 1-Line Framework Integrations
 </h2>
 <p style={{ color: "var(--text-muted)", maxWidth: "52ch", margin: "0 auto 1.25rem", fontSize: "0.9rem", lineHeight: 1.7 }}>
 Kyros works with <strong style={{ color: "var(--text)" }}>any LLM provider</strong> — OpenAI, Anthropic Claude, Google Gemini, Mistral, or local models via Ollama. Just plug in the memory layer.
 </p>
 <div style={{ display: "flex", flexWrap: "wrap" as const, justifyContent: "center", gap: "0.5rem" }}>
 {["OpenAI", "Anthropic", "Google Gemini", "Mistral", "Ollama (Local)"].map((p) => (
 <span
 key={p}
 style={{
 padding: "0.25rem 0.75rem",
 borderRadius: 9999,
 border: S.border,
 background: "var(--bg)",
 fontSize: "0.65rem",
 fontFamily: "var(--font-mono)",
 color: "var(--text-muted)",
 fontWeight: 600,
 }}
 >
 {p}
 </span>
 ))}
 </div>
 </div>

 <div className="grid lg:grid-cols-12 gap-8 items-start">
 {/* Integration selector */}
 <div className="lg:col-span-4 space-y-2">
 {([
 { id: "crewai", label: "CrewAI", desc: "Episodic and semantic tools injected directly into CrewAI Agent lists." },
 { id: "langchain", label: "LangChain", desc: "Idiomatic ConversationChain memory wrappers — works with any LangChain-compatible LLM." },
 { id: "llamaindex", label: "LlamaIndex", desc: "Data memory components for chat engines and query structures." },
 ] as const).map((tab) => (
 <button
 key={tab.id}
 onClick={() => setActiveIntegration(tab.id)}
 style={{
 width: "100%",
 padding: "1rem 1.25rem",
 borderRadius: 8,
 textAlign: "left" as const,
 cursor: "pointer",
 border: activeIntegration === tab.id ? S.border : `1.5px solid var(--border-light)`,
 background: activeIntegration === tab.id ? "var(--primary)" : "var(--bg)",
 boxShadow: activeIntegration === tab.id ? S.shadow : "none",
 transition: "all 0.15s",
 }}
 >
 <span style={{ fontSize: "0.8rem", fontWeight: 800, display: "block", marginBottom: "0.25rem", color: "var(--text)" }}>{tab.label}</span>
 <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", display: "block", lineHeight: 1.5 }}>{tab.desc}</span>
 </button>
 ))}
 </div>

 {/* Code window */}
 <div
 className="lg:col-span-8"
 style={{
 borderRadius: 10,
 border: S.border,
 overflow: "hidden",
 boxShadow: S.shadowLg,
 }}
 >
 <div
 style={{
 display: "flex",
 alignItems: "center",
 justifyContent: "space-between",
 padding: "0.75rem 1rem",
 background: "var(--bg-alt)",
 borderBottom: S.border,
 }}
 >
 <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
 <span style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--border-light)" }} />
 <span style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--border-light)" }} />
 <span style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--border-light)" }} />
 </div>
 <span style={{ fontSize: "0.65rem", fontFamily: "var(--font-mono)", color: "var(--text-muted)", fontWeight: 600 }}>integration_setup.py</span>
 <div style={{ width: 40 }} />
 </div>

 <div
 style={{
 padding: "1.5rem",
 fontFamily: "var(--font-mono)",
 fontSize: "0.72rem",
 color: "#d4cfc8",
 lineHeight: 1.8,
 overflowX: "auto",
 background: "var(--bg-dark)",
 }}
 >
 {activeIntegration === "crewai" && (
 <pre style={{ margin: 0 }}>
 <code>{`from kyros.integrations.crewai import get_kyros_tools
from crewai import Agent, Crew, Task

# Works with any LLM backend your CrewAI is configured with
# (OpenAI, Anthropic, Gemini, Mistral, Ollama, etc.)
tools = get_kyros_tools(agent_id="finance-agent")

researcher = Agent(
 role="Financial Researcher",
 goal="Investigate market trends",
 tools=tools # Memory tools auto-injected into every agent turn
)

# Kyros memory is automatically queried and stored during execution.`}</code>
 </pre>
 )}
 {activeIntegration === "langchain" && (
 <pre style={{ margin: 0 }}>
 <code>{`from kyros.integrations.langchain import KyrosChatMemory
from langchain.chains import ConversationChain

# KyrosChatMemory is provider-agnostic — use it with any LLM:
# ChatOpenAI, ChatAnthropic, ChatGoogleGenerativeAI, ChatMistralAI, etc.
from langchain_openai import ChatOpenAI # or swap for any provider

memory = KyrosChatMemory(
 agent_id="support-agent"
 # api_key and base_url resolved from env vars
)

chain = ConversationChain(
 llm=ChatOpenAI(model="gpt-4o"), # swap any LangChain LLM here
 memory=memory
)

# Conversations are automatically stored and semantically indexed
response = chain.run("My server host is staging.internal")`}</code>
 </pre>
 )}
 {activeIntegration === "llamaindex" && (
 <pre style={{ margin: 0 }}>
 <code>{`from kyros.integrations.llama_index import KyrosMemory
from llama_index.core.chat_engine import SimpleChatEngine

# KyrosMemory is compatible with any LlamaIndex LLM backend:
# OpenAI, Anthropic, Gemini, Mistral, or local Ollama models
memory = KyrosMemory(
 agent_id="data-analyst-agent"
 # api_key resolved from KYROS_API_KEY env var
)

engine = SimpleChatEngine.from_defaults(
 memory=memory # Kyros persists context across sessions
)

response = engine.chat("Summarize Q3 financial results.")`}</code>
 </pre>
 )}
 </div>
 </div>
 </div>
 </div>
 </section>

 {/* ══════════════════════════════════════════
 PROXY MODE SECTION
 Light gray background, hard-border cards
 ══════════════════════════════════════════ */}
 <section
 style={{
 background: "var(--bg)",
 borderBottom: S.border,
 padding: "5rem 1.5rem",
 }}
 >
 <div style={{ maxWidth: "1152px", margin: "0 auto" }}>
 <div className="grid lg:grid-cols-12 gap-10 items-center">
 <div className="lg:col-span-6 space-y-5">
 <div
 style={{
 display: "inline-flex",
 alignItems: "center",
 gap: "0.5rem",
 padding: "0.3rem 0.9rem",
 borderRadius: 9999,
 border: S.border,
 background: "var(--primary)",
 fontFamily: "var(--font-mono)",
 fontSize: "0.65rem",
 fontWeight: 700,
 letterSpacing: "0.1em",
 textTransform: "uppercase" as const,
 color: "var(--text)",
 boxShadow: S.shadow,
 }}
 >
 Proxy Mode
 </div>

 <h2
 style={{
 fontSize: "clamp(1.75rem, 3.5vw, 2.5rem)",
 fontWeight: 900,
 letterSpacing: "-0.04em",
 color: "var(--text)",
 lineHeight: 1.1,
 margin: 0,
 }}
 >
 Intercept LLM payloads without writing code
 </h2>

 <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", lineHeight: 1.75, margin: 0 }}>
 Integrate Kyros with legacy platforms that do not support custom memory SDKs. Point your OpenAI, Gemini, or Mistral client <code style={{ fontFamily: "var(--font-mono)", fontSize: "0.82rem", background: "var(--bg-alt)", padding: "0.125rem 0.375rem", borderRadius: 4, border: S.borderLight }}>base_url</code> directly to the Kyros proxy endpoint. Kyros automatically queries active memory, injects context into the prompts, and hashes the turn before routing to the provider.
 </p>
 </div>

 <div className="lg:col-span-6">
 <div
 style={{
 border: S.border,
 borderRadius: S.radius,
 background: "var(--bg-alt)",
 padding: "1.5rem",
 boxShadow: S.shadowLg,
 }}
 >
 <span style={{ fontSize: "0.6rem", fontFamily: "var(--font-mono)", textTransform: "uppercase" as const, letterSpacing: "0.1em", color: "var(--text-muted)", fontWeight: 700, display: "block", marginBottom: "1rem" }}>
 Standard OpenAI vs Kyros Proxy Payload
 </span>
 <div className="grid grid-cols-2 gap-4">
 {/* Standard */}
 <div
 style={{
 padding: "1rem",
 borderRadius: 8,
 background: "var(--bg)",
 border: S.border,
 }}
 >
 <h4 style={{ fontSize: "0.72rem", fontWeight: 800, color: "var(--text-muted)", marginBottom: "0.75rem", margin: "0 0 0.75rem" }}>Standard Payload</h4>
 <pre style={{ fontSize: "0.65rem", fontFamily: "var(--font-mono)", color: "var(--text-muted)", margin: 0, overflowX: "auto" }}>
{`{
 "model": "gpt-4",
 "messages": [
 {
 "role": "user",
 "content": "Generate review"
 }
 ]
}`}
 </pre>
 </div>
 {/* Proxy */}
 <div
 style={{
 padding: "1rem",
 borderRadius: 8,
 background: "var(--bg-dark)",
 border: S.border,
 }}
 >
 <h4 style={{ fontSize: "0.72rem", fontWeight: 800, color: "var(--primary)", marginBottom: "0.75rem", margin: "0 0 0.75rem" }}>Intercepted Payload</h4>
 <pre style={{ fontSize: "0.65rem", fontFamily: "var(--font-mono)", color: "rgba(249,247,242,0.7)", margin: 0, overflowX: "auto" }}>
{`{
 "model": "gpt-4",
 "messages": [
 {
 "role": "system",
 "content": "[Memory context:
User prefers strict typing]"
 },
 {
 "role": "user",
 "content": "Generate review"
 }
 ]
}`}
 </pre>
 </div>
 </div>
 </div>
 </div>
 </div>
 </div>
 </section>

 {/* ══════════════════════════════════════════
 SYSTEM SPECIFICATIONS — Numbered Timeline
 Cream background, editorial numbered items
 ══════════════════════════════════════════ */}
 <section
 style={{
 background: "var(--bg-alt)",
 borderBottom: S.border,
 padding: "5rem 1.5rem",
 }}
 >
 <div style={{ maxWidth: "1152px", margin: "0 auto" }}>
 <div style={{ textAlign: "center", marginBottom: "4rem" }}>
 <h2
 style={{
 fontSize: "clamp(1.75rem, 4vw, 2.75rem)",
 fontWeight: 900,
 letterSpacing: "-0.04em",
 color: "var(--text)",
 margin: "0 0 1rem",
 }}
 >
 System Specifications & Features
 </h2>
 <p style={{ color: "var(--text-muted)", maxWidth: "50ch", margin: "0 auto", fontSize: "0.9rem", lineHeight: 1.7 }}>
 Every layer of Kyros is engineered for production-grade reliability, security, and extensibility.
 </p>
 </div>

 <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
 {[
 { num: "01", title: "Three Biological Memory Modules", desc: "Episodic (time-ordered conversation logs), semantic (subject–predicate–object fact triples), and procedural (workflow state machines) subsystems share a unified REST API and storage backend.", tag: "Architecture" },
 { num: "02", title: "Ebbinghaus Temporal Decay Engine", desc: "Memory relevance scores decay over time using configurable half-life parameters per memory type. Prevents context window bloat and keeps recalls focused on recent, high-confidence data.", tag: "Memory Science" },
 { num: "03", title: "SHA-256 Merkle Integrity Auditing", desc: "Every memory write is hashed into an append-only Merkle chain. Tampering, injection attacks, and data corruption are detected instantly through root comparison and subtree validation.", tag: "Security" },
 { num: "04", title: "Adaptive Belief Propagation Graph", desc: "When contradictory facts are stored, Kyros propagates confidence score adjustments through the semantic graph using breadth-first traversal, resolving conflicts automatically.", tag: "Reasoning" },
 { num: "05", title: "Causal Relationship Chain Tracking", desc: "Parent–child links between memory nodes allow agents to trace the exact chain of reasoning that led to a conclusion, enabling transparent and auditable AI decision-making.", tag: "Explainability" },
 { num: "06", title: "Zero-Code LLM Proxy Interception", desc: "Point any LLM client's base_url at the Kyros proxy endpoint. Kyros automatically intercepts the request, injects relevant memory context into the system prompt, and routes to your provider.", tag: "Integration" },
 ].map((f, i) => (
 <div
 key={f.num}
 style={{
 display: "flex",
 gap: "2rem",
 padding: "2rem 0",
 borderBottom: i < 5 ? S.border : "none",
 alignItems: "flex-start",
 }}
 className="group"
 >
 {/* Big number */}
 <div
 style={{
 fontSize: "clamp(2.5rem, 5vw, 4rem)",
 fontWeight: 900,
 color: "var(--text)",
 lineHeight: 1,
 letterSpacing: "-0.05em",
 flexShrink: 0,
 minWidth: "3rem",
 fontFamily: "var(--font-mono)",
 opacity: 0.15,
 }}
 >
 {f.num}
 </div>

 {/* Content */}
 <div style={{ flex: 1, paddingTop: "0.375rem" }}>
 <div style={{ display: "flex", flexWrap: "wrap" as const, alignItems: "center", gap: "0.75rem", marginBottom: "0.625rem" }}>
 <h3
 style={{
 fontSize: "1rem",
 fontWeight: 900,
 color: "var(--text)",
 margin: 0,
 letterSpacing: "-0.02em",
 }}
 >
 {f.title}
 </h3>
 <span
 style={{
 display: "inline-block",
 padding: "0.2rem 0.6rem",
 borderRadius: 9999,
 border: S.border,
 background: "var(--bg)",
 fontSize: "0.6rem",
 fontFamily: "var(--font-mono)",
 fontWeight: 700,
 textTransform: "uppercase" as const,
 letterSpacing: "0.08em",
 color: "var(--text-muted)",
 }}
 >
 {f.tag}
 </span>
 </div>
 <p style={{ fontSize: "0.88rem", color: "var(--text-muted)", lineHeight: 1.75, margin: 0, maxWidth: "68ch" }}>
 {f.desc}
 </p>
 </div>
 </div>
 ))}
 </div>
 </div>
 </section>

 {/* ══════════════════════════════════════════
 UP IN 60 SECONDS — Installation
 Dark background, code tabs
 ══════════════════════════════════════════ */}
 <section
 style={{
 background: "var(--bg-dark)",
 color: "var(--text-on-dark)",
 padding: "5rem 1.5rem",
 }}
 >
 <div style={{ maxWidth: "896px", margin: "0 auto" }}>
 <h2
 style={{
 fontSize: "clamp(1.75rem, 4vw, 2.75rem)",
 fontWeight: 900,
 letterSpacing: "-0.04em",
 color: "var(--text-on-dark)",
 textAlign: "center",
 margin: "0 0 2.5rem",
 }}
 >
 Up in 60 seconds
 </h2>

 <div
 style={{
 border: "2px solid rgba(249,247,242,0.15)",
 borderRadius: S.radius,
 overflow: "hidden",
 boxShadow: "7px 7px 0 rgba(249,247,242,0.08)",
 }}
 >
 {/* Tabs */}
 <div
 style={{
 display: "flex",
 borderBottom: "2px solid rgba(249,247,242,0.15)",
 background: "rgba(249,247,242,0.04)",
 padding: "0 1rem",
 }}
 >
 {([
 { id: "docker", label: "Self-Host (Docker)" },
 { id: "python", label: "Python SDK" },
 { id: "typescript", label: "TypeScript SDK" },
 ] as const).map((tab) => (
 <button
 key={tab.id}
 onClick={() => setActiveCodeTab(tab.id)}
 style={{
 padding: "1rem 1.25rem",
 fontFamily: "var(--font-mono)",
 fontSize: "0.72rem",
 fontWeight: 700,
 color: activeCodeTab === tab.id ? "var(--primary)" : "rgba(249,247,242,0.45)",
 background: "transparent",
 border: "none",
 borderBottom: activeCodeTab === tab.id ? "2px solid var(--primary)" : "2px solid transparent",
 cursor: "pointer",
 transition: "color 0.15s",
 marginBottom: "-2px",
 }}
 >
 {tab.label}
 </button>
 ))}
 </div>

 {/* Code */}
 <div
 style={{
 padding: "1.5rem",
 fontFamily: "var(--font-mono)",
 fontSize: "0.72rem",
 color: "rgba(249,247,242,0.75)",
 lineHeight: 1.8,
 overflowX: "auto",
 background: "#0a0908",
 }}
 >
 {activeCodeTab === "docker" && (
 <pre style={{ margin: 0 }}>
 <code>{`# Clone the repository
git clone https://github.com/Kyros-494/kyros-ai
cd kyros-ai

# Start the PostgreSQL + pgvector + Redis container stacks
docker compose up -d

# API server running locally on: http://localhost:8000
# Visual Dashboard: http://localhost:8000/dashboard
# Dev API Key: mk_live_default_dev_key_123456`}</code>
 </pre>
 )}
 {activeCodeTab === "python" && (
 <pre style={{ margin: 0 }}>
 <code>{`# Install dependencies
pip install kyros-sdk

# Initialize client
from kyros import KyrosClient

client = KyrosClient(
 base_url="http://localhost:8000",
 api_key="mk_live_default_dev_key_123456"
)

# Store episodic memory
client.remember("agent-1", "User prefers strict typing.")

# Recall memories
results = client.recall("agent-1", "What type guidelines does user follow?")
print(results.results[0].content)
# -> "User prefers strict typing."`}</code>
 </pre>
 )}
 {activeCodeTab === "typescript" && (
 <pre style={{ margin: 0 }}>
 <code>{`// Install dependencies
npm install @kyros.494/sdk

// Initialize client
import { KyrosClient } from '@kyros.494/sdk';
const client = new KyrosClient({
 baseUrl: 'http://localhost:8000',
 apiKey: 'mk_live_default_dev_key_123456'
});

// Store and recall memories
await client.remember('agent-123', 'User prefers TypeScript and dark mode');

const results = await client.query({
 agentId: 'agent-1',
 query: 'What type guidelines does user follow?',
 memoryTypes: ['semantic']
});`}</code>
 </pre>
 )}
 </div>
 </div>
 </div>
 </section>

 </div>
 );
}
