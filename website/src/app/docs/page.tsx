"use client";

import React, { useState, useMemo } from "react";
import openapiData from "./openapi.json";

type ActiveTab = "guides" | "usecases" | "reference";
type GuideId = "intro" | "authentication" | "errors" | "quickstart" | "python-sdk" | "typescript-sdk" | "self-hosting" | "llm-integrations";
type UsecaseId = "coding-companion" | "personalized-crm" | "customer-support" | "travel-planner";

interface Guide {
 id: GuideId;
 title: string;
 category: string;
}

interface UsecaseDoc {
 id: UsecaseId;
 title: string;
 category: string;
}

interface OpenApiEndpoint {
 tags?: string[];
 summary?: string;
 description?: string;
 parameters?: Array<{
 name: string;
 schema?: { type?: string; default?: unknown };
 required?: boolean;
 description?: string;
 }>;
 requestBody?: {
 content?: Record<string, {
 schema?: {
 $ref?: string;
 };
 }>;
 };
 responses?: Record<string, {
 description?: string;
 }>;
}

interface OpenApiSchema {
 properties?: Record<string, {
 type?: string;
 default?: unknown;
 description?: string;
 $ref?: string;
 }>;
 required?: string[];
}

interface OpenApiSpec {
 paths?: Record<string, Record<string, OpenApiEndpoint>>;
 components?: {
 schemas?: Record<string, OpenApiSchema>;
 };
}

const openapi = openapiData as unknown as OpenApiSpec;

// Static Guides
const guides: Guide[] = [
 { id: "intro", title: "Introduction", category: "Getting Started" },
 { id: "authentication", title: "Authentication", category: "Getting Started" },
 { id: "errors", title: "Errors", category: "Getting Started" },
 { id: "quickstart", title: "Quickstart Guide", category: "Getting Started" },
 { id: "python-sdk", title: "Python SDK Guide", category: "SDKs" },
 { id: "typescript-sdk", title: "TypeScript SDK Guide", category: "SDKs" },
 { id: "self-hosting", title: "Self-Hosting", category: "Server" },
 { id: "llm-integrations", title: "LLM Integrations", category: "Server" },
];

// Static Usecase Docs
const usecaseDocs: UsecaseDoc[] = [
 { id: "coding-companion", title: "Personal Coding Companion", category: "Developer Tools" },
 { id: "personalized-crm", title: "Personalized CRM Assistant", category: "Enterprise CRM" },
 { id: "customer-support", title: "Customer Support Agent", category: "Customer Success" },
 { id: "travel-planner", title: "Travel Planner Agent", category: "Consumer Apps" },
];

// Helper to dereference schemas
const getSchemaDetails = (ref: string): OpenApiSchema | null => {
 if (!ref || !ref.startsWith("#/components/schemas/")) return null;
 const schemaName = ref.replace("#/components/schemas/", "");
 return openapi.components?.schemas?.[schemaName] || null;
};

const S = {
 border: "2px solid var(--border)",
 borderLight: "1px solid var(--border-light)",
 shadow: "var(--shadow)",
 shadowLg: "var(--shadow-lg)",
};

// Custom Link styling
const linkStyle = {
 color: "var(--text)",
 fontWeight: 800,
 textDecoration: "underline",
 textDecorationColor: "var(--primary)",
 textDecorationThickness: "2px",
};

// Reusable CodeBlock component with Copy button
function CodeBlock({ code, language }: { code: string; language?: string }) {
 const [copied, setCopied] = useState(false);

 const handleCopy = () => {
 navigator.clipboard.writeText(code);
 setCopied(true);
 setTimeout(() => setCopied(false), 2000);
 };

 return (
 <div style={{ position: "relative", border: S.border, borderRadius: 8, background: "var(--bg-dark)", overflow: "hidden", marginTop: "0.5rem" }}>
 {language && (
 <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "#161513", borderBottom: S.border, padding: "0.5rem 0.8rem", fontSize: "0.6rem", fontFamily: "var(--font-mono)", color: "#8a847e" }}>
 <span>{language.toUpperCase()}</span>
 <button 
 onClick={handleCopy}
 style={{ background: "transparent", border: "none", color: copied ? "var(--primary)" : "#8a847e", fontWeight: "bold", cursor: "pointer", outline: "none", fontSize: "0.6rem" }}
 >
 {copied ? "COPIED!" : "COPY"}
 </button>
 </div>
 )}
 {!language && (
 <button 
 onClick={handleCopy}
 style={{ position: "absolute", right: "0.5rem", top: "0.5rem", background: "var(--border)", border: "none", color: copied ? "var(--primary)" : "var(--bg)", fontWeight: "bold", fontSize: "0.65rem", padding: "0.25rem 0.5rem", borderRadius: 4, cursor: "pointer", zIndex: 2 }}
 >
 {copied ? "COPIED" : "COPY"}
 </button>
 )}
 <pre style={{ margin: 0, padding: "1.25rem", color: "#e6e1da", fontSize: "0.76rem", overflowX: "auto", fontFamily: "var(--font-mono)" }}>
 <code style={{ display: "block" }}>{code}</code>
 </pre>
 </div>
 );
}

// Rich Mock Responses for Endpoints
const mockResponses: Record<string, string> = {
 "/v1/remember": `{
 "status": "success",
 "memory_id": "mem_8f9a2b5c-4d32-47ef-83e9-7c1568c0de5d",
 "episodic_created": true,
 "semantic_facts_extracted": 3,
 "integrity_hash": "a4f89d3c52e1f40aa991bf28a7e0c70fa4f89d3c52e1f40aa991bf28a7e0c70f",
 "timestamp": "2026-06-18T01:10:00Z"
}`,
 "/v1/recall": `{
 "query": "Where does the user live?",
 "results": [
 {
 "id": "mem_3d8f1a2c-9a1b-4d4f-b643-8f921ea84ef3",
 "type": "episodic",
 "content": "User resides in Amsterdam.",
 "score": 0.942,
 "decay_weight": 0.985,
 "timestamp": "2026-06-18T00:30:00Z"
 }
 ]
}`,
 "/v1/memory/episodic/remember": `{
 "status": "success",
 "memory_id": "mem_9a7b2c5d-2b4a-4281-9fe2-019cf3994bb5",
 "hash": "b2f69a3c52e1f40aa991bf28a7e0c70fb2f69a3c52e1f40aa991bf28a7e0c70f"
}`,
 "/v1/memory/episodic/recall": `{
 "results": [
 {
 "id": "mem_01c27e3d-8ab6-4c4c-90ef-72f10689b9a1",
 "content": "User resides in Amsterdam.",
 "score": 0.897,
 "timestamp": "2026-06-17T18:30:00Z"
 }
 ]
}`,
 "/v1/memory/episodic/{memory_id}": ``,
 "/v1/memory/semantic/facts": `{
 "fact_id": "fact_0a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
 "status": "updated",
 "confidence": 0.95,
 "belief_updated": true,
 "nodes_modified": ["user", "package_preference"]
}`,
 "/v1/memory/semantic/query": `{
 "results": [
 {
 "subject": "user",
 "predicate": "prefers",
 "value": "Python",
 "confidence": 0.98,
 "last_updated": "2026-06-18T01:05:00Z"
 }
 ]
}`,
 "/v1/memory/semantic/graph/{agent_id}": `{
 "agent_id": "agent-123",
 "nodes": [
 { "id": "user", "label": "User", "type": "entity" },
 { "id": "python", "label": "Python", "type": "attribute" }
 ],
 "edges": [
 {
 "source": "user",
 "target": "python",
 "relationship": "prefers",
 "confidence": 0.95,
 "last_updated": "2026-06-18T01:05:00Z"
 }
 ]
}`,
 "/v1/memory/procedural/store": `{
 "status": "success",
 "procedure_id": "proc_1c2d3e4f-5a6b-7c8d-9e0f-1a2b3c4d5e6f",
 "task_type": "billing"
}`,
 "/v1/memory/procedural/match": `{
 "best_match": {
 "procedure_id": "proc_1c2d3e4f-5a6b-7c8d-9e0f-1a2b3c4d5e6f",
 "name": "Process Refund",
 "steps": [
 { "action": "check_invoice", "params": { "required": true } },
 { "action": "gateway_refund", "params": { "gateway": "stripe" } }
 ],
 "success_rate": 0.96,
 "confidence_score": 0.88
 }
}`,
 "/v1/memory/procedural/outcome": `{
 "status": "recorded",
 "procedure_id": "proc_1c2d3e4f-5a6b-7c8d-9e0f-1a2b3c4d5e6f",
 "new_success_rate": 0.962
}`,
 "/v1/search/unified": `{
 "query": "billing credentials",
 "episodic_results": [
 { "id": "mem_123", "content": "Requested payment details for billing", "score": 0.78 }
 ],
 "semantic_results": [
 { "subject": "user", "predicate": "uses_gateway", "value": "Stripe", "confidence": 0.95 }
 ],
 "procedural_results": [
 { "id": "proc_1c2d3e4f", "name": "Process Refund", "score": 0.91 }
 ]
}`,
 "/v1/admin/summarise/{agent_id}": `{
 "agent_id": "agent-123",
 "total_memories": 412,
 "semantic_facts": 34,
 "active_procedural_flows": 5,
 "compressed_summary": "User is a software developer specializing in Python/TS backend development. Operates out of Amsterdam. Frequently handles API integrations with Stripe and PostgreSQL databases. Prefers dark themes and tab indentations."
}`,
 "/v1/admin/export/{agent_id}": `{
 "agent_id": "agent-123",
 "exported_at": "2026-06-18T01:10:00Z",
 "memories": [
 { "type": "episodic", "content": "User prefers Python backend.", "timestamp": "2026-06-17T18:30:00Z" }
 ]
}`,
 "/v1/admin/staleness-report/{agent_id}": `{
 "agent_id": "agent-123",
 "calculated_at": "2026-06-18T01:10:00Z",
 "stale_facts_count": 4,
 "suggested_cleanup_ids": ["fact_98a7b2c1", "fact_12c3d4e5"]
}`,
 "/v1/admin/decay-rates": `{
 "trip_search": 0.25,
 "coding_sessions": 0.05,
 "default": 0.1
}`,
 "/v1/admin/memory/{memory_id}/proof": `{
 "memory_id": "mem_8f9a2b5c-4d32-47ef-83e9-7c1568c0de5d",
 "root_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
 "proof": [
 { "position": "left", "hash": "c0fa4f89d3c52e1f40aa991bf28a7e0c70f2f69a3c52e1f40aa991b" }
 ]
}`
};

export default function DocsPage() {
 const [activeTab, setActiveTab] = useState<ActiveTab>("guides");
 const [selectedGuide, setSelectedGuide] = useState<GuideId>("intro");
 const [selectedUsecase, setSelectedUsecase] = useState<UsecaseId>("coding-companion");
 const [selectedEndpoint, setSelectedEndpoint] = useState<string>("/v1/remember");
 const [searchQuery, setSearchQuery] = useState("");
 const [activeSnippetTab, setActiveSnippetTab] = useState<"curl" | "python" | "typescript">("curl");
 const [snippetsCopied, setSnippetsCopied] = useState(false);

 // Group endpoints by tags
 const endpoints = useMemo(() => {
 const list: { path: string; method: string; tag: string; summary: string; spec: OpenApiEndpoint }[] = [];
 const paths = openapi.paths;
 if (!paths) return list;

 Object.keys(paths).forEach((path) => {
 Object.keys(paths[path]).forEach((method) => {
 const spec = paths[path][method];
 const tag = spec.tags && spec.tags[0] ? spec.tags[0] : "General";
 list.push({
 path,
 method: method.toUpperCase(),
 tag,
 summary: spec.summary || path,
 spec,
 });
 });
 });
 return list;
 }, []);

 // Filtered lists based on search
 const filteredGuides = useMemo(() => {
 return guides.filter((g) =>
 g.title.toLowerCase().includes(searchQuery.toLowerCase())
 );
 }, [searchQuery]);

 const filteredUsecases = useMemo(() => {
 return usecaseDocs.filter((u) =>
 u.title.toLowerCase().includes(searchQuery.toLowerCase())
 );
 }, [searchQuery]);

 const filteredEndpoints = useMemo(() => {
 return endpoints.filter(
 (e) =>
 e.path.toLowerCase().includes(searchQuery.toLowerCase()) ||
 e.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
 e.tag.toLowerCase().includes(searchQuery.toLowerCase())
 );
 }, [endpoints, searchQuery]);

 // Find active endpoint details
 const activeEndpoint = useMemo(() => {
 return endpoints.find((e) => e.path === selectedEndpoint);
 }, [endpoints, selectedEndpoint]);

 // Generate Snippets
 const snippets = useMemo(() => {
 if (!activeEndpoint) return { curl: "", python: "", typescript: "" };
 const { path, method, spec } = activeEndpoint;
 const isPost = method === "POST";
 const ref = spec.requestBody?.content?.["application/json"]?.schema?.[
 "$ref"
 ];
 const schema = ref ? getSchemaDetails(ref) : null;

 // Build sample payload properties
 const samplePayload: Record<string, unknown> = {};
 const properties = schema?.properties;
 if (properties) {
 Object.keys(properties).forEach((key) => {
 const prop = properties[key];
 if (key === "agent_id") {
 samplePayload[key] = "agent-123";
 } else if (key === "content") {
 samplePayload[key] = "User prefers Python backend.";
 } else if (key === "query") {
 samplePayload[key] = "What is the user's preference?";
 } else if (prop.type === "string") {
 samplePayload[key] = prop.default || "string";
 } else if (prop.type === "number" || prop.type === "integer") {
 samplePayload[key] = prop.default !== undefined ? prop.default : 0;
 } else if (prop.type === "boolean") {
 samplePayload[key] = prop.default !== undefined ? prop.default : false;
 } else {
 samplePayload[key] = {};
 }
 });
 }

 const payloadStr = JSON.stringify(samplePayload, null, 2);

 const curl = `curl -X ${method} http://localhost:8000${path} \\
 -H "Content-Type: application/json" \\
 -H "X-API-Key: your-api-key" ${
 isPost && ref ? `\\\n -d '${payloadStr.split("\n").join("\n ")}'` : ""
 }`;

 // Python SDK conversion mapping
 let python = "";
 if (path.includes("/v1/remember")) {
 python = `from kyros import KyrosClient\n\nclient = KyrosClient(api_key="your-api-key")\n\n# Asynchronously registers episodic logs, extracts facts, and propagates beliefs\nresponse = client.smart_remember(\n agent_id="agent-123",\n content="User prefers Python backend."\n)`;
 } else if (path.includes("/v1/recall")) {
 python = `from kyros import KyrosClient\n\nclient = KyrosClient(api_key="your-api-key")\n\n# High-speed semantic search across all memory tables\nresults = client.smart_recall(\n agent_id="agent-123",\n query="What is the user's preference?"\n)`;
 } else if (path.includes("/episodic/remember")) {
 python = `from kyros import KyrosClient\n\nclient = KyrosClient(api_key="your-api-key")\n\nresponse = client.remember(\n agent_id="agent-123",\n content="User resides in Amsterdam."\n)`;
 } else if (path.includes("/episodic/recall")) {
 python = `from kyros import KyrosClient\n\nclient = KyrosClient(api_key="your-api-key")\n\nresults = client.recall(\n agent_id="agent-123",\n query="Where does the user live?"\n)`;
 } else if (path.includes("/semantic/facts")) {
 python = `from kyros import KyrosClient\n\nclient = KyrosClient(api_key="your-api-key")\n\nfact = client.store_fact(\n agent_id="agent-123",\n subject="user",\n predicate="prefers",\n value="Python"\n)`;
 } else if (path.includes("/procedural/store")) {
 python = `from kyros import KyrosClient\n\nclient = KyrosClient(api_key="your-api-key")\n\nprocedure = client.store_procedure(\n agent_id="agent-123",\n name="Send Email",\n description="Sends notification emails",\n task_type="comms",\n steps=[{"action": "send"}]\n)`;
 } else {
 python = `import httpx\n\nresponse = httpx.${method.toLowerCase()}(\n "http://localhost:8000${path}",\n headers={"X-API-Key": "your-api-key"},\n json=${payloadStr.split("\n").join("\n ")}\n)`;
 }

 // TypeScript SDK conversion mapping
 let typescript = "";
 if (path.includes("/v1/remember")) {
 typescript = `import { KyrosClient } from '@kyros.494/sdk';\n\nconst client = new KyrosClient({ apiKey: 'your-api-key' });\n\nconst response = await client.smartRemember('agent-123', 'User prefers Python backend.');`;
 } else if (path.includes("/v1/recall")) {
 typescript = `import { KyrosClient } from '@kyros.494/sdk';\n\nconst client = new KyrosClient({ apiKey: 'your-api-key' });\n\nconst results = await client.smartRecall('agent-123', 'What is the user\\'s preference?');`;
 } else if (path.includes("/episodic/remember")) {
 typescript = `import { KyrosClient } from '@kyros.494/sdk';\n\nconst client = new KyrosClient({ apiKey: 'your-api-key' });\n\nconst response = await client.remember('agent-123', 'User resides in Amsterdam.');`;
 } else if (path.includes("/episodic/recall")) {
 typescript = `import { KyrosClient } from '@kyros.494/sdk';\n\nconst client = new KyrosClient({ apiKey: 'your-api-key' });\n\nconst results = await client.recall('agent-123', 'Where does the user live?');`;
 } else if (path.includes("/semantic/facts")) {
 typescript = `import { KyrosClient } from '@kyros.494/sdk';\n\nconst client = new KyrosClient({ apiKey: 'your-api-key' });\n\nconst fact = await client.storeFact(\n 'agent-123',\n 'user',\n 'prefers',\n 'Python'\n);`;
 } else if (path.includes("/procedural/store")) {
 typescript = `import { KyrosClient } from '@kyros.494/sdk';\n\nconst client = new KyrosClient({ apiKey: 'your-api-key' });\n\nconst procedure = await client.storeProcedure(\n 'agent-123',\n 'Send Email',\n 'Sends notification emails',\n 'comms',\n [{ action: 'send' }]\n);`;
 } else {
 typescript = `// Fallback to fetch API\nconst response = await fetch("http://localhost:8000${path}", {\n method: "${method}",\n headers: {\n "Content-Type": "application/json",\n "X-API-Key": "your-api-key"\n },\n body: ${isPost ? `JSON.stringify(${payloadStr.split("\n").join("\n ")})` : "undefined"}\n});`;
 }

 return { curl, python, typescript };
 }, [activeEndpoint]);

 return (
 <div style={{ background: "var(--bg)", minHeight: "100vh", display: "flex", flexDirection: "column", width: "100%" }}>
 {/* 3-Column Work Area */}
 <div 
 style={{ 
 maxWidth: "1536px", 
 margin: "0 auto", 
 padding: "2rem 1.5rem", 
 width: "100%",
 flex: 1
 }}
 className="flex flex-col lg:flex-row gap-8 items-start"
 >
 
 {/* LEFT COLUMN: Sidebar Navigation */}
 <aside 
 style={{ 
 background: "var(--bg-alt)", 
 border: S.border, 
 borderRadius: "var(--radius)",
 boxShadow: S.shadow,
 padding: "1.25rem",
 position: "sticky",
 top: "5.5rem",
 zIndex: 10,
 }}
 className="w-full lg:w-72 shrink-0"
 >
 {/* Search Bar */}
 <div style={{ marginBottom: "1rem" }}>
 <input
 type="text"
 placeholder="Search API docs..."
 value={searchQuery}
 onChange={(e) => setSearchQuery(e.target.value)}
 style={{
 width: "100%",
 padding: "0.55rem 0.8rem",
 borderRadius: 8,
 border: S.border,
 background: "var(--bg)",
 color: "var(--text)",
 fontSize: "0.825rem",
 fontWeight: 600,
 outline: "none",
 fontFamily: "var(--font-sans)",
 }}
 className="focus:ring-2 focus:ring-[var(--primary)]"
 />
 </div>

 {/* Navigation Mode Switcher Buttons */}
 <div 
 style={{ 
 display: "grid", 
 gridTemplateColumns: "1fr 1fr 1fr", 
 border: S.border,
 background: "var(--bg)",
 borderRadius: 8,
 padding: 2,
 marginBottom: "1.25rem",
 fontFamily: "var(--font-mono)",
 fontSize: "0.7rem",
 }}
 >
 {(["guides", "usecases", "reference"] as const).map((tab) => {
 const isActive = activeTab === tab;
 return (
 <button
 key={tab}
 onClick={() => {
 setActiveTab(tab);
 setSearchQuery("");
 }}
 style={{
 padding: "0.45rem 0.25rem",
 border: "none",
 borderRadius: 6,
 background: isActive ? "var(--border)" : "transparent",
 color: isActive ? "var(--text-on-dark)" : "var(--text-muted)",
 fontWeight: 800,
 cursor: "pointer",
 textTransform: "uppercase",
 letterSpacing: "0.05em",
 transition: "all 0.1s ease",
 }}
 >
 {tab === "guides" ? "Guides" : tab === "usecases" ? "Usecases" : "API Ref"}
 </button>
 );
 })}
 </div>

 {/* Developer Guides Navigation */}
 {activeTab === "guides" && (
 <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
 {["Getting Started", "SDKs", "Server"].map((cat) => {
 const catGuides = filteredGuides.filter((g) => g.category === cat);
 if (catGuides.length === 0) return null;
 return (
 <div key={cat}>
 <h4 style={{ 
 fontSize: "0.6rem", 
 fontFamily: "var(--font-mono)", 
 textTransform: "uppercase", 
 letterSpacing: "0.08em", 
 color: "var(--text-muted)", 
 marginBottom: "0.4rem", 
 paddingLeft: "0.3rem"
 }}>
 {cat}
 </h4>
 <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "0.2rem" }}>
 {catGuides.map((g) => {
 const isSel = selectedGuide === g.id;
 return (
 <li key={g.id}>
 <button
 onClick={() => setSelectedGuide(g.id)}
 style={{
 width: "100%",
 textAlign: "left",
 padding: "0.45rem 0.6rem",
 borderRadius: 6,
 background: isSel ? "var(--primary)" : "transparent",
 color: "var(--text)",
 border: isSel ? S.border : "1.5px solid transparent",
 fontSize: "0.8rem",
 fontWeight: isSel ? 800 : 500,
 cursor: "pointer",
 transition: "all 0.1s",
 }}
 className={!isSel ? "hover:bg-[var(--bg)]" : ""}
 >
 {g.title}
 </button>
 </li>
 );
 })}
 </ul>
 </div>
 );
 })}
 </div>
 )}

 {/* Usecases Navigation */}
 {activeTab === "usecases" && (
 <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
 {["Developer Tools", "Enterprise CRM", "Customer Success", "Consumer Apps"].map((cat) => {
 const catUsecases = filteredUsecases.filter((u) => u.category === cat);
 if (catUsecases.length === 0) return null;
 return (
 <div key={cat}>
 <h4 style={{ 
 fontSize: "0.6rem", 
 fontFamily: "var(--font-mono)", 
 textTransform: "uppercase", 
 letterSpacing: "0.08em", 
 color: "var(--text-muted)", 
 marginBottom: "0.4rem", 
 paddingLeft: "0.3rem"
 }}>
 {cat}
 </h4>
 <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "0.2rem" }}>
 {catUsecases.map((u) => {
 const isSel = selectedUsecase === u.id;
 return (
 <li key={u.id}>
 <button
 onClick={() => setSelectedUsecase(u.id)}
 style={{
 width: "100%",
 textAlign: "left",
 padding: "0.45rem 0.6rem",
 borderRadius: 6,
 background: isSel ? "var(--primary)" : "transparent",
 color: "var(--text)",
 border: isSel ? S.border : "1.5px solid transparent",
 fontSize: "0.8rem",
 fontWeight: isSel ? 800 : 500,
 cursor: "pointer",
 transition: "all 0.1s",
 }}
 className={!isSel ? "hover:bg-[var(--bg)]" : ""}
 >
 {u.title}
 </button>
 </li>
 );
 })}
 </ul>
 </div>
 );
 })}
 </div>
 )}

 {/* API Reference Navigation */}
 {activeTab === "reference" && (
 <div style={{ display: "flex", flexDirection: "column", gap: "1rem", maxHeight: "400px", overflowY: "auto" }}>
 {Array.from(new Set(filteredEndpoints.map((e) => e.tag))).map((tag) => {
 const tagEndpoints = filteredEndpoints.filter((e) => e.tag === tag);
 return (
 <div key={tag}>
 <h4 style={{ 
 fontSize: "0.6rem", 
 fontFamily: "var(--font-mono)", 
 textTransform: "uppercase", 
 letterSpacing: "0.08em", 
 color: "var(--text-muted)", 
 marginBottom: "0.4rem", 
 paddingLeft: "0.3rem"
 }}>
 {tag}
 </h4>
 <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "0.2rem" }}>
 {tagEndpoints.map((e) => {
 const isSel = selectedEndpoint === e.path;
 return (
 <li key={e.path}>
 <button
 onClick={() => setSelectedEndpoint(e.path)}
 style={{
 width: "100%",
 textAlign: "left",
 padding: "0.45rem 0.5rem",
 borderRadius: 6,
 background: isSel ? "var(--primary)" : "transparent",
 color: "var(--text)",
 border: isSel ? S.border : "1.5px solid transparent",
 fontSize: "0.75rem",
 fontWeight: isSel ? 800 : 500,
 cursor: "pointer",
 display: "flex",
 alignItems: "center",
 gap: "0.4rem",
 transition: "all 0.1s",
 }}
 className={!isSel ? "hover:bg-[var(--bg)]" : ""}
 >
 <span
 style={{
 fontFamily: "var(--font-mono)",
 fontSize: "0.55rem",
 fontWeight: 900,
 padding: "0.1rem 0.25rem",
 borderRadius: 4,
 lineHeight: 1,
 background: e.method === "POST" ? "#16a34a" : e.method === "GET" ? "#2563eb" : "#dc2626",
 color: "white",
 }}
 >
 {e.method}
 </span>
 <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
 {e.summary}
 </span>
 </button>
 </li>
 );
 })}
 </ul>
 </div>
 );
 })}
 </div>
 )}
 </aside>

 {/* MIDDLE & RIGHT COLUMNS: Main Content and Sandbox Code */}
 <main className="flex-1 flex flex-col gap-8 w-full min-w-0">
 
 {/* Guides Layout */}
 {activeTab === "guides" && (
 <div 
 style={{ 
 background: "var(--bg)", 
 border: S.border, 
 borderRadius: "var(--radius)", 
 boxShadow: S.shadowLg, 
 padding: "2.5rem 2rem",
 }}
 className="w-full"
 >
 {selectedGuide === "intro" && (
 <div className="flex flex-col xl:flex-row gap-8 items-start">
 <article className="flex-1 flex flex-col gap-5">
 <h1 style={{ fontSize: "2rem", fontWeight: 950, letterSpacing: "-0.03em", margin: 0, borderBottom: S.border, paddingBottom: "0.75rem" }}>
 Introduction to Kyros
 </h1>
 <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", lineHeight: 1.75 }}>
 Kyros is an open-source, biologically-inspired persistent memory operating system designed specifically for AI agents. Traditional large language models are stateless; they forget conversation context, factual attributes, and procedural steps between interactions. Kyros bridges this gap by offering secure, self-correcting, and audit-ready memory management.
 </p>

 <h2 style={{ fontSize: "1.25rem", fontWeight: 900, margin: "1rem 0 0" }}>Memory Typologies</h2>
 <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
 <div style={{ padding: "1.25rem", border: S.border, borderRadius: 8, background: "var(--bg-alt)", boxShadow: S.shadow }}>
 <h3 style={{ fontSize: "0.85rem", fontWeight: 900, color: "var(--text)", marginBottom: "0.5rem", fontFamily: "var(--font-mono)" }}>Episodic Memory</h3>
 <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", lineHeight: 1.6, margin: 0 }}>
 Tracks chronological conversation streams, tool logs, observations, and raw interactions. Uses vector indices to recall relevant histories.
 </p>
 </div>
 <div style={{ padding: "1.25rem", border: S.border, borderRadius: 8, background: "var(--bg-alt)", boxShadow: S.shadow }}>
 <h3 style={{ fontSize: "0.85rem", fontWeight: 900, color: "var(--text)", marginBottom: "0.5rem", fontFamily: "var(--font-mono)" }}>Semantic Memory</h3>
 <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", lineHeight: 1.6, margin: 0 }}>
 Stores consolidated facts as entities and predicates. Dynamically propagates belief adjustments to resolve contradictory details.
 </p>
 </div>
 <div style={{ padding: "1.25rem", border: S.border, borderRadius: 8, background: "var(--bg-alt)", boxShadow: S.shadow }}>
 <h3 style={{ fontSize: "0.85rem", fontWeight: 900, color: "var(--text)", marginBottom: "0.5rem", fontFamily: "var(--font-mono)" }}>Procedural Memory</h3>
 <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", lineHeight: 1.6, margin: 0 }}>
 Captures step-by-step agent execution workflows. Matches context descriptors against saved procedure templates to guide next steps.
 </p>
 </div>
 </div>

 <h2 style={{ fontSize: "1.25rem", fontWeight: 900, margin: "1rem 0 0" }}>Key Engineering Principles</h2>
 <ul style={{ paddingLeft: "1.25rem", margin: 0, display: "flex", flexDirection: "column", gap: "0.6rem", fontSize: "0.85rem", color: "var(--text)" }}>
 <li><strong>Ebbinghaus Temporal Decay:</strong> Importance weights degrade over time according to category rates, preventing index bloat.</li>
 <li><strong>Merkle Tree Cryptographic Auditing:</strong> Every change creates a hash signature added to a validation ledger to detect poisoning.</li>
 <li><strong>Adaptive Belief Propagation:</strong> BFS node traversals recalculate confidences in facts when contradictory statements are ingested.</li>
 </ul>
 </article>
 
 {/* Right Panel */}
 <div className="w-full xl:w-96 shrink-0">
 <div style={{ padding: "1.25rem", border: S.border, borderRadius: 8, background: "var(--bg-dark)", color: "var(--text-on-dark)", boxShadow: S.shadow }}>
 <h3 style={{ fontSize: "0.8rem", fontFamily: "var(--font-mono)", color: "var(--primary)", marginTop: 0 }}>KYROS ECOSYSTEM</h3>
 <p style={{ fontSize: "0.72rem", color: "rgba(249,247,242,0.6)", lineHeight: 1.6, margin: 0 }}>
 All requests are securely validated. Client SDKs encapsulate API details and handle token authorization headers automatically in the background.
 </p>
 </div>
 </div>
 </div>
 )}

 {selectedGuide === "authentication" && (
 <div className="flex flex-col xl:flex-row gap-8 items-start">
 <article className="flex-1 flex flex-col gap-5">
 <h1 style={{ fontSize: "2rem", fontWeight: 950, letterSpacing: "-0.03em", margin: 0, borderBottom: S.border, paddingBottom: "0.75rem" }}>
 Authentication
 </h1>
 <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", lineHeight: 1.75 }}>
 The Kyros API uses API keys to authenticate requests. You can view and manage your API keys in the <a href="http://localhost:8000/dashboard" target="_blank" rel="noopener noreferrer" style={linkStyle}>Kyros Dashboard</a>.
 </p>
 <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", lineHeight: 1.75 }}>
 Test secret keys have the prefix <code style={{ background: "var(--bg-alt)", padding: "0.1rem 0.35rem", borderRadius: 4, fontFamily: "var(--font-mono)" }}>mk_test_</code> and live mode secret keys have the prefix <code style={{ background: "var(--bg-alt)", padding: "0.1rem 0.35rem", borderRadius: 4, fontFamily: "var(--font-mono)" }}>mk_live_</code>. Alternatively, you can configure restricted API keys for granular agent credentials.
 </p>
 <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", lineHeight: 1.75 }}>
 Your API keys carry many privileges. Keep your keys safe. Do not embed secret keys in source code or client-side applications. Instead, use your server platform&apos;s secrets vault or set your keys in environment variables.
 </p>
 <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", lineHeight: 1.75 }}>
 Make all API requests over HTTPS. Calls made over plain HTTP fail. API requests without authentication also fail.
 </p>
 </article>

 {/* Right side authentication widgets matching Stripe */}
 <div className="w-full xl:w-[420px] shrink-0 flex flex-col gap-6">
 
 {/* Authenticated Request cURL Box */}
 <CodeBlock 
 language="cURL Request"
 code={`curl http://localhost:8000/v1/remember \\
 -H "X-API-Key: mk_test_tR3PYbc...96th88S4VQ2u"`}
 />

 {/* Your API Key Alert Box */}
 <div style={{ padding: "1.25rem", border: S.border, borderRadius: 8, background: "var(--bg-alt)", color: "var(--text)", boxShadow: S.shadow }}>
 <h4 style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)", textTransform: "uppercase", margin: "0 0 0.5rem", fontWeight: 900 }}>
 Your API Key
 </h4>
 <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", lineHeight: 1.6, margin: 0 }}>
 A sample test API key is included in the examples here, so you can test any example right away. Do not submit any personally identifiable information in requests made with this key.
 </p>
 </div>

 </div>
 </div>
 )}

 {selectedGuide === "errors" && (
 <div className="flex flex-col xl:flex-row gap-8 items-start">
 <article className="flex-1 flex flex-col gap-5">
 <h1 style={{ fontSize: "2rem", fontWeight: 950, letterSpacing: "-0.03em", margin: 0, borderBottom: S.border, paddingBottom: "0.75rem" }}>
 Errors
 </h1>
 <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", lineHeight: 1.75 }}>
 Kyros uses conventional HTTP response codes to indicate the success or failure of an API request. In general: Codes in the <code style={{ background: "var(--bg-alt)", padding: "0.1rem 0.35rem", borderRadius: 4, fontFamily: "var(--font-mono)" }}>2xx</code> range indicate success. Codes in the <code style={{ background: "var(--bg-alt)", padding: "0.1rem 0.35rem", borderRadius: 4, fontFamily: "var(--font-mono)" }}>4xx</code> range indicate an error that failed given the information provided (e.g., a required parameter was omitted, token limit exceeded, etc.). Codes in the <code style={{ background: "var(--bg-alt)", padding: "0.1rem 0.35rem", borderRadius: 4, fontFamily: "var(--font-mono)" }}>5xx</code> range indicate an error with Kyros&apos;s servers (these are rare).
 </p>
 <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", lineHeight: 1.75 }}>
 Some <code style={{ background: "var(--bg-alt)", padding: "0.1rem 0.35rem", borderRadius: 4, fontFamily: "var(--font-mono)" }}>4xx</code> errors that could be handled programmatically include details (error messages, code tags) inside the JSON response validation structure.
 </p>
 </article>

 {/* Right side HTTP Status Code Summary Table matching Stripe */}
 <div className="w-full xl:w-[420px] shrink-0 flex flex-col gap-6">
 <div style={{ border: S.border, borderRadius: 8, background: "var(--bg-dark)", color: "var(--text-on-dark)", overflow: "hidden", boxShadow: S.shadow }}>
 <div style={{ borderBottom: S.border, background: "#161513", padding: "0.75rem 1rem" }}>
 <span style={{ fontSize: "0.65rem", fontFamily: "var(--font-mono)", fontWeight: 900, color: "var(--primary)" }}>
 HTTP STATUS CODE SUMMARY
 </span>
 </div>
 <div style={{ padding: "1rem", fontFamily: "var(--font-sans)", fontSize: "0.72rem", overflowX: "auto" }}>
 <table style={{ width: "100%", borderCollapse: "collapse", color: "#e6e1da", textAlign: "left" }}>
 <thead>
 <tr style={{ borderBottom: "1px solid rgba(249,247,242,0.1)", color: "rgba(249,247,242,0.4)" }}>
 <th style={{ padding: "0.4rem 0.5rem" }}>Code</th>
 <th style={{ padding: "0.4rem 0.5rem" }}>Status</th>
 <th style={{ padding: "0.4rem 0.5rem" }}>Description</th>
 </tr>
 </thead>
 <tbody>
 {[
 { code: "200", status: "OK", desc: "Request completed successfully." },
 { code: "201", status: "Created", desc: "Resource was stored successfully." },
 { code: "400", status: "Bad Request", desc: "Missing parameters or malformed body." },
 { code: "401", status: "Unauthorized", desc: "No valid API key provided in headers." },
 { code: "403", status: "Forbidden", desc: "The API key doesn't have permissions." },
 { code: "404", status: "Not Found", desc: "The requested resource does not exist." },
 { code: "429", status: "Too Many Requests", desc: "Rate limit threshold was hit." },
 { code: "500", status: "Server Errors", desc: "Internal error on Kyros server." }
 ].map((row) => (
 <tr key={row.code} style={{ borderBottom: "1px solid rgba(249,247,242,0.05)" }}>
 <td style={{ padding: "0.5rem", fontFamily: "var(--font-mono)", fontWeight: "bold", color: "var(--primary)" }}>{row.code}</td>
 <td style={{ padding: "0.5rem", fontWeight: "bold" }}>{row.status}</td>
 <td style={{ padding: "0.5rem", color: "rgba(249,247,242,0.7)" }}>{row.desc}</td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>
 </div>
 </div>
 </div>
 )}

 {selectedGuide === "quickstart" && (
 <div className="flex flex-col xl:flex-row gap-8 items-start">
 <article className="flex-1 flex flex-col gap-5">
 <h1 style={{ fontSize: "2rem", fontWeight: 950, letterSpacing: "-0.03em", margin: 0, borderBottom: S.border, paddingBottom: "0.75rem" }}>
 Quickstart Guide
 </h1>
 <p style={{ fontSize: "0.9rem", color: "var(--text-muted)" }}>
 Run the Kyros server stack locally using <a href="https://docs.docker.com/compose/" target="_blank" rel="noopener noreferrer" style={linkStyle}>Docker Compose</a>.
 </p>

 <h2 style={{ fontSize: "1.25rem", fontWeight: 900, margin: "1rem 0 0" }}>1. Clone & Run Stack</h2>
 <CodeBlock 
 code={`git clone https://github.com/Kyros-494/kyros-ai\ncd kyros-ai\ndocker compose up -d`}
 />

 <h2 style={{ fontSize: "1.25rem", fontWeight: 900, margin: "1rem 0 0" }}>2. Configure Environments</h2>
 <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
 Copy the default template configuration file to load standard settings:
 </p>
 <CodeBlock 
 code={`cp .env.example .env`}
 />

 <h2 style={{ fontSize: "1.25rem", fontWeight: 900, margin: "1rem 0 0" }}>3. Validate Services</h2>
 <ul style={{ paddingLeft: "1.25rem", margin: 0, display: "flex", flexDirection: "column", gap: "0.5rem", fontSize: "0.85rem" }}>
 <li>API Endpoint: <code style={{ color: "var(--text)", fontWeight: "bold", background: "var(--bg-alt)", padding: "0.1rem 0.35rem", borderRadius: 4, fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>http://localhost:8000</code></li>
 <li>Developer Console Dashboard: <code style={{ color: "var(--text)", fontWeight: "bold", background: "var(--bg-alt)", padding: "0.1rem 0.35rem", borderRadius: 4, fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>http://localhost:8000/dashboard</code></li>
 </ul>
 </article>

 {/* Right side info card */}
 <div className="w-full xl:w-96 shrink-0">
 <div style={{ padding: "1.25rem", border: S.border, borderRadius: 8, background: "var(--bg-alt)", color: "var(--text)", boxShadow: S.shadow }}>
 <h4 style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)", textTransform: "uppercase", margin: "0 0 0.5rem", fontWeight: 900 }}>
 Docker Requirements
 </h4>
 <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", lineHeight: 1.6, margin: 0 }}>
 Make sure Docker and Docker Compose are installed and running on your system before launching. The engine requires PostgreSQL/pgvector and Redis containers. For help, read the <a href="https://docs.docker.com/" target="_blank" rel="noopener noreferrer" style={linkStyle}>Docker documentation</a>.
 </p>
 </div>
 </div>
 </div>
 )}

 {selectedGuide === "python-sdk" && (
 <div className="flex flex-col xl:flex-row gap-8 items-start">
 <article className="flex-1 flex flex-col gap-5">
 <h1 style={{ fontSize: "2rem", fontWeight: 950, letterSpacing: "-0.03em", margin: 0, borderBottom: S.border, paddingBottom: "0.75rem" }}>
 Python SDK Guide
 </h1>
 <p style={{ fontSize: "0.9rem", color: "var(--text-muted)" }}>
 Verify the client-side library to integrate Kyros with your Python agents. You can check the package updates on the official <a href="https://pypi.org/" target="_blank" rel="noopener noreferrer" style={linkStyle}>PyPI Python Package Repository</a>.
 </p>

 <h2 style={{ fontSize: "1.25rem", fontWeight: 900, margin: "1rem 0 0" }}>Installation</h2>
 <CodeBlock 
 code={`pip install kyros-sdk`}
 />

 <h2 style={{ fontSize: "1.25rem", fontWeight: 900, margin: "1rem 0 0" }}>Remembering & Recalling</h2>
 <CodeBlock 
 code={`from kyros import KyrosClient\n\n# Store memory block\nclient.remember("agent-123", "User resides in Amsterdam.")\n\n# Semantic recall\nresults = client.recall("agent-123", "Where does the user live?")\nprint(results.results[0].content)`}
 />
 </article>

 {/* Right side info card */}
 <div className="w-full xl:w-96 shrink-0">
 <div style={{ padding: "1.25rem", border: S.border, borderRadius: 8, background: "var(--bg-alt)", color: "var(--text)", boxShadow: S.shadow }}>
 <h4 style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)", textTransform: "uppercase", margin: "0 0 0.5rem", fontWeight: 900 }}>
 Requirements
 </h4>
 <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", lineHeight: 1.6, margin: 0 }}>
 Requires Python 3.8 or above. Fits seamlessly into LangChain, LlamaIndex, and CrewAI setups.
 </p>
 </div>
 </div>
 </div>
 )}

 {selectedGuide === "typescript-sdk" && (
 <div className="flex flex-col xl:flex-row gap-8 items-start">
 <article className="flex-1 flex flex-col gap-5">
 <h1 style={{ fontSize: "2rem", fontWeight: 950, letterSpacing: "-0.03em", margin: 0, borderBottom: S.border, paddingBottom: "0.75rem" }}>
 TypeScript SDK Guide
 </h1>
 <p style={{ fontSize: "0.9rem", color: "var(--text-muted)" }}>
 Add the SDK dependency package to your JavaScript/TypeScript code. The client library is available on the <a href="https://www.npmjs.com/" target="_blank" rel="noopener noreferrer" style={linkStyle}>npm registry</a>.
 </p>

 <h2 style={{ fontSize: "1.25rem", fontWeight: 900, margin: "1rem 0 0" }}>Installation</h2>
 <CodeBlock 
 code={`npm install @kyros.494/sdk`}
 />

 <h2 style={{ fontSize: "1.25rem", fontWeight: 900, margin: "1rem 0 0" }}>Basic Client Setup</h2>
 <CodeBlock 
 code={`import { KyrosClient } from '@kyros.494/sdk';\n\nconst client = new KyrosClient({\n apiKey: 'mk_live_default_dev_key_123456',\n baseUrl: 'http://localhost:8000'\n});\n\nasync function main() {\n await client.remember('agent-123', 'User prefers TypeScript.');\n const results = await client.recall('agent-123', 'What language?');\n console.log(results.results[0].content);\n}\n\nmain().catch(console.error);`}
 />
 </article>

 {/* Right side info card */}
 <div className="w-full xl:w-96 shrink-0">
 <div style={{ padding: "1.25rem", border: S.border, borderRadius: 8, background: "var(--bg-alt)", color: "var(--text)", boxShadow: S.shadow }}>
 <h4 style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)", textTransform: "uppercase", margin: "0 0 0.5rem", fontWeight: 900 }}>
 Node Support
 </h4>
 <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", lineHeight: 1.6, margin: 0 }}>
 Supports Node.js 16+, Next.js, and browser environments. Includes complete TypeScript types out of the box.
 </p>
 </div>
 </div>
 </div>
 )}

 {selectedGuide === "self-hosting" && (
 <div className="flex flex-col xl:flex-row gap-8 items-start">
 <article className="flex-1 flex flex-col gap-5">
 <h1 style={{ fontSize: "2rem", fontWeight: 950, letterSpacing: "-0.03em", margin: 0, borderBottom: S.border, paddingBottom: "0.75rem" }}>
 Self-Hosting in Production
 </h1>
 <p style={{ fontSize: "0.9rem", color: "var(--text-muted)" }}>
 Guidance on deploying the memory service in production environments.
 </p>

 <h2 style={{ fontSize: "1.25rem", fontWeight: 900, margin: "1rem 0 0" }}>Migrations & Database</h2>
 <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", lineHeight: 1.7 }}>
 FastAPI runs automatic <a href="https://alembic.sqlalchemy.org/" target="_blank" rel="noopener noreferrer" style={linkStyle}>Alembic schema migrations</a> on startup in dev/test environments. In production, set `KYROS_ENVIRONMENT=production` and run migrations manually:
 </p>
 <CodeBlock 
 code={`alembic upgrade head`}
 />

 <h2 style={{ fontSize: "1.25rem", fontWeight: 900, margin: "1rem 0 0" }}>Security Infrastructure</h2>
 <ul style={{ paddingLeft: "1.25rem", margin: 0, display: "flex", flexDirection: "column", gap: "0.5rem", fontSize: "0.85rem" }}>
 <li><strong>Row-Level Security (RLS):</strong> PostgreSQL partitions tables by tenant context. Access policies are verified cryptographically.</li>
 <li><strong>API Credential Safety:</strong> Plaintext keys are never stored in the database. Hashes are updated using HMAC pepper key configurations.</li>
 </ul>
 </article>

 {/* Right side info card */}
 <div className="w-full xl:w-96 shrink-0">
 <div style={{ padding: "1.25rem", border: S.border, borderRadius: 8, background: "var(--bg-alt)", color: "var(--text)", boxShadow: S.shadow }}>
 <h4 style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)", textTransform: "uppercase", margin: "0 0 0.5rem", fontWeight: 900 }}>
 Production Tip
 </h4>
 <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", lineHeight: 1.6, margin: 0 }}>
 Always run migrations before scaling web instances to prevent table schema locks during startup.
 </p>
 </div>
 </div>
 </div>
 )}

 {selectedGuide === "llm-integrations" && (
 <div className="flex flex-col xl:flex-row gap-8 items-start">
 <article className="flex-1 flex flex-col gap-5">
 <h1 style={{ fontSize: "2rem", fontWeight: 950, letterSpacing: "-0.03em", margin: 0, borderBottom: S.border, paddingBottom: "0.75rem" }}>
 LLM Integrations
 </h1>
 <p style={{ fontSize: "0.9rem", color: "var(--text-muted)" }}>
 Route factual extraction prompts and context consolidation logic to providers.
 </p>

 <h2 style={{ fontSize: "1.25rem", fontWeight: 900, margin: "1rem 0 0" }}>Provider Keys</h2>
 <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
 Set api keys in the environment variables to activate providers:
 </p>
 <CodeBlock 
 code={`OPENAI_API_KEY=sk-proj-...\nGEMINI_API_KEY=AIzaSy...\nANTHROPIC_API_KEY=sk-ant-...`}
 />
 <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", lineHeight: 1.75 }}>
 If multiple keys are present, the consolidation logic falls back sequentially to locate available models in development and production gates.
 </p>
 </article>

 {/* Right side info card */}
 <div className="w-full xl:w-96 shrink-0">
 <div style={{ padding: "1.25rem", border: S.border, borderRadius: 8, background: "var(--bg-alt)", color: "var(--text)", boxShadow: S.shadow }}>
 <h4 style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)", textTransform: "uppercase", margin: "0 0 0.5rem", fontWeight: 900 }}>
 Local Models
 </h4>
 <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", lineHeight: 1.6, margin: 0 }}>
 Supports local model connections using <a href="https://ollama.com/" target="_blank" rel="noopener noreferrer" style={linkStyle}>Ollama</a> or <a href="https://github.com/vllm-project/vllm" target="_blank" rel="noopener noreferrer" style={linkStyle}>vLLM</a> backends. Set <code style={{ fontFamily: "var(--font-mono)", fontSize: "0.65rem" }}>OLLAMA_BASE_URL</code> in environment configs.
 </p>
 </div>
 </div>
 </div>
 )}
 </div>
 )}

 {/* Usecases Layout */}
 {activeTab === "usecases" && (
 <div 
 style={{ 
 background: "var(--bg)", 
 border: S.border, 
 borderRadius: "var(--radius)", 
 boxShadow: S.shadowLg, 
 padding: "2.5rem 2rem",
 }}
 className="w-full"
 >
 {selectedUsecase === "coding-companion" && (
 <article style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
 <h1 style={{ fontSize: "2rem", fontWeight: 950, letterSpacing: "-0.03em", margin: 0, borderBottom: S.border, paddingBottom: "0.75rem" }}>
 Personal Coding Companion
 </h1>
 <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", lineHeight: 1.75 }}>
 Developers frequently use AI assistants that lack local preference continuity. Setting preferred code standards (e.g., strict TypeScript typing, tab indentation size) inside general prompts consumes large token overheads. Kyros stores these variables persistently.
 </p>

 <h2 style={{ fontSize: "1.25rem", fontWeight: 900, margin: "1rem 0 0" }}>Ingesting Preferences</h2>
 <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
 When a developer states a guideline (e.g. &quot;Use strict typing configurations&quot;), the IDE client records this episodic memory:
 </p>
 <CodeBlock 
 code={`# Python SDK Ingestion\nclient.remember("developer-123", "Preferred type check: always configure strict mode.")`}
 />

 <h2 style={{ fontSize: "1.25rem", fontWeight: 900, margin: "1rem 0 0" }}>Context Retrieval on Prompt</h2>
 <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
 When issuing a coding task request, query the memory vector database dynamically:
 </p>
 <CodeBlock 
 code={`# Recall related context before execution\ncontext = client.recall("developer-123", "TypeScript configs")`}
 />
 </article>
 )}

 {selectedUsecase === "personalized-crm" && (
 <article style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
 <h1 style={{ fontSize: "2rem", fontWeight: 950, letterSpacing: "-0.03em", margin: 0, borderBottom: S.border, paddingBottom: "0.75rem" }}>
 Personalized CRM Assistant
 </h1>
 <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", lineHeight: 1.75 }}>
 In sales, tracking customer preferences (e.g., preferred contact hour, package sizes) is vital. Standard databases overwrite histories, whereas Kyros maps facts in semantic relationship structures to resolve conflict occurrences.
 </p>

 <h2 style={{ fontSize: "1.25rem", fontWeight: 900, margin: "1rem 0 0" }}>Storing Structured Facts</h2>
 <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
 Build subject-predicate-object semantic connections representing client info:
 </p>
 <CodeBlock 
 code={`# TypeScript SDK Fact Storage\nawait client.storeFact("agent-crm", "customer_1", "package", "Enterprise Tier");`}
 />

 <h2 style={{ fontSize: "1.25rem", fontWeight: 900, margin: "1rem 0 0" }}>Conflict Resolution</h2>
 <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", lineHeight: 1.75 }}>
 If the client changes their package (e.g. &quot;Downgrade package to Growth Tier&quot;), saving the new fact triggers belief propagation. Conflicting package nodes are automatically marked for decay and confidence scores update.
 </p>
 </article>
 )}

 {selectedUsecase === "customer-support" && (
 <article style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
 <h1 style={{ fontSize: "2rem", fontWeight: 950, letterSpacing: "-0.03em", margin: 0, borderBottom: S.border, paddingBottom: "0.75rem" }}>
 Customer Support Agent
 </h1>
 <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", lineHeight: 1.75 }}>
 Support agents require both episodic knowledge of historical tickets and procedural guides to execute operations (like processing a payment refund) consistently.
 </p>

 <h2 style={{ fontSize: "1.25rem", fontWeight: 900, margin: "1rem 0 0" }}>Loading Support Workflows</h2>
 <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
 Save standard operating procedures into Kyros procedural memory:
 </p>
 <CodeBlock 
 code={`# Storing a standardized refund procedure\nclient.store_procedure(\n agent_id="support-bot",\n name="Process Refund",\n description="Steps required to issue a payment refund",\n task_type="billing",\n steps=[\n {"action": "check_invoice", "params": {"required": True}},\n {"action": "gateway_refund", "params": {"gateway": "stripe"}}\n ]\n)`}
 />

 <h2 style={{ fontSize: "1.25rem", fontWeight: 900, margin: "1rem 0 0" }}>Workflow Matching</h2>
 <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
 When a customer asks for billing assistance, search procedural records to load the correct workflow path:
 </p>
 <CodeBlock 
 code={`# Find procedural steps matching request description\naction_plan = client.match_procedure("support-bot", "Customer requesting money back for invoice 5")`}
 />
 </article>
 )}

 {selectedUsecase === "travel-planner" && (
 <article style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
 <h1 style={{ fontSize: "2rem", fontWeight: 950, letterSpacing: "-0.03em", margin: 0, borderBottom: S.border, paddingBottom: "0.75rem" }}>
 Travel Planner Agent
 </h1>
 <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", lineHeight: 1.75 }}>
 Travel recommendations require temporary interest states. An agent should remember that a user is planning a trip to &quot;Paris&quot; this month, but should forget this detail next year to avoid indexing drift.
 </p>

 <h2 style={{ fontSize: "1.25rem", fontWeight: 900, margin: "1rem 0 0" }}>Ebbinghaus Retention Curves</h2>
 <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", lineHeight: 1.7 }}>
 By configuring decay rates on episodic memory types, short-term interests (such as trip search parameters) fade naturally after a defined temporal period, keeping LLM prompt tokens focused strictly on high-priority items.
 </p>
 <CodeBlock 
 code={`# Update episodic category decay rate to high coefficient\nclient.set_decay_rates({"trip_search": 0.25})`}
 />
 </article>
 )}
 </div>
 )}

 {/* Reference Layout: Stripe-inspired 2-Column Split */}
 {activeTab === "reference" && activeEndpoint && (
 <div className="flex flex-col xl:flex-row gap-8 items-start w-full">
 
 {/* Reference Left Pane: Endpoint details, parameters, descriptions */}
 <div 
 style={{ 
 flex: 1, 
 background: "var(--bg)", 
 border: S.border, 
 borderRadius: "var(--radius)", 
 boxShadow: S.shadowLg, 
 padding: "2.5rem 2rem",
 }}
 className="w-full min-w-0"
 >
 {/* Method and Path Badge */}
 <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1rem" }}>
 <span
 style={{
 fontFamily: "var(--font-mono)",
 fontSize: "0.75rem",
 fontWeight: 900,
 padding: "0.25rem 0.6rem",
 borderRadius: 6,
 border: S.border,
 background: activeEndpoint.method === "POST" ? "#16a34a" : activeEndpoint.method === "GET" ? "#2563eb" : "#dc2626",
 color: "white",
 }}
 >
 {activeEndpoint.method}
 </span>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.85rem", fontWeight: 700, color: "var(--text)" }}>
 {activeEndpoint.path}
 </span>
 </div>

 <h1 style={{ fontSize: "2rem", fontWeight: 950, letterSpacing: "-0.03em", margin: "0 0 0.5rem", color: "var(--text)" }}>
 {activeEndpoint.spec.summary}
 </h1>
 <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", lineHeight: 1.75, marginBottom: "2rem", wordBreak: "break-word" }}>
 {activeEndpoint.spec.description}
 </p>

 {/* Request Parameters (Path / Query) */}
 {activeEndpoint.spec.parameters && activeEndpoint.spec.parameters.length > 0 && (
 <div style={{ marginBottom: "2rem" }}>
 <h3 style={{ fontSize: "0.7rem", fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text)", marginBottom: "0.75rem" }}>
 Query & Path Parameters
 </h3>
 <div style={{ border: S.border, borderRadius: 8, overflow: "hidden", boxShadow: S.shadow }}>
 <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.78rem", textAlign: "left", tableLayout: "fixed" }}>
 <thead>
 <tr style={{ background: "var(--bg-dark)", color: "var(--text-on-dark)", borderBottom: S.border, fontFamily: "var(--font-mono)" }}>
 <th style={{ padding: "0.75rem 1rem", fontWeight: 700, width: "25%" }}>Parameter</th>
 <th style={{ padding: "0.75rem 1rem", fontWeight: 700, width: "15%" }}>Type</th>
 <th style={{ padding: "0.75rem 1rem", fontWeight: 700, width: "15%" }}>Required</th>
 <th style={{ padding: "0.75rem 1rem", fontWeight: 700, width: "45%" }}>Description</th>
 </tr>
 </thead>
 <tbody>
 {activeEndpoint.spec.parameters.map((param) => (
 <tr key={param.name} style={{ borderBottom: S.borderLight, background: "var(--bg)" }}>
 <td style={{ padding: "0.75rem 1rem", fontFamily: "var(--font-mono)", fontWeight: 800, wordBreak: "break-all" }}>{param.name}</td>
 <td style={{ padding: "0.75rem 1rem" }}>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.7rem", padding: "0.1rem 0.3rem", background: "var(--bg-alt)", border: S.borderLight, borderRadius: 4 }}>
 {param.schema?.type || "string"}
 </span>
 </td>
 <td style={{ padding: "0.75rem 1rem", fontFamily: "var(--font-mono)", color: param.required ? "#dc2626" : "var(--text-muted)" }}>
 {param.required ? "true" : "false"}
 </td>
 <td style={{ padding: "0.75rem 1rem", color: "var(--text-muted)", lineHeight: 1.5, wordBreak: "break-word" }}>{param.description || "—"}</td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>
 </div>
 )}

 {/* Request Body Properties */}
 {activeEndpoint.spec.requestBody?.content?.["application/json"]?.schema?.["$ref"] && (
 <div style={{ marginBottom: "2.5rem" }}>
 <h3 style={{ fontSize: "0.7rem", fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text)", marginBottom: "0.75rem" }}>
 Request Body Fields
 </h3>
 {(() => {
 const ref = activeEndpoint.spec.requestBody.content["application/json"].schema["$ref"];
 const schema = getSchemaDetails(ref);
 const properties = schema?.properties;
 if (!schema || !properties) {
 return <p style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>No request body schemas defined.</p>;
 }
 return (
 <div style={{ border: S.border, borderRadius: 8, overflow: "hidden", boxShadow: S.shadow }}>
 <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.78rem", textAlign: "left", tableLayout: "fixed" }}>
 <thead>
 <tr style={{ background: "var(--bg-dark)", color: "var(--text-on-dark)", borderBottom: S.border, fontFamily: "var(--font-mono)" }}>
 <th style={{ padding: "0.75rem 1rem", fontWeight: 700, width: "25%" }}>Field Name</th>
 <th style={{ padding: "0.75rem 1rem", fontWeight: 700, width: "15%" }}>Type</th>
 <th style={{ padding: "0.75rem 1rem", fontWeight: 700, width: "15%" }}>Required</th>
 <th style={{ padding: "0.75rem 1rem", fontWeight: 700, width: "45%" }}>Description</th>
 </tr>
 </thead>
 <tbody>
 {Object.keys(properties).map((key) => {
 const prop = properties[key];
 const isRequired = schema.required && schema.required.includes(key);
 return (
 <tr key={key} style={{ borderBottom: S.borderLight, background: "var(--bg)" }}>
 <td style={{ padding: "0.75rem 1rem", fontFamily: "var(--font-mono)", fontWeight: 800, wordBreak: "break-all" }}>{key}</td>
 <td style={{ padding: "0.75rem 1rem" }}>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.7rem", padding: "0.1rem 0.3rem", background: "var(--bg-alt)", border: S.borderLight, borderRadius: 4 }}>
 {prop.type || (prop["$ref"] ? "object" : "any")}
 </span>
 </td>
 <td style={{ padding: "0.75rem 1rem", fontFamily: "var(--font-mono)", color: isRequired ? "#dc2626" : "var(--text-muted)" }}>
 {isRequired ? "true" : "false"}
 </td>
 <td style={{ padding: "0.75rem 1rem", color: "var(--text-muted)", lineHeight: 1.5, wordBreak: "break-word" }}>{prop.description || "—"}</td>
 </tr>
 );
 })}
 </tbody>
 </table>
 </div>
 );
 })()}
 </div>
 )}

 {/* Responses List */}
 <div>
 <h3 style={{ fontSize: "0.7rem", fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text)", marginBottom: "0.75rem" }}>
 HTTP Status Responses
 </h3>
 <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
 {activeEndpoint.spec.responses ? (
 Object.keys(activeEndpoint.spec.responses).map((status) => {
 const res = activeEndpoint.spec.responses![status];
 return (
 <div
 key={status}
 style={{
 padding: "0.75rem 1rem",
 borderRadius: 8,
 border: S.border,
 background: "var(--bg-alt)",
 display: "flex",
 justifyContent: "between",
 alignItems: "center",
 fontSize: "0.78rem",
 }}
 >
 <span style={{ fontFamily: "var(--font-mono)", fontWeight: 800 }}>
 Status Code: <strong style={{ color: "#16a34a" }}>{status}</strong>
 </span>
 <span style={{ marginLeft: "auto", color: "var(--text-muted)", wordBreak: "break-word" }}>{res.description}</span>
 </div>
 );
 })
 ) : (
 <p style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>No response status codes documented.</p>
 )}
 </div>
 </div>
 </div>

 {/* Reference Right Pane: Sticky code sandbox editor + Live Response viewer */}
 <div 
 style={{ 
 position: "sticky", 
 top: "5.5rem",
 zIndex: 5,
 }}
 className="w-full xl:w-[420px] shrink-0 flex flex-col gap-6"
 >
 {/* 1. Request Code Block */}
 <div 
 style={{ 
 border: S.border, 
 background: "var(--bg-dark)", 
 borderRadius: "var(--radius)", 
 overflow: "hidden", 
 boxShadow: S.shadow 
 }}
 >
 {/* Top Editor Tab Bar */}
 <div 
 style={{ 
 display: "flex", 
 alignItems: "center",
 justifyContent: "space-between",
 borderBottom: S.border, 
 background: "#161513", 
 padding: "0 0.5rem" 
 }}
 >
 <div style={{ display: "flex" }}>
 {([
 { id: "curl", label: "cURL" },
 { id: "python", label: "Python" },
 { id: "typescript", label: "TypeScript" },
 ] as const).map((tab) => {
 const isActive = activeSnippetTab === tab.id;
 return (
 <button
 key={tab.id}
 onClick={() => setActiveSnippetTab(tab.id)}
 style={{
 padding: "0.85rem 1rem",
 background: "transparent",
 color: isActive ? "var(--primary)" : "#8a847e",
 border: "none",
 borderBottom: isActive ? "2px solid var(--primary)" : "2px solid transparent",
 fontSize: "0.7rem",
 fontFamily: "var(--font-mono)",
 fontWeight: 800,
 cursor: "pointer",
 transition: "all 0.15s",
 }}
 >
 {tab.label}
 </button>
 );
 })}
 </div>
 <button 
 onClick={() => {
 navigator.clipboard.writeText(snippets[activeSnippetTab]);
 setSnippetsCopied(true);
 setTimeout(() => setSnippetsCopied(false), 2000);
 }}
 style={{ 
 background: "transparent", 
 border: "none", 
 color: snippetsCopied ? "var(--primary)" : "#8a847e", 
 fontWeight: "bold", 
 cursor: "pointer", 
 fontSize: "0.6rem",
 paddingRight: "0.5rem"
 }}
 >
 {snippetsCopied ? "COPIED!" : "COPY"}
 </button>
 </div>

 {/* Preformatted Code Content */}
 <div 
 style={{ 
 padding: "1.25rem", 
 fontFamily: "var(--font-mono)", 
 fontSize: "0.72rem", 
 color: "#e6e1da", 
 lineHeight: 1.6, 
 overflowX: "auto", 
 minHeight: "220px",
 background: "var(--bg-dark)"
 }}
 >
 <pre style={{ margin: 0 }}><code style={{ display: "block" }}>{snippets[activeSnippetTab]}</code></pre>
 </div>
 </div>

 {/* 2. Response JSON Mock Block */}
 {mockResponses[activeEndpoint.path] && (
 <CodeBlock 
 language="RESPONSE 200 OK (JSON)"
 code={mockResponses[activeEndpoint.path]}
 />
 )}

 </div>

 </div>
 )}

 </main>
 </div>
 </div>
 );
}
