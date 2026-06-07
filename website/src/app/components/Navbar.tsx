"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";

export default function Navbar() {
  const pathname = usePathname();
  const [stars, setStars] = useState<number | null>(null);

  useEffect(() => {
    // Fetch live stars count from the correct GitHub repository
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
        setStars(42); // Fallback star count
      });
  }, []);

  const navLinks = [
    { href: "/", label: "Home" },
    { href: "/docs", label: "Docs" },
    { href: "/developers", label: "Developers" },
    { href: "/usecases", label: "Usecases" },
    { href: "/research", label: "Research" },
    { href: "/simulation", label: "Simulation" },
    { href: "/architecture", label: "Architecture" },
  ];

  const isActive = (path: string) => {
    if (path === "/") {
      return pathname === "/";
    }
    return pathname.startsWith(path);
  };

  return (
    <nav className="sticky top-0 z-50 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/" className="flex items-center gap-2.5">
            <Image
              src="/kyros-logo.png"
              alt="Kyros Logo"
              width={28}
              height={28}
              className="rounded border border-slate-700"
            />
            <span className="text-lg font-bold tracking-tight text-white font-sans">
              Kyros
            </span>
          </Link>
        </div>

        {/* Desktop Navigation Links */}
        <div className="hidden md:flex items-center gap-6 text-sm font-medium">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`transition-colors ${
                isActive(link.href)
                  ? "text-blue-400 font-semibold"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* GitHub Stars Badge */}
        <div className="flex items-center gap-4">
          <a
            href="https://github.com/Kyros-494/kyros-ai"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-slate-700 bg-slate-800 text-xs font-mono text-slate-300 hover:text-white hover:border-slate-600 transition-all"
          >
            <svg
              className="w-4 h-4 fill-current"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                clipRule="evenodd"
                d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.646.64.699 1.026 1.592 1.026 2.683 0 3.842-2.337 4.687-4.565 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.577.688.479C19.138 20.162 22 16.418 22 12c0-5.523-4.477-10-10-10z"
              />
            </svg>
            <span>Star</span>
            <span className="pl-1.5 border-l border-slate-700 text-blue-400">
              {stars !== null ? stars : "..."}
            </span>
          </a>
        </div>
      </div>
    </nav>
  );
}
