"use client";

import React, { useState } from "react";

const S = {
 border: "2px solid var(--border)",
 borderLight: "1px solid var(--border-light)",
 shadow: "var(--shadow)",
 shadowLg: "var(--shadow-lg)",
};

const ALL_CATEGORIES = ["All", "Beginner", "Intermediate", "Advanced", "Enterprise"];

const useCases = [
 {
 id: 1,
 level: "Beginner",
 industry: "Productivity",
 icon: "💬",
 title: "Persistent Chatbot Memory",
 subtitle: "Build a chatbot that actually remembers you",
 problem:
 "Standard AI assistants forget everything the moment a session ends. Users must repeat their name, preferences, and context on every new conversation — creating a frustrating, impersonal experience.",
 solution:
 "Kyros persists user-specific episodic and semantic memories across sessions. Each new conversation retrieves the most contextually relevant facts via vector similarity, injecting only what matters into the prompt.",
 outcome:
 "A returning user is greeted by name, their past preferences are already known, and the assistant picks up exactly where it left off — with zero prompt engineering from the developer.",
 codeSnippet: `# Store a memory event
kyros.ingest(
 content="User prefers dark mode and Python.",
 user_id="user_abc123",
 type="semantic"
)

# Later — retrieve relevant context
memories = kyros.recall(
 query="User UI preferences",
 user_id="user_abc123",
 top_k=3
)`,
 apiEndpoint: "POST /v1/memories/ingest",
 tags: ["Memory", "Personalization", "Chatbot"],
 },
 {
 id: 2,
 level: "Beginner",
 industry: "Customer Support",
 icon: "🎧",
 title: "Customer Support Context Retention",
 subtitle: "Never make customers repeat themselves again",
 problem:
 "Support agents (AI or human) lack full customer history. Every ticket is siloed. Customers grow frustrated repeating the same issues across 5 support interactions.",
 solution:
 "Kyros acts as a persistent CRM-layer for AI agents. Each support interaction is stored with timestamps. Future queries fetch the relevant complaint history, product version, and last resolution status.",
 outcome:
 "Support agents resolve tickets 40% faster with instant context. Customers feel heard. AI escalation reduces because the system already knows what was tried.",
 codeSnippet: `# After each support call
kyros.ingest(
 content="User reported billing error on invoice #4821. Refund initiated.",
 user_id="customer_99",
 metadata={"ticket_id": "T-4821", "status": "resolved"}
)

# On next ticket open
history = kyros.recall(
 query="billing issues",
 user_id="customer_99"
)`,
 apiEndpoint: "POST /v1/memories/ingest",
 tags: ["Support", "CRM", "Context"],
 },
 {
 id: 3,
 level: "Intermediate",
 industry: "Developer Tools",
 icon: "🤖",
 title: "Multi-Agent Shared Memory",
 subtitle: "Let your AI agents work as a real team",
 problem:
 "Autonomous agent pipelines (researcher → coder → QA) have no shared state. The researcher's findings are invisible to the coder. Agents duplicate work, lose context, and produce inconsistent results.",
 solution:
 "All agents in a pipeline write and read from a shared, tenant-isolated Kyros memory space. Merkle tree integrity verification ensures no agent receives tampered context. Each agent tags memories by role.",
 outcome:
 "The coder agent instantly knows what the researcher discovered. The QA agent already has the test criteria. Pipeline latency drops and output consistency improves dramatically.",
 codeSnippet: `# Researcher agent stores findings
kyros.ingest(
 content="React 19 concurrent mode is stable. No breaking changes.",
 agent_id="researcher_v2",
 session_id="sprint_42"
)

# Coder agent retrieves research
context = kyros.recall(
 query="React 19 compatibility",
 session_id="sprint_42",
 agent_id="researcher_v2"
)`,
 apiEndpoint: "POST /v1/memories/ingest",
 tags: ["Multi-Agent", "Shared State", "Pipelines"],
 },
 {
 id: 4,
 level: "Intermediate",
 industry: "Health & Wellness",
 icon: "🏥",
 title: "Longitudinal Patient AI Companion",
 subtitle: "Medical AI that remembers the full patient journey",
 problem:
 "Health AI assistants start cold every session. Doctors repeat patient history manually. Crucial patterns (medication reactions, visit triggers) are buried in unstructured notes.",
 solution:
 "Kyros stores structured semantic memories per patient: diagnosis history, medication logs, appointment notes. Vector similarity retrieves relevant past events when answering new queries.",
 outcome:
 "The health assistant surfaces relevant history automatically. Doctors review AI-surfaced context rather than hunting through EHR records. Patient safety improves through continuity.",
 codeSnippet: `# Log patient interaction
kyros.ingest(
 content="Patient allergic to penicillin. Reported rash in 2023.",
 user_id="patient_P-4892",
 type="semantic",
 metadata={"severity": "moderate", "year": 2023}
)

# Query relevant history before prescribing
history = kyros.recall(
 query="drug allergies and reactions",
 user_id="patient_P-4892"
)`,
 apiEndpoint: "POST /v1/memories/ingest",
 tags: ["Healthcare", "Continuity", "Safety"],
 },
 {
 id: 5,
 level: "Advanced",
 industry: "Finance & Legal",
 icon: "️",
 title: "Bitemporal Audit Trails for Compliance",
 subtitle: "What did the agent know, and when did it know it?",
 problem:
 "Financial and legal AI systems must demonstrate auditability. Regulators ask: 'What information did the system act on at time T?' Traditional databases overwrite states — making reconstruction impossible.",
 solution:
 "Kyros stores bitemporal metadata on every memory: valid_time (when the fact was true) and transaction_time (when it was recorded). You can reconstruct exact agent state at any historical moment.",
 outcome:
 "Full regulatory-grade audit trail for autonomous agent decisions. Comply with MiFID II, SEC rules, or HIPAA audit requirements. Prove exactly what the agent knew and when.",
 codeSnippet: `# Bitemporal ingestion
kyros.ingest(
 content="Client risk tolerance: Conservative.",
 user_id="client_883",
 valid_from="2024-01-01",
 valid_until="2024-06-30",
 recorded_at="2024-01-01T09:00:00Z"
)

# Reconstruct what agent believed on May 1st
# as recorded before June 15th
snapshot = kyros.bitemporal_query(
 user_id="client_883",
 as_of_valid="2024-05-01",
 as_of_transaction="2024-06-14"
)`,
 apiEndpoint: "GET /v1/memories/bitemporal",
 tags: ["Compliance", "Audit", "Bitemporal"],
 },
 {
 id: 6,
 level: "Advanced",
 industry: "Developer Tools",
 icon: "📉",
 title: "Ebbinghaus Token Optimization",
 subtitle: "Stop wasting tokens on irrelevant memories",
 problem:
 "Long-running AI workflows accumulate thousands of stale memory fragments. Injecting all of them into the prompt burns tokens, degrades LLM reasoning quality, and balloons costs.",
 solution:
 "Kyros applies the Ebbinghaus Forgetting Curve to decay memory relevance weights over time. Temporary events fade in hours; structural facts persist. Only high-density, relevant memories surface.",
 outcome:
 "Context window utilization drops by 60–80%. LLMs receive sharper, more focused prompts. Token costs fall linearly with decay pruning. Agent accuracy improves as noise disappears.",
 codeSnippet: `# Memory decay config
kyros.configure({
 "decay": {
 "episodic_half_life_hours": 24,
 "semantic_half_life_days": 90,
 "minimum_weight_threshold": 0.05
 }
})

# Recall only high-weight memories
relevant = kyros.recall(
 query="User project status",
 user_id="dev_u42",
 min_weight=0.3, # filter decayed noise
 top_k=5
)`,
 apiEndpoint: "GET /v1/memories/recall",
 tags: ["Token Efficiency", "Decay", "Cost"],
 },
 {
 id: 7,
 level: "Enterprise",
 industry: "E-commerce",
 icon: "🛒",
 title: "Personalized AI Shopping Assistant",
 subtitle: "Shopping that gets smarter with every purchase",
 problem:
 "E-commerce recommendation engines use collaborative filtering — what similar users bought. They ignore the individual's evolving taste, constraints, and stated intent over time.",
 solution:
 "Kyros builds a per-user preference model from browsing signals, stated preferences, and purchase history. Each conversation retrieves this profile to generate hyper-personalized recommendations.",
 outcome:
 "Conversion rates increase as recommendations precisely match individual taste. Return rate drops. The AI assistant evolves with the customer — knowing their size, style, and budget automatically.",
 codeSnippet: `# Store browsing intent
kyros.ingest(
 content="User interested in running shoes under $120, size 10.",
 user_id="shopper_77a",
 metadata={"category": "footwear", "budget": 120}
)

# On next session — hyper-targeted results
profile = kyros.recall(
 query="footwear preferences budget",
 user_id="shopper_77a"
)
# → Inject into product recommendation LLM call`,
 apiEndpoint: "POST /v1/memories/ingest",
 tags: ["E-commerce", "Personalization", "Revenue"],
 },
 {
 id: 8,
 level: "Enterprise",
 industry: "Education",
 icon: "🎓",
 title: "Adaptive AI Tutor with Learning Memory",
 subtitle: "A tutor that remembers exactly where each student struggles",
 problem:
 "AI tutors reset every session. Students re-explain their weak areas. Tutors repeat content the student already mastered. There is no persistent model of each learner's knowledge graph.",
 solution:
 "Kyros builds a per-student semantic knowledge graph. Topics mastered are weighted high. Persistent confusion patterns are flagged. Each session starts with a precise model of where to focus.",
 outcome:
 "Students progress 30% faster with zero repetition of mastered content. The tutor surfaces exactly the right challenge level. Retention improves as the system tracks long-term forgetting patterns.",
 codeSnippet: `# After each session
kyros.ingest(
 content="Student mastered quadratic equations. Struggles with trigonometry.",
 user_id="student_s1042",
 metadata={
 "mastered": ["quadratics"],
 "struggling": ["trig_identities"]
 }
)

# Next session prep
state = kyros.recall(
 query="mathematics weak areas",
 user_id="student_s1042"
)`,
 apiEndpoint: "POST /v1/memories/ingest",
 tags: ["EdTech", "Personalization", "Adaptive"],
 },
];

const LEVEL_COLORS: Record<string, { bg: string; color: string; border: string }> = {
 Beginner: { bg: "#dcfce7", color: "#15803d", border: "#86efac" },
 Intermediate: { bg: "#fef9c3", color: "#a16207", border: "#fde047" },
 Advanced: { bg: "#fee2e2", color: "#dc2626", border: "#fca5a5" },
 Enterprise: { bg: "#ede9fe", color: "#7c3aed", border: "#c4b5fd" },
};

export default function UsecasesPage() {
 const [activeCategory, setActiveCategory] = useState("All");
 const [expandedId, setExpandedId] = useState<number | null>(null);
 const [copiedId, setCopiedId] = useState<number | null>(null);

 const filtered = activeCategory === "All"
 ? useCases
 : useCases.filter((uc) => uc.level === activeCategory);

 const handleCopy = (id: number, code: string) => {
 navigator.clipboard.writeText(code);
 setCopiedId(id);
 setTimeout(() => setCopiedId(null), 2000);
 };

 return (
 <div style={{ background: "var(--bg)", color: "var(--text)", width: "100%" }}>
 {/* Hero */}
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
 <span>◆</span> Real-World Use Cases
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
 From simple chatbots<br />to enterprise compliance
 </h1>
 <p style={{ color: "rgba(249,247,242,0.6)", maxWidth: "56ch", fontSize: "1rem", lineHeight: 1.8, margin: "0 0 2.5rem" }}>
 Kyros handles memory at every level of complexity. Browse real-world patterns from beginner-friendly chatbot memory
 all the way to enterprise-grade bitemporal audit trails — with working code for each.
 </p>

 {/* Stats row */}
 <div style={{ display: "flex", gap: "2.5rem", flexWrap: "wrap" }}>
 {[
 { value: "8+", label: "Use Case Patterns" },
 { value: "4", label: "Complexity Levels" },
 { value: "6", label: "Industries Covered" },
 { value: "∞", label: "Combinations Possible" },
 ].map((stat) => (
 <div key={stat.label}>
 <div style={{ fontSize: "2rem", fontWeight: 900, fontFamily: "var(--font-mono)", color: "var(--primary)", lineHeight: 1 }}>
 {stat.value}
 </div>
 <div style={{ fontSize: "0.72rem", color: "rgba(249,247,242,0.5)", marginTop: "0.3rem", fontFamily: "var(--font-mono)", letterSpacing: "0.05em" }}>
 {stat.label}
 </div>
 </div>
 ))}
 </div>
 </div>
 </section>

 {/* Filter Bar */}
 <section style={{ borderBottom: S.border, background: "var(--bg-alt)", padding: "1rem 1.5rem", position: "sticky", top: 64, zIndex: 10 }}>
 <div style={{ maxWidth: "1152px", margin: "0 auto", display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
 <span style={{ fontSize: "0.7rem", fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" as const, letterSpacing: "0.1em", marginRight: "0.25rem" }}>
 Filter:
 </span>
 {ALL_CATEGORIES.map((cat) => (
 <button
 key={cat}
 onClick={() => setActiveCategory(cat)}
 style={{
 padding: "0.4rem 1rem",
 borderRadius: 9999,
 border: activeCategory === cat ? S.border : S.borderLight,
 background: activeCategory === cat ? "var(--text)" : "var(--bg)",
 color: activeCategory === cat ? "var(--bg)" : "var(--text)",
 fontFamily: "var(--font-mono)",
 fontSize: "0.72rem",
 fontWeight: 700,
 cursor: "pointer",
 transition: "all 0.15s",
 letterSpacing: "0.02em",
 }}
 >
 {cat}
 {cat !== "All" && (
 <span style={{ marginLeft: "0.4rem", opacity: 0.6 }}>
 ({useCases.filter((u) => u.level === cat).length})
 </span>
 )}
 </button>
 ))}
 <span style={{ marginLeft: "auto", fontSize: "0.7rem", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
 Showing {filtered.length} of {useCases.length}
 </span>
 </div>
 </section>

 {/* Use Cases Grid */}
 <section style={{ padding: "3rem 1.5rem 6rem", background: "var(--bg)" }}>
 <div style={{ maxWidth: "1152px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "2rem" }}>
 {filtered.map((uc) => {
 const levelStyle = LEVEL_COLORS[uc.level];
 const isExpanded = expandedId === uc.id;
 return (
 <div
 key={uc.id}
 style={{
 border: S.border,
 borderRadius: "var(--radius)",
 background: "var(--bg)",
 boxShadow: isExpanded ? S.shadowLg : S.shadow,
 overflow: "hidden",
 transition: "box-shadow 0.2s",
 }}
 >
 {/* Card Header */}
 <div
 style={{
 padding: "1.5rem 2rem",
 borderBottom: S.border,
 background: "var(--bg-dark)",
 display: "flex",
 alignItems: "flex-start",
 gap: "1.25rem",
 cursor: "pointer",
 }}
 onClick={() => setExpandedId(isExpanded ? null : uc.id)}
 >
 {/* Icon */}
 <div
 style={{
 width: 56,
 height: 56,
 borderRadius: 12,
 border: "2px solid rgba(249,247,242,0.15)",
 background: "rgba(249,247,242,0.06)",
 display: "flex",
 alignItems: "center",
 justifyContent: "center",
 fontSize: "1.6rem",
 flexShrink: 0,
 }}
 >
 {uc.icon}
 </div>

 {/* Title block */}
 <div style={{ flex: 1 }}>
 <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem", flexWrap: "wrap" }}>
 <span
 style={{
 padding: "0.2rem 0.6rem",
 borderRadius: 4,
 background: levelStyle.bg,
 color: levelStyle.color,
 border: `1px solid ${levelStyle.border}`,
 fontFamily: "var(--font-mono)",
 fontSize: "0.6rem",
 fontWeight: 800,
 textTransform: "uppercase" as const,
 letterSpacing: "0.08em",
 }}
 >
 {uc.level}
 </span>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.65rem", color: "rgba(249,247,242,0.4)", letterSpacing: "0.05em" }}>
 {uc.industry}
 </span>
 </div>
 <h2
 style={{
 fontSize: "1.2rem",
 fontWeight: 900,
 letterSpacing: "-0.03em",
 color: "var(--text-on-dark)",
 margin: "0 0 0.35rem",
 lineHeight: 1.25,
 }}
 >
 {uc.title}
 </h2>
 <p style={{ fontSize: "0.82rem", color: "rgba(249,247,242,0.5)", margin: 0 }}>
 {uc.subtitle}
 </p>
 </div>

 {/* Tags + expand */}
 <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "0.75rem" }}>
 <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", justifyContent: "flex-end" }}>
 {uc.tags.map((tag) => (
 <span
 key={tag}
 style={{
 padding: "0.2rem 0.5rem",
 borderRadius: 4,
 border: "1px solid rgba(232,245,66,0.25)",
 background: "rgba(232,245,66,0.08)",
 fontFamily: "var(--font-mono)",
 fontSize: "0.58rem",
 color: "var(--primary)",
 fontWeight: 700,
 letterSpacing: "0.05em",
 }}
 >
 {tag}
 </span>
 ))}
 </div>
 <span
 style={{
 fontFamily: "var(--font-mono)",
 fontSize: "0.7rem",
 color: "rgba(249,247,242,0.4)",
 display: "flex",
 alignItems: "center",
 gap: "0.3rem",
 }}
 >
 {isExpanded ? "▲ Collapse" : "▼ Expand"}
 </span>
 </div>
 </div>

 {/* Card Body — 3 cols */}
 <div
 style={{
 display: "grid",
 gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
 gap: 0,
 borderBottom: isExpanded ? S.border : "none",
 }}
 >
 {[
 { label: " The Problem", text: uc.problem, accentColor: "#dc2626" },
 { label: " Kyros Solution", text: uc.solution, accentColor: "var(--text)" },
 { label: " Business Outcome", text: uc.outcome, accentColor: "#16a34a" },
 ].map((col, ci) => (
 <div
 key={col.label}
 style={{
 padding: "1.75rem 2rem",
 borderRight: ci < 2 ? S.borderLight : "none",
 }}
 >
 <h4
 style={{
 fontSize: "0.6rem",
 fontFamily: "var(--font-mono)",
 fontWeight: 800,
 textTransform: "uppercase" as const,
 letterSpacing: "0.12em",
 color: col.accentColor,
 margin: "0 0 0.875rem",
 }}
 >
 {col.label}
 </h4>
 <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", lineHeight: 1.8, margin: 0 }}>
 {col.text}
 </p>
 </div>
 ))}
 </div>

 {/* Expanded: Code Snippet */}
 {isExpanded && (
 <div>
 <div
 style={{
 display: "flex",
 justifyContent: "space-between",
 alignItems: "center",
 padding: "0.875rem 1.5rem",
 background: "var(--bg-alt)",
 borderBottom: S.borderLight,
 }}
 >
 <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.65rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" as const, letterSpacing: "0.1em" }}>
 Python · Code Example
 </span>
 <span
 style={{
 padding: "0.15rem 0.5rem",
 border: S.borderLight,
 borderRadius: 4,
 fontFamily: "var(--font-mono)",
 fontSize: "0.6rem",
 color: "var(--text-muted)",
 }}
 >
 {uc.apiEndpoint}
 </span>
 </div>
 <button
 onClick={() => handleCopy(uc.id, uc.codeSnippet)}
 style={{
 padding: "0.375rem 0.875rem",
 border: S.border,
 borderRadius: 6,
 background: copiedId === uc.id ? "var(--text)" : "var(--bg)",
 color: copiedId === uc.id ? "var(--bg)" : "var(--text)",
 fontFamily: "var(--font-mono)",
 fontSize: "0.65rem",
 fontWeight: 700,
 cursor: "pointer",
 transition: "all 0.15s",
 display: "flex",
 alignItems: "center",
 gap: "0.4rem",
 }}
 >
 {copiedId === uc.id ? " Copied!" : "⎘ Copy"}
 </button>
 </div>
 <pre
 style={{
 margin: 0,
 padding: "1.5rem",
 background: "#0f0e0c",
 color: "#e8f542",
 fontFamily: "var(--font-mono)",
 fontSize: "0.8rem",
 lineHeight: 1.8,
 overflowX: "auto",
 borderTop: "none",
 }}
 >
 <code style={{ color: "#a3e635" }}>{uc.codeSnippet}</code>
 </pre>
 <div
 style={{
 padding: "1rem 1.5rem",
 background: "var(--bg-alt)",
 borderTop: S.borderLight,
 display: "flex",
 alignItems: "center",
 gap: "0.75rem",
 }}
 >
 <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
 See full API reference →
 </span>
 <a
 href="/docs"
 style={{
 padding: "0.3rem 0.75rem",
 border: S.border,
 borderRadius: 6,
 background: "var(--text)",
 color: "var(--bg)",
 fontFamily: "var(--font-mono)",
 fontSize: "0.65rem",
 fontWeight: 700,
 textDecoration: "none",
 display: "inline-flex",
 alignItems: "center",
 gap: "0.35rem",
 }}
 >
 API Docs ↗
 </a>
 </div>
 </div>
 )}
 </div>
 );
 })}
 </div>
 </section>

 {/* CTA */}
 <section
 style={{
 background: "var(--primary)",
 borderTop: S.border,
 padding: "4rem 1.5rem",
 }}
 >
 <div style={{ maxWidth: "1152px", margin: "0 auto", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "2rem" }}>
 <div>
 <h2 style={{ fontSize: "clamp(1.5rem, 3vw, 2.25rem)", fontWeight: 900, letterSpacing: "-0.04em", color: "var(--text)", margin: "0 0 0.75rem", lineHeight: 1.1 }}>
 Ready to build your use case?
 </h2>
 <p style={{ fontSize: "0.9rem", color: "rgba(17,16,16,0.65)", margin: 0, maxWidth: "48ch" }}>
 Every pattern above is a working Kyros integration. Start with the quickstart and be production-ready in under 30 minutes.
 </p>
 </div>
 <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
 <a
 href="/docs"
 style={{
 padding: "0.875rem 1.75rem",
 border: S.border,
 borderRadius: "var(--radius)",
 background: "var(--bg-dark)",
 color: "var(--text-on-dark)",
 fontWeight: 800,
 fontSize: "0.875rem",
 textDecoration: "none",
 boxShadow: S.shadow,
 display: "inline-flex",
 alignItems: "center",
 gap: "0.5rem",
 }}
 >
 View API Reference →
 </a>
 <a
 href="/simulation"
 style={{
 padding: "0.875rem 1.75rem",
 border: S.border,
 borderRadius: "var(--radius)",
 background: "var(--bg)",
 color: "var(--text)",
 fontWeight: 800,
 fontSize: "0.875rem",
 textDecoration: "none",
 boxShadow: S.shadow,
 display: "inline-flex",
 alignItems: "center",
 gap: "0.5rem",
 }}
 >
 Try the Sandbox
 </a>
 </div>
 </div>
 </section>
 </div>
 );
}
