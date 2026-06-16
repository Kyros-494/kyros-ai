"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";

export default function Navbar() {
  const pathname = usePathname();
  const [stars, setStars] = useState<number | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalName, setModalName] = useState("");
  const [modalEmail, setModalEmail] = useState("");
  const [generatedKey, setGeneratedKey] = useState("");
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState("");
  const [isCopied, setIsCopied] = useState(false);

  const handleGenerateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!modalName.trim() || !modalEmail.trim()) {
      setModalError("Name and email are required");
      return;
    }
    setModalLoading(true);
    setModalError("");
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "https://api.kyros.ai";
      const res = await fetch(`${baseUrl}/v1/admin/public/sandbox/keys`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ name: modalName, email: modalEmail }),
      });
      if (!res.ok) {
        throw new Error("Failed to generate API key. Please try again.");
      }
      const data = await res.json();
      if (data && data.api_key) {
        setGeneratedKey(data.api_key);
      } else {
        throw new Error("Invalid response structure from server.");
      }
    } catch (err: any) {
      setModalError(err.message || "An unexpected error occurred");
    } finally {
      setModalLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(generatedKey);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  const resetModal = () => {
    setModalName("");
    setModalEmail("");
    setGeneratedKey("");
    setModalError("");
    setModalLoading(false);
    setIsCopied(false);
    setIsModalOpen(false);
  };

  useEffect(() => {
    fetch("https://api.github.com/repos/Kyros-494/kyros-ai")
      .then((res) => {
        if (!res.ok) throw new Error("Rate limit or connection issue");
        return res.json();
      })
      .then((data) => {
        if (data && typeof data.stargazers_count === "number") {
          setStars(data.stargazers_count);
        }
      })
      .catch((err) => {
        console.warn("Using fallback star count:", err);
        setStars(42);
      });
  }, []);

  const navLinks = [
    { href: "/", label: "Home" },
    { href: "/docs", label: "Docs" },
    { href: "/developers", label: "Developers" },
    { href: "/usecases", label: "Usecases" },
    { href: "/simulation", label: "Simulation" },
    { href: "/architecture", label: "Architecture" },
    { href: "/tic-tac-toe", label: "Tic-Tac-Toe" },
  ];

  const isActive = (path: string) => {
    if (path === "/") {
      return pathname === "/";
    }
    return pathname.startsWith(path);
  };

  return (
    <nav className="sticky top-0 z-50 border-b border-zinc-900 bg-zinc-950/70 backdrop-blur-md">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
<<<<<<< Updated upstream
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="relative w-8 h-8 rounded-lg overflow-hidden border border-zinc-800 bg-zinc-900 flex items-center justify-center group-hover:border-cyan-500/50 transition-all duration-350">
              <Image
                src="/kyros-logo.png"
                alt="Kyros Logo"
                width={20}
                height={20}
              />
            </div>
            <span className="text-base font-bold tracking-tight text-white font-sans group-hover:text-cyan-400 transition-colors">
=======
          <Link href="/" className="flex items-center gap-2.5">
            <Image
              src="/kyros-logo.png"
              alt="Kyros Logo"
              width={28}
              height={28}
              className="object-contain"
            />
            <span className="text-lg font-bold tracking-tight text-white font-sans">
>>>>>>> Stashed changes
              Kyros
            </span>
          </Link>
        </div>

        {/* Desktop Navigation Links */}
        <div className="hidden lg:flex items-center gap-1 bg-zinc-900/50 p-1 rounded-full border border-zinc-900">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`px-3 py-1.5 rounded-full text-xs font-medium tracking-wide transition-all ${
                isActive(link.href)
                  ? "text-cyan-400 bg-zinc-900 shadow-sm border border-zinc-800"
                  : "text-zinc-400 hover:text-zinc-200 border border-transparent"
              }`}
            >
              {navLinks.find((l) => l.href === link.href)?.label}
            </Link>
          ))}
        </div>

        {/* GitHub Badge & Mobile Trigger */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-cyan-500/30 bg-cyan-950/20 text-xs font-semibold text-cyan-400 hover:bg-cyan-950/40 hover:border-cyan-500/50 transition-all shadow-[0_0_12px_rgba(6,182,212,0.15)]"
          >
            Get API Key
          </button>

          <a
            href="https://github.com/Kyros-494/kyros-ai"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-zinc-800 bg-zinc-950 text-xs font-mono text-zinc-300 hover:text-white hover:border-zinc-700 transition-all shadow-sm"
          >
            <svg
              className="w-4 h-4 fill-current text-zinc-400 hover:text-white"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                clipRule="evenodd"
                d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.646.64.699 1.026 1.592 1.026 2.683 0 3.842-2.337 4.687-4.565 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.577.688.479C19.138 20.162 22 16.418 22 12c0-5.523-4.477-10-10-10z"
              />
            </svg>
            <span className="hidden sm:inline">Star on GitHub</span>
            <span className="pl-1.5 border-l border-zinc-800 text-cyan-400 font-bold">
              {stars !== null ? stars : "..."}
            </span>
          </a>

          {/* Mobile Menu Trigger */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="lg:hidden p-2 text-zinc-400 hover:text-white bg-zinc-900 border border-zinc-800 rounded-lg focus:outline-none"
            aria-label="Toggle menu"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              {isMobileMenuOpen ? (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              ) : (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {isMobileMenuOpen && (
        <div className="lg:hidden border-t border-zinc-900 bg-zinc-950/95 px-6 py-4 flex flex-col gap-2">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setIsMobileMenuOpen(false)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                isActive(link.href)
                  ? "text-cyan-400 bg-zinc-900/60"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              {link.label}
            </Link>
          ))}
          <button
            onClick={() => {
              setIsMobileMenuOpen(false);
              setIsModalOpen(true);
            }}
            className="mt-2 w-full text-center px-4 py-2 rounded-lg text-sm font-semibold text-cyan-400 bg-cyan-950/20 border border-cyan-500/20 hover:bg-cyan-950/40"
          >
            Get API Key
          </button>
        </div>
      )}

      {/* API Key Modal Popup */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-950/80 backdrop-blur-sm animate-fade-in">
          <div className="relative w-full max-w-md p-6 rounded-2xl border border-zinc-800 bg-zinc-900/90 shadow-2xl backdrop-blur-md">
            {/* Background Glow */}
            <div className="absolute -top-12 -left-12 w-28 h-28 rounded-full bg-cyan-500/10 blur-xl pointer-events-none" />
            <div className="absolute -bottom-12 -right-12 w-28 h-28 rounded-full bg-purple-500/10 blur-xl pointer-events-none" />

            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white tracking-tight">
                Generate API Key
              </h3>
              <button
                onClick={resetModal}
                className="p-1 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {!generatedKey ? (
              <form onSubmit={handleGenerateKey} className="space-y-4">
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Provide your name and email to instantiate a free sandbox workspace. This key grants access to Kyros AI persistence endpoints.
                </p>

                <div>
                  <label className="block text-[10px] font-mono uppercase tracking-wider text-zinc-500 mb-1.5">
                    Name
                  </label>
                  <input
                    type="text"
                    required
                    value={modalName}
                    onChange={(e) => setModalName(e.target.value)}
                    placeholder="Jane Doe"
                    className="w-full px-3.5 py-2 rounded-lg border border-zinc-850 bg-zinc-950 text-xs text-white placeholder-zinc-650 focus:outline-none focus:border-cyan-500/50 transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-mono uppercase tracking-wider text-zinc-500 mb-1.5">
                    Email Address
                  </label>
                  <input
                    type="email"
                    required
                    value={modalEmail}
                    onChange={(e) => setModalEmail(e.target.value)}
                    placeholder="jane@company.com"
                    className="w-full px-3.5 py-2 rounded-lg border border-zinc-850 bg-zinc-950 text-xs text-white placeholder-zinc-650 focus:outline-none focus:border-cyan-500/50 transition-colors"
                  />
                </div>

                {modalError && (
                  <p className="text-xs text-rose-400 font-medium">
                    {modalError}
                  </p>
                )}

                <button
                  type="submit"
                  disabled={modalLoading}
                  className="w-full py-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-medium text-xs tracking-wide transition-all shadow-[0_4px_12px_rgba(6,182,212,0.15)] disabled:opacity-50 disabled:pointer-events-none"
                >
                  {modalLoading ? "Generating..." : "Generate Key"}
                </button>
              </form>
            ) : (
              <div className="space-y-4">
                <p className="text-xs text-zinc-450 leading-relaxed">
                  Your sandbox workspace is ready. Save this key carefully. It will not be displayed again.
                </p>

                <div className="space-y-1">
                  <span className="block text-[10px] font-mono uppercase tracking-wider text-zinc-550">
                    API Key
                  </span>
                  <div className="flex items-center gap-2 p-3 rounded-lg border border-zinc-850 bg-zinc-950 font-mono text-xs text-cyan-400 select-all break-all relative group">
                    <span className="flex-1 pr-8">{generatedKey}</span>
                    <button
                      onClick={handleCopy}
                      className="absolute right-2 top-2 p-1 rounded-md border border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-white hover:border-zinc-700 transition-all"
                      title="Copy to clipboard"
                    >
                      {isCopied ? (
                        <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                        </svg>
                      )}
                    </button>
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="block text-[10px] font-mono uppercase tracking-wider text-zinc-550">
                    Default Endpoint
                  </span>
                  <div className="p-3 rounded-lg border border-zinc-850 bg-zinc-950 font-mono text-xs text-zinc-350 select-all">
                    https://api.kyros.ai
                  </div>
                </div>

                <button
                  onClick={resetModal}
                  className="w-full py-2.5 rounded-lg border border-zinc-800 bg-zinc-900 hover:bg-zinc-850 text-zinc-300 font-medium text-xs tracking-wide transition-all"
                >
                  Done
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
