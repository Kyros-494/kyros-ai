"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";

export default function Navbar() {
 const pathname = usePathname();
 const [stars, setStars] = useState<number | null>(null);
 const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
 const [scrolled, setScrolled] = useState(false);

 useEffect(() => {
 const handleScroll = () => setScrolled(window.scrollY > 8);
 window.addEventListener("scroll", handleScroll, { passive: true });
 return () => window.removeEventListener("scroll", handleScroll);
 }, []);

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
 { href: "/contact", label: "Contact" },
 ];

 const isActive = (path: string) => {
 if (path === "/") return pathname === "/";
 return pathname.startsWith(path);
 };

 return (
 <nav
 style={{
 background: "var(--bg)",
 borderBottom: "2px solid var(--border)",
 position: "sticky",
 top: 0,
 zIndex: 50,
 boxShadow: scrolled ? "0 2px 0 var(--border)" : "none",
 transition: "box-shadow 0.2s",
 }}
 >
 <div
 style={{ maxWidth: "1152px", margin: "0 auto", padding: "0 1.5rem" }}
 className="h-16 flex items-center justify-between"
 >
 {/* Logo */}
 <div className="flex items-center gap-3">
 <Link href="/" className="flex items-center gap-2.5 group">
 <div
 style={{
 width: 36,
 height: 36,
 borderRadius: 8,
 overflow: "hidden",
 border: "2px solid var(--border)",
 background: "var(--bg-dark)",
 display: "flex",
 alignItems: "center",
 justifyContent: "center",
 boxShadow: "3px 3px 0 var(--border)",
 transition: "transform 0.15s, box-shadow 0.15s",
 }}
 className="group-hover:[transform:translate(-1px,-1px)] group-hover:[box-shadow:4px_4px_0_var(--border)]"
 >
 <Image
 src="/apple-touch-icon.png"
 alt="Kyros Logo"
 width={22}
 height={22}
 />
 </div>
 <span
 style={{
 fontSize: "1.05rem",
 fontWeight: 900,
 letterSpacing: "-0.03em",
 color: "var(--text)",
 fontFamily: "var(--font-sans)",
 }}
 >
 Kyros
 </span>
 </Link>
 </div>

 {/* Desktop Navigation Links */}
 <div className="hidden lg:flex items-center gap-1">
 {navLinks.map((link) => (
 <Link
 key={link.href}
 href={link.href}
 style={{
 padding: "0.375rem 0.875rem",
 borderRadius: 6,
 fontSize: "0.8rem",
 fontWeight: isActive(link.href) ? 800 : 500,
 color: isActive(link.href) ? "var(--text)" : "var(--text-muted)",
 background: isActive(link.href) ? "var(--primary)" : "transparent",
 border: isActive(link.href) ? "1.5px solid var(--border)" : "1.5px solid transparent",
 textDecoration: "none",
 transition: "all 0.15s",
 letterSpacing: "-0.01em",
 }}
 className={isActive(link.href) ? "" : "hover:text-[var(--text)] hover:bg-[var(--bg-alt)]"}
 >
 {link.label}
 </Link>
 ))}
 </div>

 {/* GitHub Badge & Mobile Trigger */}
 <div className="flex items-center gap-3">
 <a
 href="https://github.com/Kyros-494/kyros-ai"
 target="_blank"
 rel="noopener noreferrer"
 style={{
 display: "flex",
 alignItems: "center",
 gap: "0.5rem",
 padding: "0.375rem 0.875rem",
 border: "2px solid var(--border)",
 background: "var(--bg)",
 borderRadius: 8,
 fontSize: "0.7rem",
 fontFamily: "var(--font-mono)",
 fontWeight: 700,
 color: "var(--text)",
 textDecoration: "none",
 boxShadow: "3px 3px 0 var(--border)",
 transition: "transform 0.15s, box-shadow 0.15s",
 }}
 className="hover:[transform:translate(-1px,-1px)] hover:[box-shadow:4px_4px_0_var(--border)]"
 >
 <svg
 style={{ width: 15, height: 15, fill: "currentColor" }}
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
 <span
 style={{
 paddingLeft: "0.5rem",
 borderLeft: "1.5px solid var(--border)",
 color: "var(--text)",
 fontWeight: 900,
 }}
 >
 {stars !== null ? stars : "…"}
 </span>
 </a>

 {/* Mobile Menu Trigger */}
 <button
 onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
 style={{
 display: "none",
 padding: "0.5rem",
 border: "2px solid var(--border)",
 background: "var(--bg)",
 borderRadius: 8,
 cursor: "pointer",
 color: "var(--text)",
 boxShadow: "3px 3px 0 var(--border)",
 }}
 className="lg:hidden !flex items-center justify-center"
 aria-label="Toggle menu"
 >
 <svg
 style={{ width: 18, height: 18 }}
 fill="none"
 stroke="currentColor"
 viewBox="0 0 24 24"
 strokeWidth={2.5}
 >
 {isMobileMenuOpen ? (
 <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
 ) : (
 <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
 )}
 </svg>
 </button>
 </div>
 </div>

 {/* Mobile Menu Dropdown */}
 {isMobileMenuOpen && (
 <div
 style={{
 borderTop: "2px solid var(--border)",
 background: "var(--bg)",
 padding: "1rem 1.5rem",
 display: "flex",
 flexDirection: "column",
 gap: "0.25rem",
 }}
 className="lg:hidden"
 >
 {navLinks.map((link) => (
 <Link
 key={link.href}
 href={link.href}
 onClick={() => setIsMobileMenuOpen(false)}
 style={{
 padding: "0.625rem 1rem",
 borderRadius: 8,
 fontSize: "0.875rem",
 fontWeight: isActive(link.href) ? 800 : 600,
 color: "var(--text)",
 background: isActive(link.href) ? "var(--primary)" : "transparent",
 border: isActive(link.href) ? "2px solid var(--border)" : "2px solid transparent",
 textDecoration: "none",
 transition: "all 0.15s",
 }}
 >
 {link.label}
 </Link>
 ))}
 </div>
 )}
 </nav>
 );
}
