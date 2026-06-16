"use client";

import React, { useState } from "react";

export default function DevelopersPage() {
  const [activeTab, setActiveTab] = useState<"onboarding" | "cli" | "proxy">("onboarding");

  return (
    <div className="max-w-5xl mx-auto px-6 py-12 bg-black text-slate-100 flex-1 w-full">
      <header className="mb-12">
        <h1 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">Developer Center</h1>
        <p className="mt-3 text-slate-400 max-w-xl">
          Everything developers need to integrate Kyros, deploy SDKs, and configure bitemporal proxy routing.
        </p>
      </header>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 bg-slate-800/40 rounded-t-lg overflow-hidden text-sm">
        {([
          { id: "onboarding", label: "Local Onboarding & Packaging" },
          { id: "cli", label: "Admin CLI Reference" },
          { id: "proxy", label: "Zero-Code Proxy Mode" },
        ] as const).map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 py-4 text-center font-medium transition-all ${
              activeTab === tab.id
                ? "text-blue-400 bg-slate-900 border-b-2 border-blue-500"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="p-8 border-x border-b border-slate-800 bg-slate-900 rounded-b-lg space-y-8">
        
        {activeTab === "onboarding" && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-white">Local Editable Installation (Pre-Publication)</h2>
            <p className="text-slate-300 text-sm leading-relaxed">
              If you want to install and develop the SDK packages locally without downloading from package repositories, reference the local directories directly:
            </p>
            
            <div className="space-y-4">
              <h3 className="text-base font-bold text-slate-200">Python SDK Local Mode</h3>
              <pre className="p-4 bg-slate-950 border border-slate-800 rounded font-mono text-xs text-slate-300">
{`# From the project root folder
pip install -e sdks/python

# With optional framework dependencies (CrewAI, LangChain, etc.)
pip install -e sdks/python[all]`}
              </pre>
            </div>

            <div className="space-y-4">
              <h3 className="text-base font-bold text-slate-200">TypeScript SDK Reference</h3>
              <p className="text-slate-300 text-sm">Add this path dependency inside your project package.json:</p>
              <pre className="p-4 bg-slate-950 border border-slate-800 rounded font-mono text-xs text-slate-300">
{`"dependencies": {
  "@kyros.494/sdk": "file:../kyros-ai/sdks/typescript"
}`}
              </pre>
            </div>

            <h2 className="text-xl font-bold text-white pt-4">Packaging & Publication</h2>
            <div className="space-y-4">
              <h3 className="text-base font-bold text-slate-200">PyPI Release (Python SDK)</h3>
              <pre className="p-4 bg-slate-950 border border-slate-800 rounded font-mono text-xs text-slate-300">
{`cd sdks/python
python -m build
python -m twine upload dist/*`}
              </pre>
            </div>
          </div>
        )}

        {activeTab === "cli" && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-white">Interactive Admin Command-Line Interface</h2>
            <p className="text-slate-300 text-sm leading-relaxed">
              The Python SDK includes a CLI binary named <code className="text-blue-400 font-mono">kyros</code>. Make sure your local environment is configured with <code className="text-blue-400 font-mono">KYROS_API_KEY</code> and <code className="text-blue-400 font-mono">KYROS_BASE_URL</code>.
            </p>

            <table className="w-full text-left border-collapse border border-slate-800 text-sm">
              <thead>
                <tr className="bg-slate-800/40 border-b border-slate-800 font-mono text-xs text-slate-450">
                  <th className="p-3">Command</th>
                  <th className="p-3">Parameters</th>
                  <th className="p-3">Usage</th>
                </tr>
              </thead>
              <tbody className="text-slate-300">
                <tr className="border-b border-slate-800">
                  <td className="p-3 font-mono text-xs text-blue-400">kyros status</td>
                  <td className="p-3 text-slate-500">—</td>
                  <td className="p-3 text-xs">Verify database and Redis cache connections status</td>
                </tr>
                <tr className="border-b border-slate-800">
                  <td className="p-3 font-mono text-xs text-blue-400">kyros remember</td>
                  <td className="p-3 font-mono text-xs">--agent &lt;id&gt; --content &lt;text&gt;</td>
                  <td className="p-3 text-xs">Ingest a new episodic memory block manually</td>
                </tr>
                <tr className="border-b border-slate-800">
                  <td className="p-3 font-mono text-xs text-blue-400">kyros recall</td>
                  <td className="p-3 font-mono text-xs">--agent &lt;id&gt; --query &lt;query&gt;</td>
                  <td className="p-3 text-xs">Retrieve matching facts based on semantic distance</td>
                </tr>
                <tr className="border-b border-slate-800">
                  <td className="p-3 font-mono text-xs text-blue-400">kyros audit</td>
                  <td className="p-3 font-mono text-xs">--agent &lt;id&gt;</td>
                  <td className="p-3 text-xs">Verify tree consistency and cryptographic root validations</td>
                </tr>
                <tr className="border-b border-slate-800">
                  <td className="p-3 font-mono text-xs text-blue-400">kyros tenant-create</td>
                  <td className="p-3 font-mono text-xs">--name &lt;name&gt; --email &lt;email&gt;</td>
                  <td className="p-3 text-xs">Register a new organization and fetch API token keys</td>
                </tr>
              </tbody>
            </table>
          </div>
        )}

        {activeTab === "proxy" && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-white">Zero-Code API Interception Proxy</h2>
            <p className="text-slate-300 text-sm leading-relaxed">
              Instead of manually calling memory SDK methods inside application functions, Kyros features an API proxy. 
              Configure your existing LLM libraries (OpenAI, LangChain, Vercel AI SDK) to route traffic to the proxy server endpoint. The proxy automatically grabs conversation lines, extracts facts, checks context memories, and returns LLM answers seamlessly.
            </p>

            <div className="space-y-4">
              <h3 className="text-base font-bold text-slate-200">OpenAI Client Redirection</h3>
              <pre className="p-4 bg-slate-950 border border-slate-800 rounded font-mono text-xs text-slate-300">
{`import openai
from kyros import KyrosClient

# Setup Kyros Proxy
kyros = KyrosClient(api_key="mk_live_default_dev_key_123456")

# Point OpenAI calls to the Kyros proxy listener
response = openai.ChatCompletion.create(
    api_base="http://localhost:8000/v1/proxy", # intercepts requests
    model="gpt-4",
    messages=[{"role": "user", "content": "My name is Alice"}]
)`}
              </pre>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
