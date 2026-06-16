"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";

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
  const procedureSteps = [
    { name: "Query context", desc: "Retrieve active task context & state" },
    { name: "Verify signatures", desc: "Validate Merkle tree cryptographic integrity" },
    { name: "Apply decay", desc: "Calculate forgetting curve coefficients" },
    { name: "Propagate beliefs", desc: "Resolve graph contradictions" },
  ];

<<<<<<< Updated upstream
=======
  // Code Tab state
  const [activeCodeTab, setActiveCodeTab] = useState<"python" | "typescript" | "docker">("python");

  // Architecture hover state
  const [hoveredArchNode, setHoveredArchNode] = useState<string | null>(null);

>>>>>>> Stashed changes
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
          return { ...fact, confidence: 0.12, status: "conflict" };
        }
        if (fact.predicate === "prefers_backend") {
          return { ...fact, confidence: 0.22, status: "conflict" };
        }
        return fact;
      })
    );

    setTimeout(() => {
      setSemanticFacts(prev => [
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
          setCurrentProcedureStep(prev => prev + 1);
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
<<<<<<< Updated upstream
    <div className="relative w-full min-h-full bg-zinc-950 text-zinc-100 bg-grid-pattern pb-24">
      {/* Background glow effects */}
      <div className="absolute top-0 left-1/4 w-[50%] h-[35%] rounded-full bg-cyan-500/10 blur-3xl opacity-35 pointer-events-none animate-pulse-glow" />
      <div className="absolute top-1/3 right-1/4 w-[40%] h-[40%] rounded-full bg-purple-500/5 blur-3xl opacity-25 pointer-events-none" />

      {/* Hero Section */}
      <header className="relative max-w-6xl mx-auto px-6 pt-28 pb-20 text-center flex flex-col items-center">
        {/* Release badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-cyan-500/20 bg-cyan-500/5 text-xs font-medium text-cyan-400 mb-8 animate-fade-in shadow-[0_0_15px_rgba(6,182,212,0.05)]">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
          Introducing Kyros v0.1.0 (Persistent Memory Engine)
        </div>

        <h1 className="text-4xl sm:text-7xl font-bold tracking-tight text-white leading-[1.1] max-w-4xl font-sans text-glow">
          Persistent memory for <span className="bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 bg-clip-text text-transparent">autonomous AI agents</span>
        </h1>

        <p className="mt-8 max-w-2xl text-base sm:text-lg text-zinc-400 leading-relaxed font-normal">
          Provide your agents with biological-inspired memory structures: Episodic log streams, semantic graphs, and procedural workflows. Audited with cryptographic integrity and structured with natural temporal decay.
=======
    <div className="flex flex-col min-h-full bg-black text-slate-100 font-sans selection:bg-blue-500/30">
      
      {/* Decorative Grid Overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#0c0c0e_1px,transparent_1px),linear-gradient(to_bottom,#0c0c0e_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none z-0" />

      {/* Hero Section */}
      <header className="relative max-w-4xl mx-auto px-6 pt-32 pb-20 text-center flex flex-col items-center z-10">
        {/* Logo Container */}
        <div className="mb-8 flex justify-center">
          <Image
            src="/kyros-logo.png"
            alt="Kyros Logo"
            width={72}
            height={72}
            className="object-contain"
          />
        </div>

        {/* Brand Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-blue-500/30 bg-blue-950/20 text-xs font-semibold text-blue-400 font-mono mb-8 backdrop-blur-sm">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
          Kyros Persistent Memory Engine
        </div>

        <h1 className="text-4xl sm:text-7xl font-bold tracking-tight text-white leading-tight font-sans">
          Give AI Agents
          <span className="block mt-2 bg-gradient-to-r from-blue-400 via-blue-500 to-blue-600 bg-clip-text text-transparent">
            Persistent Memory
          </span>
        </h1>

        <p className="mt-8 max-w-2xl text-lg text-slate-400 leading-relaxed font-sans">
          An open-source, biologically-inspired memory operating system. Partition agent state across episodic logs, semantic facts, and procedural workflows with cryptographic integrity audits and natural decay parameters.
>>>>>>> Stashed changes
        </p>

        <div className="mt-12 flex flex-col sm:flex-row gap-4 items-center w-full sm:w-auto">
          <Link
            href="/docs"
            className="w-full sm:w-auto px-8 py-4 rounded bg-blue-600 hover:bg-blue-500 text-white font-medium tracking-wide transition-all shadow-lg hover:shadow-blue-500/20 text-center"
          >
            Read Documentation
          </Link>
          <a
            href="https://github.com/Kyros-494/kyros-ai"
            target="_blank"
            rel="noopener noreferrer"
<<<<<<< Updated upstream
            className="px-6 py-3 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-medium text-sm tracking-wide transition-all shadow-[0_4px_20px_rgba(6,182,212,0.25)] hover:scale-[1.02]"
=======
            className="w-full sm:w-auto px-8 py-4 rounded border border-slate-800 text-slate-300 font-medium bg-slate-900/60 hover:bg-slate-900 transition-colors text-center"
>>>>>>> Stashed changes
          >
            GitHub Repository
          </a>
<<<<<<< Updated upstream
          <Link
            href="/docs"
            className="px-6 py-3 rounded-full border border-zinc-800 text-zinc-300 font-medium text-sm bg-zinc-900/50 hover:bg-zinc-900 transition-colors backdrop-blur-sm"
          >
            View Documentation
          </Link>
=======
>>>>>>> Stashed changes
        </div>
      </header>

      {/* Capabilities Stats Grid */}
<<<<<<< Updated upstream
      <section className="relative max-w-6xl mx-auto px-6 py-8 mb-20">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { value: "3 Modules", label: "Episodic, Semantic, Procedural" },
            { value: "0-Config", label: "Auto-Migration Startup" },
            { value: "Apache 2.0", label: "Permissive Open Source Core" },
=======
      <section className="relative border-y border-slate-850 bg-slate-900/20 z-10">
        <div className="max-w-6xl mx-auto px-6 py-12 grid grid-cols-2 sm:grid-cols-4 gap-8 text-center">
          {[
            { value: "3 Modules", label: "Episodic, Semantic, Procedural" },
            { value: "0-Config", label: "Auto-Migration Startup" },
            { value: "Apache 2.0", label: "Permissive Open Source" },
>>>>>>> Stashed changes
            { value: "Python & TS", label: "Native Client SDKs" },
          ].map((stat) => (
            <div key={stat.label} className="p-6 rounded-2xl border border-zinc-900 bg-zinc-900/20 backdrop-blur-sm flex flex-col justify-center">
              <span className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                {stat.value}
              </span>
              <span className="mt-1 text-[10px] font-mono uppercase tracking-wider text-zinc-500">
                {stat.label}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* Interactive System Architecture Diagram */}
      <section className="relative max-w-5xl mx-auto px-6 py-28 w-full z-10">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-white tracking-tight">
            System Architecture
          </h2>
          <p className="mt-4 text-slate-400 max-w-xl mx-auto">
            Kyros acts as a secure mediation layer between your autonomous agents and the underlying persistent vector and graph database instances.
          </p>
        </div>

        <div className="border border-slate-850 rounded-xl bg-slate-900/30 p-8 backdrop-blur-sm shadow-2xl relative overflow-hidden flex flex-col items-center">
          <div className="w-full max-w-3xl aspect-[16/9] relative">
            <svg viewBox="0 0 800 450" className="w-full h-full text-slate-500 select-none">
              {/* Definitions */}
              <defs>
                <linearGradient id="blueGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#ff7c4d" />
                  <stop offset="100%" stopColor="#ff4a00" />
                </linearGradient>
                <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor" />
                </marker>
              </defs>

              {/* Ingestion Stream */}
              <g 
                className="cursor-pointer"
                onMouseEnter={() => setHoveredArchNode("ingestion")}
                onMouseLeave={() => setHoveredArchNode(null)}
              >
                <rect 
                  x="40" y="180" width="160" height="90" rx="6" 
                  fill={hoveredArchNode === "ingestion" ? "#121214" : "#09090b"} 
                  stroke={hoveredArchNode === "ingestion" ? "#ff4a00" : "#27272a"} 
                  strokeWidth="1.5"
                  className="transition-all duration-300"
                />
                <text x="120" y="225" fill="#ffffff" textAnchor="middle" fontWeight="bold" fontSize="14">Agent / LLM Proxy</text>
                <text x="120" y="245" fill="#a1a1aa" textAnchor="middle" fontSize="11" fontFamily="monospace">Remember / Recall API</text>
              </g>

              {/* Connections to Engine */}
              <path d="M 200 225 L 300 225" stroke={hoveredArchNode === "ingestion" ? "#ff4a00" : "#27272a"} strokeWidth="1.5" markerEnd="url(#arrow)" className="transition-all duration-300" />

              {/* Kyros Engine Core */}
              <g 
                className="cursor-pointer"
                onMouseEnter={() => setHoveredArchNode("engine")}
                onMouseLeave={() => setHoveredArchNode(null)}
              >
                <rect 
                  x="310" y="80" width="180" height="290" rx="8" 
                  fill={hoveredArchNode === "engine" ? "#141416" : "#080808"} 
                  stroke={hoveredArchNode === "engine" ? "#ff4a00" : "#27272a"} 
                  strokeWidth="2"
                  className="transition-all duration-300"
                />
                <text x="400" y="115" fill="#ffffff" textAnchor="middle" fontWeight="bold" fontSize="15">Kyros Memory Engine</text>
                
                {/* Internal components */}
                <rect x="330" y="140" width="140" height="45" rx="4" fill="#18181b" stroke="#27272a" />
                <text x="400" y="167" fill="#ff4a00" textAnchor="middle" fontSize="12" fontWeight="500">Episodic Logger</text>

                <rect x="330" y="205" width="140" height="45" rx="4" fill="#18181b" stroke="#27272a" />
                <text x="400" y="232" fill="#ff4a00" textAnchor="middle" fontSize="12" fontWeight="500">Semantic Graph</text>

                <rect x="330" y="270" width="140" height="45" rx="4" fill="#18181b" stroke="#27272a" />
                <text x="400" y="297" fill="#ff4a00" textAnchor="middle" fontSize="12" fontWeight="500">Procedural Skills</text>
                
                <text x="400" y="345" fill="#52525b" textAnchor="middle" fontSize="10" fontFamily="monospace">Merkle Integrity Audits</text>
              </g>

              {/* Connections to Storage */}
              <path d="M 490 175 L 590 175" stroke={hoveredArchNode === "engine" || hoveredArchNode === "vector" ? "#ff4a00" : "#27272a"} strokeWidth="1.5" markerEnd="url(#arrow)" className="transition-all duration-300" />
              <path d="M 490 275 L 590 275" stroke={hoveredArchNode === "engine" || hoveredArchNode === "graph" ? "#ff4a00" : "#27272a"} strokeWidth="1.5" markerEnd="url(#arrow)" className="transition-all duration-300" />

              {/* Vector Storage */}
              <g 
                className="cursor-pointer"
                onMouseEnter={() => setHoveredArchNode("vector")}
                onMouseLeave={() => setHoveredArchNode(null)}
              >
                <rect 
                  x="600" y="120" width="160" height="90" rx="6" 
                  fill={hoveredArchNode === "vector" ? "#121214" : "#09090b"} 
                  stroke={hoveredArchNode === "vector" ? "#ff4a00" : "#27272a"} 
                  strokeWidth="1.5"
                  className="transition-all duration-300"
                />
                <text x="680" y="165" fill="#ffffff" textAnchor="middle" fontWeight="bold" fontSize="13">pgvector Database</text>
                <text x="680" y="185" fill="#a1a1aa" textAnchor="middle" fontSize="10" fontFamily="monospace">Vector Index & Logs</text>
              </g>

              {/* Graph Storage */}
              <g 
                className="cursor-pointer"
                onMouseEnter={() => setHoveredArchNode("graph")}
                onMouseLeave={() => setHoveredArchNode(null)}
              >
                <rect 
                  x="600" y="240" width="160" height="90" rx="6" 
                  fill={hoveredArchNode === "graph" ? "#121214" : "#09090b"} 
                  stroke={hoveredArchNode === "graph" ? "#ff4a00" : "#27272a"} 
                  strokeWidth="1.5"
                  className="transition-all duration-300"
                />
                <text x="680" y="285" fill="#ffffff" textAnchor="middle" fontWeight="bold" fontSize="13">Semantic Facts Store</text>
                <text x="680" y="305" fill="#a1a1aa" textAnchor="middle" fontSize="10" fontFamily="monospace">Belief Graph & Rules</text>
              </g>
            </svg>
          </div>

          {/* Dynamic explanation block */}
          <div className="w-full mt-6 p-4 rounded bg-slate-900 border border-slate-850 min-h-[80px] flex items-center justify-center text-center">
            {hoveredArchNode === "ingestion" && (
              <p className="text-sm text-slate-300">
                <strong>API Request Ingestion:</strong> The client SDK coordinates calls directly to the server. Alternatively, point your OpenAI/Gemini wrapper baseUrl to the Kyros proxy to auto-intercept and parse context.
              </p>
            )}
            {hoveredArchNode === "engine" && (
              <p className="text-sm text-slate-300">
                <strong>Memory Consolidation Engine:</strong> Ingested events are chronologically written to episodic logs, parsed into semantic graph relationships, and resolved dynamically through Ebbinghaus half-life parameters.
              </p>
            )}
            {hoveredArchNode === "vector" && (
              <p className="text-sm text-slate-300">
                <strong>pgvector Storage:</strong> Stores high-dimensional dense embeddings for semantic search. Relies on structured PostgreSQL indexes to guarantee low retrieval latencies.
              </p>
            )}
            {hoveredArchNode === "graph" && (
              <p className="text-sm text-slate-300">
                <strong>Semantic Relations:</strong> Maps facts using entities and predicates. Propagates confidence adjustments recursively whenever conflicting information is saved.
              </p>
            )}
            {!hoveredArchNode && (
              <p className="text-sm text-slate-500 font-mono">
                Hover over any system architecture node to inspect components.
              </p>
            )}
          </div>
        </div>
      </section>

      {/* Interactive Simulator Section */}
<<<<<<< Updated upstream
      <section className="max-w-6xl mx-auto px-6 py-16 w-full relative">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
            Interactive Memory Playground
          </h2>
          <p className="mt-4 text-zinc-400 max-w-xl mx-auto text-sm">
            Interact with the client-side simulator to see how Kyros parses, secures, decays, and propagates state in real time.
          </p>
        </div>

        <div className="grid lg:grid-cols-12 gap-8 items-start">
          {/* Playground Left Panel - Tabs & Settings */}
          <div className="lg:col-span-4 space-y-4">
=======
      <section className="relative max-w-5xl mx-auto px-6 py-12 w-full z-10 border-t border-slate-850">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-white tracking-tight">
            Interactive Memory Playground
          </h2>
          <p className="mt-4 text-slate-400 max-w-xl mx-auto">
            Interact with the client-side simulator to see how Kyros parses, secures, decays, and propagates state in real time. Or view the full sandbox on the <Link href="/simulation" className="text-blue-400 hover:underline">Simulation Page</Link>.
          </p>
        </div>

        <div className="border border-slate-850 rounded-xl bg-slate-900/30 overflow-hidden shadow-xl">
          {/* Playground Tabs */}
          <div className="flex border-b border-slate-850 bg-slate-900/60 text-sm">
>>>>>>> Stashed changes
            {[
              { id: "episodic", label: "Episodic Logger", desc: "Sequential log stream of conversations, actions, and observations with cryptographic hashes." },
              { id: "semantic", label: "Semantic Graph", desc: "Triples database representing facts and relationships. Features graph-based belief updates." },
              { id: "procedural", label: "Procedural Workflows", desc: "Workflow and task state execution trackers that measure agent performance." },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActivePlaygroundTab(tab.id as any)}
                className={`w-full p-5 rounded-2xl text-left transition-all border ${
                  activePlaygroundTab === tab.id
<<<<<<< Updated upstream
                    ? "bg-zinc-900/60 border-cyan-500/30 shadow-lg shadow-cyan-950/20"
                    : "bg-zinc-900/10 border-zinc-900 hover:border-zinc-850 hover:bg-zinc-900/20"
=======
                    ? "text-blue-400 bg-black border-b-2 border-blue-500"
                    : "text-slate-400 hover:text-slate-200"
>>>>>>> Stashed changes
                }`}
              >
                <h3 className={`text-sm font-semibold mb-1 transition-colors ${activePlaygroundTab === tab.id ? "text-cyan-400" : "text-white"}`}>
                  {tab.label}
                </h3>
                <p className="text-xs text-zinc-400 leading-relaxed">{tab.desc}</p>
              </button>
            ))}
          </div>

<<<<<<< Updated upstream
          {/* Playground Right Panel - Interactive UI */}
          <div className="lg:col-span-8 p-6 rounded-2xl border border-zinc-900 bg-zinc-900/20 backdrop-blur-sm min-h-[420px] flex flex-col justify-between">
            {/* Episodic Logger UI */}
=======
          <div className="p-6 bg-black min-h-[350px]">
            {/* Episodic Simulator */}
>>>>>>> Stashed changes
            {activePlaygroundTab === "episodic" && (
              <div className="space-y-6 flex-1 flex flex-col justify-between">
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500">
                      Episodic Log Feed ( তামপর-স্পষ্ট / Tamper-evident )
                    </span>
                    <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-900">
                      Auto-Hashed Sequence
                    </span>
                  </div>

                  <div className="space-y-3 max-h-[260px] overflow-y-auto pr-1">
                    {episodicMemories.map((mem) => (
                      <div
                        key={mem.id}
                        className="p-4 rounded-xl border border-zinc-900 bg-zinc-950/40 flex justify-between items-center gap-4 hover:border-zinc-800 transition-colors"
                      >
                        <div className="space-y-1.5 flex-1 min-w-0">
                          <p className="text-xs text-zinc-200 leading-relaxed">{mem.content}</p>
                          <div className="flex flex-wrap gap-4 text-[10px] font-mono text-zinc-500">
                            <span>Stored: {mem.timestamp}</span>
                            <span className="text-zinc-600 font-mono truncate max-w-[150px]">Hash: {mem.hash}</span>
                          </div>
                        </div>
                        <div className="flex flex-col items-end shrink-0">
                          <span className="text-[9px] font-mono text-zinc-500">Decay Weight</span>
                          <span className="text-sm font-semibold text-emerald-400 font-mono">
                            {mem.decay}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <form onSubmit={handleAddEpisodic} className="flex gap-2 pt-4 border-t border-zinc-900/60">
                  <input
                    type="text"
                    value={episodicInput}
                    onChange={(e) => setEpisodicInput(e.target.value)}
<<<<<<< Updated upstream
                    placeholder="Type raw agent experiences (e.g. 'User wants Python deployment')"
                    className="flex-1 px-4 py-2.5 rounded-lg bg-zinc-950 border border-zinc-900 text-zinc-200 placeholder-zinc-650 focus:outline-none focus:border-cyan-500 text-xs transition-colors"
                  />
                  <button
                    type="submit"
                    className="px-4 py-2.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black font-semibold text-xs transition-colors shrink-0"
=======
                    placeholder="Enter raw event (e.g. 'User prefers strict typing.')"
                    className="flex-1 px-4 py-3 rounded bg-slate-900 border border-slate-800 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-blue-500 text-sm"
                  />
                  <button
                    type="submit"
                    className="px-5 py-3 rounded bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm transition-colors"
>>>>>>> Stashed changes
                  >
                    Commit Experience
                  </button>
                </form>
<<<<<<< Updated upstream
=======

                <div className="space-y-3">
                  <span className="text-xs font-mono uppercase tracking-wider text-slate-500 block">
                    Episodic Logs (Tamper-evident, hashed sequence)
                  </span>
                  {episodicMemories.map((mem) => (
                    <div
                      key={mem.id}
                      className="p-4 rounded border border-slate-850 bg-slate-900/30 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 text-sm hover:border-slate-800 transition-colors"
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
>>>>>>> Stashed changes
              </div>
            )}

            {/* Semantic Graph UI */}
            {activePlaygroundTab === "semantic" && (
<<<<<<< Updated upstream
              <div className="space-y-6 flex-1 flex flex-col justify-between">
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500">
                      Semantic Facts database
                    </span>
                    <div className="flex gap-2">
                      <button
                        onClick={handleTriggerConflict}
                        disabled={conflictTriggered}
                        className="px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 disabled:opacity-50 text-zinc-300 font-semibold text-[10px] transition-colors"
=======
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-mono uppercase tracking-wider text-slate-500">
                    Semantic Facts Database
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={handleTriggerConflict}
                      disabled={conflictTriggered}
                      className="px-4 py-2 rounded bg-slate-900 hover:bg-slate-850 disabled:opacity-50 text-slate-300 font-medium text-xs transition-colors border border-slate-800"
                    >
                      Simulate Identity Conflict
                    </button>
                    {conflictTriggered && (
                      <button
                        onClick={handleResetSemantic}
                        className="px-4 py-2 rounded bg-slate-900 border border-slate-800 hover:bg-slate-850 text-slate-400 font-medium text-xs transition-colors"
>>>>>>> Stashed changes
                      >
                        Trigger Identity Conflict
                      </button>
                      {conflictTriggered && (
                        <button
                          onClick={handleResetSemantic}
                          className="px-3 py-1.5 rounded-lg bg-zinc-900/30 border border-zinc-800 hover:bg-zinc-900 text-zinc-400 font-semibold text-[10px] transition-colors"
                        >
                          Reset Graph
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Fact Database Table */}
                  <div className="border border-zinc-900 rounded-xl overflow-hidden bg-zinc-950/20">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-zinc-900 bg-zinc-950/50 text-zinc-500 font-mono text-[9px] uppercase tracking-wider">
                          <th className="py-2.5 px-4">Subject</th>
                          <th className="py-2.5 px-4">Predicate</th>
                          <th className="py-2.5 px-4">Object</th>
                          <th className="py-2.5 px-4 text-right">Confidence</th>
                          <th className="py-2.5 px-4 text-right">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {semanticFacts.map((fact) => (
                          <tr
                            key={fact.id}
                            className={`border-b border-zinc-900 text-zinc-300 hover:bg-zinc-900/10 transition-all ${
                              fact.status === "resolved"
                                ? "bg-emerald-950/10 text-emerald-300"
                                : fact.status === "conflict"
                                ? "bg-rose-950/10 text-rose-350"
                                : ""
                            }`}
                          >
                            <td className="py-3 px-4 font-mono text-zinc-400">{fact.subject}</td>
                            <td className="py-3 px-4 font-mono text-cyan-400/80">{fact.predicate}</td>
                            <td className="py-3 px-4 font-medium">{fact.object}</td>
                            <td className="py-3 px-4 text-right font-mono">
                              {(fact.confidence * 100).toFixed(0)}%
                            </td>
                            <td className="py-3 px-4 text-right">
                              <span
                                className={`inline-block px-2 py-0.5 rounded-full text-[9px] font-mono font-bold uppercase ${
                                  fact.status === "resolved"
                                    ? "bg-emerald-500/10 text-emerald-400"
                                    : fact.status === "conflict"
                                    ? "bg-rose-500/10 text-rose-450"
                                    : "bg-zinc-900 text-zinc-500"
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
                </div>

<<<<<<< Updated upstream
                {conflictTriggered && (
                  <div className="p-4 rounded-xl border border-rose-950/40 bg-rose-950/5 text-[10px] text-rose-300 font-mono leading-relaxed animate-fade-in">
                    [Belief Propagation Node]: Conflict resolved. Updated &quot;name&quot; to &quot;Bob&quot; and &quot;prefers_backend&quot; to &quot;Go&quot;. Conflicting Alice statements decayed.
=======
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm border-collapse">
                    <thead>
                      <tr className="border-b border-slate-850 text-slate-500 font-mono text-xs">
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
                          className={`border-b border-slate-850 transition-colors ${
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
                              className={`inline-block px-2 py-0.5 rounded text-xs font-mono uppercase tracking-wider ${
                                fact.status === "updated"
                                  ? "bg-emerald-500/20 text-emerald-400"
                                  : fact.status === "decayed"
                                  ? "bg-rose-500/10 text-rose-400"
                                  : "bg-slate-900 text-slate-500 border border-slate-800"
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
                  <div className="p-4 rounded border border-slate-800 bg-slate-900/40 text-xs text-slate-400 font-mono leading-relaxed">
                    [Belief Propagation Engine]: Detected name update to &quot;Bob&quot; and backend language change to &quot;Go&quot;. Conflicting context scores updated. Old facts marked for decay pruning.
>>>>>>> Stashed changes
                  </div>
                )}
              </div>
            )}

            {/* Procedural Workflows UI */}
            {activePlaygroundTab === "procedural" && (
              <div className="space-y-6 flex-1 flex flex-col justify-between">
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500">
                      Workflow execution pipeline
                    </span>
                    <span className="text-xs text-zinc-300 font-medium">Procedure: handle_user_context</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    {procedureSteps.map((step, idx) => {
                      const isCompleted = idx < currentProcedureStep;
                      const isActive = idx === currentProcedureStep;
                      return (
                        <div
                          key={step.name}
                          className={`p-4 rounded-xl border transition-all ${
                            isActive
                              ? "border-cyan-500 bg-cyan-950/10"
                              : isCompleted
                              ? "border-emerald-900 bg-emerald-950/5"
                              : "border-zinc-900 bg-zinc-900/10"
                          }`}
                        >
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-[9px] font-mono text-zinc-500">STEP 0{idx + 1}</span>
                            {isCompleted && (
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                            )}
                            {isActive && (
                              <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 animate-ping" />
                            )}
                          </div>
                          <h4 className={`text-xs font-bold mb-1 ${isActive ? "text-cyan-400" : isCompleted ? "text-emerald-400" : "text-zinc-300"}`}>
                            {step.name}
                          </h4>
                          <p className="text-[10px] text-zinc-500 leading-relaxed">{step.desc}</p>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="flex justify-end pt-4 border-t border-zinc-900/60">
                  <button
                    onClick={handleRunProcedure}
                    disabled={runningProcedure}
<<<<<<< Updated upstream
                    className="px-4 py-2.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-black font-semibold text-xs transition-all"
=======
                    className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium text-xs transition-colors"
>>>>>>> Stashed changes
                  >
                    {runningProcedure ? "Running workflow..." : "Execute workflow"}
                  </button>
                </div>
<<<<<<< Updated upstream
=======

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  {procedureSteps.map((step, idx) => {
                    const isCompleted = idx < currentProcedureStep;
                    const isActive = idx === currentProcedureStep;
                    return (
                      <div
                        key={step.name}
                        className={`p-4 rounded border transition-all ${
                          isActive
                            ? "border-blue-500 bg-blue-950/20"
                            : isCompleted
                            ? "border-emerald-800 bg-emerald-950/5"
                            : "border-slate-850 bg-slate-900/20"
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
>>>>>>> Stashed changes
              </div>
            )}
          </div>
        </div>
      </section>

<<<<<<< Updated upstream
      {/* Built-in Model Context Protocol (MCP) Showcase */}
      <section className="max-w-6xl mx-auto px-6 py-16 w-full">
        <div className="grid lg:grid-cols-12 gap-8 items-center">
          <div className="lg:col-span-5 space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-purple-500/20 bg-purple-500/5 text-[10px] font-medium text-purple-400">
              Protocol Ready
            </div>
            <h2 className="text-3xl font-bold tracking-tight text-white leading-tight">
              Connect memory to Cursor, Cline, and Windsurf instantly
            </h2>
            <p className="text-zinc-400 text-sm leading-relaxed">
              Kyros ships with a built-in Model Context Protocol (MCP) server. Run a single command to register Kyros as a local workspace toolset, allowing your IDE agents to recall context across development cycles.
            </p>
            <ul className="space-y-2 text-zinc-400 text-xs">
              <li className="flex items-center gap-2">
                <span className="w-1 h-1 rounded-full bg-cyan-400" />
                Zero external dependencies
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1 h-1 rounded-full bg-cyan-400" />
                Exposes remember, recall, and store_fact
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1 h-1 rounded-full bg-cyan-400" />
                Works via stdio JSON-RPC channels
              </li>
            </ul>
          </div>

          {/* Terminal Mockup */}
          <div className="lg:col-span-7">
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 overflow-hidden shadow-2xl backdrop-blur-sm">
              {/* Terminal header */}
              <div className="flex items-center justify-between px-4 py-3 bg-zinc-900/80 border-b border-zinc-800">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
                  <span className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
                  <span className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
                </div>
                <span className="text-[10px] font-mono text-zinc-500">terminal &mdash; kyros mcp</span>
                <span className="w-10" />
              </div>
              {/* Terminal body */}
              <div className="p-6 font-mono text-[11px] text-zinc-300 leading-relaxed bg-zinc-950/80 min-h-[220px]">
                <div className="text-zinc-500 font-mono text-[10px] mb-2"># Boot the built-in MCP server locally</div>
                <div className="text-cyan-400 mb-4">$ kyros mcp start</div>
                <div className="text-zinc-400">[info] Initializing Stdio MCP host</div>
                <div className="text-zinc-400">[info] Registered tool: remember (Store episodic memories)</div>
                <div className="text-zinc-400">[info] Registered tool: recall (Semantic memory queries)</div>
                <div className="text-zinc-400">[info] Registered tool: store_fact (Record triple facts)</div>
                <div className="text-emerald-400/90 font-bold mb-4">[ready] MCP server listening on stdio JSON-RPC</div>
                
                <div className="text-zinc-500 font-mono text-[10px] mb-2">&lt;IDE Agent connected &gt;</div>
                <div className="text-cyan-500">[mcp] Calling tool &quot;recall&quot; &mdash; agent_id: cursor-env</div>
                <div className="text-zinc-400">[mcp] Found 3 matching episodic memories (Confidence: 0.96)</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Integration Code Tabs */}
      <section id="quickstart" className="max-w-6xl mx-auto px-6 py-16 w-full border-t border-zinc-900/60">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-white tracking-tight">
            1-Line Framework Integrations
          </h2>
          <p className="mt-4 text-zinc-400 max-w-xl mx-auto text-sm">
            Leverage environment-based configuration to connect Kyros memory to your orchestrators instantly.
          </p>
        </div>

        <div className="grid lg:grid-cols-12 gap-8 items-start">
          {/* Integration selector tabs */}
          <div className="lg:col-span-4 space-y-2">
            {[
              { id: "crewai", label: "CrewAI", desc: "Episodic and semantic tools injected directly into CrewAI Agent lists." },
              { id: "langchain", label: "LangChain", desc: "Idiomatic ConversationChain memory wrappers for chat sessions." },
              { id: "llamaindex", label: "LlamaIndex", desc: "Data memory components for chat engines and query structures." },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveIntegration(tab.id as any)}
                className={`w-full p-4 rounded-xl text-left border transition-all ${
                  activeIntegration === tab.id
                    ? "bg-zinc-900/60 border-cyan-500/20 text-cyan-400"
                    : "bg-zinc-900/10 border-zinc-900 text-zinc-400 hover:border-zinc-800"
                }`}
              >
                <span className="text-xs font-bold block mb-1">{tab.label}</span>
                <span className="text-[11px] text-zinc-500 block leading-relaxed">{tab.desc}</span>
              </button>
            ))}
          </div>

          {/* Integration code window */}
          <div className="lg:col-span-8 rounded-xl border border-zinc-800 bg-zinc-900/40 overflow-hidden shadow-xl backdrop-blur-sm">
            {/* Header bar */}
            <div className="flex items-center justify-between px-4 py-3 bg-zinc-900/80 border-b border-zinc-800">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-zinc-700" />
                <span className="w-1.5 h-1.5 rounded-full bg-zinc-700" />
                <span className="w-1.5 h-1.5 rounded-full bg-zinc-700" />
              </div>
              <span className="text-[10px] font-mono text-zinc-500">integration_setup.py</span>
              <div className="w-10" />
            </div>
            
            <div className="p-6 font-mono text-[11px] text-zinc-300 leading-relaxed overflow-x-auto bg-zinc-950/80">
              {activeIntegration === "crewai" && (
                <pre>
                  <code>{`from kyros.integrations.crewai import get_kyros_tools
from crewai import Agent, Crew, Task

# Initialize memory tools. The base_url and api_key parameters
# are resolved automatically from environment variables.
tools = get_kyros_tools(agent_id="finance-agent")

researcher = Agent(
    role="Financial Researcher",
    goal="Investigate market trends",
    tools=tools
)

# Kyros tools are invoked automatically as the researcher builds context.`}</code>
                </pre>
              )}

              {activeIntegration === "langchain" && (
                <pre>
                  <code>{`from kyros.integrations.langchain import KyrosChatMemory
from langchain.chains import ConversationChain
from langchain.llms import OpenAI

# Initialize Kyros memory component. api_key and base_url 
# are resolved from environment variables if omitted.
memory = KyrosChatMemory(
    agent_id="support-agent"
)

chain = ConversationChain(
    llm=OpenAI(),
    memory=memory
)

# Conversations are automatically stored and semantically indexed
response = chain.run("My server host is staging.internal")`}</code>
                </pre>
              )}

              {activeIntegration === "llamaindex" && (
                <pre>
                  <code>{`from kyros.integrations.llama_index import KyrosMemory
from llama_index.core.chat_engine import SimpleChatEngine

# Setup client-side memory
memory = KyrosMemory(
    agent_id="data-analyst-agent",
    api_key="your-api-key"
)

engine = SimpleChatEngine.from_defaults(
    memory=memory
)

response = engine.chat("Summarize Q3 financial results.")`}</code>
                </pre>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Zero-Code LLM Proxy Interceptor Section */}
      <section className="max-w-6xl mx-auto px-6 py-16 w-full border-t border-zinc-900/60">
        <div className="grid lg:grid-cols-12 gap-8 items-center">
          <div className="lg:col-span-6 space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-cyan-500/20 bg-cyan-500/5 text-[10px] font-medium text-cyan-400">
              Proxy Mode
            </div>
            <h2 className="text-3xl font-bold tracking-tight text-white leading-tight">
              Intercept LLM payloads without writing code
            </h2>
            <p className="text-zinc-400 text-sm leading-relaxed">
              Integrate Kyros with legacy platforms that do not support custom memory SDKs. Point your OpenAI, Gemini, or Mistral client `base_url` directly to the Kyros proxy endpoint. Kyros automatically queries active memory, injects context into the prompts, and hashes the turn before routing to the provider.
            </p>
          </div>

          <div className="lg:col-span-6 rounded-xl border border-zinc-800 bg-zinc-900/40 p-6 backdrop-blur-sm">
            <div className="space-y-4">
              <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 block">
                Standard OpenAI vs Kyros Proxy Payload
              </span>
              <div className="grid grid-cols-2 gap-4">
                {/* Standard */}
                <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-900">
                  <h4 className="text-xs font-semibold text-zinc-400 mb-2">Standard Payload</h4>
                  <pre className="text-[9px] font-mono text-zinc-650 overflow-x-auto">
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
                <div className="p-4 rounded-lg bg-cyan-950/10 border border-cyan-900/40">
                  <h4 className="text-xs font-semibold text-cyan-400 mb-2">Intercepted Payload</h4>
                  <pre className="text-[9px] font-mono text-cyan-300/80 overflow-x-auto">
{`{
  "model": "gpt-4",
  "messages": [
    {
      "role": "system",
      "content": "[Memory context: User prefers strict typing]"
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
      </section>

      {/* Feature Grid */}
      <section className="max-w-6xl mx-auto px-6 py-24 border-t border-zinc-900/60">
=======
      {/* Feature Specification Cards Grid */}
      <section className="relative max-w-6xl mx-auto px-6 py-24 border-t border-slate-850 z-10">
>>>>>>> Stashed changes
        <h2 className="text-3xl font-bold text-white text-center mb-16 tracking-tight">
          System Specifications & Features
        </h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            {
              title: "Three Memory Modules",
              desc: "Episodic (conversations), semantic (structured facts), and procedural (predefined workflows) subsystems integrated within a unified architecture.",
              icon: (
                <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              ),
            },
            {
              title: "Ebbinghaus Temporal Decay",
              desc: "Memories fade dynamically according to category decay rates. Prevents token bloat, keeps search queries relevant, and optimizes context windows.",
              icon: (
                <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              ),
            },
            {
              title: "Cryptographic Tamper Auditing",
              desc: "Protects memory chains using SHA-256 hashes and Merkle tree verification logic. Instantly detects external injections and poisoning attacks.",
              icon: (
                <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              ),
            },
            {
              title: "Causal Relationship Chains",
              desc: "Establishes explicit parent-child links between independent memory nodes, allowing the agent to audit reasoning chains and trace causality.",
              icon: (
                <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 12l3-3 3 3 4-4M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              ),
            },
            {
              title: "Adaptive Belief Propagation",
              desc: "Graph-based conflict resolution updating network confidence states iteratively using breadth-first traversal whenever new info is parsed.",
              icon: (
                <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H17" />
                </svg>
              ),
            },
            {
              title: "Zero-Code API Proxy Mode",
              desc: "Point an existing LLM wrapper base_url directly to the Kyros proxy server. Intercepts request payloads to inject and log context automatically.",
              icon: (
                <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              ),
            },
          ].map((f) => (
            <div
              key={f.title}
<<<<<<< Updated upstream
              className="p-6 rounded-2xl border border-zinc-900 bg-zinc-900/10 hover:border-cyan-500/20 hover:bg-zinc-900/20 transition-all duration-300 glow-card"
=======
              className="p-6 rounded border border-slate-850 bg-slate-900/10 hover:border-slate-800 hover:bg-slate-900/30 transition-all duration-300"
>>>>>>> Stashed changes
            >
              <div className="mb-4 bg-zinc-900 w-10 h-10 rounded-lg flex items-center justify-center border border-zinc-800">{f.icon}</div>
              <h3 className="font-semibold text-white mb-2 text-base">
                {f.title}
              </h3>
              <p className="text-xs text-zinc-400 leading-relaxed">
                {f.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

<<<<<<< Updated upstream
      {/* Up in 60 seconds / Installation tabs */}
      <section className="max-w-4xl mx-auto px-6 py-16 w-full border-t border-zinc-900/60">
        <h3 className="text-2xl font-bold text-white text-center mb-10 tracking-tight">
          Up in 60 seconds
        </h3>
        
        <div className="border border-zinc-900 rounded-xl overflow-hidden bg-zinc-900/20 backdrop-blur-sm shadow-xl">
          <div className="flex border-b border-zinc-900 bg-zinc-950/40 px-4">
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
                    ? "text-cyan-400 border-cyan-500"
                    : "text-zinc-500 hover:text-zinc-300 border-transparent"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="p-6 bg-zinc-950/80 font-mono text-[11px] text-zinc-355 leading-relaxed overflow-x-auto">
            {activeCodeTab === "docker" && (
              <pre>
                <code>{`# Clone the repository
=======
      {/* Integration Code Blocks / Tabs */}
      <section id="quickstart" className="relative border-t border-slate-850 bg-slate-900/10 z-10">
        <div className="max-w-4xl mx-auto px-6 py-24">
          <h2 className="text-3xl font-bold text-white text-center mb-4 tracking-tight">
            Up in 60 Seconds
          </h2>
          <p className="text-center text-slate-400 mb-12 max-w-lg mx-auto">
            Self-host the memory server using Docker or deploy the Python and TypeScript SDK wrapper.
          </p>

          <div className="border border-slate-850 rounded-lg overflow-hidden bg-slate-900/30 shadow-xl">
            {/* Code Tabs */}
            <div className="flex border-b border-slate-850 bg-slate-900/60 px-4">
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
            <div className="p-6 bg-black/80 font-mono text-xs text-slate-300 leading-relaxed overflow-x-auto">
              {activeCodeTab === "docker" && (
                <pre>
                  <code>{`# Clone the repository
>>>>>>> Stashed changes
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
              <pre>
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

<<<<<<< Updated upstream
            {activeCodeTab === "typescript" && (
              <pre>
                <code>{`// Install dependencies
=======
              {activeCodeTab === "typescript" && (
                <pre>
                  <code>{`// Install dependencies
>>>>>>> Stashed changes
npm install @kyros.494/sdk

// Initialize client
import { KyrosClient } from '@kyros.494/sdk';
const client = new KyrosClient({
  baseUrl: 'http://localhost:8000',
  apiKey: 'mk_live_default_dev_key_123456'
});

// Store and recall memories
await client.remember('agent-123', 'User prefers TypeScript and dark mode');

<<<<<<< Updated upstream
const results = await client.query({
  agentId: 'agent-1',
  query: 'What type guidelines does user follow?',
  memoryTypes: ['semantic']
});`}</code>
              </pre>
            )}
=======
const results = await client.recall('agent-123', 'What language does the user prefer?');`}</code>
                </pre>
              )}
            </div>
>>>>>>> Stashed changes
          </div>
        </div>
      </section>
    </div>
  );
}
