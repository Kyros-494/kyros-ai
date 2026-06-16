"use client";

import React, { useState, useMemo } from "react";
import openapiData from "./openapi.json";

type ActiveTab = "guides" | "usecases" | "reference";
type GuideId = "intro" | "quickstart" | "python-sdk" | "typescript-sdk" | "self-hosting" | "llm-integrations";
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

export default function DocsPage() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("guides");
  const [selectedGuide, setSelectedGuide] = useState<GuideId>("intro");
  const [selectedUsecase, setSelectedUsecase] = useState<UsecaseId>("coding-companion");
  const [selectedEndpoint, setSelectedEndpoint] = useState<string>("/v1/memory/episodic/remember");
  const [searchQuery, setSearchQuery] = useState("");
  const [activeSnippetTab, setActiveSnippetTab] = useState<"curl" | "python" | "typescript">("curl");

  // Typecast openapiData
  const openapi = openapiData as any;

  // Static Guides
  const guides: Guide[] = [
    { id: "intro", title: "Introduction", category: "Getting Started" },
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

  // Group endpoints by tags
  const endpoints = useMemo(() => {
    const list: { path: string; method: string; tag: string; summary: string; spec: any }[] = [];
    if (!openapi.paths) return list;

    Object.keys(openapi.paths).forEach((path) => {
      Object.keys(openapi.paths[path]).forEach((method) => {
        const spec = openapi.paths[path][method];
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
  }, [openapi]);

  // Filtered lists based on search
  const filteredGuides = useMemo(() => {
    return guides.filter((g) =>
      g.title.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [guides, searchQuery]);

  const filteredUsecases = useMemo(() => {
    return usecaseDocs.filter((u) =>
      u.title.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [usecaseDocs, searchQuery]);

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

  // Helper to dereference schemas
  const getSchemaDetails = (ref: string) => {
    if (!ref || !ref.startsWith("#/components/schemas/")) return null;
    const schemaName = ref.replace("#/components/schemas/", "");
    return openapi.components?.schemas?.[schemaName] || null;
  };

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
    const samplePayload: Record<string, any> = {};
    if (schema && schema.properties) {
      Object.keys(schema.properties).forEach((key) => {
        const prop = schema.properties[key];
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
    isPost && ref ? `\\\n  -d '${payloadStr.split("\n").join("\n  ")}'` : ""
  }`;

    // Python SDK conversion mapping
    let python = "";
    if (path.includes("/episodic/remember")) {
      python = `from kyros import KyrosClient\n\nclient = KyrosClient(api_key=\"your-api-key\")\n\nresponse = client.remember(\n    agent_id=\"agent-123\",\n    content=\"User prefers Python backend.\"\n)`;
    } else if (path.includes("/episodic/recall")) {
      python = `from kyros import KyrosClient\n\nclient = KyrosClient(api_key=\"your-api-key\")\n\nresults = client.recall(\n    agent_id=\"agent-123\",\n    query=\"What is the user's preference?\"\n)`;
    } else if (path.includes("/semantic/facts")) {
      python = `from kyros import KyrosClient\n\nclient = KyrosClient(api_key=\"your-api-key\")\n\nfact = client.store_fact(\n    agent_id=\"agent-123\",\n    subject=\"user\",\n    predicate=\"prefers\",\n    value=\"Python\"\n)`;
    } else if (path.includes("/procedural/store")) {
      python = `from kyros import KyrosClient\n\nclient = KyrosClient(api_key=\"your-api-key\")\n\nprocedure = client.store_procedure(\n    agent_id=\"agent-123\",\n    name=\"Send Email\",\n    description=\"Sends notification emails\",\n    task_type=\"comms\",\n    steps=[{\"action\": \"send\"}]\n)`;
    } else {
      python = `import httpx\n\n# Fallback to direct HTTP call\nresponse = httpx.${method.toLowerCase()}(\n    \"http://localhost:8000${path}\",\n    headers={\"X-API-Key\": \"your-api-key\"},\n    json=${payloadStr.split("\n").join("\n    ")}\n)`;
    }

    // TypeScript SDK conversion mapping
    let typescript = "";
    if (path.includes("/episodic/remember")) {
      typescript = `import { KyrosClient } from '@kyros.494/sdk';\n\nconst client = new KyrosClient({ apiKey: 'your-api-key' });\n\nconst response = await client.remember('agent-123', 'User prefers Python backend.');`;
    } else if (path.includes("/episodic/recall")) {
      typescript = `import { KyrosClient } from '@kyros.494/sdk';\n\nconst client = new KyrosClient({ apiKey: 'your-api-key' });\n\nconst results = await client.recall('agent-123', 'What is the user\\'s preference?');`;
    } else if (path.includes("/semantic/facts")) {
      typescript = `import { KyrosClient } from '@kyros.494/sdk';\n\nconst client = new KyrosClient({ apiKey: 'your-api-key' });\n\nconst fact = await client.storeFact(\n  'agent-123',\n  'user',\n  'prefers',\n  'Python'\n);`;
    } else if (path.includes("/procedural/store")) {
      typescript = `import { KyrosClient } from '@kyros.494/sdk';\n\nconst client = new KyrosClient({ apiKey: 'your-api-key' });\n\nconst procedure = await client.storeProcedure(\n  'agent-123',\n  'Send Email',\n  'Sends notification emails',\n  'comms',\n  [{ action: 'send' }]\n);`;
    } else {
      typescript = `// Fallback to fetch API\nconst response = await fetch(\"http://localhost:8000${path}\", {\n  method: \"${method}\",\n  headers: {\n    \"Content-Type\": \"application/json\",\n    \"X-API-Key\": \"your-api-key\"\n  },\n  body: ${isPost ? `JSON.stringify(${payloadStr.split("\n").join("\n  ")})` : "undefined"}\n});`;
    }

    return { curl, python, typescript };
  }, [activeEndpoint]);

  return (
    <div className="max-w-7xl mx-auto px-6 py-12 flex flex-col lg:flex-row gap-8 bg-black text-slate-100 flex-1 w-full relative z-10">
      
      {/* Sidebar Section */}
      <aside className="w-full lg:w-72 shrink-0">
        <div className="sticky top-24 border border-slate-850 bg-slate-900/30 rounded p-4 backdrop-blur-sm">
          {/* Search Bar */}
          <div className="mb-4">
            <input
              type="text"
              placeholder="Search docs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 rounded bg-slate-950 border border-slate-800 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Navigation Mode Switcher */}
          <div className="grid grid-cols-3 border-b border-slate-850 mb-4 text-[11px] font-mono text-center">
            <button
              onClick={() => {
                setActiveTab("guides");
                setSearchQuery("");
              }}
              className={`pb-2 font-semibold ${
                activeTab === "guides"
                  ? "text-blue-400 border-b-2 border-blue-500"
                  : "text-slate-500 hover:text-slate-300"
              }`}
            >
              Developer
            </button>
            <button
              onClick={() => {
                setActiveTab("usecases");
                setSearchQuery("");
              }}
              className={`pb-2 font-semibold ${
                activeTab === "usecases"
                  ? "text-blue-400 border-b-2 border-blue-500"
                  : "text-slate-500 hover:text-slate-300"
              }`}
            >
              Usecases
            </button>
            <button
              onClick={() => {
                setActiveTab("reference");
                setSearchQuery("");
              }}
              className={`pb-2 font-semibold ${
                activeTab === "reference"
                  ? "text-blue-400 border-b-2 border-blue-500"
                  : "text-slate-500 hover:text-slate-300"
              }`}
            >
              API Ref
            </button>
          </div>

          {/* Developer Guides Navigation */}
          {activeTab === "guides" && (
            <div className="space-y-4">
              {["Getting Started", "SDKs", "Server"].map((cat) => {
                const catGuides = filteredGuides.filter((g) => g.category === cat);
                if (catGuides.length === 0) return null;
                return (
                  <div key={cat}>
                    <h4 className="text-[10px] font-mono uppercase tracking-wider text-slate-600 mb-1.5 px-2">
                      {cat}
                    </h4>
                    <ul className="space-y-0.5">
                      {catGuides.map((g) => (
                        <li key={g.id}>
                          <button
                            onClick={() => setSelectedGuide(g.id)}
                            className={`w-full text-left px-2 py-1.5 rounded text-sm transition-all ${
                              selectedGuide === g.id
                                ? "bg-blue-955 text-blue-400 font-medium"
                                : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
                            }`}
                          >
                            {g.title}
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })}
            </div>
          )}

          {/* Usecases Navigation */}
          {activeTab === "usecases" && (
            <div className="space-y-4">
              {["Developer Tools", "Enterprise CRM", "Customer Success", "Consumer Apps"].map((cat) => {
                const catUsecases = filteredUsecases.filter((u) => u.category === cat);
                if (catUsecases.length === 0) return null;
                return (
                  <div key={cat}>
                    <h4 className="text-[10px] font-mono uppercase tracking-wider text-slate-600 mb-1.5 px-2">
                      {cat}
                    </h4>
                    <ul className="space-y-0.5">
                      {catUsecases.map((u) => (
                        <li key={u.id}>
                          <button
                            onClick={() => setSelectedUsecase(u.id)}
                            className={`w-full text-left px-2 py-1.5 rounded text-sm transition-all ${
                              selectedUsecase === u.id
                                ? "bg-blue-955 text-blue-400 font-medium"
                                : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
                            }`}
                          >
                            {u.title}
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })}
            </div>
          )}

          {/* API Reference Navigation */}
          {activeTab === "reference" && (
            <div className="space-y-4 max-h-[500px] overflow-y-auto pr-1">
              {Array.from(new Set(filteredEndpoints.map((e) => e.tag))).map((tag) => {
                const tagEndpoints = filteredEndpoints.filter((e) => e.tag === tag);
                return (
                  <div key={tag}>
                    <h4 className="text-[10px] font-mono uppercase tracking-wider text-slate-600 mb-1.5 px-2">
                      {tag}
                    </h4>
                    <ul className="space-y-0.5">
                      {tagEndpoints.map((e) => (
                        <li key={e.path}>
                          <button
                            onClick={() => setSelectedEndpoint(e.path)}
                            className={`w-full text-left px-2 py-1.5 rounded text-xs transition-all flex items-center gap-2 ${
                              selectedEndpoint === e.path
                                ? "bg-blue-955 text-blue-400 font-medium"
                                : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
                            }`}
                          >
                            <span
                              className={`text-[8px] font-mono font-bold px-1 py-0.5 rounded leading-none shrink-0 ${
                                e.method === "POST"
                                  ? "bg-emerald-500/10 text-emerald-400"
                                  : e.method === "GET"
                                  ? "bg-sky-500/10 text-sky-400"
                                  : "bg-rose-500/10 text-rose-400"
                              }`}
                            >
                              {e.method}
                            </span>
                            <span className="truncate">{e.summary}</span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </aside>

      {/* Main Content Pane */}
      <main className="flex-1 min-w-0 border border-slate-850 bg-slate-900/10 p-8 rounded backdrop-blur-sm relative">
        
        {/* Guides View */}
        {activeTab === "guides" && (
          <div>
            {selectedGuide === "intro" && (
              <article className="space-y-6">
                <h1 className="text-3xl font-bold text-white border-b border-slate-850 pb-3">
                  Introduction to Kyros
                </h1>
                <p className="text-slate-300 leading-relaxed text-sm">
                  Kyros is an open-source, biologically-inspired persistent memory operating system designed specifically for AI agents. Traditional large language models are stateless; they forget conversation context, factual attributes, and procedural steps between interactions. Kyros bridges this gap by offering secure, self-correcting, and audit-ready memory management.
                </p>

                <h2 className="text-xl font-bold text-white mt-8">Memory Typologies</h2>
                <div className="grid md:grid-cols-3 gap-4 mt-4">
                  <div className="p-4 rounded border border-slate-855 bg-slate-900/20">
                    <h3 className="text-sm font-semibold text-blue-400 mb-2">Episodic Memory</h3>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      Tracks chronological conversation streams, tool logs, observations, and raw interactions. Uses vector indices to recall relevant histories.
                    </p>
                  </div>
                  <div className="p-4 rounded border border-slate-855 bg-slate-900/20">
                    <h3 className="text-sm font-semibold text-blue-400 mb-2">Semantic Memory</h3>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      Stores consolidated facts as entities and predicates. Dynamically propagates belief adjustments to resolve contradictory details.
                    </p>
                  </div>
                  <div className="p-4 rounded border border-slate-855 bg-slate-900/20">
                    <h3 className="text-sm font-semibold text-blue-400 mb-2">Procedural Memory</h3>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      Captures step-by-step agent execution workflows. Matches context descriptors against saved procedure templates to guide next steps.
                    </p>
                  </div>
                </div>

                <h2 className="text-xl font-bold text-white mt-8">Key Engineering Principles</h2>
                <ul className="list-disc list-inside space-y-3 text-slate-350 text-sm">
                  <li><strong>Ebbinghaus Temporal Decay:</strong> Importance weights degrade over time according to category rates, preventing index bloat.</li>
                  <li><strong>Merkle Tree Cryptographic Auditing:</strong> Every change creates a hash signature added to a validation ledger to detect poisoning.</li>
                  <li><strong>Adaptive Belief Propagation:</strong> BFS node traversals recalculate confidences in facts when contradictory statements are ingested.</li>
                </ul>
              </article>
            )}

            {selectedGuide === "quickstart" && (
              <article className="space-y-6">
                <h1 className="text-3xl font-bold text-white border-b border-slate-855 pb-3">
                  Quickstart Guide
                </h1>
                <p className="text-slate-300 text-sm">
                  Run the Kyros server stack locally using Docker Compose.
                </p>

                <h2 className="text-lg font-bold text-white mt-6">1. Clone & Run Stack</h2>
                <pre className="p-4 bg-black border border-slate-800 rounded font-mono text-xs text-slate-300 overflow-x-auto">
{`git clone https://github.com/Kyros-494/kyros-ai
cd kyros-ai
docker compose up -d`}
                </pre>

                <h2 className="text-lg font-bold text-white mt-6">2. Configure Environments</h2>
                <p className="text-slate-355 text-sm">
                  Copy the default template configuration file to load standard settings:
                </p>
                <pre className="p-4 bg-black border border-slate-800 rounded font-mono text-xs text-slate-300">
{`cp .env.example .env`}
                </pre>

                <h2 className="text-lg font-bold text-white mt-6">3. Validate Services</h2>
                <ul className="list-disc list-inside space-y-2 text-slate-355 text-sm">
                  <li>API Endpoint: <code className="text-blue-400 font-mono text-xs">http://localhost:8000</code></li>
                  <li>Developer Console Dashboard: <code className="text-blue-400 font-mono text-xs">http://localhost:8000/dashboard</code></li>
                </ul>
              </article>
            )}

            {selectedGuide === "python-sdk" && (
              <article className="space-y-6">
                <h1 className="text-3xl font-bold text-white border-b border-slate-855 pb-3">
                  Python SDK Guide
                </h1>
                <p className="text-slate-300 text-sm">
                  Verify the client-side library to integrate Kyros with your Python agents.
                </p>

                <h2 className="text-lg font-bold text-white mt-6">Installation</h2>
                <pre className="p-4 bg-black border border-slate-800 rounded font-mono text-xs text-slate-300">
{`pip install kyros-sdk`}
                </pre>

                <h2 className="text-lg font-bold text-white mt-6">Remembering & Recalling</h2>
                <pre className="p-4 bg-black border border-slate-800 rounded font-mono text-xs text-slate-300">
{`from kyros import KyrosClient

client = KyrosClient(
    api_key="mk_live_default_dev_key_123456",
    base_url="http://localhost:8000"
)

<<<<<<< Updated upstream
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
=======
# Store memory block
client.remember("agent-123", "User resides in Amsterdam.")

# Semantic recall
results = client.recall("agent-123", "Where does the user live?")
print(results.results[0].content)`}
                </pre>
              </article>
            )}

            {selectedGuide === "typescript-sdk" && (
              <article className="space-y-6">
                <h1 className="text-3xl font-bold text-white border-b border-slate-855 pb-3">
                  TypeScript SDK Guide
                </h1>
                <p className="text-slate-300 text-sm">
                  Add the SDK dependency package to your JavaScript/TypeScript code.
                </p>

                <h2 className="text-lg font-bold text-white mt-6">Installation</h2>
                <pre className="p-4 bg-black border border-slate-800 rounded font-mono text-xs text-slate-300">
{`npm install @kyros.494/sdk`}
                </pre>

                <h2 className="text-lg font-bold text-white mt-6">Basic Client Setup</h2>
                <pre className="p-4 bg-black border border-slate-800 rounded font-mono text-xs text-slate-300">
>>>>>>> Stashed changes
{`import { KyrosClient } from '@kyros.494/sdk';

const client = new KyrosClient({
  apiKey: 'mk_live_default_dev_key_123456',
  baseUrl: 'http://localhost:8000'
});

async function main() {
  await client.remember('agent-123', 'User prefers TypeScript.');
  const results = await client.recall('agent-123', 'What language?');
  console.log(results.results[0].content);
}

main().catch(console.error);`}
                </pre>
              </article>
            )}

            {selectedGuide === "self-hosting" && (
              <article className="space-y-6">
                <h1 className="text-3xl font-bold text-white border-b border-slate-855 pb-3">
                  Self-Hosting in Production
                </h1>
                <p className="text-slate-300 text-sm">
                  Guidance on deploying the memory service in production environments.
                </p>

                <h2 className="text-lg font-bold text-white mt-6">Migrations & Database</h2>
                <p className="text-slate-355 text-sm leading-relaxed">
                  FastAPI runs automatic Alembic schema migrations on startup in dev/test environments. In production, set `KYROS_ENVIRONMENT=production` and run migrations manually:
                </p>
                <pre className="p-4 bg-black border border-slate-800 rounded font-mono text-xs text-slate-300">
{`alembic upgrade head`}
                </pre>

                <h2 className="text-lg font-bold text-white mt-6">Security Infrastructure</h2>
                <ul className="list-disc list-inside space-y-2 text-slate-355 text-sm">
                  <li><strong>Row-Level Security (RLS):</strong> PostgreSQL partitions tables by tenant context. Access policies are verified cryptographically.</li>
                  <li><strong>API Credential Safety:</strong> Plaintext keys are never stored in the database. Hashes are updated using HMAC pepper key configurations.</li>
                </ul>
              </article>
            )}

            {selectedGuide === "llm-integrations" && (
              <article className="space-y-6">
                <h1 className="text-3xl font-bold text-white border-b border-slate-855 pb-3">
                  LLM Integrations
                </h1>
                <p className="text-slate-300 text-sm">
                  Route factual extraction prompts and context consolidation logic to providers.
                </p>

                <h2 className="text-lg font-bold text-white mt-6">Provider Keys</h2>
                <p className="text-slate-355 text-sm">
                  Set api keys in the environment variables to activate providers:
                </p>
                <pre className="p-4 bg-black border border-slate-800 rounded font-mono text-xs text-slate-300">
{`OPENAI_API_KEY=sk-proj-...
GEMINI_API_KEY=AIzaSy...
ANTHROPIC_API_KEY=sk-ant-...`}
                </pre>
                <p className="text-slate-355 text-sm leading-relaxed">
                  If multiple keys are present, the consolidation logic falls back sequentially to locate available models in development and production gates.
                </p>
              </article>
            )}
          </div>
        )}

        {/* Usecases View */}
        {activeTab === "usecases" && (
          <div>
            {selectedUsecase === "coding-companion" && (
              <article className="space-y-6">
                <h1 className="text-3xl font-bold text-white border-b border-slate-850 pb-3">
                  Personal Coding Companion Usecase
                </h1>
                <p className="text-slate-300 text-sm leading-relaxed">
                  Developers frequently use AI assistants that lack local preference continuity. Setting preferred code standards (e.g., strict TypeScript typing, tab indentation size) inside general prompts consumes large token overheads. Kyros stores these variables persistently.
                </p>

                <h2 className="text-lg font-bold text-white mt-6">Ingesting Preferences</h2>
                <p className="text-slate-350 text-sm">
                  When a developer states a guideline (e.g. &quot;Use strict typing configurations&quot;), the IDE client records this episodic memory:
                </p>
                <pre className="p-4 bg-black border border-slate-800 rounded font-mono text-xs text-slate-300">
{`# Python SDK Ingestion
client.remember("developer-123", "Preferred type check: always configure strict mode.")`}
                </pre>

                <h2 className="text-lg font-bold text-white mt-6">Context Retrieval on Prompt</h2>
                <p className="text-slate-350 text-sm">
                  When issuing a coding task request, query the memory vector database dynamically:
                </p>
                <pre className="p-4 bg-black border border-slate-800 rounded font-mono text-xs text-slate-300">
{`# Recall related context before execution
context = client.recall("developer-123", "TypeScript configs")`}
                </pre>
              </article>
            )}

            {selectedUsecase === "personalized-crm" && (
              <article className="space-y-6">
                <h1 className="text-3xl font-bold text-white border-b border-slate-850 pb-3">
                  Personalized CRM Assistant Usecase
                </h1>
                <p className="text-slate-300 text-sm leading-relaxed">
                  In sales, tracking customer preferences (e.g., preferred contact hour, package sizes) is vital. Standard databases overwrite histories, whereas Kyros maps facts in semantic relationship structures to resolve conflict occurrences.
                </p>

                <h2 className="text-lg font-bold text-white mt-6">Storing Structured Facts</h2>
                <p className="text-slate-350 text-sm">
                  Build subject-predicate-object semantic connections representing client info:
                </p>
                <pre className="p-4 bg-black border border-slate-800 rounded font-mono text-xs text-slate-300">
{`# TypeScript SDK Fact Storage
await client.storeFact("agent-crm", "customer_1", "package", "Enterprise Tier");`}
                </pre>

                <h2 className="text-lg font-bold text-white mt-6">Conflict Resolution</h2>
                <p className="text-slate-350 text-sm">
                  If the client changes their package (e.g. &quot;Downgrade package to Growth Tier&quot;), saving the new fact triggers belief propagation. Conflicting package nodes are automatically marked for decay and confidence scores update.
                </p>
              </article>
            )}

            {selectedUsecase === "customer-support" && (
              <article className="space-y-6">
                <h1 className="text-3xl font-bold text-white border-b border-slate-850 pb-3">
                  Customer Support Agent Usecase
                </h1>
                <p className="text-slate-300 text-sm leading-relaxed">
                  Support agents require both episodic knowledge of historical tickets and procedural guides to execute operations (like processing a payment refund) consistently.
                </p>

                <h2 className="text-lg font-bold text-white mt-6">Loading Support Workflows</h2>
                <p className="text-slate-350 text-sm">
                  Save standard operating procedures into Kyros procedural memory:
                </p>
                <pre className="p-4 bg-black border border-slate-800 rounded font-mono text-xs text-slate-300">
{`# Storing a standardized refund procedure
client.store_procedure(
    agent_id="support-bot",
    name="Process Refund",
    description="Steps required to issue a payment refund",
    task_type="billing",
    steps=[
        {"action": "check_invoice", "params": {"required": True}},
        {"action": "gateway_refund", "params": {"gateway": "stripe"}}
    ]
)`}
                </pre>

                <h2 className="text-lg font-bold text-white mt-6">Workflow Matching</h2>
                <p className="text-slate-350 text-sm">
                  When a customer asks for billing assistance, search procedural records to load the correct workflow path:
                </p>
                <pre className="p-4 bg-black border border-slate-800 rounded font-mono text-xs text-slate-300">
{`# Find procedural steps matching request description
action_plan = client.match_procedure("support-bot", "Customer requesting money back for invoice 5")`}
                </pre>
              </article>
            )}

            {selectedUsecase === "travel-planner" && (
              <article className="space-y-6">
                <h1 className="text-3xl font-bold text-white border-b border-slate-850 pb-3">
                  Travel Planner Agent Usecase
                </h1>
                <p className="text-slate-300 text-sm leading-relaxed">
                  Travel recommendations require temporary interest states. An agent should remember that a user is planning a trip to &quot;Paris&quot; this month, but should forget this detail next year to avoid indexing drift.
                </p>

                <h2 className="text-lg font-bold text-white mt-6">Ebbinghaus Retention Curves</h2>
                <p className="text-slate-350 text-sm leading-relaxed">
                  By configuring decay rates on episodic memory types, short-term interests (such as trip search parameters) fade naturally after a defined temporal period, keeping LLM prompt tokens focused strictly on high-priority items.
                </p>
                <pre className="p-4 bg-black border border-slate-800 rounded font-mono text-xs text-slate-300">
{`# Update episodic category decay rate to high coefficient
client.set_decay_rates({"trip_search": 0.25})`}
                </pre>
              </article>
            )}
          </div>
        )}

        {/* API Reference View */}
        {activeTab === "reference" && activeEndpoint && (
          <div className="flex flex-col xl:flex-row gap-8">
            {/* Left Column: API specifications */}
            <div className="flex-1 min-w-0">
              {/* Method and Path */}
              <div className="flex items-center gap-3 mb-4">
                <span
                  className={`text-xs font-mono font-bold px-2 py-1 rounded ${
                    activeEndpoint.method === "POST"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : activeEndpoint.method === "GET"
                      ? "bg-sky-500/10 text-sky-400 border border-sky-500/20"
                      : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                  }`}
                >
                  {activeEndpoint.method}
                </span>
                <span className="font-mono text-sm text-slate-300">{activeEndpoint.path}</span>
              </div>

              <h1 className="text-3xl font-bold text-white mb-2">
                {activeEndpoint.spec.summary}
              </h1>
              <p className="text-slate-400 text-sm leading-relaxed mb-8">
                {activeEndpoint.spec.description}
              </p>

              {/* Request Parameters (Path / Query) */}
              {activeEndpoint.spec.parameters && activeEndpoint.spec.parameters.length > 0 && (
                <div className="mb-8">
                  <h3 className="text-sm font-mono uppercase tracking-wider text-slate-500 mb-3">
                    Query & Path Parameters
                  </h3>
                  <table className="w-full text-left border-collapse text-xs border border-slate-850">
                    <thead>
                      <tr className="bg-slate-900 border-b border-slate-850 font-mono text-slate-400">
                        <th className="p-3">Parameter</th>
                        <th className="p-3">Type</th>
                        <th className="p-3">Required</th>
                        <th className="p-3">Description</th>
                      </tr>
                    </thead>
                    <tbody className="text-slate-300 font-sans">
                      {activeEndpoint.spec.parameters.map((param: any) => (
                        <tr key={param.name} className="border-b border-slate-855">
                          <td className="p-3 font-mono text-blue-400">{param.name}</td>
                          <td className="p-3 font-mono text-slate-500">{param.schema?.type || "string"}</td>
                          <td className="p-3 font-mono text-slate-500">
                            {param.required ? "true" : "false"}
                          </td>
                          <td className="p-3">{param.description || "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Request Body Properties */}
              {activeEndpoint.spec.requestBody?.content?.["application/json"]?.schema?.[
                "$ref"
              ] && (
                <div className="mb-8">
                  <h3 className="text-sm font-mono uppercase tracking-wider text-slate-500 mb-3">
                    Request Body Properties
                  </h3>
                  {(() => {
                    const ref =
                      activeEndpoint.spec.requestBody.content["application/json"]
                        .schema["$ref"];
                    const schema = getSchemaDetails(ref);
                    if (!schema || !schema.properties) {
                      return <p className="text-xs text-slate-500">No properties defined.</p>;
                    }
                    return (
                      <table className="w-full text-left border-collapse text-xs border border-slate-855">
                        <thead>
                          <tr className="bg-slate-900 border-b border-slate-850 font-mono text-slate-400">
                            <th className="p-3">Field Name</th>
                            <th className="p-3">Type</th>
                            <th className="p-3">Required</th>
                            <th className="p-3">Description</th>
                          </tr>
                        </thead>
                        <tbody className="text-slate-300 font-sans">
                          {Object.keys(schema.properties).map((key) => {
                            const prop = schema.properties[key];
                            const isRequired =
                              schema.required && schema.required.includes(key);
                            return (
                              <tr key={key} className="border-b border-slate-855">
                                <td className="p-3 font-mono text-blue-400">{key}</td>
                                <td className="p-3 font-mono text-slate-500">
                                  {prop.type || (prop["$ref"] ? "object" : "any")}
                                </td>
                                <td className="p-3 font-mono text-slate-500">
                                  {isRequired ? "true" : "false"}
                                </td>
                                <td className="p-3">{prop.description || "—"}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    );
                  })()}
                </div>
              )}

              {/* Responses List */}
              <div>
                <h3 className="text-sm font-mono uppercase tracking-wider text-slate-500 mb-3">
                  Responses
                </h3>
                <div className="space-y-2">
                  {Object.keys(activeEndpoint.spec.responses).map((status) => {
                    const res = activeEndpoint.spec.responses[status];
                    return (
                      <div
                        key={status}
                        className="p-3 rounded border border-slate-855 bg-slate-900/20 flex items-center justify-between text-xs"
                      >
                        <span className="font-mono text-slate-350">
                          Status Code: <strong className="text-white">{status}</strong>
                        </span>
                        <span className="text-slate-400">{res.description}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Right Column: Code Snippets sandbox */}
            <div className="w-full xl:w-96 shrink-0">
              <div className="sticky top-24 border border-slate-855 bg-black rounded overflow-hidden shadow-2xl">
                {/* Tabs */}
                <div className="flex border-b border-slate-855 bg-slate-900/60 px-2 text-xs font-mono">
                  {[
                    { id: "curl", label: "cURL" },
                    { id: "python", label: "Python SDK" },
                    { id: "typescript", label: "TypeScript" },
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveSnippetTab(tab.id as any)}
                      className={`py-3 px-3 font-semibold border-b-2 transition-all ${
                        activeSnippetTab === tab.id
                          ? "text-blue-400 border-blue-500"
                          : "text-slate-500 hover:text-slate-300"
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>

                {/* Preformatted Code Content */}
                <div className="p-4 bg-slate-950/60 font-mono text-[11px] text-slate-300 leading-relaxed overflow-x-auto min-h-[300px]">
                  <pre>
                    <code>{snippets[activeSnippetTab]}</code>
                  </pre>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
