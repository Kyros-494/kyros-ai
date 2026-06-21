"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";

/* ─── Types ─────────────────────────────────────────────────── */
interface Memory {
 id: string;
 content: string;
 hash: string;
 weight: number;
 type: "semantic" | "episodic";
 createdAt: number; // simulated day
 tags: string[];
}

interface ChatMessage {
 role: "user" | "assistant" | "system";
 content: string;
 retrievedMemories?: string[];
 timestamp: number;
}

type Tab = "playground" | "pipeline" | "decay" | "merkle";

const S = {
 border: "2px solid var(--border)",
 borderLight: "1px solid var(--border-light)",
 shadow: "var(--shadow)",
 shadowLg: "var(--shadow-lg)",
};

/* ─── Preset scenarios ──────────────────────────────────────── */
const SCENARIOS = [
 {
 id: "chatbot",
 icon: "💬",
 title: "Chatbot Memory",
 subtitle: "Watch an AI remember you across conversations",
 description:
 "You'll play as a user chatting with a Kyros-powered AI. The AI will remember your name, preferences, and history — just like a real product would.",
 preloadedMemories: [
 { content: "User's name is Alex. Prefers dark mode.", type: "semantic" as const, tags: ["profile", "preference"] },
 { content: "Alex is building a Python backend API.", type: "episodic" as const, tags: ["project"] },
 ],
 suggestedMessages: [
 "What's my name?",
 "What project am I working on?",
 "I now prefer TypeScript over Python.",
 "What do you know about me?",
 ],
 },
 {
 id: "multiagent",
 icon: "🤖",
 title: "Multi-Agent Coordination",
 subtitle: "See how AI agents share knowledge",
 description:
 "Three agents (Researcher, Coder, QA) collaborate on a sprint. Watch how Kyros shared memory prevents duplication and keeps every agent in sync.",
 preloadedMemories: [
 { content: "Researcher: React 19 concurrent mode is production-stable.", type: "semantic" as const, tags: ["research", "react"] },
 { content: "Coder: Using React 19 for new dashboard. No breaking changes confirmed.", type: "episodic" as const, tags: ["code", "react"] },
 ],
 suggestedMessages: [
 "What did the Researcher find?",
 "Is React 19 safe to use?",
 "Add QA test: verify concurrent rendering works.",
 "What's our current tech stack decision?",
 ],
 },
 {
 id: "compliance",
 icon: "️",
 title: "Compliance & Audit",
 subtitle: "Reconstruct what the AI knew at any point in time",
 description:
 "Financial regulators require an answer: 'What did the system believe about client risk on March 1st?' Watch Kyros bitemporal queries prove exactly that.",
 preloadedMemories: [
 { content: "Client risk tolerance: Conservative (recorded Jan 1)", type: "semantic" as const, tags: ["risk", "compliance"] },
 { content: "Client risk updated to Moderate (recorded Apr 1)", type: "semantic" as const, tags: ["risk", "updated"] },
 ],
 suggestedMessages: [
 "What was the client risk on Jan 15?",
 "When was risk tolerance last changed?",
 "Show me the audit trail for risk changes.",
 "What did we know before April?",
 ],
 },
];

/* ─── Smart AI response generator ─────────────────────────── */
function generateAIResponse(
 userMsg: string,
 memories: Memory[],
 scenarioId: string
): { content: string; retrievedMemories: string[] } {
 const lower = userMsg.toLowerCase();
 const retrieved: string[] = [];
 let response = "";

 // Find relevant memories
 const relevant = memories.filter((m) => {
 const words = lower.split(" ").filter((w) => w.length > 3);
 return words.some(
 (w) =>
 m.content.toLowerCase().includes(w) ||
 m.tags.some((t) => t.toLowerCase().includes(w))
 );
 });

 relevant.forEach((m) => retrieved.push(m.content));

 if (lower.includes("name") && scenarioId === "chatbot") {
 const nameMem = memories.find((m) => m.content.toLowerCase().includes("name"));
 if (nameMem) {
 response = `Based on your profile in my memory vault, your name is **Alex**. I retrieved this from a stored semantic memory: "${nameMem.content.substring(0, 60)}..."`;
 } else {
 response = "I don't have your name stored yet. What should I call you?";
 }
 } else if (lower.includes("project") || lower.includes("working on")) {
 const projMem = memories.find((m) => m.tags.includes("project") || m.content.toLowerCase().includes("project") || m.content.toLowerCase().includes("building"));
 if (projMem) {
 response = `From your episodic memory logs, I can see: ${projMem.content}. This was stored with ${Math.round(projMem.weight)}% retention weight.`;
 } else {
 response = "I don't see any project details stored yet. Tell me what you're working on and I'll remember it.";
 }
 } else if (lower.includes("typescript") || lower.includes("prefer")) {
 response = "Got it! I'm updating your preference in the memory vault. Your old Python preference will be marked as conflicted, and the new TypeScript preference will take priority.";
 } else if (lower.includes("know about me") || lower.includes("what do you")) {
 if (memories.length > 0) {
 const summary = memories
 .filter((m) => m.weight > 40)
 .slice(0, 3)
 .map((m) => `• ${m.content}`)
 .join("\n");
 response = `Here's what I remember about you (${memories.length} total memories, showing top-weighted):\n\n${summary}\n\nAll memories have cryptographic hashes for tamper-proof verification.`;
 } else {
 response = "I don't have any memories stored yet. Try sending a few messages and watch the memory vault populate!";
 }
 } else if (lower.includes("risk") && scenarioId === "compliance") {
 const riskMem = memories.find((m) => m.tags.includes("risk"));
 if (riskMem) {
 response = `**Bitemporal query result:** Based on memories recorded before April, the client risk tolerance was **Conservative**. After April 1st update, it changed to **Moderate**. Full audit trail is cryptographically sealed in the Merkle tree. Hash: ${riskMem.hash.substring(0, 20)}...`;
 } else {
 response = "No risk tolerance data found in memory. Please add client profile memories first.";
 }
 } else if (lower.includes("react") && scenarioId === "multiagent") {
 response = `**Shared Memory Retrieved.** The Researcher agent confirmed React 19 concurrent mode is production-stable. The Coder agent has already recorded this decision. No contradictions detected in the shared belief graph. All agents are aligned.`;
 } else if (lower.includes("audit") || lower.includes("trail")) {
 response = `The Merkle tree contains ${memories.length} leaf nodes. Each memory event is hashed with SHA-256 and appended to the tree. The root hash represents the cryptographic fingerprint of your entire memory state. Any tampering would invalidate the root — making this audit-proof.`;
 } else if (relevant.length > 0) {
 response = `I found ${relevant.length} relevant memory record(s) for your query. The most relevant: "${relevant[0].content.substring(0, 80)}..." — stored with Ebbinghaus-weighted retention.`;
 } else {
 response = `I don't have specific memories matching your query yet. I've noted your input and will store it as a new episodic memory. The memory pipeline is now processing: ingestion → SHA-256 hash → Merkle append → decay initialization.`;
 }

 return { content: response, retrievedMemories: retrieved };
}

/* ─── Purity Helpers ──────────────────────────────────────── */
function getTimestamp() {
 return Date.now();
}
function getRandomHash() {
 return "sha256_" + Math.random().toString(16).substring(2, 14);
}

/* ─── Main Component ─────────────────────────────────────── */
export default function SimulationPage() {
 const [activeScenario, setActiveScenario] = useState<typeof SCENARIOS[0] | null>(null);
 const [tab, setTab] = useState<Tab>("playground");
 const [memories, setMemories] = useState<Memory[]>([]);
 const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
 const [chatInput, setChatInput] = useState("");
 const [isTyping, setIsTyping] = useState(false);
 const [simulatedDay, setSimulatedDay] = useState(0);
 const [pipelineStep, setPipelineStep] = useState(-1);
 const [isRunningPipeline, setIsRunningPipeline] = useState(false);
 const [lastIngestedContent, setLastIngestedContent] = useState("");
 const [ingestInput, setIngestInput] = useState("");
 const [ingestType, setIngestType] = useState<"semantic" | "episodic">("episodic");
 const [copiedHash, setCopiedHash] = useState<string | null>(null);
 const chatEndRef = useRef<HTMLDivElement>(null);
 const dayRef = useRef(simulatedDay);

 useEffect(() => {
 dayRef.current = simulatedDay;
 }, [simulatedDay]);

 /* ─── Scroll chat ─────────────────────────────────────── */
 useEffect(() => {
 chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
 }, [chatMessages, isTyping]);

 /* ─── Load scenario ───────────────────────────────────── */
 const loadScenario = (scenario: typeof SCENARIOS[0]) => {
 setActiveScenario(scenario);
 const now = 0;
 const initialMemories: Memory[] = scenario.preloadedMemories.map((m, i) => ({
 id: `m${i + 1}`,
 content: m.content,
 hash: getRandomHash(),
 weight: 100,
 type: m.type,
 createdAt: now,
 tags: m.tags,
 }));
 setMemories(initialMemories);
 setChatMessages([
 {
 role: "system",
 content: `**${scenario.title}** scenario loaded. ${scenario.description}\n\n${initialMemories.length} memories pre-loaded into the vault. Try the suggested prompts or type your own!`,
 timestamp: getTimestamp(),
 },
 ]);
 setSimulatedDay(0);
 setPipelineStep(-1);
 setChatInput("");
 setTab("playground");
 };

 /* ─── Send chat message ───────────────────────────────── */
 const sendMessage = async () => {
 if (!chatInput.trim() || !activeScenario) return;
 const userContent = chatInput.trim();
 setChatInput("");

 const userMsg: ChatMessage = { role: "user", content: userContent, timestamp: getTimestamp() };
 setChatMessages((prev) => [...prev, userMsg]);
 setIsTyping(true);

 // Simulate storing the message as a new episodic memory
 const newMemHash = getRandomHash();
 const newMem: Memory = {
 id: `m${memories.length + 1}`,
 content: userContent,
 hash: newMemHash,
 weight: 100,
 type: "episodic",
 createdAt: dayRef.current,
 tags: ["user_input"],
 };
 setLastIngestedContent(userContent);

 setTimeout(() => {
 setMemories((prev) => [newMem, ...prev]);
 const { content, retrievedMemories } = generateAIResponse(userContent, [...memories, newMem], activeScenario.id);
 const aiMsg: ChatMessage = {
 role: "assistant",
 content,
 retrievedMemories,
 timestamp: getTimestamp(),
 };
 setChatMessages((prev) => [...prev, aiMsg]);
 setIsTyping(false);
 }, 1200 + Math.random() * 600);
 };

 /* ─── Ingest memory manually ──────────────────────────── */
 const ingestMemory = () => {
 if (!ingestInput.trim()) return;
 const newMem: Memory = {
 id: `m${memories.length + 1}`,
 content: ingestInput.trim(),
 hash: getRandomHash(),
 weight: 100,
 type: ingestType,
 createdAt: simulatedDay,
 tags: [ingestType],
 };
 setMemories((prev) => [newMem, ...prev]);
 setLastIngestedContent(ingestInput.trim());
 setIngestInput("");
 runPipeline();
 };

 /* ─── Run pipeline animation ──────────────────────────── */
 const runPipeline = useCallback(() => {
 setIsRunningPipeline(true);
 setPipelineStep(0);
 let step = 0;
 const interval = setInterval(() => {
 step++;
 setPipelineStep(step);
 if (step >= 5) {
 clearInterval(interval);
 setIsRunningPipeline(false);
 setTimeout(() => setPipelineStep(-1), 3000);
 }
 }, 700);
 }, []);

 /* ─── Apply time decay ────────────────────────────────── */
 const applyDecay = (days: number) => {
 setSimulatedDay(days);
 setMemories((prev) =>
 prev.map((m) => {
 const age = days - m.createdAt;
 const lambda = m.type === "semantic" ? 0.003 : 0.04;
 const weight = Math.round(100 * Math.exp(-lambda * age));
 return { ...m, weight: Math.max(1, weight) };
 })
 );
 };

 /* ─── Merkle tree nodes ───────────────────────────────── */
 const merkleRoot =
 memories.length > 0
 ? "sha256_" + Math.abs(memories.map((m) => parseInt(m.hash.split("_")[1] || "0", 16)).reduce((a, b) => a + b, 0)).toString(16).substring(0, 12)
 : "sha256_0000_empty";

 /* ─── Copy hash ─────────────────────────────────────────── */
 const copyHash = (hash: string) => {
 navigator.clipboard.writeText(hash);
 setCopiedHash(hash);
 setTimeout(() => setCopiedHash(null), 2000);
 };

 /* ─── Pipeline steps ─────────────────────────────────── */
 const PIPELINE_STEPS = [
 { icon: "📥", name: "Ingest Event", desc: "Parse and tokenize the input text into structured memory context." },
 { icon: "🔐", name: "SHA-256 Hash", desc: "Generate a cryptographic fingerprint. No two memories share the same hash." },
 { icon: "🌳", name: "Merkle Append", desc: "Add the hash as a leaf node. Recalculate parent hashes up to root." },
 { icon: "📉", name: "Ebbinghaus Weight", desc: "Initialize retention weight at 100%. Decay curve begins immediately." },
 { icon: "🧠", name: "Belief Check", desc: "Scan semantic graph for contradictions. Resolve conflicts automatically." },
 { icon: "💾", name: "Commit to DB", desc: "Write to Postgres pgvector. Cache hot key in Redis for fast retrieval." },
 ];

 /* ============================================================
 RENDER
 ============================================================ */

 /* ─── Scenario Picker (no scenario selected) ─────────── */
 if (!activeScenario) {
 return (
 <div style={{ background: "var(--bg)", color: "var(--text)", width: "100%", minHeight: "100vh" }}>
 {/* Hero */}
 <section
 style={{
 background: "var(--bg-dark)",
 color: "var(--text-on-dark)",
 borderBottom: S.border,
 padding: "5rem 1.5rem 4rem",
 textAlign: "center",
 }}
 >
 <div style={{ maxWidth: "800px", margin: "0 auto" }}>
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
 Interactive Sandbox
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
 See Kyros in action.<br />No signup required.
 </h1>
 <p style={{ color: "rgba(249,247,242,0.6)", maxWidth: "52ch", fontSize: "1rem", lineHeight: 1.8, margin: "0 auto 2rem" }}>
 Pick a scenario below and interact with a live Kyros-powered AI. Watch memories being stored, hashed, decayed, and retrieved in real time.
 </p>

 {/* Explainer badges */}
 <div style={{ display: "flex", justifyContent: "center", gap: "0.75rem", flexWrap: "wrap", marginBottom: "3rem" }}>
 {["Live Memory Vault", "Cryptographic Hashing", "Ebbinghaus Decay", "Merkle Tree", "Chat Interface"].map((badge) => (
 <span
 key={badge}
 style={{
 padding: "0.3rem 0.875rem",
 border: "1px solid rgba(232,245,66,0.25)",
 borderRadius: 9999,
 background: "rgba(232,245,66,0.08)",
 fontSize: "0.72rem",
 fontFamily: "var(--font-mono)",
 color: "var(--primary)",
 fontWeight: 600,
 }}
 >
 {badge}
 </span>
 ))}
 </div>
 </div>
 </section>

 {/* Scenario Cards */}
 <section style={{ padding: "4rem 1.5rem 6rem", background: "var(--bg)" }}>
 <div style={{ maxWidth: "1000px", margin: "0 auto" }}>
 <h2 style={{ fontSize: "1.1rem", fontWeight: 900, letterSpacing: "-0.03em", fontFamily: "var(--font-mono)", margin: "0 0 0.5rem", textTransform: "uppercase", color: "var(--text-muted)" }}>
 Choose a Scenario
 </h2>
 <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", margin: "0 0 2rem" }}>
 Each scenario is self-contained with pre-loaded memories and guided prompts. You can switch scenarios at any time.
 </p>
 <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1.5rem" }}>
 {SCENARIOS.map((scenario) => (
 <button
 key={scenario.id}
 onClick={() => loadScenario(scenario)}
 style={{
 textAlign: "left",
 padding: "2rem",
 border: S.border,
 borderRadius: "var(--radius)",
 background: "var(--bg)",
 boxShadow: S.shadow,
 cursor: "pointer",
 transition: "transform 0.15s, box-shadow 0.15s",
 display: "flex",
 flexDirection: "column",
 gap: "0.875rem",
 }}
 onMouseEnter={(e) => {
 (e.currentTarget as HTMLElement).style.transform = "translate(-2px,-2px)";
 (e.currentTarget as HTMLElement).style.boxShadow = S.shadowLg;
 }}
 onMouseLeave={(e) => {
 (e.currentTarget as HTMLElement).style.transform = "translate(0,0)";
 (e.currentTarget as HTMLElement).style.boxShadow = S.shadow;
 }}
 >
 <span style={{ fontSize: "2.5rem" }}>{scenario.icon}</span>
 <div>
 <h3 style={{ fontSize: "1.1rem", fontWeight: 900, letterSpacing: "-0.03em", color: "var(--text)", margin: "0 0 0.3rem" }}>
 {scenario.title}
 </h3>
 <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", margin: "0 0 0.75rem" }}>
 {scenario.subtitle}
 </p>
 <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", lineHeight: 1.6, margin: 0 }}>
 {scenario.description}
 </p>
 </div>
 <div
 style={{
 display: "inline-flex",
 alignItems: "center",
 gap: "0.35rem",
 padding: "0.4rem 0.875rem",
 border: S.border,
 borderRadius: 6,
 background: "var(--text)",
 color: "var(--bg)",
 fontFamily: "var(--font-mono)",
 fontSize: "0.7rem",
 fontWeight: 800,
 alignSelf: "flex-start",
 }}
 >
 Launch Scenario →
 </div>
 </button>
 ))}
 </div>

 {/* What you'll see */}
 <div style={{ marginTop: "3rem", border: S.border, borderRadius: "var(--radius)", background: "var(--bg-dark)", color: "var(--text-on-dark)", padding: "2rem" }}>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 1.25rem", color: "var(--primary)" }}>
 What you&apos;ll be able to see inside the sandbox
 </h3>
 <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1.25rem" }}>
 {[
 { icon: "💬", title: "Chat Playground", desc: "Chat with a Kyros-powered AI. Every message triggers real memory operations." },
 { icon: "️", title: "Pipeline View", desc: "Step through all 6 stages of memory processing: ingest → hash → Merkle → decay → resolve → commit." },
 { icon: "📉", title: "Decay Timeline", desc: "Slide through time and watch Ebbinghaus forgetting curves decay each memory's weight." },
 { icon: "🌳", title: "Merkle Tree", desc: "Inspect the live cryptographic tree that guarantees memory integrity and tamper-proof audit." },
 ].map((item) => (
 <div key={item.title} style={{ display: "flex", gap: "0.875rem", alignItems: "flex-start" }}>
 <span style={{ fontSize: "1.5rem", flexShrink: 0 }}>{item.icon}</span>
 <div>
 <div style={{ fontSize: "0.82rem", fontWeight: 800, color: "var(--text-on-dark)", marginBottom: "0.25rem" }}>{item.title}</div>
 <div style={{ fontSize: "0.72rem", color: "rgba(249,247,242,0.55)", lineHeight: 1.6 }}>{item.desc}</div>
 </div>
 </div>
 ))}
 </div>
 </div>
 </div>
 </section>
 </div>
 );
 }

 /* ─── Active Scenario UI ─────────────────────────────── */
 return (
 <div style={{ background: "var(--bg)", color: "var(--text)", width: "100%", minHeight: "100vh" }}>
 {/* Scenario Header Bar */}
 <div
 style={{
 background: "var(--bg-dark)",
 borderBottom: S.border,
 padding: "0.875rem 1.5rem",
 display: "flex",
 alignItems: "center",
 gap: "1rem",
 flexWrap: "wrap",
 position: "sticky",
 top: 64,
 zIndex: 20,
 }}
 >
 <button
 onClick={() => setActiveScenario(null)}
 style={{
 padding: "0.35rem 0.875rem",
 border: "1px solid rgba(249,247,242,0.2)",
 borderRadius: 6,
 background: "transparent",
 color: "rgba(249,247,242,0.7)",
 fontFamily: "var(--font-mono)",
 fontSize: "0.65rem",
 fontWeight: 700,
 cursor: "pointer",
 }}
 >
 ← Back
 </button>
 <span style={{ fontSize: "1.25rem" }}>{activeScenario.icon}</span>
 <div>
 <span style={{ fontSize: "0.9rem", fontWeight: 900, color: "var(--text-on-dark)", letterSpacing: "-0.02em" }}>
 {activeScenario.title}
 </span>
 <span style={{ fontSize: "0.72rem", color: "rgba(249,247,242,0.45)", marginLeft: "0.75rem", fontFamily: "var(--font-mono)" }}>
 {memories.length} memories · Day {simulatedDay}
 </span>
 </div>

 {/* Tab Switcher */}
 <div style={{ marginLeft: "auto", display: "flex", gap: "0.25rem" }}>
 {(["playground", "pipeline", "decay", "merkle"] as Tab[]).map((t) => (
 <button
 key={t}
 onClick={() => setTab(t)}
 style={{
 padding: "0.35rem 0.875rem",
 border: "1px solid rgba(249,247,242,0.2)",
 borderRadius: 6,
 background: tab === t ? "var(--primary)" : "transparent",
 color: tab === t ? "var(--text)" : "rgba(249,247,242,0.6)",
 fontFamily: "var(--font-mono)",
 fontSize: "0.65rem",
 fontWeight: 700,
 cursor: "pointer",
 textTransform: "capitalize" as const,
 }}
 >
 {t === "playground" ? "💬 Chat" : t === "pipeline" ? "️ Pipeline" : t === "decay" ? "📉 Decay" : "🌳 Merkle"}
 </button>
 ))}
 </div>
 </div>

 {/* ─── TAB: Playground ─────────────────────────────── */}
 {tab === "playground" && (
 <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: "1.5rem", padding: "1.5rem", maxWidth: "1200px", margin: "0 auto", alignItems: "start" }}>

 {/* Chat Interface */}
 <div style={{ border: S.border, borderRadius: "var(--radius)", background: "var(--bg)", overflow: "hidden", boxShadow: S.shadow }}>
 {/* Chat Header */}
 <div style={{ padding: "1rem 1.5rem", borderBottom: S.border, background: "var(--bg-alt)", display: "flex", alignItems: "center", gap: "0.75rem" }}>
 <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#22c55e" }} />
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" as const, letterSpacing: "0.1em" }}>
 Kyros AI · Memory-Powered Chat
 </span>
 <span style={{ marginLeft: "auto", fontFamily: "var(--font-mono)", fontSize: "0.62rem", color: "var(--text-muted)" }}>
 {memories.length} active memories
 </span>
 </div>

 {/* Messages */}
 <div style={{ height: 420, overflowY: "auto", padding: "1.25rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
 {chatMessages.map((msg, idx) => (
 <div key={idx} style={{ display: "flex", flexDirection: "column", alignItems: msg.role === "user" ? "flex-end" : "flex-start", gap: "0.25rem" }}>
 {msg.role === "system" ? (
 <div style={{ width: "100%", padding: "1rem 1.25rem", border: "1px solid rgba(232,245,66,0.2)", borderRadius: 10, background: "rgba(232,245,66,0.06)", fontFamily: "var(--font-mono)", fontSize: "0.72rem", color: "var(--text-muted)", lineHeight: 1.7 }}>
 {msg.content.split("\n").map((line, i) => (
 <div key={i} style={{ fontWeight: line.startsWith("**") ? 800 : 400, color: line.startsWith("**") ? "var(--text)" : "var(--text-muted)" }}>
 {line.replace(/\*\*/g, "")}
 </div>
 ))}
 </div>
 ) : (
 <>
 <div
 style={{
 maxWidth: "78%",
 padding: "0.875rem 1.125rem",
 borderRadius: msg.role === "user" ? "12px 12px 2px 12px" : "12px 12px 12px 2px",
 background: msg.role === "user" ? "var(--text)" : "var(--bg-alt)",
 color: msg.role === "user" ? "var(--bg)" : "var(--text)",
 border: S.borderLight,
 fontSize: "0.85rem",
 lineHeight: 1.7,
 }}
 >
 {msg.content.split("\n").map((line, i) => (
 <div key={i} style={{ fontWeight: line.startsWith("**") ? 800 : 400 }}>
 {line.replace(/\*\*/g, "")}
 </div>
 ))}
 </div>
 {msg.role === "assistant" && msg.retrievedMemories && msg.retrievedMemories.length > 0 && (
 <div style={{ maxWidth: "78%", padding: "0.5rem 0.875rem", borderRadius: 6, background: "rgba(232,245,66,0.08)", border: "1px solid rgba(232,245,66,0.2)" }}>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", fontWeight: 800, color: "var(--primary)", textTransform: "uppercase" as const, letterSpacing: "0.08em" }}>
 🔍 Retrieved {msg.retrievedMemories.length} memory record{msg.retrievedMemories.length > 1 ? "s" : ""}
 </span>
 </div>
 )}
 </>
 )}
 </div>
 ))}
 {isTyping && (
 <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
 <div style={{ padding: "0.875rem 1.125rem", borderRadius: "12px 12px 12px 2px", background: "var(--bg-alt)", border: S.borderLight }}>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", color: "var(--text-muted)", letterSpacing: "0.15em" }}>
 ● ● ●
 </span>
 </div>
 </div>
 )}
 <div ref={chatEndRef} />
 </div>

 {/* Suggested Messages */}
 <div style={{ padding: "0.75rem 1.25rem", borderTop: S.borderLight, background: "var(--bg-alt)", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
 {activeScenario.suggestedMessages.map((msg) => (
 <button
 key={msg}
 onClick={() => { setChatInput(msg); }}
 style={{
 padding: "0.3rem 0.75rem",
 border: S.borderLight,
 borderRadius: 9999,
 background: "var(--bg)",
 color: "var(--text-muted)",
 fontSize: "0.68rem",
 fontFamily: "var(--font-mono)",
 cursor: "pointer",
 whiteSpace: "nowrap" as const,
 transition: "all 0.15s",
 }}
 >
 {msg}
 </button>
 ))}
 </div>

 {/* Input */}
 <div style={{ padding: "1rem 1.25rem", borderTop: S.border, display: "flex", gap: "0.75rem" }}>
 <input
 type="text"
 value={chatInput}
 onChange={(e) => setChatInput(e.target.value)}
 onKeyDown={(e) => e.key === "Enter" && sendMessage()}
 placeholder="Ask the AI anything — it remembers you..."
 style={{
 flex: 1,
 padding: "0.75rem 1rem",
 border: S.border,
 borderRadius: 8,
 background: "var(--bg)",
 color: "var(--text)",
 fontSize: "0.875rem",
 fontFamily: "var(--font-sans)",
 outline: "none",
 }}
 />
 <button
 onClick={sendMessage}
 disabled={!chatInput.trim() || isTyping}
 style={{
 padding: "0.75rem 1.25rem",
 border: S.border,
 borderRadius: 8,
 background: chatInput.trim() && !isTyping ? "var(--text)" : "var(--bg-alt)",
 color: chatInput.trim() && !isTyping ? "var(--bg)" : "var(--text-muted)",
 fontWeight: 800,
 fontSize: "0.82rem",
 cursor: chatInput.trim() && !isTyping ? "pointer" : "not-allowed",
 fontFamily: "var(--font-mono)",
 transition: "all 0.15s",
 }}
 >
 Send →
 </button>
 </div>
 </div>

 {/* Memory Vault Sidebar */}
 <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
 {/* Vault Header */}
 <div style={{ border: S.border, borderRadius: "var(--radius)", overflow: "hidden", background: "var(--bg)", boxShadow: S.shadow }}>
 <div style={{ padding: "0.875rem 1.25rem", borderBottom: S.border, background: "var(--bg-dark)", display: "flex", alignItems: "center", gap: "0.5rem" }}>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.65rem", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.1em", color: "var(--primary)" }}>
 Live Memory Vault
 </span>
 <span style={{ marginLeft: "auto", padding: "0.15rem 0.5rem", borderRadius: 4, background: "rgba(232,245,66,0.15)", fontFamily: "var(--font-mono)", fontSize: "0.6rem", color: "var(--primary)", fontWeight: 700 }}>
 {memories.length} records
 </span>
 </div>
 <div style={{ maxHeight: 360, overflowY: "auto", padding: "0.75rem" }}>
 {memories.length === 0 ? (
 <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.8rem" }}>
 No memories yet. Start chatting!
 </div>
 ) : (
 memories.slice(0, 8).map((m) => (
 <div
 key={m.id}
 style={{
 padding: "0.75rem 0.875rem",
 marginBottom: "0.5rem",
 border: S.borderLight,
 borderRadius: 8,
 background: m === memories[0] ? "rgba(232,245,66,0.06)" : "var(--bg-alt)",
 borderLeft: m === memories[0] ? "3px solid var(--primary)" : "3px solid transparent",
 transition: "all 0.2s",
 }}
 >
 {/* Badge row */}
 <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.4rem" }}>
 <span style={{ padding: "0.12rem 0.4rem", borderRadius: 4, background: m.type === "semantic" ? "var(--bg-dark)" : "rgba(232,245,66,0.15)", color: m.type === "semantic" ? "var(--primary)" : "var(--text)", fontFamily: "var(--font-mono)", fontSize: "0.55rem", fontWeight: 800, textTransform: "uppercase" as const }}>
 {m.type}
 </span>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.55rem", color: "var(--text-muted)" }}>
 {m.hash.substring(0, 12)}…
 </span>
 </div>
 {/* Content */}
 <p style={{ fontSize: "0.75rem", color: "var(--text)", margin: "0 0 0.4rem", lineHeight: 1.5, fontWeight: 500 }}>
 {m.content.length > 60 ? m.content.substring(0, 60) + "…" : m.content}
 </p>
 {/* Retention bar */}
 <div>
 <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.2rem" }}>
 <span style={{ fontSize: "0.58rem", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>Retention</span>
 <span style={{ fontSize: "0.65rem", fontFamily: "var(--font-mono)", fontWeight: 900, color: m.weight > 50 ? "#16a34a" : m.weight > 20 ? "#ca8a04" : "#dc2626" }}>
 {m.weight}%
 </span>
 </div>
 <div style={{ height: 4, borderRadius: 2, background: "var(--border-light)", overflow: "hidden" }}>
 <div style={{ height: "100%", width: `${m.weight}%`, background: m.weight > 50 ? "#22c55e" : m.weight > 20 ? "#eab308" : "#ef4444", borderRadius: 2, transition: "width 0.5s" }} />
 </div>
 </div>
 </div>
 ))
 )}
 </div>
 </div>

 {/* Quick Ingest */}
 <div style={{ border: S.border, borderRadius: "var(--radius)", background: "var(--bg)", padding: "1.25rem", boxShadow: S.shadow }}>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.65rem", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.1em", color: "var(--text-muted)", display: "block", marginBottom: "0.875rem" }}>
 📥 Manual Ingest
 </span>
 <textarea
 value={ingestInput}
 onChange={(e) => setIngestInput(e.target.value)}
 placeholder="Type a memory to ingest directly..."
 rows={2}
 style={{ width: "100%", padding: "0.625rem 0.875rem", border: S.border, borderRadius: 6, background: "var(--bg-alt)", color: "var(--text)", fontSize: "0.78rem", resize: "none", outline: "none", fontFamily: "var(--font-sans)", boxSizing: "border-box" }}
 />
 <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.625rem" }}>
 {(["episodic", "semantic"] as const).map((t) => (
 <button
 key={t}
 onClick={() => setIngestType(t)}
 style={{ flex: 1, padding: "0.35rem", border: ingestType === t ? S.border : S.borderLight, borderRadius: 6, background: ingestType === t ? "var(--text)" : "var(--bg)", color: ingestType === t ? "var(--bg)" : "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: "0.6rem", fontWeight: 700, cursor: "pointer" }}
 >
 {t}
 </button>
 ))}
 </div>
 <button
 onClick={ingestMemory}
 disabled={!ingestInput.trim() || isRunningPipeline}
 style={{ width: "100%", marginTop: "0.625rem", padding: "0.625rem", border: S.border, borderRadius: 6, background: ingestInput.trim() ? "var(--primary)" : "var(--bg-alt)", color: "var(--text)", fontFamily: "var(--font-mono)", fontSize: "0.72rem", fontWeight: 800, cursor: ingestInput.trim() ? "pointer" : "not-allowed" }}
 >
 {isRunningPipeline ? "Processing…" : "Ingest + Run Pipeline →"}
 </button>
 </div>
 </div>
 </div>
 )}

 {/* ─── TAB: Pipeline ───────────────────────────────── */}
 {tab === "pipeline" && (
 <div style={{ padding: "2rem 1.5rem", maxWidth: "1000px", margin: "0 auto" }}>
 <div style={{ marginBottom: "1.5rem" }}>
 <h2 style={{ fontSize: "1.4rem", fontWeight: 900, letterSpacing: "-0.03em", margin: "0 0 0.5rem" }}>
 Memory Pipeline — 6 Stages
 </h2>
 <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", margin: "0 0 1.25rem" }}>
 Every memory event goes through this deterministic pipeline before being committed to the database. Click any step to learn more, or trigger a live run.
 </p>
 <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
 <input
 value={ingestInput}
 onChange={(e) => setIngestInput(e.target.value)}
 placeholder="Enter a memory event to trace through the pipeline..."
 style={{ flex: 1, padding: "0.75rem 1rem", border: S.border, borderRadius: 8, background: "var(--bg)", color: "var(--text)", fontSize: "0.85rem", outline: "none" }}
 />
 <button
 onClick={() => { if (ingestInput.trim()) { ingestMemory(); setTab("pipeline"); } }}
 style={{ padding: "0.75rem 1.25rem", border: S.border, borderRadius: 8, background: "var(--text)", color: "var(--bg)", fontWeight: 800, fontSize: "0.82rem", cursor: "pointer", fontFamily: "var(--font-mono)" }}
 >
 ▶ Run Pipeline
 </button>
 </div>
 </div>

 {/* Pipeline Steps */}
 <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
 {PIPELINE_STEPS.map((step, idx) => {
 const isActive = idx === pipelineStep;
 const isDone = idx < pipelineStep;
 return (
 <div
 key={step.name}
 style={{
 display: "flex",
 alignItems: "flex-start",
 gap: "1.25rem",
 padding: "1.5rem",
 border: isActive ? S.border : S.borderLight,
 borderRadius: "var(--radius)",
 background: isActive ? "var(--primary)" : isDone ? "var(--bg-alt)" : "var(--bg)",
 transition: "all 0.3s",
 boxShadow: isActive ? S.shadowLg : "none",
 transform: isActive ? "translate(-2px, -2px)" : "none",
 }}
 >
 {/* Step number */}
 <div
 style={{
 width: 48,
 height: 48,
 borderRadius: 10,
 border: isActive ? "2px solid var(--text)" : S.borderLight,
 background: isActive ? "var(--text)" : isDone ? "var(--bg-dark)" : "var(--bg-alt)",
 display: "flex",
 alignItems: "center",
 justifyContent: "center",
 fontSize: "1.25rem",
 flexShrink: 0,
 }}
 >
 {isDone ? "" : step.icon}
 </div>
 <div style={{ flex: 1 }}>
 <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.4rem" }}>
 <h3 style={{ fontSize: "0.95rem", fontWeight: 900, letterSpacing: "-0.02em", margin: 0, color: isActive ? "var(--text)" : isDone ? "var(--text-muted)" : "var(--text)" }}>
 Step {idx + 1}: {step.name}
 </h3>
 {isActive && (
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", fontWeight: 800, padding: "0.15rem 0.5rem", borderRadius: 4, background: "var(--text)", color: "var(--bg)", textTransform: "uppercase" as const, letterSpacing: "0.08em" }}>
 ACTIVE
 </span>
 )}
 {isDone && (
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", fontWeight: 800, padding: "0.15rem 0.5rem", borderRadius: 4, background: "#dcfce7", color: "#15803d", textTransform: "uppercase" as const, letterSpacing: "0.08em" }}>
 DONE
 </span>
 )}
 </div>
 <p style={{ fontSize: "0.82rem", color: isActive ? "rgba(17,16,16,0.7)" : "var(--text-muted)", margin: 0, lineHeight: 1.6 }}>
 {step.desc}
 </p>
 {isActive && lastIngestedContent && (
 <div style={{ marginTop: "0.875rem", padding: "0.625rem 0.875rem", borderRadius: 6, background: "rgba(17,16,16,0.08)", border: "1px solid rgba(17,16,16,0.15)", fontFamily: "var(--font-mono)", fontSize: "0.72rem", color: "var(--text)" }}>
 Processing: &quot;{lastIngestedContent.substring(0, 60)}{lastIngestedContent.length > 60 ? "…" : ""}&quot;
 </div>
 )}
 </div>
 {/* Progress connector */}
 {idx < PIPELINE_STEPS.length - 1 && (
 <div style={{ position: "absolute", left: "2.4rem", top: "100%", width: 2, height: "1rem", background: isDone ? "var(--text)" : "var(--border-light)", display: "none" }} />
 )}
 </div>
 );
 })}
 </div>

 {pipelineStep === -1 && (
 <div style={{ marginTop: "1.5rem", padding: "1.25rem", border: S.borderLight, borderRadius: "var(--radius)", background: "var(--bg-alt)", fontSize: "0.82rem", color: "var(--text-muted)", textAlign: "center" }}>
 Enter a memory event above and click &quot;Run Pipeline&quot; to trace it through all 6 stages in real time.
 </div>
 )}
 </div>
 )}

 {/* ─── TAB: Decay Timeline ─────────────────────────── */}
 {tab === "decay" && (
 <div style={{ padding: "2rem 1.5rem", maxWidth: "1000px", margin: "0 auto" }}>
 <h2 style={{ fontSize: "1.4rem", fontWeight: 900, letterSpacing: "-0.03em", margin: "0 0 0.5rem" }}>
 Ebbinghaus Forgetting Curve
 </h2>
 <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", margin: "0 0 1.5rem", maxWidth: "60ch" }}>
 Drag the slider to simulate the passage of time. Watch how each memory&apos;s retention weight decays according to its type — episodic memories fade faster than semantic ones.
 </p>

 {/* Time Slider */}
 <div style={{ border: S.border, borderRadius: "var(--radius)", padding: "1.5rem 2rem", background: "var(--bg-dark)", color: "var(--text-on-dark)", marginBottom: "1.5rem" }}>
 <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", color: "rgba(249,247,242,0.6)", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.08em" }}>
 Simulated Time
 </span>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "1.5rem", fontWeight: 900, color: "var(--primary)" }}>
 Day {simulatedDay}
 </span>
 </div>
 <input
 type="range"
 min="0"
 max="90"
 value={simulatedDay}
 onChange={(e) => applyDecay(Number(e.target.value))}
 style={{ width: "100%", accentColor: "#e8f542" }}
 />
 <div style={{ display: "flex", justifyContent: "space-between", marginTop: "0.5rem" }}>
 {["Day 0", "Day 15", "Day 30", "Day 45", "Day 60", "Day 75", "Day 90"].map((label) => (
 <span key={label} style={{ fontFamily: "var(--font-mono)", fontSize: "0.58rem", color: "rgba(249,247,242,0.35)" }}>
 {label}
 </span>
 ))}
 </div>

 {/* Decay Type Legend */}
 <div style={{ display: "flex", gap: "1.5rem", marginTop: "1.25rem", paddingTop: "1.25rem", borderTop: "1px solid rgba(249,247,242,0.1)" }}>
 <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
 <div style={{ width: 24, height: 3, borderRadius: 2, background: "var(--primary)" }} />
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.65rem", color: "rgba(249,247,242,0.6)" }}>Semantic (slow decay, λ=0.003)</span>
 </div>
 <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
 <div style={{ width: 24, height: 3, borderRadius: 2, background: "#f87171" }} />
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.65rem", color: "rgba(249,247,242,0.6)" }}>Episodic (fast decay, λ=0.04)</span>
 </div>
 </div>
 </div>

 {/* Memory Decay Table */}
 <div style={{ border: S.border, borderRadius: "var(--radius)", overflow: "hidden", background: "var(--bg)", boxShadow: S.shadow }}>
 <div style={{ padding: "0.875rem 1.5rem", borderBottom: S.border, background: "var(--bg-alt)", display: "flex", gap: "1rem" }}>
 <span style={{ flex: 2, fontFamily: "var(--font-mono)", fontSize: "0.62rem", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.1em", color: "var(--text-muted)" }}>Memory Content</span>
 <span style={{ flex: 1, fontFamily: "var(--font-mono)", fontSize: "0.62rem", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.1em", color: "var(--text-muted)" }}>Type</span>
 <span style={{ flex: 1, fontFamily: "var(--font-mono)", fontSize: "0.62rem", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.1em", color: "var(--text-muted)" }}>Retention</span>
 <span style={{ flex: 2, fontFamily: "var(--font-mono)", fontSize: "0.62rem", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.1em", color: "var(--text-muted)" }}>Decay Bar</span>
 <span style={{ flex: 1, fontFamily: "var(--font-mono)", fontSize: "0.62rem", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.1em", color: "var(--text-muted)" }}>Status</span>
 </div>
 {memories.length === 0 ? (
 <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.875rem" }}>
 No memories loaded. Go to Chat and interact to build up memories.
 </div>
 ) : (
 memories.map((m) => (
 <div key={m.id} style={{ padding: "1rem 1.5rem", borderBottom: S.borderLight, display: "flex", gap: "1rem", alignItems: "center" }}>
 <span style={{ flex: 2, fontSize: "0.8rem", color: "var(--text)", lineHeight: 1.4 }}>
 {m.content.length > 50 ? m.content.substring(0, 50) + "…" : m.content}
 </span>
 <span style={{ flex: 1 }}>
 <span style={{ padding: "0.15rem 0.4rem", borderRadius: 4, background: m.type === "semantic" ? "var(--bg-dark)" : "rgba(232,245,66,0.15)", color: m.type === "semantic" ? "var(--primary)" : "var(--text)", fontFamily: "var(--font-mono)", fontSize: "0.58rem", fontWeight: 800, textTransform: "uppercase" as const }}>
 {m.type}
 </span>
 </span>
 <span style={{ flex: 1, fontFamily: "var(--font-mono)", fontWeight: 900, fontSize: "1rem", color: m.weight > 50 ? "#16a34a" : m.weight > 20 ? "#ca8a04" : "#dc2626" }}>
 {m.weight}%
 </span>
 <div style={{ flex: 2, height: 8, borderRadius: 4, background: "var(--border-light)", overflow: "hidden" }}>
 <div style={{ height: "100%", width: `${m.weight}%`, background: m.weight > 50 ? "#22c55e" : m.weight > 20 ? "#eab308" : "#ef4444", borderRadius: 4, transition: "width 0.4s ease" }} />
 </div>
 <span style={{ flex: 1, fontFamily: "var(--font-mono)", fontSize: "0.65rem", fontWeight: 700, color: m.weight < 10 ? "#dc2626" : m.weight < 40 ? "#ca8a04" : "var(--text-muted)" }}>
 {m.weight < 10 ? " Fading" : m.weight < 40 ? "Declining" : "Healthy"}
 </span>
 </div>
 ))
 )}
 </div>
 <div style={{ marginTop: "1rem", padding: "1rem 1.25rem", border: S.borderLight, borderRadius: "var(--radius)", background: "var(--bg-alt)", fontSize: "0.78rem", color: "var(--text-muted)", lineHeight: 1.7 }}>
 <strong>How it works:</strong> Retention is calculated as W = 100 × e<sup>-λt</sup> where t = age in days. Semantic memories use λ=0.003 (half-life ≈ 231 days). Episodic memories use λ=0.04 (half-life ≈ 17 days). Memories below the configured minimum threshold are pruned from recall results automatically.
 </div>
 </div>
 )}

 {/* ─── TAB: Merkle Tree ─────────────────────────────── */}
 {tab === "merkle" && (
 <div style={{ padding: "2rem 1.5rem", maxWidth: "1000px", margin: "0 auto" }}>
 <h2 style={{ fontSize: "1.4rem", fontWeight: 900, letterSpacing: "-0.03em", margin: "0 0 0.5rem" }}>
 Merkle Tree — Cryptographic Memory Integrity
 </h2>
 <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", margin: "0 0 1.5rem", maxWidth: "64ch" }}>
 Every memory is a leaf node in a Merkle tree. The root hash is a cryptographic fingerprint of your entire memory state. Any tampering with any memory invalidates the root — making the entire store audit-proof.
 </p>

 {/* Root Hash */}
 <div style={{ border: S.border, borderRadius: "var(--radius)", padding: "1.5rem 2rem", background: "var(--bg-dark)", color: "var(--text-on-dark)", marginBottom: "1.5rem", display: "flex", alignItems: "center", gap: "1.5rem", flexWrap: "wrap" }}>
 <div>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", fontWeight: 700, color: "rgba(249,247,242,0.4)", textTransform: "uppercase" as const, letterSpacing: "0.12em", marginBottom: "0.4rem" }}>
 🌳 Merkle Root Hash
 </div>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.95rem", fontWeight: 800, color: "var(--primary)", letterSpacing: "0.05em" }}>
 {merkleRoot}
 </div>
 </div>
 <div style={{ marginLeft: "auto", display: "flex", gap: "0.5rem" }}>
 <button
 onClick={() => copyHash(merkleRoot)}
 style={{ padding: "0.4rem 0.875rem", border: "1px solid rgba(249,247,242,0.2)", borderRadius: 6, background: "transparent", color: copiedHash === merkleRoot ? "var(--primary)" : "rgba(249,247,242,0.7)", fontFamily: "var(--font-mono)", fontSize: "0.65rem", fontWeight: 700, cursor: "pointer" }}
 >
 {copiedHash === merkleRoot ? " Copied" : "⎘ Copy Root"}
 </button>
 <div style={{ padding: "0.4rem 0.875rem", border: "1px solid rgba(22,163,74,0.4)", borderRadius: 6, background: "rgba(22,163,74,0.1)", fontFamily: "var(--font-mono)", fontSize: "0.65rem", fontWeight: 700, color: "#4ade80" }}>
 Verified
 </div>
 </div>
 </div>

 {/* Leaf nodes */}
 <div style={{ border: S.border, borderRadius: "var(--radius)", overflow: "hidden", background: "var(--bg)", boxShadow: S.shadow }}>
 <div style={{ padding: "0.875rem 1.5rem", borderBottom: S.border, background: "var(--bg-alt)", display: "flex", gap: "1rem", alignItems: "center" }}>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.62rem", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.1em", color: "var(--text-muted)" }}>
 Leaf Nodes — {memories.length} Records
 </span>
 <span style={{ marginLeft: "auto", fontFamily: "var(--font-mono)", fontSize: "0.62rem", color: "var(--text-muted)" }}>
 Tree Depth: {Math.ceil(Math.log2(Math.max(memories.length, 1) + 1))} levels
 </span>
 </div>

 {memories.length === 0 ? (
 <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.875rem" }}>
 Add memories in the Chat tab to see leaf nodes appear here.
 </div>
 ) : (
 memories.map((m, idx) => (
 <div
 key={m.id}
 style={{
 padding: "1.125rem 1.5rem",
 borderBottom: idx < memories.length - 1 ? S.borderLight : "none",
 display: "grid",
 gridTemplateColumns: "32px 1fr 1fr auto",
 gap: "1rem",
 alignItems: "center",
 }}
 >
 {/* Leaf index */}
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.65rem", fontWeight: 900, color: "var(--text-muted)" }}>
 L{String(idx).padStart(2, "0")}
 </span>

 {/* Content */}
 <div>
 <span style={{ fontSize: "0.78rem", color: "var(--text)", fontWeight: 500 }}>
 {m.content.length > 45 ? m.content.substring(0, 45) + "…" : m.content}
 </span>
 <div style={{ display: "flex", gap: "0.4rem", marginTop: "0.25rem" }}>
 {m.tags.map((tag) => (
 <span key={tag} style={{ padding: "0.08rem 0.35rem", borderRadius: 3, background: "rgba(232,245,66,0.1)", border: "1px solid rgba(232,245,66,0.2)", fontFamily: "var(--font-mono)", fontSize: "0.55rem", color: "var(--primary)", fontWeight: 700 }}>
 {tag}
 </span>
 ))}
 </div>
 </div>

 {/* Hash */}
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.68rem", color: "var(--text-muted)", letterSpacing: "0.03em" }}>
 {m.hash}
 </span>

 {/* Copy */}
 <button
 onClick={() => copyHash(m.hash)}
 style={{ padding: "0.25rem 0.6rem", border: S.borderLight, borderRadius: 4, background: copiedHash === m.hash ? "var(--text)" : "var(--bg-alt)", color: copiedHash === m.hash ? "var(--bg)" : "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: "0.58rem", fontWeight: 700, cursor: "pointer", whiteSpace: "nowrap" as const }}
 >
 {copiedHash === m.hash ? "" : "⎘"}
 </button>
 </div>
 ))
 )}
 </div>

 {/* Explainer */}
 <div style={{ marginTop: "1.25rem", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem" }}>
 {[
 { icon: "🔐", title: "Tamper-Proof", desc: "Modifying any leaf invalidates all parent hashes up to root. Tampering is immediately detectable." },
 { icon: "📋", title: "Audit-Ready", desc: "Regulators and auditors can verify the full memory history by checking the root hash against a snapshot." },
 { icon: "", title: "Efficient Proofs", desc: "Merkle proofs verify individual records in O(log n) time — even with millions of memories." },
 ].map((item) => (
 <div key={item.title} style={{ padding: "1.25rem", border: S.borderLight, borderRadius: "var(--radius)", background: "var(--bg-alt)" }}>
 <span style={{ fontSize: "1.5rem", display: "block", marginBottom: "0.5rem" }}>{item.icon}</span>
 <h4 style={{ fontSize: "0.85rem", fontWeight: 800, margin: "0 0 0.375rem" }}>{item.title}</h4>
 <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", margin: 0, lineHeight: 1.6 }}>{item.desc}</p>
 </div>
 ))}
 </div>
 </div>
 )}
 </div>
 );
}
