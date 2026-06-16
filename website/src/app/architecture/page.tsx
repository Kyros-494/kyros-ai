"use client";

import React, { useState } from "react";

export default function ArchitecturePage() {
  const [activeFlow, setActiveFlow] = useState<"none" | "store" | "recall">("none");

  const runFlow = (flow: "store" | "recall") => {
    setActiveFlow("none");
    // Trigger animation flow
    setTimeout(() => {
      setActiveFlow(flow);
    }, 50);
  };

  const layers = [
    {
      name: "Client Ingestion Layer",
      desc: "Native Python & TypeScript client SDK wrappers handle request formatting and incorporate robust exponential backoff connection retry loops for API stability.",
      details: ["HTTP Request Retry", "Client Authorization", "Bitemporal Parameter Bindings"]
    },
    {
      name: "Gateway Security Layer",
      desc: "FastAPI router matches routes, validates X-API-Key and Bearer tokens via Auth Middleware, and bypasses public playground endpoints.",
      details: ["Token Validation Middleware", "Rate Limiter Gateways", "Public Assets Bypass"]
    },
    {
      name: "Intelligence Engine Layer",
      desc: "Orchestrates cognitive memory services: calculates forgetting curves, constructs Merkle Tree proofs, and runs BFS graph belief resolution updates.",
      details: ["Ebbinghaus Decay Calculator", "Merkle Tree Proof Maker", "Belief BFS Propagation"]
    },
    {
      name: "Hybrid Storage Layer",
      desc: "Stores raw memory records, vector embeddings, and relationships into PostgreSQL with pgvector. Caches hot query indexes dynamically in Redis.",
      details: ["PostgreSQL + pgvector", "Redis Hot Key-Value Cache", "Row-Level Security Policies"]
    }
  ];

  return (
    <div className="max-w-6xl mx-auto px-6 py-12 bg-black text-slate-100 flex-1 w-full space-y-16">
      
      {/* Header */}
      <header className="space-y-4 max-w-2xl">
        <h1 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">System Architecture & Dataflow</h1>
        <p className="text-slate-400 text-sm leading-relaxed">
          Kyros manages agent memory ingestion, cryptographic auditing, and hybrid storage scaling inside a multi-tier low-latency network.
        </p>
      </header>

      {/* Interactive SVG Diagram Control Panel */}
      <section className="space-y-6">
        <div className="flex justify-between items-center flex-wrap gap-4">
          <div>
            <h2 className="text-xl font-bold text-white">Interactive Dataflow Visualizer</h2>
            <p className="text-xs text-slate-400">Click a data flow to animate the pipeline path.</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => runFlow("store")}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded font-medium text-xs transition-colors"
            >
              Animate Store Flow
            </button>
            <button
              onClick={() => runFlow("recall")}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 rounded font-medium text-xs transition-colors"
            >
              Animate Recall Flow
            </button>
            <button
              onClick={() => setActiveFlow("none")}
              className="px-3 py-2 bg-slate-900 text-slate-500 hover:text-slate-400 text-xs font-mono"
            >
              Clear
            </button>
          </div>
        </div>

        {/* Animated SVG Diagram */}
        <div className="border border-slate-800 bg-slate-850 p-8 rounded-lg flex justify-center items-center overflow-x-auto">
          <svg width="760" height="180" viewBox="0 0 760 180" className="w-full max-w-3xl">
            {/* Definitions for animations */}
            <defs>
              <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569" />
              </marker>
            </defs>

            {/* Connecting Paths */}
            {/* Path 1: SDK -> Gateway */}
            <path d="M 120 90 L 220 90" stroke="#334155" strokeWidth="2" fill="none" markerEnd="url(#arrow)" />
            {/* Path 2: Gateway -> Engine */}
            <path d="M 340 90 L 440 90" stroke="#334155" strokeWidth="2" fill="none" markerEnd="url(#arrow)" />
            {/* Path 3: Engine -> Storage */}
            <path d="M 560 90 L 660 90" stroke="#334155" strokeWidth="2" fill="none" markerEnd="url(#arrow)" />

            {/* Ingestion Animation Flow */}
            {activeFlow === "store" && (
              <>
                <circle r="5" fill="#ff4a00">
                  <animateMotion dur="2s" repeatCount="indefinite" path="M 120 90 L 220 90 L 340 90 L 440 90 L 560 90 L 660 90" />
                </circle>
              </>
            )}

            {/* Recall Animation Flow */}
            {activeFlow === "recall" && (
              <>
                {/* Data query path */}
                <circle r="5" fill="#ff916a">
                  <animateMotion dur="1.8s" repeatCount="indefinite" path="M 120 90 L 220 90 L 340 90 L 440 90 L 560 90 L 660 90" />
                </circle>
                {/* Returned context path */}
                <circle r="5" fill="#ffdcd0">
                  <animateMotion dur="1.8s" repeatCount="indefinite" path="M 660 90 L 560 90 L 440 90 L 340 90 L 220 90 L 120 90" />
                </circle>
              </>
            )}

            {/* Block 1: Client SDKs */}
            <rect x="10" y="40" width="110" height="100" rx="8" fill="#1e293b" stroke="#475569" strokeWidth="1" />
            <text x="65" y="85" fill="#ffffff" fontSize="12" fontWeight="bold" textAnchor="middle" fontFamily="sans-serif">Client SDKs</text>
            <text x="65" y="105" fill="#64748b" fontSize="9" textAnchor="middle" fontFamily="monospace">Python / TS</text>

            {/* Block 2: Gateway Security */}
            <rect x="220" y="40" width="120" height="100" rx="8" fill="#1e293b" stroke="#475569" strokeWidth="1" />
            <text x="280" y="85" fill="#ffffff" fontSize="12" fontWeight="bold" textAnchor="middle" fontFamily="sans-serif">Gateway & Auth</text>
            <text x="280" y="105" fill="#64748b" fontSize="9" textAnchor="middle" fontFamily="monospace">FastAPI Middleware</text>

            {/* Block 3: Cognitive Engine */}
            <rect x="440" y="40" width="120" height="100" rx="8" fill="#1e293b" stroke="#475569" strokeWidth="1" />
            <text x="500" y="80" fill="#ffffff" fontSize="12" fontWeight="bold" textAnchor="middle" fontFamily="sans-serif">Memory Engine</text>
            <text x="500" y="98" fill="#64748b" fontSize="9" textAnchor="middle" fontFamily="monospace">Decay & Belief</text>
            <text x="500" y="112" fill="#64748b" fontSize="9" textAnchor="middle" fontFamily="monospace">Merkle Audits</text>

            {/* Block 4: Hybrid Databases */}
            <rect x="660" y="40" width="90" height="100" rx="8" fill="#1e293b" stroke="#475569" strokeWidth="1" />
            <text x="705" y="80" fill="#ffffff" fontSize="12" fontWeight="bold" textAnchor="middle" fontFamily="sans-serif">Databases</text>
            <text x="705" y="98" fill="#64748b" fontSize="9" textAnchor="middle" fontFamily="monospace">PG + vector</text>
            <text x="705" y="112" fill="#64748b" fontSize="9" textAnchor="middle" fontFamily="monospace">Redis Cache</text>
          </svg>
        </div>
      </section>

      {/* Detailed Architectural Specifications */}
      <section className="grid sm:grid-cols-2 gap-8 border-t border-slate-800 pt-16">
        {layers.map((l) => (
          <div key={l.name} className="space-y-3">
            <h3 className="text-lg font-bold text-white">{l.name}</h3>
            <p className="text-sm text-slate-400 leading-relaxed">{l.desc}</p>
            <div className="flex flex-wrap gap-2 pt-1">
              {l.details.map((detail) => (
                <span key={detail} className="px-2 py-1 bg-slate-800 text-slate-300 font-mono text-xxs rounded border border-slate-750">
                  {detail}
                </span>
              ))}
            </div>
          </div>
        ))}
      </section>

    </div>
  );
}
