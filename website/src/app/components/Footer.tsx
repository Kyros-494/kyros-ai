import React from "react";
import Link from "next/link";
import Image from "next/image";

export default function Footer() {
 return (
 <footer
 style={{
 background: "var(--bg-dark)",
 color: "var(--text-on-dark)",
 borderTop: "2px solid var(--border)",
 }}
 >
 {/* Main Footer Grid */}
 <div
 style={{ maxWidth: "1152px", margin: "0 auto", padding: "4rem 1.5rem" }}
 className="grid grid-cols-1 md:grid-cols-4 gap-10"
 >
 {/* Brand Column */}
 <div style={{ gridColumn: "1", display: "flex", flexDirection: "column", gap: "1rem" }}>
 <Link href="/" className="inline-flex items-center gap-2.5 group" style={{ textDecoration: "none" }}>
 <div
 style={{
 width: 36,
 height: 36,
 borderRadius: 8,
 overflow: "hidden",
 border: "2px solid rgba(249,247,242,0.2)",
 background: "#1a1a16",
 display: "flex",
 alignItems: "center",
 justifyContent: "center",
 flexShrink: 0,
 }}
 >
 <Image src="/apple-touch-icon.png" alt="Kyros Logo" width={22} height={22} />
 </div>
 <span
 style={{
 fontSize: "1rem",
 fontWeight: 900,
 letterSpacing: "-0.03em",
 color: "var(--text-on-dark)",
 fontFamily: "var(--font-sans)",
 }}
 >
 Kyros AI
 </span>
 </Link>
 <p
 style={{
 color: "rgba(249,247,242,0.5)",
 fontSize: "0.75rem",
 lineHeight: 1.7,
 maxWidth: "22ch",
 margin: 0,
 }}
 >
 Persistent, self-correcting memory layer for autonomous AI agents. Built for production
 security and speed.
 </p>

 {/* GitHub link */}
 <a
 href="https://github.com/Kyros-494/kyros-ai"
 target="_blank"
 rel="noopener noreferrer"
 style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", marginTop: "0.25rem", textDecoration: "none", color: "rgba(249,247,242,0.4)", fontSize: "0.72rem", fontFamily: "var(--font-mono)", transition: "color 0.15s" }}
 >
 <svg style={{ width: 13, height: 13, fill: "currentColor" }} viewBox="0 0 24 24" aria-hidden="true">
 <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.646.64.699 1.026 1.592 1.026 2.683 0 3.842-2.337 4.687-4.565 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.577.688.479C19.138 20.162 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
 </svg>
 Open Source on GitHub
 </a>
 </div>

 {/* Product Column */}
 <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
 <h4
 style={{
 fontSize: "0.65rem",
 fontWeight: 700,
 color: "rgba(249,247,242,0.4)",
 textTransform: "uppercase",
 letterSpacing: "0.12em",
 fontFamily: "var(--font-mono)",
 margin: 0,
 }}
 >
 Product
 </h4>
 <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.625rem" }}>
 {[
 { href: "/docs", label: "Documentation" },
 { href: "/simulation", label: "System Simulator" },
 { href: "/architecture", label: "Architecture Deep Dive" },
 { href: "/contact", label: "Contact & Waitlist" },
 ].map((item) => (
 <li key={item.href}>
 <Link
 href={item.href}
 style={{
 color: "rgba(249,247,242,0.55)",
 fontSize: "0.8rem",
 textDecoration: "none",
 fontWeight: 500,
 transition: "color 0.15s",
 }}
 className="hover:text-[var(--text-on-dark)]"
 >
 {item.label}
 </Link>
 </li>
 ))}
 </ul>
 </div>

 {/* Developers Column */}
 <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
 <h4
 style={{
 fontSize: "0.65rem",
 fontWeight: 700,
 color: "rgba(249,247,242,0.4)",
 textTransform: "uppercase",
 letterSpacing: "0.12em",
 fontFamily: "var(--font-mono)",
 margin: 0,
 }}
 >
 Developers
 </h4>
 <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.625rem" }}>
 {[
 { href: "/developers", label: "Developer Guide", external: false },
 { href: "https://github.com/Kyros-494/kyros-ai", label: "GitHub Source", external: true },
 ].map((item) => (
 <li key={item.href}>
 {item.external ? (
 <a
 href={item.href}
 target="_blank"
 rel="noopener noreferrer"
 style={{
 color: "rgba(249,247,242,0.55)",
 fontSize: "0.8rem",
 textDecoration: "none",
 fontWeight: 500,
 transition: "color 0.15s",
 }}
 className="hover:text-[var(--text-on-dark)]"
 >
 {item.label}
 </a>
 ) : (
 <Link
 href={item.href}
 style={{
 color: "rgba(249,247,242,0.55)",
 fontSize: "0.8rem",
 textDecoration: "none",
 fontWeight: 500,
 transition: "color 0.15s",
 }}
 className="hover:text-[var(--text-on-dark)]"
 >
 {item.label}
 </Link>
 )}
 </li>
 ))}
 </ul>
 </div>

 {/* Contact Column */}
 <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
 <h4
 style={{
 fontSize: "0.65rem",
 fontWeight: 700,
 color: "rgba(249,247,242,0.4)",
 textTransform: "uppercase",
 letterSpacing: "0.12em",
 fontFamily: "var(--font-mono)",
 margin: 0,
 }}
 >
 Contact
 </h4>
 <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.75rem" }}>
 <li>
 <a
 href="https://x.com/kyros_494"
 target="_blank"
 rel="noopener noreferrer"
 className="flex items-center gap-2 group"
 style={{ textDecoration: "none", color: "rgba(249,247,242,0.55)", fontSize: "0.8rem", fontWeight: 500, transition: "color 0.15s" }}
 >
 <svg style={{ width: 14, height: 14, fill: "currentColor" }} viewBox="0 0 24 24" aria-hidden="true">
 <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.746l7.73-8.835L1.254 2.25H8.08l4.259 5.63L18.244 2.25zm-1.161 17.52h1.833L7.084 4.126H5.117L17.083 19.77z" />
 </svg>
 <span className="group-hover:text-[var(--text-on-dark)] transition-colors">@kyros_494</span>
 </a>
 </li>
 <li>
 <a
 href="mailto:kyros.494@gmail.com"
 className="flex items-center gap-2 group"
 style={{ textDecoration: "none", color: "rgba(249,247,242,0.55)", fontSize: "0.8rem", fontWeight: 500, transition: "color 0.15s" }}
 >
 <svg style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
 </svg>
 <span className="group-hover:text-[var(--text-on-dark)] transition-colors">kyros.494@gmail.com</span>
 </a>
 </li>
 </ul>
 </div>
 </div>

 {/* Bottom Bar */}
 <div
 style={{
 maxWidth: "1152px",
 margin: "0 auto",
 padding: "1.25rem 1.5rem",
 borderTop: "1px solid rgba(249,247,242,0.1)",
 display: "flex",
 flexWrap: "wrap",
 justifyContent: "space-between",
 alignItems: "center",
 gap: "0.75rem",
 }}
 >
 <span
 style={{
 color: "rgba(249,247,242,0.3)",
 fontFamily: "var(--font-mono)",
 fontSize: "0.65rem",
 letterSpacing: "0.05em",
 }}
 >
 Apache 2.0 Core · MIT Client SDK
 </span>
 <div className="flex items-center gap-4">
 <a
 href="https://x.com/kyros_494"
 target="_blank"
 rel="noopener noreferrer"
 style={{ color: "rgba(249,247,242,0.3)", fontSize: "0.7rem", display: "flex", alignItems: "center", gap: "0.375rem", textDecoration: "none", transition: "color 0.15s" }}
 className="hover:text-[var(--text-on-dark)]"
 >
 <svg style={{ width: 11, height: 11, fill: "currentColor" }} viewBox="0 0 24 24">
 <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.746l7.73-8.835L1.254 2.25H8.08l4.259 5.63L18.244 2.25zm-1.161 17.52h1.833L7.084 4.126H5.117L17.083 19.77z" />
 </svg>
 X / Twitter
 </a>
 <span style={{ color: "rgba(249,247,242,0.2)" }}>·</span>
 <a
 href="mailto:kyros.494@gmail.com"
 style={{ color: "rgba(249,247,242,0.3)", fontSize: "0.7rem", textDecoration: "none", transition: "color 0.15s" }}
 className="hover:text-[var(--text-on-dark)]"
 >
 kyros.494@gmail.com
 </a>
 </div>
 </div>
 </footer>
 );
}
