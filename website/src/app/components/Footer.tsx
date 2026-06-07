import React from "react";
import Link from "next/link";

export default function Footer() {
  return (
    <footer className="border-t border-slate-800 bg-slate-900 mt-auto">
      <div className="max-w-6xl mx-auto px-6 py-12 flex flex-col md:flex-row justify-between items-center gap-6 text-sm">
        <div className="flex items-center gap-3">
          <span className="text-slate-500 font-semibold tracking-wider uppercase font-mono">
            Kyros AI persistent memory
          </span>
        </div>
        <div className="flex flex-wrap gap-6 text-slate-400">
          <a
            href="https://github.com/Kyros-494/kyros-ai"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-white transition-colors"
          >
            GitHub
          </a>
          <Link href="/docs" className="hover:text-white transition-colors">
            Documentation
          </Link>
          <Link href="/research" className="hover:text-white transition-colors">
            Performance Research
          </Link>
          <Link href="/simulation" className="hover:text-white transition-colors">
            System Simulator
          </Link>
          <span className="text-slate-600">Apache 2.0 License</span>
        </div>
      </div>
    </footer>
  );
}
