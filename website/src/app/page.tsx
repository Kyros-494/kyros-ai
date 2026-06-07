"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";

export default function Home() {
  // Playground State
  const [activePlaygroundTab, setActivePlaygroundTab] = useState<"episodic" | "semantic" | "procedural">("episodic");
  
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
    { id: "fact-2", subject: "user_1", predicate: "preference_backend", object: "Python", confidence: 0.95, status: "stable" },
    { id: "fact-3", subject: "user_1", predicate: "preference_db", object: "PostgreSQL", confidence: 0.92, status: "stable" },
  ]);
  const [conflictTriggered, setConflictTriggered] = useState(false);

  // Procedural Memory Simulator State
  const [runningProcedure, setRunningProcedure] = useState(false);
  const [currentProcedureStep, setCurrentProcedureStep] = useState(-1);
  const procedureSteps = [
    { name: "Query existing context", desc: "Retrieve agent's current state and active tasks" },
    { name: "Verify memory cryptographic proofs", desc: "Validate SHA-256 signatures via Merkle tree" },
    { name: "Calculate Ebbinghaus decay curve", desc: "Update weights based on temporal half-life parameters" },
    { name: "Execute model belief propagation", desc: "Propagate changes through the semantic graph" },
  ];

  // Code Tab state
  const [activeCodeTab, setActiveCodeTab] = useState<"python" | "typescript" | "docker">("python");

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
    setSemanticFacts(prev =>
      prev.map(fact => {
        if (fact.predicate === "name") {
          return { ...fact, confidence: 0.12, status: "decayed" };
        }
        if (fact.predicate === "preference_backend") {
          return { ...fact, confidence: 0.22, status: "decayed" };
        }
        return fact;
      })
    );

    setTimeout(() => {
      setSemanticFacts(prev => [
        ...prev,
        { id: "fact-4", subject: "user_1", predicate: "name", object: "Bob", confidence: 0.99, status: "updated" },
        { id: "fact-5", subject: "user_1", predicate: "preference_backend", object: "Go", confidence: 0.97, status: "updated" },
      ]);
    }, 800);
  };

  const handleResetSemantic = () => {
    setConflictTriggered(false);
    setSemanticFacts([
      { id: "fact-1", subject: "user_1", predicate: "name", object: "Alice", confidence: 0.98, status: "stable" },
      { id: "fact-2", subject: "user_1", predicate: "preference_backend", object: "Python", confidence: 0.95, status: "stable" },
      { id: "fact-3", subject: "user_1", predicate: "preference_db", object: "PostgreSQL", confidence: 0.92, status: "stable" },
    ]);
  };

  // Handle Procedural execution simulation
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (runningProcedure) {
      if (currentProcedureStep < procedureSteps.length - 1) {
        timer = setTimeout(() => {
          setCurrentProcedureStep(prev => prev + 1);
        }, 1200);
      } else {
        timer = setTimeout(() => {
          setRunningProcedure(false);
          setCurrentProcedureStep(-1);
        }, 1500);
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
    <div className="flex flex-col min-h-full bg-slate-900 text-slate-100 font-sans">
      
      {/* Hero Section */}
      <header className="max-w-4xl mx-auto px-6 pt-24 pb-16 text-center flex flex-col items-center">
        <h1 className="text-4xl sm:text-6xl font-bold tracking-tight text-white leading-tight font-sans">
          Persistent Memory Operating System for AI Agents
        </h1>

        <p className="mt-6 max-w-2xl text-lg text-slate-400 leading-relaxed">
          Provide your autonomous agents with biological-inspired memory structures: Episodic events, semantic facts, and procedural skills. Securely audited with cryptographic integrity and structured with natural decay parameters.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row gap-4 items-center">
          <a
            href="https://github.com/Kyros-494/kyros-ai"
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-3 rounded-md bg-blue-600 hover:bg-blue-500 text-white font-medium tracking-wide transition-all shadow-md"
          >
            Get Started on GitHub
          </a>
          <Link
            href="/docs"
            className="px-6 py-3 rounded-md border border-slate-700 text-slate-300 font-medium bg-slate-800 hover:bg-slate-700 transition-colors"
          >
            View Documentation
          </Link>
        </div>
      </header>

      {/* Capabilities Stats Grid (Metrics-Free) */}
      <section className="border-y border-slate-800 bg-slate-800/40">
        <div className="max-w-6xl mx-auto px-6 py-12 grid grid-cols-2 sm:grid-cols-4 gap-8 text-center">
          {[
            { value: "3 Modules", label: "Episodic, Semantic, Procedural" },
            { value: "0-Config", label: "Auto-Migration Startup" },
            { value: "Apache 2.0", label: "Permissive Licensing" },
            { value: "Python & TS", label: "Native Client SDKs" },
          ].map((stat) => (
            <div key={stat.label} className="flex flex-col items-center">
              <span className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                {stat.value}
              </span>
              <span className="mt-2 text-xs font-mono uppercase tracking-wider text-slate-500">
                {stat.label}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* Interactive Simulator Section */}
      <section className="max-w-5xl mx-auto px-6 py-24 w-full">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-white tracking-tight">
            Interactive Memory Playground
          </h2>
          <p className="mt-3 text-slate-400 max-w-xl mx-auto">
            Interact with the client-side simulator to see how Kyros parses, secures, decays, and propagates state in real time. Or view the full sandbox on the <Link href="/simulation" className="text-blue-400 hover:underline">Simulation Page</Link>.
          </p>
        </div>

        <div className="border border-slate-800 rounded-xl bg-slate-800/50 overflow-hidden shadow-xl">
          {/* Playground Tabs */}
          <div className="flex border-b border-slate-800 bg-slate-800/80 text-sm">
            {[
              { id: "episodic", label: "Episodic Logger" },
              { id: "semantic", label: "Semantic Graph" },
              { id: "procedural", label: "Procedural Workflows" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActivePlaygroundTab(tab.id as any)}
                className={`flex-1 py-4 text-center font-medium transition-all ${
                  activePlaygroundTab === tab.id
                    ? "text-blue-400 bg-slate-900 border-b-2 border-blue-500"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="p-6 bg-slate-900 min-h-[350px]">
            {/* Episodic Simulator */}
            {activePlaygroundTab === "episodic" && (
              <div className="space-y-6">
                <form onSubmit={handleAddEpisodic} className="flex gap-3">
                  <input
                    type="text"
                    value={episodicInput}
                    onChange={(e) => setEpisodicInput(e.target.value)}
                    placeholder="Enter raw event (e.g. 'User prefers strict typing.')"
                    className="flex-1 px-4 py-3 rounded-md bg-slate-800 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 text-sm"
                  />
                  <button
                    type="submit"
                    className="px-5 py-3 rounded-md bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm transition-colors"
                  >
                    Remember Event
                  </button>
                </form>

                <div className="space-y-3">
                  <span className="text-xs font-mono uppercase tracking-wider text-slate-500 block">
                    Episodic Logs (Tamper-evident, hashed sequence)
                  </span>
                  {episodicMemories.map((mem) => (
                    <div
                      key={mem.id}
                      className="p-4 rounded-md border border-slate-800 bg-slate-800/30 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 text-sm hover:border-slate-700 transition-colors"
                    >
                      <div className="space-y-1.5 flex-1">
                        <p className="text-slate-200">{mem.content}</p>
                        <div className="flex flex-wrap gap-4 text-xs font-mono text-slate-500">
                          <span>Stored: {mem.timestamp}</span>
                          <span className="text-blue-400/80 font-mono">Hash: {mem.hash.substring(0, 16)}...</span>
                        </div>
                      </div>
                      <div className="flex flex-col items-end shrink-0">
                        <span className="text-xs font-mono text-slate-400">Decay Weight</span>
                        <span className="text-lg font-bold text-emerald-400 font-mono">
                          {mem.decay}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Semantic Simulator */}
            {activePlaygroundTab === "semantic" && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-mono uppercase tracking-wider text-slate-500">
                    Semantic Facts Database
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={handleTriggerConflict}
                      disabled={conflictTriggered}
                      className="px-4 py-2 rounded-md bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-300 font-medium text-xs transition-colors"
                    >
                      Simulate Identity Conflict
                    </button>
                    {conflictTriggered && (
                      <button
                        onClick={handleResetSemantic}
                        className="px-4 py-2 rounded-md bg-slate-800 border border-slate-700 hover:bg-slate-700 text-slate-400 font-medium text-xs transition-colors"
                      >
                        Reset Facts
                      </button>
                    )}
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm border-collapse">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-500 font-mono text-xs">
                        <th className="py-3 px-4">Subject</th>
                        <th className="py-3 px-4">Predicate</th>
                        <th className="py-3 px-4">Object</th>
                        <th className="py-3 px-4 text-right">Confidence</th>
                        <th className="py-3 px-4 text-right">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {semanticFacts.map((fact) => (
                        <tr
                          key={fact.id}
                          className={`border-b border-slate-800 transition-colors ${
                            fact.status === "updated"
                              ? "bg-emerald-950/20 text-emerald-300"
                              : fact.status === "decayed"
                              ? "bg-rose-950/10 text-slate-500"
                              : "text-slate-300"
                          }`}
                        >
                          <td className="py-3.5 px-4 font-mono text-xs">{fact.subject}</td>
                          <td className="py-3.5 px-4 font-mono text-xs text-blue-400">{fact.predicate}</td>
                          <td className="py-3.5 px-4 font-medium">{fact.object}</td>
                          <td className="py-3.5 px-4 text-right font-mono text-xs">
                            {(fact.confidence * 100).toFixed(0)}%
                          </td>
                          <td className="py-3.5 px-4 text-right">
                            <span
                              className={`inline-block px-2 py-0.5 rounded-full text-xs font-mono uppercase tracking-wider ${
                                fact.status === "updated"
                                  ? "bg-emerald-500/20 text-emerald-400"
                                  : fact.status === "decayed"
                                  ? "bg-rose-500/10 text-rose-400"
                                  : "bg-slate-800 text-slate-400"
                              }`}
                            >
                              {fact.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {conflictTriggered && (
                  <div className="p-4 rounded-md border border-slate-700 bg-slate-800/40 text-xs text-slate-300 font-mono leading-relaxed">
                    [Belief Propagation Engine]: Detected name update to &quot;Bob&quot; and backend language change to &quot;Go&quot;. Conflicting context scores updated. Old facts marked for decay pruning.
                  </div>
                )}
              </div>
            )}

            {/* Procedural Simulator */}
            {activePlaygroundTab === "procedural" && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <div className="space-y-1">
                    <span className="text-xs font-mono uppercase tracking-wider text-slate-500 block">
                      Workflow execution pipeline
                    </span>
                    <p className="text-sm text-slate-300 font-medium">Procedure: handle_user_context</p>
                  </div>
                  <button
                    onClick={handleRunProcedure}
                    disabled={runningProcedure}
                    className="px-4 py-2 rounded-md bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium text-xs transition-colors"
                  >
                    {runningProcedure ? "Running workflow..." : "Execute workflow"}
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  {procedureSteps.map((step, idx) => {
                    const isCompleted = idx < currentProcedureStep;
                    const isActive = idx === currentProcedureStep;
                    return (
                      <div
                        key={step.name}
                        className={`p-4 rounded-md border transition-all ${
                          isActive
                            ? "border-blue-500 bg-blue-950/20"
                            : isCompleted
                            ? "border-emerald-800 bg-emerald-950/5"
                            : "border-slate-800 bg-slate-800/20"
                        }`}
                      >
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-xs font-mono font-bold text-slate-500">STEP 0{idx + 1}</span>
                          {isCompleted && (
                            <span className="w-2 h-2 rounded-full bg-emerald-500" />
                          )}
                          {isActive && (
                            <span className="w-2 h-2 rounded-full bg-blue-500 animate-ping" />
                          )}
                        </div>
                        <h4 className={`text-sm font-semibold mb-1 ${isActive ? "text-blue-400" : isCompleted ? "text-emerald-400" : "text-slate-300"}`}>
                          {step.name}
                        </h4>
                        <p className="text-xs text-slate-500 leading-relaxed">{step.desc}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Feature Cards Grid (SVG Icons, solid branding) */}
      <section className="max-w-6xl mx-auto px-6 py-24 border-t border-slate-800">
        <h2 className="text-3xl font-bold text-white text-center mb-16 tracking-tight">
          System Specifications & Features
        </h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            {
              title: "Three Memory Modules",
              desc: "Episodic (conversations), semantic (structured facts), and procedural (predefined workflows) subsystems integrated within a unified architecture.",
              icon: (
                <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              ),
            },
            {
              title: "Ebbinghaus Temporal Decay",
              desc: "Memories fade dynamically according to category decay rates. Prevents token bloat, keeps search queries relevant, and optimizes context windows.",
              icon: (
                <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              ),
            },
            {
              title: "Cryptographic Tamper Auditing",
              desc: "Protects memory chains using SHA-256 hashes and Merkle tree verification logic. Instantly detects external injections and poisoning attacks.",
              icon: (
                <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              ),
            },
            {
              title: "Causal Relationship Chains",
              desc: "Establishes explicit parent-child links between independent memory nodes, allowing the agent to audit reasoning chains and trace causality.",
              icon: (
                <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 12l3-3 3 3 4-4M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              ),
            },
            {
              title: "Adaptive Belief Propagation",
              desc: "Graph-based conflict resolution updating network confidence states iteratively using breadth-first traversal whenever new info is parsed.",
              icon: (
                <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H17" />
                </svg>
              ),
            },
            {
              title: "Zero-Code API Proxy Mode",
              desc: "Point an existing LLM wrapper base_url directly to the Kyros proxy server. Intercepts request payloads to inject and log context automatically.",
              icon: (
                <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              ),
            },
          ].map((f) => (
            <div
              key={f.title}
              className="p-6 rounded-lg border border-slate-800 bg-slate-800/20 hover:border-slate-700 hover:bg-slate-800/40 transition-all animate-fade-in"
            >
              <div className="mb-4">{f.icon}</div>
              <h3 className="font-semibold text-white mb-2 text-base">
                {f.title}
              </h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                {f.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Integration Code Blocks / Tabs */}
      <section id="quickstart" className="border-t border-slate-800 bg-slate-900/50">
        <div className="max-w-4xl mx-auto px-6 py-24">
          <h2 className="text-3xl font-bold text-white text-center mb-4 tracking-tight">
            Up in 60 Seconds
          </h2>
          <p className="text-center text-slate-400 mb-12 max-w-lg mx-auto">
            Self-host the memory server using Docker or deploy the Python and TypeScript SDK wrapper.
          </p>

          <div className="border border-slate-800 rounded-lg overflow-hidden bg-slate-800/40 shadow-xl">
            {/* Code Tabs */}
            <div className="flex border-b border-slate-800 bg-slate-800/60 px-4">
              {[
                { id: "docker", label: "Self-Host (Docker)" },
                { id: "python", label: "Python SDK" },
                { id: "typescript", label: "TypeScript SDK" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveCodeTab(tab.id as any)}
                  className={`py-3.5 px-4 font-mono text-xs font-semibold border-b-2 transition-all ${
                    activeCodeTab === tab.id
                      ? "text-blue-400 border-blue-500"
                      : "text-slate-500 hover:text-slate-300 border-transparent"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Code Content */}
            <div className="p-6 bg-slate-900/80 font-mono text-xs text-slate-300 leading-relaxed overflow-x-auto">
              {activeCodeTab === "docker" && (
                <pre>
                  <code>{`# Clone the repository
git clone https://github.com/Kyros-494/kyros-ai
cd kyros-ai

# Start the PostgreSQL + pgvector + Redis container stacks
docker compose up -d

# API server running on: http://localhost:8000
# Visual Dashboard: http://localhost:8000/dashboard
# Dev API Key: mk_live_default_dev_key_123456`}</code>
                </pre>
              )}

              {activeCodeTab === "python" && (
                <pre>
                  <code>{`# Install dependencies
pip install kyros-sdk

# Initialize client
import kyros
client = kyros.Client(
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
                <pre>
                  <code>{`// Install dependencies
npm install @kyros/sdk

// Initialize client
import { KyrosClient } from '@kyros/sdk';
const client = new KyrosClient({
  baseUrl: 'http://localhost:8000',
  apiKey: 'mk_live_default_dev_key_123456'
});

// Store and recall memories
await client.storeEpisode({
  agentId: 'agent-1',
  content: 'User prefers strict typing.'
});

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
