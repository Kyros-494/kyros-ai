"use client";

import React, { useState } from "react";

type DocSection = "intro" | "quickstart" | "concepts" | "config" | "selfhost" | "python" | "typescript" | "integrations";

export default function DocsPage() {
  const [activeSection, setActiveSection] = useState<DocSection>("intro");

  const menuItems: { id: DocSection; label: string }[] = [
    { id: "intro", label: "Introduction" },
    { id: "quickstart", label: "Quickstart Guide" },
    { id: "concepts", label: "Core Concepts" },
    { id: "config", label: "Configuration" },
    { id: "selfhost", label: "Self-Hosting Guide" },
    { id: "python", label: "Python SDK Reference" },
    { id: "typescript", label: "TypeScript SDK Reference" },
    { id: "integrations", label: "LLM Integrations" },
  ];

  return (
    <div className="max-w-6xl mx-auto px-6 py-12 flex flex-col md:flex-row gap-8 bg-slate-900 text-slate-100 flex-1 w-full">
      {/* Sidebar Navigation */}
      <aside className="w-full md:w-64 shrink-0">
        <div className="sticky top-24 border border-slate-800 bg-slate-800/30 rounded-lg p-4">
          <h3 className="text-xs font-mono uppercase tracking-wider text-slate-500 mb-4 px-2">Documentation</h3>
          <ul className="space-y-1">
            {menuItems.map((item) => (
              <li key={item.id}>
                <button
                  onClick={() => setActiveSection(item.id)}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium transition-all ${
                    activeSection === item.id
                      ? "bg-blue-600/10 text-blue-400 font-semibold"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                  }`}
                >
                  {item.label}
                </button>
              </li>
            ))}
          </ul>
        </div>
      </aside>

      {/* Main Content Pane */}
      <main className="flex-1 min-w-0 border border-slate-800 bg-slate-850 p-8 rounded-lg">
        {activeSection === "intro" && (
          <article className="space-y-6">
            <h1 className="text-3xl font-bold text-white border-b border-slate-800 pb-3">Introduction to Kyros AI</h1>
            <p className="text-slate-300 leading-relaxed text-sm">
              Kyros AI is an open-source, biologically-inspired persistent memory operating system for autonomous agents. While traditional LLM context windows are static and discard historical context, Kyros dynamically manages memories, resolves identity conflicts, and audits memory chains cryptographically.
            </p>
            <h2 className="text-xl font-bold text-white mt-6">Core Architectures</h2>
            <ul className="list-disc list-inside space-y-2 text-slate-300 text-sm">
              <li><strong>Episodic Module:</strong> Preserves raw interaction histories and chronological conversation lines.</li>
              <li><strong>Semantic Module:</strong> Extracts facts, entities, and relationships into a structured context graph.</li>
              <li><strong>Procedural Module:</strong> Stores task workflows and execution steps to allow reproducible actions.</li>
            </ul>
          </article>
        )}

        {activeSection === "quickstart" && (
          <article className="space-y-6">
            <h1 className="text-3xl font-bold text-white border-b border-slate-800 pb-3">Quickstart Guide</h1>
            <p className="text-slate-300 text-sm">
              Get Kyros up and running locally in less than 60 seconds using Docker Compose.
            </p>
            <h2 className="text-lg font-bold text-white">1. Clone & Run Stack</h2>
            <pre className="p-4 bg-slate-900 border border-slate-800 rounded font-mono text-xs text-slate-300 overflow-x-auto">
{`git clone https://github.com/Kyros-494/kyros-ai
cd kyros-ai
docker compose up -d`}
            </pre>
            <h2 className="text-lg font-bold text-white">2. Set Environment Variables</h2>
            <p className="text-slate-300 text-sm">
              Copy the default template file to activate dev connections:
            </p>
            <pre className="p-4 bg-slate-900 border border-slate-800 rounded font-mono text-xs text-slate-300">
{`cp .env.example .env`}
            </pre>
            <h2 className="text-lg font-bold text-white">3. Access Services</h2>
            <ul className="list-disc list-inside space-y-1 text-slate-300 text-sm">
              <li>API Base URL: <code className="text-blue-400 font-mono">http://localhost:8000</code></li>
              <li>Interactive Swagger Docs: <code className="text-blue-400 font-mono">http://localhost:8000/docs</code></li>
              <li>Developer Dashboard: <code className="text-blue-400 font-mono">http://localhost:8000/dashboard</code></li>
            </ul>
          </article>
        )}

        {activeSection === "concepts" && (
          <article className="space-y-6">
            <h1 className="text-3xl font-bold text-white border-b border-slate-800 pb-3">Core Memory Concepts</h1>
            <h2 className="text-lg font-bold text-white">Ebbinghaus Temporal Decay</h2>
            <p className="text-slate-300 text-sm leading-relaxed">
              To prevent context bloat, memory importance weights degrade over time using the Ebbinghaus forgetting curve formula. Short-term observations decay within a day, whereas persistent facts are structured with a long half-life to stay relevant.
            </p>
            <h2 className="text-lg font-bold text-white">Merkle Tree Audits</h2>
            <p className="text-slate-300 text-sm leading-relaxed">
              Every memory event generates a SHA-256 leaf block appended to a client-specific Merkle Tree. The audit engine crawls the node sequence and checks parent roots to discover external injections or malicious alterations dynamically.
            </p>
            <h2 className="text-lg font-bold text-white">Belief Propagation</h2>
            <p className="text-slate-300 text-sm leading-relaxed">
              When conflicting records are parsed (e.g. user updates backend preference), the belief engine runs graph propagation to degrade confidence score of stale facts and update new entities recursively.
            </p>
          </article>
        )}

        {activeSection === "config" && (
          <article className="space-y-6">
            <h1 className="text-3xl font-bold text-white border-b border-slate-800 pb-3">Configuration Settings</h1>
            <p className="text-slate-300 text-sm">
              Kyros utilizes environment variables for database configurations, security configurations, and LLM integrations.
            </p>
            <table className="w-full text-left border-collapse border border-slate-800 text-sm">
              <thead>
                <tr className="bg-slate-800/40 border-b border-slate-800 font-mono text-xs text-slate-400">
                  <th className="p-3">Variable Name</th>
                  <th className="p-3">Description</th>
                  <th className="p-3">Default Value</th>
                </tr>
              </thead>
              <tbody className="text-slate-300">
                <tr className="border-b border-slate-800">
                  <td className="p-3 font-mono text-xs">KYROS_DATABASE_URL</td>
                  <td className="p-3">PostgreSQL pgvector connection string</td>
                  <td className="p-3 font-mono text-xs">postgresql+asyncpg://...</td>
                </tr>
                <tr className="border-b border-slate-800">
                  <td className="p-3 font-mono text-xs">KYROS_REDIS_URL</td>
                  <td className="p-3">Redis connection URL for context cache</td>
                  <td className="p-3 font-mono text-xs">redis://localhost:6379/0</td>
                </tr>
                <tr className="border-b border-slate-800">
                  <td className="p-3 font-mono text-xs">KYROS_ENVIRONMENT</td>
                  <td className="p-3">Startup mode (development / test / production)</td>
                  <td className="p-3 font-mono text-xs">development</td>
                </tr>
              </tbody>
            </table>
          </article>
        )}

        {activeSection === "selfhost" && (
          <article className="space-y-6">
            <h1 className="text-3xl font-bold text-white border-b border-slate-800 pb-3">Self-Hosting Guide</h1>
            <p className="text-slate-300 text-sm leading-relaxed">
              When hosting Kyros in production or staging servers:
            </p>
            <ul className="list-disc list-inside space-y-2 text-slate-300 text-sm">
              <li><strong>Migrations in Production:</strong> Startup auto-migrations are disabled when <code className="text-blue-400 font-mono">KYROS_ENVIRONMENT=production</code>. Ensure you run migrations as a pre-deploy phase: <code className="text-blue-400 font-mono">alembic upgrade head</code>.</li>
              <li><strong>Row-Level Security:</strong> postgresql uses RLS policies based on tenant context. Always set tenant context when querying the database.</li>
              <li><strong>API Keys Hashing:</strong> Plaintext keys are never stored; database holds SHA-256 hashes for auth validations.</li>
            </ul>
          </article>
        )}

        {activeSection === "python" && (
          <article className="space-y-6">
            <h1 className="text-3xl font-bold text-white border-b border-slate-800 pb-3">Python SDK Reference</h1>
            <p className="text-slate-300 text-sm">
              Install the Python SDK package from source or directly via GitHub:
            </p>
            <pre className="p-4 bg-slate-900 border border-slate-800 rounded font-mono text-xs text-slate-300">
{`pip install git+https://github.com/Kyros-494/kyros-ai.git#subdirectory=sdks/python`}
            </pre>
            <h2 className="text-lg font-bold text-white">Initialization</h2>
            <pre className="p-4 bg-slate-900 border border-slate-800 rounded font-mono text-xs text-slate-300">
{`from kyros import KyrosClient

client = KyrosClient(
    api_key="mk_live_default_dev_key_123456",
    base_url="http://localhost:8000"
)`}
            </pre>
            <h2 className="text-lg font-bold text-white">Methods</h2>
            <ul className="list-disc list-inside space-y-1 text-slate-300 text-sm">
              <li><code className="text-blue-400 font-mono">client.remember(agent_id, content)</code>: Ingest memory block</li>
              <li><code className="text-blue-400 font-mono">client.recall(agent_id, query)</code>: Semantic search</li>
              <li><code className="text-blue-400 font-mono">client.audit_integrity(agent_id)</code>: Validate Merkle hash</li>
            </ul>
          </article>
        )}

        {activeSection === "typescript" && (
          <article className="space-y-6">
            <h1 className="text-3xl font-bold text-white border-b border-slate-800 pb-3">TypeScript SDK Reference</h1>
            <p className="text-slate-300 text-sm">
              Add the SDK dependency reference in your <code className="text-blue-400 font-mono">package.json</code>:
            </p>
            <pre className="p-4 bg-slate-900 border border-slate-800 rounded font-mono text-xs text-slate-300">
{`"@kyros.494/sdk": "file:../kyros-ai/sdks/typescript"`}
            </pre>
            <h2 className="text-lg font-bold text-white">Initialization</h2>
            <pre className="p-4 bg-slate-900 border border-slate-800 rounded font-mono text-xs text-slate-300">
{`import { KyrosClient } from '@kyros.494/sdk';

const client = new KyrosClient({
  apiKey: 'mk_live_default_dev_key_123456',
  baseUrl: 'http://localhost:8000'
});`}
            </pre>
          </article>
        )}

        {activeSection === "integrations" && (
          <article className="space-y-6">
            <h1 className="text-3xl font-bold text-white border-b border-slate-800 pb-3">LLM Provider Integrations</h1>
            <p className="text-slate-300 text-sm">
              Kyros routes causal graph updates and archival logic to LLM providers based on configured environment variables:
            </p>
            <pre className="p-4 bg-slate-900 border border-slate-800 rounded font-mono text-xs text-slate-300 overflow-x-auto">
{`# Providers keys
OPENAI_API_KEY=sk-proj-...
GEMINI_API_KEY=AIzaSy...
ANTHROPIC_API_KEY=sk-ant-...
MISTRAL_API_KEY=yourKeyHere...`}
            </pre>
            <p className="text-slate-300 text-sm leading-relaxed">
              If multiple provider keys are loaded, the gateway prioritizes routing API queries in the following sequence: Mistral, Gemini, OpenAI, Anthropic.
            </p>
          </article>
        )}
      </main>
    </div>
  );
}
