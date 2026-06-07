"use client";

import React from "react";

export default function UsecasesPage() {
  const useCases = [
    {
      title: "Chatbot Personalization & Context Maintenance",
      problem: "Standard AI assistants forget user details across chat sessions. Injecting the entire conversation history into the prompt consumes massive tokens, increases costs, and eventually overflows the context window.",
      solution: "Kyros recalls relevant episodic memories and semantic facts based on user query similarity. The system dynamically updates customer facts, handles conflicts (e.g. changing name or package preferences), and prunes irrelevant noise automatically.",
      benefit: "Provides a seamless, personalized conversational interface that maintains identity across months of interactions, without manual prompt stuffing.",
    },
    {
      title: "Multi-Agent Coordination & Shared Memory",
      problem: "Autonomous agents working in teams (e.g. a researcher agent, coder agent, and QA agent) struggle to share state, coordinate tasks, and prevent duplicate executions without a shared databases ledger.",
      solution: "By utilizing Kyros, all agents point to a common, tenant-isolated memory stream. The coder agent immediately recalls what the researcher found. Merkle tree verification ensures all shared facts are verified and have not been injected with external prompts.",
      benefit: "Allows independent, highly collaborative agent workflows where each member acts on consistent, audited information.",
    },
    {
      title: "Bitemporal Auditing for Financial & Legal Assistants",
      problem: "Financial data or legal compliance tasks require tracking not only what happened, but *when* it was recorded and *when* it was effective (bitemporal timelines). Traditional RAG databases overwrite historical states.",
      solution: "Kyros features bitemporal columns on semantic relationships. You can query: 'What did the agent believe the user's risk tolerance was on May 1st, according to logs recorded before June 15th?'.",
      benefit: "Enables tamper-proof decision traces, making autonomous financial or legal analysis auditable and compliant.",
    },
    {
      title: "Dynamic Token Optimization & Context Pruning",
      problem: "Long-running conversations accumulate massive token noise, degrading the reasoning performance of LLMs and raising execution costs.",
      solution: "Using the Ebbinghaus Forgetting Curve, Kyros decays memory importance weights over time. Temporary events (e.g., 'let me look at that file') fade in hours, whereas structural profile facts remain permanently cached.",
      benefit: "Drastically reduces context window size, ensuring LLMs receive only high-density, highly relevant background context.",
    },
  ];

  return (
    <div className="max-w-5xl mx-auto px-6 py-12 bg-slate-900 text-slate-100 flex-1 w-full">
      <header className="mb-16 text-center md:text-left">
        <h1 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">Real-World Use Cases</h1>
        <p className="mt-3 text-slate-400 max-w-xl">
          Discover how developers integrate Kyros to build resilient, stateful, and secure AI agent applications.
        </p>
      </header>

      <div className="grid gap-8">
        {useCases.map((uc, index) => (
          <div
            key={uc.title}
            className="p-8 border border-slate-800 bg-slate-800/20 rounded-lg space-y-4 hover:border-slate-700 transition-all"
          >
            <div className="flex items-center gap-4">
              <span className="flex items-center justify-center w-8 h-8 rounded bg-blue-600/10 text-blue-400 font-mono text-sm font-bold">
                0{index + 1}
              </span>
              <h2 className="text-xl font-bold text-white">{uc.title}</h2>
            </div>
            
            <div className="grid md:grid-cols-3 gap-6 pt-2">
              <div className="space-y-1">
                <h4 className="text-xs font-mono uppercase text-rose-400">The Problem</h4>
                <p className="text-sm text-slate-400 leading-relaxed">{uc.problem}</p>
              </div>
              <div className="space-y-1">
                <h4 className="text-xs font-mono uppercase text-blue-400">Kyros Solution</h4>
                <p className="text-sm text-slate-300 leading-relaxed">{uc.solution}</p>
              </div>
              <div className="space-y-1">
                <h4 className="text-xs font-mono uppercase text-emerald-400">The Outcome</h4>
                <p className="text-sm text-slate-300 leading-relaxed">{uc.benefit}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
