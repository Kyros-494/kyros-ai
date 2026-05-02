import Image from "next/image";

export default function Home() {
  return (
    <div className="flex flex-col min-h-full bg-white dark:bg-zinc-950 font-sans">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-zinc-100 dark:border-zinc-800 bg-white/80 dark:bg-zinc-950/80 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Image
              src="/kyros-logo.png"
              alt="Kyros"
              width={32}
              height={32}
              className="rounded-lg"
            />
            <span className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">
              Kyros
            </span>
          </div>
          <div className="flex items-center gap-6 text-sm font-medium text-zinc-600 dark:text-zinc-400">
            <a
              href="https://github.com/Kyros-494/kyros-ai"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-zinc-900 dark:hover:text-white transition-colors"
            >
              GitHub
            </a>
            <a
              href="https://github.com/Kyros-494/kyros-ai/tree/main/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-zinc-900 dark:hover:text-white transition-colors"
            >
              Docs
            </a>
            <a
              href={process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/docs` : "/docs"}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 rounded-full bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-700 dark:hover:bg-zinc-200 transition-colors"
            >
              API Reference
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="flex-1 flex flex-col items-center justify-center text-center px-6 py-32">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 text-xs font-medium text-zinc-600 dark:text-zinc-400 mb-8">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          Open Source · Apache 2.0
        </div>

        <h1 className="max-w-3xl text-5xl sm:text-6xl font-bold tracking-tight text-zinc-900 dark:text-white leading-tight">
          Persistent Memory for{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-600 to-indigo-600">
            AI Agents
          </span>
        </h1>

        <p className="mt-6 max-w-xl text-lg text-zinc-500 dark:text-zinc-400 leading-relaxed">
          Kyros is a production-grade memory operating system. Give your agents
          episodic, semantic, and procedural memory — with cryptographic
          integrity, Ebbinghaus decay, and zero-code proxy injection.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row gap-4 items-center">
          <a
            href="https://github.com/Kyros-494/kyros-ai"
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-3 rounded-full bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 font-medium hover:bg-zinc-700 dark:hover:bg-zinc-200 transition-colors"
          >
            Get Started on GitHub
          </a>
          <a
            href="#quickstart"
            className="px-6 py-3 rounded-full border border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 font-medium hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
          >
            Quickstart →
          </a>
        </div>
      </section>

      {/* Stats */}
      <section className="border-y border-zinc-100 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900">
        <div className="max-w-6xl mx-auto px-6 py-12 grid grid-cols-2 sm:grid-cols-4 gap-8 text-center">
          {[
            { value: "100%", label: "Precision@5 accuracy" },
            { value: "37ms", label: "Avg retrieval latency" },
            { value: "99%", label: "Fewer tokens than Mem0" },
            { value: "3", label: "Memory types" },
          ].map((stat) => (
            <div key={stat.label}>
              <div className="text-3xl font-bold text-zinc-900 dark:text-white">
                {stat.value}
              </div>
              <div className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <h2 className="text-3xl font-bold text-zinc-900 dark:text-white text-center mb-16">
          Everything your agents need to remember
        </h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            {
              icon: "🧠",
              title: "Three Memory Types",
              desc: "Episodic (conversations), semantic (facts), and procedural (workflows) — each with its own retrieval strategy.",
            },
            {
              icon: "📉",
              title: "Ebbinghaus Decay",
              desc: "Memories decay at category-specific rates. Market data expires in 1.4 days; user identity lasts 693 days.",
            },
            {
              icon: "🔐",
              title: "Merkle Integrity",
              desc: "Every memory is SHA-256 hashed with a nonce. Tamper detection via Merkle tree audit logs.",
            },
            {
              icon: "🔗",
              title: "Causal Graph",
              desc: "Link memories with cause-effect relationships. Traverse ancestry chains to understand why things happened.",
            },
            {
              icon: "🌐",
              title: "Belief Propagation",
              desc: "Confidence changes ripple through the semantic graph via BFS, keeping the agent's worldview consistent.",
            },
            {
              icon: "⚡",
              title: "Zero-Code Proxy",
              desc: "Point your LLM base_url at the Kyros proxy. Memories are injected and extracted automatically.",
            },
          ].map((f) => (
            <div
              key={f.title}
              className="p-6 rounded-2xl border border-zinc-100 dark:border-zinc-800 bg-white dark:bg-zinc-900 hover:border-zinc-200 dark:hover:border-zinc-700 transition-colors"
            >
              <div className="text-2xl mb-3">{f.icon}</div>
              <h3 className="font-semibold text-zinc-900 dark:text-white mb-2">
                {f.title}
              </h3>
              <p className="text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed">
                {f.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Quickstart */}
      <section
        id="quickstart"
        className="border-t border-zinc-100 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900"
      >
        <div className="max-w-3xl mx-auto px-6 py-24">
          <h2 className="text-3xl font-bold text-zinc-900 dark:text-white text-center mb-4">
            Up in 60 seconds
          </h2>
          <p className="text-center text-zinc-500 dark:text-zinc-400 mb-12">
            Self-host with Docker or use the Python/TypeScript SDK directly.
          </p>

          <div className="space-y-6">
            <div>
              <p className="text-xs font-mono font-semibold text-zinc-400 uppercase tracking-wider mb-2">
                1. Start the server
              </p>
              <pre className="bg-zinc-900 dark:bg-zinc-950 text-zinc-100 rounded-xl p-4 text-sm overflow-x-auto">
                <code>{`git clone https://github.com/Kyros-494/kyros-ai
cd kyros-ai
docker-compose up -d`}</code>
              </pre>
            </div>

            <div>
              <p className="text-xs font-mono font-semibold text-zinc-400 uppercase tracking-wider mb-2">
                2. Install the SDK
              </p>
              <pre className="bg-zinc-900 dark:bg-zinc-950 text-zinc-100 rounded-xl p-4 text-sm overflow-x-auto">
                <code>{`pip install kyros-sdk`}</code>
              </pre>
            </div>

            <div>
              <p className="text-xs font-mono font-semibold text-zinc-400 uppercase tracking-wider mb-2">
                3. Remember & recall
              </p>
              <pre className="bg-zinc-900 dark:bg-zinc-950 text-zinc-100 rounded-xl p-4 text-sm overflow-x-auto">
                <code>{`import os
import kyros

client = kyros.Client(api_key=os.environ["KYROS_API_KEY"])

# Store a memory
client.remember("agent-1", "User prefers Python for backend work")

# Recall relevant memories
results = client.recall("agent-1", "What language does the user prefer?")
print(results.results[0].content)
# → "User prefers Python for backend work"`}</code>
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* Integrations */}
      <section className="max-w-6xl mx-auto px-6 py-24 text-center">
        <h2 className="text-3xl font-bold text-zinc-900 dark:text-white mb-4">
          Works with your stack
        </h2>
        <p className="text-zinc-500 dark:text-zinc-400 mb-12">
          Native integrations for every major AI framework.
        </p>
        <div className="flex flex-wrap justify-center gap-4">
          {[
            "LangChain",
            "LlamaIndex",
            "CrewAI",
            "AutoGen",
            "Vercel AI SDK",
            "OpenAI",
            "Anthropic",
            "Gemini",
          ].map((name) => (
            <span
              key={name}
              className="px-4 py-2 rounded-full border border-zinc-200 dark:border-zinc-700 text-sm font-medium text-zinc-600 dark:text-zinc-400"
            >
              {name}
            </span>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-100 dark:border-zinc-800">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-zinc-400">
          <span>© {new Date().getFullYear()} Kyros. Apache 2.0 License.</span>
          <div className="flex gap-6">
            <a
              href="https://github.com/Kyros-494/kyros-ai"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-zinc-600 dark:hover:text-zinc-200 transition-colors"
            >
              GitHub
            </a>
            <a
              href="mailto:support@kyros.ai"
              className="hover:text-zinc-600 dark:hover:text-zinc-200 transition-colors"
            >
              Contact
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
