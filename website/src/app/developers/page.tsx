"use client";

import React, { useState } from "react";


/* ─── Design tokens ───────────────────────────────── */
const S = {
 border: "2px solid var(--border)",
 borderLight: "1px solid var(--border-light)",
 shadow: "var(--shadow)",
 shadowLg: "var(--shadow-lg)",
};

/* ─── Copy button component ───────────────────────── */
function CopyButton({ text }: { text: string }) {
 const [copied, setCopied] = useState(false);
 const copy = () => {
 navigator.clipboard.writeText(text).then(() => {
 setCopied(true);
 setTimeout(() => setCopied(false), 2000);
 });
 };
 return (
 <button
 onClick={copy}
 title="Copy to clipboard"
 style={{
 padding: "0.3rem 0.7rem",
 border: "1px solid rgba(249,247,242,0.15)",
 borderRadius: 6,
 background: copied ? "rgba(232,245,66,0.15)" : "rgba(249,247,242,0.06)",
 color: copied ? "var(--primary)" : "rgba(249,247,242,0.45)",
 fontFamily: "var(--font-mono)",
 fontSize: "0.6rem",
 fontWeight: 700,
 cursor: "pointer",
 transition: "all 0.15s",
 letterSpacing: "0.04em",
 flexShrink: 0,
 }}
 >
 {copied ? " Copied" : "Copy"}
 </button>
 );
}

/* ─── Code block component ────────────────────────── */
function CodeBlock({ code, lang = "bash", title }: { code: string; lang?: string; title?: string }) {
 return (
 <div style={{ border: S.border, borderRadius: 10, overflow: "hidden", boxShadow: S.shadow }}>
 <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0.625rem 1rem", background: "var(--bg-dark)", borderBottom: "1px solid rgba(249,247,242,0.08)" }}>
 <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
 <div style={{ display: "flex", gap: "0.35rem" }}>
 <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#ef4444", display: "inline-block" }} />
 <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#f59e0b", display: "inline-block" }} />
 <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#22c55e", display: "inline-block" }} />
 </div>
 {title && <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.65rem", color: "rgba(249,247,242,0.4)", letterSpacing: "0.04em" }}>{title}</span>}
 </div>
 <div style={{ display: "flex", alignItems: "center", gap: "0.625rem" }}>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.58rem", color: "rgba(249,247,242,0.25)", textTransform: "uppercase" as const, letterSpacing: "0.08em" }}>{lang}</span>
 <CopyButton text={code} />
 </div>
 </div>
 <pre style={{ margin: 0, padding: "1.25rem 1.5rem", background: "var(--bg-dark)", fontFamily: "var(--font-mono)", fontSize: "0.78rem", lineHeight: 1.9, overflowX: "auto", color: "#a3e635" }}>
 <code style={{ color: "#e2e8f0" }}>{code}</code>
 </pre>
 </div>
 );
}

/* ─── Inline code ─────────────────────────────────── */
function IC({ children }: { children: React.ReactNode }) {
 return (
 <code style={{ fontFamily: "var(--font-mono)", fontSize: "0.82em", background: "var(--bg-alt)", border: "1px solid var(--border-light)", padding: "0.1em 0.4em", borderRadius: 4, color: "var(--text)", fontWeight: 700 }}>
 {children}
 </code>
 );
}

/* ─── Section heading ─────────────────────────────── */
function SectionHeading({ label, title, desc }: { label: string; title: string; desc?: string }) {
 return (
 <div style={{ marginBottom: "1.75rem" }}>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", fontWeight: 800, textTransform: "uppercase" as const, letterSpacing: "0.12em", color: "var(--text-muted)", marginBottom: "0.5rem" }}>
 {label}
 </div>
 <h2 style={{ fontSize: "1.35rem", fontWeight: 900, letterSpacing: "-0.03em", color: "var(--text)", margin: "0 0 0.5rem" }}>
 {title}
 </h2>
 {desc && <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", lineHeight: 1.75, margin: 0, maxWidth: "64ch" }}>{desc}</p>}
 </div>
 );
}

/* ─── Info / Warning callout ──────────────────────── */
function Callout({ type = "info", children }: { type?: "info" | "warning" | "tip"; children: React.ReactNode }) {
 const styles = {
 info: { bg: "rgba(59,130,246,0.08)", border: "1.5px solid rgba(59,130,246,0.3)", icon: "ℹ", color: "#3b82f6" },
 warning: { bg: "rgba(245,158,11,0.08)", border: "1.5px solid rgba(245,158,11,0.3)", icon: "", color: "#f59e0b" },
 tip: { bg: "rgba(232,245,66,0.08)", border: "1.5px solid rgba(232,245,66,0.3)", icon: "i", color: "var(--primary)" },
 }[type];
 return (
 <div style={{ padding: "1rem 1.25rem", borderRadius: 8, background: styles.bg, border: styles.border, display: "flex", gap: "0.875rem", alignItems: "flex-start" }}>
 <span style={{ fontSize: "1rem", flexShrink: 0, marginTop: "0.05rem", color: styles.color }}>{styles.icon}</span>
 <div style={{ fontSize: "0.82rem", color: "var(--text)", lineHeight: 1.75 }}>{children}</div>
 </div>
 );
}

/* ─── Environment variable pill ───────────────────── */
function EnvVar({ name, value, desc }: { name: string; value: string; desc: string }) {
 return (
 <div style={{ padding: "0.875rem 1.125rem", border: S.borderLight, borderLeft: "3px solid var(--primary)", borderRadius: "0 8px 8px 0", background: "var(--bg-alt)", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem 2rem", alignItems: "start" }}>
 <div>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", fontWeight: 800, color: "var(--text)", marginBottom: "0.2rem" }}>{name}</div>
 <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>{desc}</div>
 </div>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", color: "rgba(232,245,66,0.8)", background: "var(--bg-dark)", padding: "0.35rem 0.75rem", borderRadius: 6, overflowX: "auto", whiteSpace: "nowrap" as const }}>
 {value}
 </div>
 </div>
 );
}

/* ─── CLI command row ─────────────────────────────── */
function CliRow({ cmd, params, desc, example }: { cmd: string; params: string; desc: string; example?: string }) {
 const [open, setOpen] = useState(false);
 return (
 <div style={{ borderBottom: S.borderLight }}>
 <div
 onClick={() => setOpen(!open)}
 style={{ display: "grid", gridTemplateColumns: "200px 1fr auto", gap: "1rem", padding: "0.875rem 1.25rem", cursor: "pointer", background: open ? "var(--bg-alt)" : "transparent", transition: "background 0.15s", alignItems: "start" }}
 >
 <code style={{ fontFamily: "var(--font-mono)", fontSize: "0.78rem", fontWeight: 900, color: "var(--text)" }}>{cmd}</code>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.7rem", color: "var(--text-muted)" }}>{params}</span>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.62rem", color: open ? "var(--primary)" : "var(--text-muted)", letterSpacing: "0.04em" }}>{open ? "▲" : "▼"}</span>
 </div>
 {open && (
 <div style={{ padding: "0 1.25rem 1.25rem", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
 <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", margin: 0, lineHeight: 1.7 }}>{desc}</p>
 {example && (
 <CodeBlock code={example} lang="bash" />
 )}
 </div>
 )}
 </div>
 );
}

/* ─── Tabs ────────────────────────────────────────── */
type TabId = "quickstart" | "sdk-python" | "sdk-typescript" | "cli" | "proxy" | "packaging" | "env";

const TABS: { id: TabId; label: string; icon: string }[] = [
 { id: "quickstart", label: "Quick Start", icon: "" },
 { id: "env", label: "Environment", icon: "" },
 { id: "sdk-python", label: "Python SDK", icon: "" },
 { id: "sdk-typescript", label: "TypeScript SDK", icon: "" },
 { id: "cli", label: "Admin CLI", icon: "" },
 { id: "proxy", label: "Proxy Mode", icon: "" },
 { id: "packaging", label: "Packaging", icon: "" },
];

/* ═══════════════════════════════════════════════════
 Main Component
═══════════════════════════════════════════════════ */
export default function DevelopersPage() {
 const [activeTab, setActiveTab] = useState<TabId>("quickstart");

 return (
 <div style={{ background: "var(--bg)", color: "var(--text)", width: "100%", minHeight: "100vh" }}>

 {/* ── Dark Hero Header ── */}
 <section style={{ background: "var(--bg-dark)", color: "var(--text-on-dark)", borderBottom: S.border, padding: "4rem 1.5rem 3rem" }}>
 <div style={{ maxWidth: "1200px", margin: "0 auto" }}>


 <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: "1.5rem" }}>
 <div>
 <div style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.25rem 0.875rem", borderRadius: 9999, border: "1.5px solid rgba(232,245,66,0.35)", background: "rgba(232,245,66,0.08)", fontFamily: "var(--font-mono)", fontSize: "0.62rem", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase" as const, color: "var(--primary)", marginBottom: "1.25rem" }}>
 ◆ Developer Center
 </div>
 <h1 style={{ fontSize: "clamp(2rem, 4vw, 3rem)", fontWeight: 900, letterSpacing: "-0.04em", color: "var(--text-on-dark)", margin: "0 0 0.875rem", lineHeight: 1.05 }}>
 Build with Kyros
 </h1>
 <p style={{ color: "rgba(249,247,242,0.55)", maxWidth: "54ch", fontSize: "0.95rem", lineHeight: 1.8, margin: 0 }}>
 SDK reference, CLI commands, proxy configuration, and packaging guides — everything you need to integrate Kyros into your AI stack.
 </p>
 </div>

 {/* Quick links */}
 <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", minWidth: 200 }}>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.58rem", fontWeight: 800, color: "rgba(249,247,242,0.3)", textTransform: "uppercase" as const, letterSpacing: "0.1em", marginBottom: "0.25rem" }}>Quick Links</div>
 {[
 { href: "https://github.com/Kyros-494/kyros-ai", label: "GitHub Repository ↗" },
 { href: "/docs", label: "API Reference →" },
 { href: "/architecture", label: "System Architecture →" },
 { href: "/contact", label: "Enterprise Inquiry →" },
 ].map((l) => (
 <a key={l.href} href={l.href} style={{ fontSize: "0.78rem", color: "rgba(249,247,242,0.45)", textDecoration: "none", fontFamily: "var(--font-mono)", transition: "color 0.15s", letterSpacing: "0.02em" }}>
 {l.label}
 </a>
 ))}
 </div>
 </div>
 </div>
 </section>

 {/* ── Two-column layout: sidebar + content ── */}
 <div style={{ maxWidth: "1200px", margin: "0 auto", display: "grid", gridTemplateColumns: "220px 1fr", gap: 0, minHeight: "calc(100vh - 320px)" }}>

 {/* ── Sidebar Nav ── */}
 <aside style={{ borderRight: S.border, padding: "2rem 0", position: "sticky", top: 64, alignSelf: "start", maxHeight: "calc(100vh - 64px)", overflowY: "auto" }}>
 <div style={{ padding: "0 1.25rem", marginBottom: "1.25rem" }}>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.58rem", fontWeight: 800, textTransform: "uppercase" as const, letterSpacing: "0.12em", color: "var(--text-muted)" }}>
 Navigation
 </div>
 </div>
 <nav>
 {TABS.map((tab) => (
 <button
 key={tab.id}
 onClick={() => setActiveTab(tab.id)}
 style={{
 width: "100%",
 padding: "0.625rem 1.25rem",
 display: "flex",
 alignItems: "center",
 gap: "0.625rem",
 border: "none",
 borderRight: activeTab === tab.id ? "3px solid var(--text)" : "3px solid transparent",
 background: activeTab === tab.id ? "var(--bg-alt)" : "transparent",
 color: activeTab === tab.id ? "var(--text)" : "var(--text-muted)",
 fontSize: "0.82rem",
 fontWeight: activeTab === tab.id ? 800 : 500,
 cursor: "pointer",
 textAlign: "left" as const,
 transition: "all 0.15s",
 letterSpacing: "-0.01em",
 }}
 >
 <span style={{ fontSize: "0.9rem" }}>{tab.icon}</span>
 {tab.label}
 </button>
 ))}
 </nav>

 {/* Sidebar footer */}
 <div style={{ padding: "1.5rem 1.25rem 0", marginTop: "1.5rem", borderTop: S.borderLight }}>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.58rem", fontWeight: 800, textTransform: "uppercase" as const, letterSpacing: "0.1em", color: "var(--text-muted)", marginBottom: "0.75rem" }}>
 Resources
 </div>
 {[
 { href: "/simulation", label: "Try Sandbox" },
 { href: "/usecases", label: "Use Cases" },
 { href: "/contact", label: "Get Help" },
 ].map((l) => (
 <a key={l.href} href={l.href} style={{ display: "block", fontSize: "0.75rem", color: "var(--text-muted)", textDecoration: "none", padding: "0.35rem 0", fontWeight: 500, transition: "color 0.15s" }}>
 {l.label}
 </a>
 ))}
 </div>
 </aside>

 {/* ── Main Content Panel ── */}
 <main style={{ padding: "2.5rem 2.5rem 5rem" }}>

 {/* ══ QUICK START ══════════════════════════════ */}
 {activeTab === "quickstart" && (
 <div style={{ display: "flex", flexDirection: "column", gap: "2.5rem" }}>
 <SectionHeading
 label="Getting Started"
 title="Up and running in 60 seconds"
 desc="Install the SDK, set your API key, and make your first memory call. No infrastructure required for local development."
 />

 {/* Step 1 */}
 <div>
 <div style={{ display: "flex", alignItems: "center", gap: "0.875rem", marginBottom: "1rem" }}>
 <div style={{ width: 28, height: 28, borderRadius: 8, background: "var(--text)", color: "var(--bg)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-mono)", fontSize: "0.7rem", fontWeight: 900, flexShrink: 0 }}>1</div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, margin: 0, letterSpacing: "-0.02em" }}>Prerequisites</h3>
 </div>
 <div style={{ display: "flex", flexDirection: "column", gap: "0.625rem", marginLeft: "2.75rem" }}>
 {[
 { tool: "Python", version: "3.9+", check: "python --version" },
 { tool: "PostgreSQL", version: "15+ with pgvector", check: "psql --version" },
 { tool: "Redis", version: "7+", check: "redis-server --version" },
 { tool: "Node.js", version: "18+ (for TypeScript SDK)", check: "node --version" },
 ].map((req) => (
 <div key={req.tool} style={{ display: "flex", alignItems: "center", gap: "1rem", padding: "0.625rem 1rem", border: S.borderLight, borderRadius: 8, background: "var(--bg-alt)" }}>
 <span style={{ fontWeight: 800, fontSize: "0.82rem", minWidth: 120 }}>{req.tool}</span>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.7rem", color: "var(--text-muted)", flex: 1 }}>Required: {req.version}</span>
 <code style={{ fontFamily: "var(--font-mono)", fontSize: "0.68rem", color: "rgba(163,230,53,0.8)", background: "var(--bg-dark)", padding: "0.2rem 0.6rem", borderRadius: 4 }}>{req.check}</code>
 </div>
 ))}
 </div>
 </div>

 {/* Step 2 */}
 <div>
 <div style={{ display: "flex", alignItems: "center", gap: "0.875rem", marginBottom: "1rem" }}>
 <div style={{ width: 28, height: 28, borderRadius: 8, background: "var(--text)", color: "var(--bg)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-mono)", fontSize: "0.7rem", fontWeight: 900, flexShrink: 0 }}>2</div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, margin: 0, letterSpacing: "-0.02em" }}>Clone and install</h3>
 </div>
 <div style={{ marginLeft: "2.75rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
 <CodeBlock
 title="terminal"
 lang="bash"
 code={`# Clone the repository
git clone https://github.com/Kyros-494/kyros-ai.git
cd kyros-ai

# Install the Python SDK in editable mode
pip install -e sdks/python

# With all optional integrations (LangChain, CrewAI, etc.)
pip install -e sdks/python[all]`}
 />
 </div>
 </div>

 {/* Step 3 */}
 <div>
 <div style={{ display: "flex", alignItems: "center", gap: "0.875rem", marginBottom: "1rem" }}>
 <div style={{ width: 28, height: 28, borderRadius: 8, background: "var(--text)", color: "var(--bg)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-mono)", fontSize: "0.7rem", fontWeight: 900, flexShrink: 0 }}>3</div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, margin: 0, letterSpacing: "-0.02em" }}>Start the server</h3>
 </div>
 <div style={{ marginLeft: "2.75rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
 <CodeBlock
 title="terminal"
 lang="bash"
 code={`# Start the Kyros API server (defaults to localhost:8000)
cd kyros-ai
uvicorn server.main:app --reload --port 8000

# In a separate terminal, verify it's running
curl http://localhost:8000/health
# → {"status":"ok","version":"1.0.0"}`}
 />
 </div>
 </div>

 {/* Step 4 */}
 <div>
 <div style={{ display: "flex", alignItems: "center", gap: "0.875rem", marginBottom: "1rem" }}>
 <div style={{ width: 28, height: 28, borderRadius: 8, background: "var(--primary)", color: "var(--text)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-mono)", fontSize: "0.7rem", fontWeight: 900, flexShrink: 0 }}>4</div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, margin: 0, letterSpacing: "-0.02em" }}>Your first memory call</h3>
 </div>
 <div style={{ marginLeft: "2.75rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
 <CodeBlock
 title="quickstart.py"
 lang="python"
 code={`import kyros

# Initialize the client
client = kyros.Client(
 api_key="mk_live_default_dev_key_123456",
 base_url="http://localhost:8000"
)

# Store a memory
result = client.ingest(
 content="User's name is Alex. Prefers Python over TypeScript.",
 user_id="user_001",
 type="semantic",
 tags=["user-profile", "preferences"]
)
print(f"Stored → hash: {result.hash[:16]}...")

# Recall relevant memories
memories = client.recall(
 query="What does the user prefer for development?",
 user_id="user_001",
 top_k=3,
 min_weight=0.2
)

for mem in memories:
 print(f"[{mem.retention_weight:.2f}] {mem.content}")`}
 />
 <Callout type="tip">
 The default dev API key is <IC>mk_live_default_dev_key_123456</IC>. For production, generate a unique key using <IC>kyros tenant-create</IC>.
 </Callout>
 </div>
 </div>

 {/* What's next */}
 <div style={{ padding: "1.5rem", border: S.border, borderRadius: 10, background: "var(--bg-alt)", boxShadow: S.shadow }}>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", fontWeight: 800, textTransform: "uppercase" as const, letterSpacing: "0.1em", color: "var(--text-muted)", marginBottom: "1rem" }}>
 What&apos;s next?
 </div>
 <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
 {[
 { tab: "env" as TabId, icon: "️", title: "Configure environment", desc: "Set up your .env and database connections" },
 { tab: "sdk-python" as TabId, icon: "🐍", title: "Full Python SDK reference", desc: "All methods, types, and examples" },
 { tab: "cli" as TabId, icon: "💻", title: "Admin CLI commands", desc: "Manage tenants, audit trails, and memory" },
 { tab: "proxy" as TabId, icon: "🔀", title: "Zero-code proxy mode", desc: "Auto-capture memories from LLM calls" },
 ].map((item) => (
 <button
 key={item.tab}
 onClick={() => setActiveTab(item.tab)}
 style={{ padding: "0.875rem 1rem", border: S.border, borderRadius: 8, background: "var(--bg)", cursor: "pointer", textAlign: "left" as const, display: "flex", gap: "0.75rem", alignItems: "flex-start", transition: "box-shadow 0.15s, transform 0.15s", boxShadow: S.shadow }}
 onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.transform = "translate(-1px,-1px)"; (e.currentTarget as HTMLElement).style.boxShadow = S.shadowLg; }}
 onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.transform = "none"; (e.currentTarget as HTMLElement).style.boxShadow = S.shadow; }}
 >
 <span style={{ fontSize: "1.1rem" }}>{item.icon}</span>
 <div>
 <div style={{ fontSize: "0.82rem", fontWeight: 800, color: "var(--text)", marginBottom: "0.2rem" }}>{item.title} →</div>
 <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{item.desc}</div>
 </div>
 </button>
 ))}
 </div>
 </div>
 </div>
 )}

 {/* ══ ENVIRONMENT CONFIG ════════════════════════ */}
 {activeTab === "env" && (
 <div style={{ display: "flex", flexDirection: "column", gap: "2.5rem" }}>
 <SectionHeading
 label="Configuration"
 title="Environment variables"
 desc="Kyros reads all configuration from environment variables. Create a .env file in the project root or export these in your shell."
 />

 <div>
 <CodeBlock title=".env" lang="bash" code={`# ─── Server Configuration ───────────────────────────
KYROS_HOST=0.0.0.0
KYROS_PORT=8000
KYROS_ENV=development # development | production

# ─── Database ────────────────────────────────────────
DATABASE_URL=postgresql://postgres:password@localhost:5432/kyros_db
REDIS_URL=redis://localhost:6379/0

# ─── Authentication ───────────────────────────────────
KYROS_SECRET_KEY=your-secret-key-min-32-chars
KYROS_DEFAULT_API_KEY=mk_live_default_dev_key_123456

# ─── Embedding Provider ───────────────────────────────
OPENAI_API_KEY=sk-... # Required for OpenAI embeddings
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536

# ─── Memory Decay Constants ───────────────────────────
SEMANTIC_DECAY_LAMBDA=0.003 # Half-life ~231 days
EPISODIC_DECAY_LAMBDA=0.04 # Half-life ~17 days
PROCEDURAL_DECAY_LAMBDA=0.001 # Half-life ~693 days

# ─── Optional: Dashboard ──────────────────────────────
DASHBOARD_PORT=8080
DASHBOARD_SECRET=dashboard-secret`} />
 </div>

 <div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 1rem" }}>Variable reference</h3>
 <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
 <EnvVar name="DATABASE_URL" value="postgresql://user:pass@host:5432/db" desc="Full PostgreSQL connection string. Must point to a database with pgvector extension installed." />
 <EnvVar name="REDIS_URL" value="redis://localhost:6379/0" desc="Redis connection string. Used for hot-key caching of embedding indices and session data." />
 <EnvVar name="KYROS_SECRET_KEY" value="random-32+-char-string" desc="Used to sign JWTs. Generate with: python -c 'import secrets; print(secrets.token_hex(32))'" />
 <EnvVar name="OPENAI_API_KEY" value="sk-..." desc="OpenAI API key for embedding generation. Swap for a local embedding server URL if running on-premise." />
 <EnvVar name="SEMANTIC_DECAY_LAMBDA" value="0.003" desc="Ebbinghaus decay constant for semantic memories. Lower = slower forgetting. Default half-life ≈ 231 days." />
 <EnvVar name="EPISODIC_DECAY_LAMBDA" value="0.04" desc="Decay constant for episodic (event-based) memories. Default half-life ≈ 17 days." />
 </div>
 </div>

 <Callout type="info">
 Run <IC>kyros status</IC> after configuring your environment to verify all connections are healthy before starting the server.
 </Callout>

 <div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 1rem" }}>Database setup</h3>
 <CodeBlock title="terminal" lang="bash" code={`# Install pgvector extension (run in psql as superuser)
CREATE EXTENSION IF NOT EXISTS vector;

# Run Kyros migrations
cd kyros-ai
alembic upgrade head

# Verify tables were created
psql $DATABASE_URL -c "\\dt"
# → memories, tenants, merkle_nodes, api_keys, ...`} />
 </div>
 </div>
 )}

 {/* ══ PYTHON SDK ════════════════════════════════ */}
 {activeTab === "sdk-python" && (
 <div style={{ display: "flex", flexDirection: "column", gap: "2.5rem" }}>
 <SectionHeading
 label="Python SDK"
 title="kyros-py reference"
 desc="The official Python SDK. Supports Python 3.9+ with optional integrations for LangChain, CrewAI, AutoGen, and more."
 />

 <div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 0.875rem" }}>Installation</h3>
 <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
 <CodeBlock lang="bash" code={`# Local development (from repo root)
pip install -e sdks/python

# With optional integrations
pip install -e sdks/python[langchain] # LangChain tools
pip install -e sdks/python[crewai] # CrewAI agents
pip install -e sdks/python[all] # Everything`} />
 </div>
 </div>

 <div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 0.875rem" }}>Client initialization</h3>
 <CodeBlock title="client.py" lang="python" code={`import kyros

# Basic initialization
client = kyros.Client(
 api_key="mk_live_...", # Your API key
 base_url="http://localhost:8000", # Server URL
 timeout=30, # Request timeout in seconds
 max_retries=3, # Retry on transient failures
)

# With custom headers (e.g., for reverse proxy)
client = kyros.Client(
 api_key="mk_live_...",
 base_url="https://your-kyros-instance.com",
 extra_headers={"X-Tenant-ID": "org_xyz"}
)`} />
 </div>

 <div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 0.875rem" }}>client.ingest() — Store a memory</h3>
 <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
 <CodeBlock title="ingest.py" lang="python" code={`result = client.ingest(
 content="User's preferred language is Python.", # Required: the memory text
 user_id="user_001", # Required: user/agent scoping
 type="semantic", # semantic | episodic | procedural
 tags=["preferences", "language"], # Optional: filter labels
 valid_from=None, # Optional: bitemporal valid start
 valid_until=None, # Optional: bitemporal valid end
 metadata={"source": "chat_turn_14"} # Optional: arbitrary JSON
)

print(result.id) # "mem_a1b2c3d4..."
print(result.hash) # "sha256_4af1b2c3..."
print(result.merkle_root) # "sha256_root_e9f3..."
print(result.retention_weight) # 1.0 (initial)`} />
 <Callout type="info">
 Memory <IC>type</IC> determines the Ebbinghaus decay constant. <IC>semantic</IC> memories decay slowest (λ=0.003), <IC>episodic</IC> faster (λ=0.04), and <IC>procedural</IC> slowest of all (λ=0.001).
 </Callout>
 </div>
 </div>

 <div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 0.875rem" }}>client.recall() — Retrieve memories</h3>
 <CodeBlock title="recall.py" lang="python" code={`memories = client.recall(
 query="What programming language does the user prefer?", # Natural language query
 user_id="user_001", # Required: user scope
 top_k=5, # Max results to return
 min_weight=0.2, # Filter out faded memories
 type_filter=["semantic", "episodic"], # Optional: filter by type
 tag_filter=["preferences"], # Optional: filter by tags
 as_of=None, # Optional: bitemporal AS OF
)

for mem in memories:
 print(f"[{mem.retention_weight:.2f}] [{mem.type}] {mem.content}")
 print(f" Hash: {mem.hash[:20]}...")
 print(f" Stored: {mem.recorded_at}")`} />
 </div>

 <div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 0.875rem" }}>client.audit() — Verify Merkle integrity</h3>
 <CodeBlock title="audit.py" lang="python" code={`# Verify the cryptographic integrity of a specific memory
proof = client.audit(memory_id="mem_a1b2c3d4")

print(proof.is_valid) # True / False
print(proof.root_hash) # Current Merkle root
print(proof.leaf_hash) # SHA-256 of the specific memory
print(proof.proof_path) # List of sibling hashes for verification
print(proof.depth) # Depth of leaf in Merkle tree

# Verify all memories for a user
report = client.audit_all(user_id="user_001")
print(f"Total: {report.total}, Valid: {report.valid}, Corrupt: {report.corrupt}")`} />
 </div>

 <div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 0.875rem" }}>client.delete() — Remove a memory</h3>
 <CodeBlock title="delete.py" lang="python" code={`# Soft delete (retains hash in Merkle tree, marks as deleted)
client.delete(memory_id="mem_a1b2c3d4")

# Hard delete — removes record entirely (Merkle tree updated)
# Note: root hash will change. External root snapshots will not match.
client.delete(memory_id="mem_a1b2c3d4", hard=True)

# Delete all memories for a user
client.delete_all(user_id="user_001")`} />
 </div>

 <div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 0.875rem" }}>LangChain integration</h3>
 <CodeBlock title="langchain_memory.py" lang="python" code={`from langchain.memory import ConversationBufferMemory
from kyros.integrations.langchain import KyrosMemory

# Drop-in replacement for LangChain's memory
memory = KyrosMemory(
 api_key="mk_live_...",
 user_id="user_001",
 base_url="http://localhost:8000",
 top_k=5,
 min_weight=0.15
)

# Use with any LangChain chain
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(model="gpt-4")
chain = ConversationChain(llm=llm, memory=memory)

response = chain.predict(input="My name is Alex")`} />
 </div>
 </div>
 )}

 {/* ══ TYPESCRIPT SDK ════════════════════════════ */}
 {activeTab === "sdk-typescript" && (
 <div style={{ display: "flex", flexDirection: "column", gap: "2.5rem" }}>
 <SectionHeading
 label="TypeScript SDK"
 title="@kyros.494/sdk reference"
 desc="The official TypeScript/JavaScript SDK. Fully typed with TypeScript 5+. Works in Node.js, Deno, Bun, and browser environments."
 />

 <div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 0.875rem" }}>Installation</h3>
 <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
 <CodeBlock lang="bash" code={`# Local development — add path dependency to package.json
npm install ../kyros-ai/sdks/typescript

# Or add directly to package.json
{
 "dependencies": {
 "@kyros.494/sdk": "file:../kyros-ai/sdks/typescript"
 }
}`} />
 </div>
 </div>

 <div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 0.875rem" }}>Client initialization</h3>
 <CodeBlock title="client.ts" lang="typescript" code={`import { KyrosClient } from "@kyros.494/sdk";

const client = new KyrosClient({
 apiKey: "mk_live_...",
 baseUrl: "http://localhost:8000", // Default
 timeout: 30_000, // 30s timeout
 maxRetries: 3,
});`} />
 </div>

 <div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 0.875rem" }}>Ingest and recall</h3>
 <CodeBlock title="memory.ts" lang="typescript" code={`// Store a memory
const result = await client.ingest({
 content: "User prefers TypeScript and React.",
 userId: "user_001",
 type: "semantic", // "semantic" | "episodic" | "procedural"
 tags: ["stack", "preferences"],
});

console.log(result.id); // "mem_a1b2c3d4..."
console.log(result.hash); // "sha256_4af1b2c3..."
console.log(result.retentionWeight); // 1.0

// Recall memories
const memories = await client.recall({
 query: "What does the user prefer for frontend?",
 userId: "user_001",
 topK: 5,
 minWeight: 0.2,
});

memories.forEach((mem) => {
 console.log(\`[\${mem.retentionWeight.toFixed(2)}] \${mem.content}\`);
});`} />
 </div>

 <div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 0.875rem" }}>Type definitions</h3>
 <CodeBlock title="types.ts" lang="typescript" code={`// Memory object returned by ingest() and recall()
interface Memory {
 id: string;
 content: string;
 userId: string;
 type: "semantic" | "episodic" | "procedural";
 hash: string; // SHA-256 content hash
 merkleRoot: string; // Root hash after append
 retentionWeight: number; // 0.0 – 1.0 (Ebbinghaus)
 embedding: number[]; // 1536-dim vector
 tags: string[];
 metadata: Record<string, unknown>;
 validFrom: string; // ISO 8601
 recordedAt: string; // ISO 8601
}

// Audit proof
interface AuditProof {
 isValid: boolean;
 rootHash: string;
 leafHash: string;
 proofPath: string[];
 depth: number;
}`} />
 </div>

 <div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 0.875rem" }}>Vercel AI SDK integration</h3>
 <CodeBlock title="route.ts" lang="typescript" code={`// app/api/chat/route.ts — Next.js App Router
import { KyrosClient } from "@kyros.494/sdk";
import { openai } from "@ai-sdk/openai";
import { streamText } from "ai";

const kyros = new KyrosClient({ apiKey: process.env.KYROS_API_KEY! });

export async function POST(req: Request) {
 const { messages, userId } = await req.json();
 const lastMessage = messages.at(-1)?.content ?? "";

 // 1. Recall relevant memories
 const memories = await kyros.recall({
 query: lastMessage,
 userId,
 topK: 4,
 minWeight: 0.15,
 });

 const context = memories.map((m) => m.content).join("\\n");

 // 2. Stream response with context injected
 const result = streamText({
 model: openai("gpt-4o"),
 system: \`You have access to this context about the user:\\n\${context}\`,
 messages,
 });

 // 3. Store the user's message as a new memory
 await kyros.ingest({
 content: lastMessage,
 userId,
 type: "episodic",
 tags: ["chat"],
 });

 return result.toDataStreamResponse();
}`} />
 </div>
 </div>
 )}

 {/* ══ ADMIN CLI ═════════════════════════════════ */}
 {activeTab === "cli" && (
 <div style={{ display: "flex", flexDirection: "column", gap: "2.5rem" }}>
 <SectionHeading
 label="Admin CLI"
 title="kyros command reference"
 desc="The Python SDK installs a kyros CLI binary for server management, memory administration, and audit operations."
 />

 <Callout type="info">
 Ensure <IC>KYROS_API_KEY</IC> and <IC>KYROS_BASE_URL</IC> are set in your environment before running CLI commands. These are read automatically from your <IC>.env</IC> file.
 </Callout>

 <div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 0.875rem" }}>Commands</h3>
 <div style={{ border: S.border, borderRadius: 10, overflow: "hidden", boxShadow: S.shadow }}>
 <div style={{ display: "grid", gridTemplateColumns: "200px 1fr auto", gap: "1rem", padding: "0.625rem 1.25rem", background: "var(--bg-alt)", borderBottom: S.border }}>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", fontWeight: 800, textTransform: "uppercase" as const, letterSpacing: "0.1em", color: "var(--text-muted)" }}>Command</span>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", fontWeight: 800, textTransform: "uppercase" as const, letterSpacing: "0.1em", color: "var(--text-muted)" }}>Flags / Parameters</span>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", fontWeight: 800, textTransform: "uppercase" as const, letterSpacing: "0.1em", color: "var(--text-muted)" }}></span>
 </div>
 {[
 {
 cmd: "kyros status",
 params: "[--verbose]",
 desc: "Checks health of all system components: API server, PostgreSQL connection, pgvector extension, Redis connection, and embedding provider. Use --verbose for detailed diagnostics.",
 example: `kyros status
# API Server → http://localhost:8000 (v1.0.0)
# PostgreSQL → kyros_db (15.4) + pgvector 0.7.0
# Redis → localhost:6379 (7.2.4) 
# Embedding API → OpenAI text-embedding-3-small`
 },
 {
 cmd: "kyros remember",
 params: "--agent <id> --content <text> [--type semantic|episodic|procedural] [--tags tag1,tag2]",
 desc: "Manually ingest a memory record for a given agent or user ID. Useful for seeding initial context or testing memory ingestion without writing code.",
 example: `kyros remember \\
 --agent "agent_001" \\
 --content "User is an expert Python developer" \\
 --type semantic \\
 --tags "expertise,python"
# → Stored mem_4a2b... (hash: sha256_9f3e...) weight: 1.00`
 },
 {
 cmd: "kyros recall",
 params: "--agent <id> --query <text> [--top-k 5] [--min-weight 0.2]",
 desc: "Recall semantically similar memories for a given agent. Runs an HNSW ANN search and returns results ranked by cosine_similarity × retention_weight.",
 example: `kyros recall \\
 --agent "agent_001" \\
 --query "What is the user's technical background?" \\
 --top-k 3
# [1.00] User is an expert Python developer
# [0.82] User has 5 years of backend experience
# [0.74] User prefers FastAPI over Django`
 },
 {
 cmd: "kyros audit",
 params: "--agent <id> [--memory-id <id>] [--full]",
 desc: "Verify the cryptographic integrity of the Merkle audit tree. Checks that all leaf hashes are consistent with the current root. Use --memory-id to audit a specific record.",
 example: `kyros audit --agent "agent_001"
# Merkle Audit Report
# Total memories: 47
# Root hash: sha256_root_8f4a...
# All 47 leaf hashes verified
# Tree depth: 6 levels`
 },
 {
 cmd: "kyros tenant-create",
 params: "--name <org-name> --email <email> [--plan free|pro|enterprise]",
 desc: "Register a new tenant organization in the system. Returns an API key scoped to that tenant. Row-Level Security in PostgreSQL automatically isolates this tenant's data.",
 example: `kyros tenant-create \\
 --name "Acme Corp" \\
 --email "dev@acme.com" \\
 --plan pro
# Tenant created: org_acme_7d8e...
# API Key: mk_live_acme_9f3a... (save this — shown once)`
 },
 {
 cmd: "kyros decay --run",
 params: "[--agent <id>] [--dry-run]",
 desc: "Manually trigger the Ebbinghaus decay recalculation for all memories. In production this runs on a cron schedule. Use --dry-run to preview changes without committing.",
 example: `kyros decay --run --dry-run
# Decay simulation (dry run — no changes committed)
# 3 memories would drop below min_weight (0.05)
# 12 memories updated
# Run without --dry-run to apply`
 },
 ].map((row) => (
 <CliRow key={row.cmd} cmd={row.cmd} params={row.params} desc={row.desc} example={row.example} />
 ))}
 </div>
 </div>
 </div>
 )}

 {/* ══ PROXY MODE ════════════════════════════════ */}
 {activeTab === "proxy" && (
 <div style={{ display: "flex", flexDirection: "column", gap: "2.5rem" }}>
 <SectionHeading
 label="Proxy Mode"
 title="Zero-code API interception"
 desc="Route your existing LLM library traffic through the Kyros proxy. Memory injection and capture happens automatically — no SDK calls needed in your application code."
 />

 {/* How it works */}
 <div style={{ padding: "1.5rem", border: S.border, borderRadius: 10, background: "var(--bg-alt)", boxShadow: S.shadow }}>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", fontWeight: 800, textTransform: "uppercase" as const, letterSpacing: "0.1em", color: "var(--text-muted)", marginBottom: "1.25rem" }}>
 How proxy mode works
 </div>
 <div style={{ display: "flex", flexDirection: "column", gap: "0.875rem" }}>
 {[
 { step: "1", icon: "→", label: "Your app calls OpenAI/Anthropic as normal", detail: "No code changes required. Just change the base_url to the Kyros proxy." },
 { step: "2", icon: "🔍", label: "Proxy intercepts the request", detail: "Extracts the user_id from the request header, queries Kyros for relevant memories." },
 { step: "3", icon: "💉", label: "Context injected into system message", detail: "Recalled memories are appended to your system prompt automatically before forwarding." },
 { step: "4", icon: "📤", label: "Enriched request forwarded to LLM", detail: "The real OpenAI/Anthropic endpoint receives the request with full memory context." },
 { step: "5", icon: "🔐", label: "Response captured and stored", detail: "The conversation turn is hashed and stored as a new episodic memory. Merkle tree updated." },
 ].map((item) => (
 <div key={item.step} style={{ display: "flex", gap: "1rem", alignItems: "flex-start" }}>
 <div style={{ width: 26, height: 26, borderRadius: 6, background: "var(--text)", color: "var(--bg)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-mono)", fontSize: "0.65rem", fontWeight: 900, flexShrink: 0 }}>{item.step}</div>
 <div>
 <div style={{ fontSize: "0.85rem", fontWeight: 800, color: "var(--text)", marginBottom: "0.2rem" }}>{item.label}</div>
 <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{item.detail}</div>
 </div>
 </div>
 ))}
 </div>
 </div>

 <div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 0.875rem" }}>OpenAI client — redirect to proxy</h3>
 <CodeBlock title="openai_proxy.py" lang="python" code={`import openai

# The ONLY change needed — point base_url to Kyros proxy
client = openai.OpenAI(
 api_key="your-openai-key",
 base_url="http://localhost:8000/v1/proxy", # ← Kyros proxy URL
)

# Add X-Kyros-User-ID header to scope memories per user
response = client.chat.completions.create(
 model="gpt-4",
 messages=[{"role": "user", "content": "What do I prefer for coding?"}],
 extra_headers={"X-Kyros-User-ID": "user_001"} # ← Required
)

print(response.choices[0].message.content)
# GPT-4 now has full access to user_001's memories!`} />
 </div>

 <div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 0.875rem" }}>LangChain — redirect to proxy</h3>
 <CodeBlock title="langchain_proxy.py" lang="python" code={`from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

# Point LangChain's OpenAI wrapper to the proxy
llm = ChatOpenAI(
 openai_api_key="your-openai-key",
 openai_api_base="http://localhost:8000/v1/proxy",
 model_name="gpt-4",
 model_kwargs={"extra_headers": {"X-Kyros-User-ID": "user_001"}}
)

response = llm([HumanMessage(content="Remind me of my preferences")])
print(response.content)`} />
 </div>

 <div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 0.875rem" }}>Proxy configuration options</h3>
 <CodeBlock title=".env" lang="bash" code={`# Proxy server settings
PROXY_HOST=0.0.0.0
PROXY_PORT=8000
PROXY_TARGET_URL=https://api.openai.com # Forward to this LLM provider

# Memory injection settings
PROXY_TOP_K=5 # How many memories to inject
PROXY_MIN_WEIGHT=0.15 # Min retention weight threshold
PROXY_MAX_CONTEXT_CHARS=2000 # Max chars of injected context

# Memory capture settings 
PROXY_CAPTURE_TURNS=true # Auto-capture conversation turns
PROXY_CAPTURE_TYPE=episodic # Memory type for auto-captures`} />
 </div>

 <Callout type="warning">
 Proxy mode captures and stores every conversation turn automatically. Make sure your users have consented to memory storage before enabling this feature in production.
 </Callout>
 </div>
 )}

 {/* ══ PACKAGING ════════════════════════════════ */}
 {activeTab === "packaging" && (
 <div style={{ display: "flex", flexDirection: "column", gap: "2.5rem" }}>
 <SectionHeading
 label="Publishing"
 title="Packaging & publication"
 desc="Instructions for building and publishing the Kyros SDKs to PyPI and npm for production distribution."
 />

 <div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 0.875rem" }}>Python SDK → PyPI</h3>
 <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
 <CodeBlock title="terminal" lang="bash" code={`# Navigate to the Python SDK directory
cd sdks/python

# Install build tools if not already installed
pip install build twine

# Build the distribution package
python -m build
# Creates: dist/kyros_memory-x.x.x.tar.gz
# dist/kyros_memory-x.x.x-py3-none-any.whl

# Upload to PyPI (requires PyPI credentials)
python -m twine upload dist/*

# Or upload to TestPyPI first
python -m twine upload --repository testpypi dist/*`} />
 <Callout type="info">
 Bump the version in <IC>sdks/python/pyproject.toml</IC> before building. Follow semantic versioning: <IC>MAJOR.MINOR.PATCH</IC>.
 </Callout>
 </div>
 </div>

 <div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 0.875rem" }}>TypeScript SDK → npm</h3>
 <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
 <CodeBlock title="terminal" lang="bash" code={`# Navigate to the TypeScript SDK directory
cd sdks/typescript

# Install dependencies
npm install

# Build the TypeScript to JavaScript
npm run build
# Creates: dist/ with .js, .d.ts, and .js.map files

# Run tests before publishing
npm test

# Publish to npm (requires npm login)
npm login
npm publish --access public
# Package name: @kyros.494/sdk`} />
 </div>
 </div>

 <div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 0.875rem" }}>Docker deployment</h3>
 <CodeBlock title="terminal" lang="bash" code={`# Build the Docker image
docker build -t kyros-ai:latest .

# Run with environment variables
docker run -d \\
 --name kyros-api \\
 -p 8000:8000 \\
 -e DATABASE_URL="postgresql://..." \\
 -e REDIS_URL="redis://..." \\
 -e OPENAI_API_KEY="sk-..." \\
 -e KYROS_SECRET_KEY="..." \\
 kyros-ai:latest

# Or with docker-compose
docker compose up -d`} />
 </div>

 <div>
 <h3 style={{ fontSize: "1rem", fontWeight: 900, letterSpacing: "-0.02em", margin: "0 0 0.875rem" }}>docker-compose.yml</h3>
 <CodeBlock title="docker-compose.yml" lang="yaml" code={`version: "3.9"

services:
 api:
 build: .
 ports:
 - "8000:8000"
 environment:
 DATABASE_URL: postgresql://postgres:password@db:5432/kyros_db
 REDIS_URL: redis://cache:6379/0
 OPENAI_API_KEY: \${OPENAI_API_KEY}
 KYROS_SECRET_KEY: \${KYROS_SECRET_KEY}
 depends_on:
 - db
 - cache

 db:
 image: pgvector/pgvector:pg15
 environment:
 POSTGRES_DB: kyros_db
 POSTGRES_PASSWORD: password
 volumes:
 - pgdata:/var/lib/postgresql/data

 cache:
 image: redis:7-alpine
 volumes:
 - redisdata:/data

volumes:
 pgdata:
 redisdata:`} />
 </div>
 </div>
 )}

 </main>
 </div>
 </div>
 );
}
