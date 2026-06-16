import React from "react";
import Link from "next/link";
import Image from "next/image";

export default function Footer() {
  return (
    <footer className="border-t border-zinc-900 bg-zinc-950 mt-auto">
      <div className="max-w-6xl mx-auto px-6 py-16 grid grid-cols-1 md:grid-cols-4 gap-8 text-sm">
        {/* Brand column */}
        <div className="space-y-4 md:col-span-1">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg overflow-hidden border border-zinc-800 bg-zinc-900 flex items-center justify-center">
              <Image
                src="/kyros-logo.png"
                alt="Kyros Logo"
                width={16}
                height={16}
              />
            </div>
            <span className="text-sm font-bold tracking-tight text-white">
              Kyros AI
            </span>
          </Link>
          <p className="text-zinc-500 text-xs leading-relaxed">
            Persistent, self-correcting memory layer for autonomous AI agents. Built for production security and speed.
          </p>
        </div>

        {/* Product Column */}
        <div className="space-y-3">
          <h4 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider font-mono">
            Product
          </h4>
          <ul className="space-y-2 text-zinc-500 text-xs">
            <li>
              <Link href="/docs" className="hover:text-zinc-300 transition-colors">
                Documentation
              </Link>
            </li>
            <li>
              <Link href="/simulation" className="hover:text-zinc-300 transition-colors">
                System Simulator
              </Link>
            </li>
            <li>
              <Link href="/architecture" className="hover:text-zinc-300 transition-colors">
                Architecture Deep Dive
              </Link>
            </li>
          </ul>
        </div>

        {/* Resources Column */}
        <div className="space-y-3">
          <h4 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider font-mono">
            Developers
          </h4>
          <ul className="space-y-2 text-zinc-500 text-xs">
            <li>
              <Link href="/developers" className="hover:text-zinc-300 transition-colors">
                Developer Guide
              </Link>
            </li>
            <li>
              <a
                href="https://github.com/Kyros-494/kyros-ai"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-zinc-300 transition-colors"
              >
                GitHub Source
              </a>
            </li>
          </ul>
        </div>

        {/* Legal Column */}
        <div className="space-y-3">
          <h4 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider font-mono">
            License & Status
          </h4>
          <ul className="space-y-2 text-zinc-500 text-xs">
            <li className="text-zinc-600">Apache 2.0 Core License</li>
            <li className="text-zinc-600">MIT Client SDK License</li>
            <li className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-zinc-400">All systems operational</span>
            </li>
          </ul>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-6 border-t border-zinc-900/60 flex flex-col sm:flex-row justify-between items-center gap-4 text-xs text-zinc-600">
        <span>&copy; {new Date().getFullYear()} Kyros AI. All rights reserved.</span>
        <div className="flex gap-4">
          <Link href="/usecases" className="hover:text-zinc-400 transition-colors">
            Usecases
          </Link>
          <span>&middot;</span>
          <a
            href="https://github.com/Kyros-494/kyros-ai/blob/main/LICENSE"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-zinc-400 transition-colors"
          >
            Terms
          </a>
<<<<<<< Updated upstream
=======
          <Link href="/docs" className="hover:text-white transition-colors">
            Documentation
          </Link>
          <Link href="/simulation" className="hover:text-white transition-colors">
            System Simulator
          </Link>
          <span className="text-slate-600">Apache 2.0 License</span>
>>>>>>> Stashed changes
        </div>
      </div>
    </footer>
  );
}
