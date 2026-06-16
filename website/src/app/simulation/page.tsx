"use client";

import React, { useState, useEffect, useCallback } from "react";

interface SimulatedMemory {
  id: string;
  content: string;
  hash: string;
  decayWeight: number;
  type: "episodic" | "semantic";
}

export default function SimulationPage() {
  // Simulator Controls State
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [simulatedDays, setSimulatedDays] = useState(0);
  const [inputText, setInputText] = useState("User mentioned their name is Alice.");
  
  // Pipeline Logs / Memory state
  const [simulationLogs, setSimulationLogs] = useState<string[]>([
    "Simulator initialized. Enter a memory event and press 'Ingest'."
  ]);
  const [memories, setMemories] = useState<SimulatedMemory[]>([
    { id: "1", content: "User is Alice", hash: "sha256_d1738ef902b4", decayWeight: 100, type: "semantic" }
  ]);

  // Tutorial State
  const [tutorialStep, setTutorialStep] = useState(0);
  const tutorialSlides = [
    {
      title: "Welcome to Kyros Sandbox!",
      desc: "This simulator lets you trace how memories flow through the Kyros AI engine. You will observe how input events are hashed, audited, decayed, and committed."
    },
    {
      title: "Step 1: Ingest Memory Events",
      desc: "Type a memory description in the input box, or use the default. Click 'Step Forward' or 'Play' to process it."
    },
    {
      title: "Step 2: Cryptographic Tree & Decay",
      desc: "Watch the Merkle Tree append leaf nodes and recalculate the Root hash. Simulate elapsed days using the slider to observe Ebbinghaus decay in action."
    },
    {
      title: "Step 3: Graph Belief Propagation",
      desc: "Input a contradiction (e.g. 'User name is Bob') to trigger belief conflict resolution. Watch old nodes decay and new nodes provision dynamically."
    }
  ];

  const steps = [
    { name: "1. Ingest Event", desc: "Receive text context and parse tokens." },
    { name: "2. SHA-256 Hash", desc: "Generate secure cryptographic signature." },
    { name: "3. Merkle Append", desc: "Add leaf node to agent's audit tree." },
    { name: "4. Ebbinghaus Decay", desc: "Compute weight based on simulated time." },
    { name: "5. Belief Resolution", desc: "Check semantic graph for contradictions." },
    { name: "6. Commit to Database", desc: "Write to Postgres and cache in Redis." }
  ];

  const handleStepForward = useCallback(() => {
    if (currentStep === 0) {
      // Ingest
      setSimulationLogs(prev => [
        `[Step 1] Ingested raw memory event: "${inputText}"`,
        ...prev
      ]);
      setCurrentStep(1);
    } else if (currentStep === 1) {
      // Hash
      const hash = "sha256_" + Math.random().toString(16).substring(2, 14);
      setSimulationLogs(prev => [
        `[Step 2] Generated SHA-256 Hash: ${hash}`,
        ...prev
      ]);
      setCurrentStep(2);
    } else if (currentStep === 2) {
      // Merkle Append
      setSimulationLogs(prev => [
        `[Step 3] Merkle Tree leaf node appended. Re-calculating parent hashes... Root updated.`,
        ...prev
      ]);
      setCurrentStep(3);
    } else if (currentStep === 3) {
      // Ebbinghaus Decay
      setSimulationLogs(prev => [
        `[Step 4] Ebbinghaus forgetting weight calculated. Base weight set to 100%.`,
        ...prev
      ]);
      setCurrentStep(4);
    } else if (currentStep === 4) {
      // Belief Resolution
      setSimulationLogs(prev => [
        `[Step 5] Checking semantic relationship links... No conflicts detected.`,
        ...prev
      ]);
      setCurrentStep(5);
    } else if (currentStep === 5) {
      // Commit
      const hash = "sha256_" + Math.random().toString(16).substring(2, 14);
      const newMemory: SimulatedMemory = {
        id: String(memories.length + 1),
        content: inputText,
        hash,
        decayWeight: 100,
        type: "episodic"
      };
      setMemories(prev => [newMemory, ...prev]);
      setSimulationLogs(prev => [
        `[Step 6] Stored in Postgres pgvector. Caching hot key in Redis. Memory pipeline complete!`,
        ...prev
      ]);
      setCurrentStep(0);
      setIsPlaying(false); // Stop loop after complete cycle
    }
  }, [currentStep, inputText, memories.length]);

  // Simulator play loop
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isPlaying) {
      timer = setInterval(() => {
        handleStepForward();
      }, 1500);
    }
    return () => clearInterval(timer);
  }, [isPlaying, handleStepForward]);

  // Simulate elapsed days and apply decay formula w = w0 * e^(-lambda * t)
  const handleDaysChange = (days: number) => {
    setSimulatedDays(days);
    setMemories(prev =>
      prev.map(m => {
        // Semantic decays slowly, episodic decays faster
        const lambda = m.type === "semantic" ? 0.005 : 0.05;
        const decay = Math.round(100 * Math.exp(-lambda * days));
        return { ...m, decayWeight: Math.max(1, decay) };
      })
    );
  };

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentStep(0);
    setSimulatedDays(0);
    setMemories([
      { id: "1", content: "User is Alice", hash: "sha256_d1738ef902b4", decayWeight: 100, type: "semantic" }
    ]);
    setSimulationLogs(["Simulator reset. Enter event to start."]);
  };

  return (
    <div className="max-w-6xl mx-auto px-6 py-12 bg-slate-900 text-slate-100 flex-1 w-full grid grid-cols-1 lg:grid-cols-3 gap-8">
      
      {/* Column 1 & 2: Simulator Panel */}
      <div className="lg:col-span-2 space-y-6">
        <header className="space-y-2">
          <h1 className="text-3xl font-bold text-white tracking-tight">Memory Pipeline Simulator</h1>
          <p className="text-slate-400 text-sm">
            Control the ingestion lifecycle. Monitor cryptographic hashing, Merkle updates, and Ebbinghaus decay.
          </p>
        </header>

        {/* Input box */}
        <div className="p-6 border border-slate-800 bg-slate-800/30 rounded-lg space-y-4">
          <label className="text-sm font-medium text-slate-300 block">Ingest New Event</label>
          <div className="flex gap-3">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="e.g. User is building a Fintech app in Python."
              className="flex-1 px-4 py-2.5 rounded bg-slate-900 border border-slate-700 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
            />
            <button
              onClick={() => {
                setCurrentStep(0);
                setIsPlaying(true);
              }}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded font-medium text-sm transition-colors"
            >
              Play Pipeline
            </button>
          </div>
        </div>

        {/* Simulator controls and steps */}
        <div className="p-6 border border-slate-800 bg-slate-850 rounded-lg space-y-6">
          <div className="flex justify-between items-center flex-wrap gap-4">
            <div className="flex gap-2">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded text-xs font-mono"
              >
                {isPlaying ? "Pause" : "Play Loop"}
              </button>
              <button
                onClick={handleStepForward}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded text-xs font-mono"
              >
                Step Forward
              </button>
              <button
                onClick={handleReset}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded text-xs font-mono"
              >
                Reset
              </button>
            </div>
            
            {/* Decay Simulator slider */}
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-400 font-mono">Elapse Time:</span>
              <input
                type="range"
                min="0"
                max="60"
                value={simulatedDays}
                onChange={(e) => handleDaysChange(Number(e.target.value))}
                className="w-32 h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer"
              />
              <span className="text-xs font-semibold text-blue-400 font-mono w-14">{simulatedDays} Days</span>
            </div>
          </div>

          {/* Visual Step Indicator */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {steps.map((step, idx) => {
              const isActive = idx === currentStep;
              const isDone = idx < currentStep;
              return (
                <div
                  key={step.name}
                  className={`p-4 rounded border transition-all ${
                    isActive
                      ? "border-blue-500 bg-blue-950/20"
                      : isDone
                      ? "border-slate-700 bg-slate-800/10 text-slate-400"
                      : "border-slate-800 bg-slate-800/20 text-slate-500"
                  }`}
                >
                  <h4 className={`text-xs font-bold font-mono mb-1 ${isActive ? "text-blue-400" : "text-slate-400"}`}>
                    {step.name}
                  </h4>
                  <p className="text-xxs leading-relaxed text-slate-500">{step.desc}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Live Simulator Logs */}
        <div className="p-6 border border-slate-800 bg-slate-900 rounded-lg space-y-3">
          <h3 className="text-xs font-mono uppercase text-slate-500">Live Console Output</h3>
          <div className="bg-slate-950 border border-slate-800 p-4 rounded font-mono text-xs text-blue-400 max-h-40 overflow-y-auto space-y-2">
            {simulationLogs.map((log, idx) => (
              <div key={idx}>{log}</div>
            ))}
          </div>
        </div>
      </div>

      {/* Column 3: Sidebar Tutorial & Active Memory Vault */}
      <div className="space-y-6">
        
        {/* Onboarding Tutorial slide card */}
        <div className="p-6 border border-slate-800 bg-slate-855 rounded-lg space-y-4">
          <h3 className="text-xs font-mono uppercase text-blue-400">Simulator Onboarding Tutorial</h3>
          <h4 className="text-base font-bold text-white">{tutorialSlides[tutorialStep].title}</h4>
          <p className="text-xs text-slate-400 leading-relaxed min-h-[72px]">
            {tutorialSlides[tutorialStep].desc}
          </p>
          <div className="flex justify-between items-center pt-2">
            <span className="text-xxs font-mono text-slate-500">Slide {tutorialStep + 1} of {tutorialSlides.length}</span>
            <div className="flex gap-2">
              <button
                onClick={() => setTutorialStep(prev => Math.max(0, prev - 1))}
                disabled={tutorialStep === 0}
                className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-30 rounded text-xxs font-semibold transition-all"
              >
                Prev
              </button>
              <button
                onClick={() => setTutorialStep(prev => Math.min(tutorialSlides.length - 1, prev + 1))}
                disabled={tutorialStep === tutorialSlides.length - 1}
                className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-30 rounded text-xxs font-semibold transition-all"
              >
                Next
              </button>
            </div>
          </div>
        </div>

        {/* Active Memory Store */}
        <div className="p-6 border border-slate-800 bg-slate-800/10 rounded-lg space-y-4">
          <h3 className="text-xs font-mono uppercase text-slate-500">Active Memory Vault</h3>
          <div className="space-y-3">
            {memories.map((m) => (
              <div key={m.id} className="p-3 border border-slate-800 bg-slate-850/80 rounded space-y-1.5 text-xs">
                <div className="flex justify-between items-center">
                  <span className={`inline-block px-1.5 py-0.5 rounded text-xxs font-mono uppercase ${
                    m.type === "semantic" ? "bg-blue-600/20 text-blue-400" : "bg-emerald-600/20 text-emerald-400"
                  }`}>
                    {m.type}
                  </span>
                  <span className="font-mono text-xxs text-slate-500">{m.hash.substring(0, 14)}</span>
                </div>
                <p className="text-slate-200 font-medium">{m.content}</p>
                <div className="flex justify-between items-center pt-1 border-t border-slate-800/50">
                  <span className="text-xxs text-slate-500 font-mono">Simulated Retention</span>
                  <span className="font-bold text-blue-400 font-mono">{m.decayWeight}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
