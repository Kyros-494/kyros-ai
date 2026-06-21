"use client";

import React, { useState } from "react";

const S = {
 border: "2px solid var(--border)",
 borderLight: "1px solid var(--border-light)",
 shadow: "var(--shadow)",
 shadowLg: "var(--shadow-lg)",
};

type FormState = "idle" | "sending" | "success" | "error";
type InquiryType = "general" | "waitlist" | "enterprise" | "partnership" | "bug";

const INQUIRY_TYPES: { value: InquiryType; label: string; icon: string; desc: string }[] = [
 { value: "waitlist", icon: "🚀", label: "Cloud Launch Waitlist", desc: "Get early access when Kyros Cloud launches" },
 { value: "enterprise", icon: "🏢", label: "Enterprise Inquiry", desc: "Custom deployment, SLAs, and volume pricing" },
 { value: "general", icon: "💬", label: "General Inquiry", desc: "Questions about Kyros, features, or roadmap" },
 { value: "partnership", icon: "🤝", label: "Partnership", desc: "Integration partners, resellers, investors" },
 { value: "bug", icon: "🐛", label: "Bug Report", desc: "Technical issue or unexpected behavior" },
];

export default function ContactPage() {
 const [inquiryType, setInquiryType] = useState<InquiryType>("general");
 const [name, setName] = useState("");
 const [email, setEmail] = useState("");
 const [company, setCompany] = useState("");
 const [message, setMessage] = useState("");
 const [formState, setFormState] = useState<FormState>("idle");

 const selectedType = INQUIRY_TYPES.find((t) => t.value === inquiryType)!;

 const getSubjectLine = () => {
 const prefix = {
 waitlist: "[Cloud Waitlist]",
 enterprise: "[Enterprise Inquiry]",
 general: "[General Inquiry]",
 partnership: "[Partnership]",
 bug: "[Bug Report]",
 }[inquiryType];
 return `${prefix} ${name ? `from ${name}` : ""}${company ? ` @ ${company}` : ""}`;
 };

 const getMailtoBody = () => {
 return encodeURIComponent(
 `Name: ${name}\nEmail: ${email}\nCompany: ${company || "N/A"}\nInquiry Type: ${selectedType.label}\n\nMessage:\n${message}`
 );
 };

 const handleSubmit = (e: React.FormEvent) => {
 e.preventDefault();
 if (!name.trim() || !email.trim() || !message.trim()) return;

 setFormState("sending");

 // Build mailto link and open it
 const subject = encodeURIComponent(getSubjectLine());
 const body = getMailtoBody();
 const mailtoUrl = `mailto:kyros.494@gmail.com?subject=${subject}&body=${body}`;

 setTimeout(() => {
 window.location.href = mailtoUrl;
 setFormState("success");
 }, 600);
 };

 const isWaitlist = inquiryType === "waitlist";

 return (
 <div style={{ background: "var(--bg)", color: "var(--text)", width: "100%", minHeight: "100vh" }}>
 {/* Hero */}
 <section
 style={{
 background: "var(--bg-dark)",
 color: "var(--text-on-dark)",
 borderBottom: S.border,
 padding: "5rem 1.5rem 4rem",
 }}
 >
 <div style={{ maxWidth: "1152px", margin: "0 auto" }}>
 <div
 style={{
 display: "inline-flex",
 alignItems: "center",
 gap: "0.5rem",
 padding: "0.3rem 0.9rem",
 borderRadius: 9999,
 border: "1.5px solid rgba(232,245,66,0.4)",
 background: "rgba(232,245,66,0.1)",
 fontFamily: "var(--font-mono)",
 fontSize: "0.65rem",
 fontWeight: 700,
 letterSpacing: "0.1em",
 textTransform: "uppercase" as const,
 color: "var(--primary)",
 marginBottom: "1.5rem",
 }}
 >
 Get in Touch
 </div>
 <h1
 style={{
 fontSize: "clamp(2.25rem, 5vw, 4rem)",
 fontWeight: 900,
 letterSpacing: "-0.04em",
 color: "var(--text-on-dark)",
 margin: "0 0 1.25rem",
 lineHeight: 1.05,
 }}
 >
 Contact & Cloud Waitlist
 </h1>
 <p style={{ color: "rgba(249,247,242,0.6)", maxWidth: "54ch", fontSize: "1rem", lineHeight: 1.8, margin: "0 0 2.5rem" }}>
 Whether you want early access to Kyros Cloud, have an enterprise inquiry, or just want to say hello —
 we read every message personally.
 </p>

 {/* Quick stats */}
 <div style={{ display: "flex", gap: "2.5rem", flexWrap: "wrap" }}>
 {[
 { value: "kyros.494@gmail.com", label: "Direct Email" },
 { value: "@kyros_494", label: "Twitter / X" },
 ].map((s) => (
 <div key={s.label}>
 <div style={{ fontSize: s.value.includes("@") ? "1rem" : "1.5rem", fontWeight: 900, fontFamily: "var(--font-mono)", color: "var(--primary)", lineHeight: 1 }}>
 {s.value}
 </div>
 <div style={{ fontSize: "0.68rem", color: "rgba(249,247,242,0.45)", marginTop: "0.3rem", fontFamily: "var(--font-mono)", letterSpacing: "0.05em" }}>
 {s.label}
 </div>
 </div>
 ))}
 </div>
 </div>
 </section>

 {/* Main Content */}
 <section style={{ padding: "3rem 1.5rem 6rem" }}>
 <div style={{ maxWidth: "1152px", margin: "0 auto", display: "grid", gridTemplateColumns: "1fr 380px", gap: "3rem", alignItems: "start" }}>

 {/* ─── Contact Form ─────────────────────────────── */}
 <div>
 {/* Inquiry type selector */}
 <div style={{ marginBottom: "2rem" }}>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.62rem", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.12em", color: "var(--text-muted)", marginBottom: "0.875rem" }}>
 What can we help you with?
 </div>
 <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "0.625rem" }}>
 {INQUIRY_TYPES.map((type) => (
 <button
 key={type.value}
 onClick={() => setInquiryType(type.value)}
 style={{
 padding: "0.875rem 1rem",
 border: inquiryType === type.value ? S.border : S.borderLight,
 borderRadius: 10,
 background: inquiryType === type.value
 ? type.value === "waitlist" ? "var(--primary)" : "var(--text)"
 : "var(--bg)",
 color: inquiryType === type.value ? (type.value === "waitlist" ? "var(--text)" : "var(--bg)") : "var(--text-muted)",
 cursor: "pointer",
 textAlign: "left" as const,
 transition: "all 0.15s",
 boxShadow: inquiryType === type.value ? S.shadow : "none",
 transform: inquiryType === type.value ? "translate(-1px,-1px)" : "none",
 }}
 >
 <div style={{ fontSize: "1.2rem", marginBottom: "0.3rem" }}>{type.icon}</div>
 <div style={{ fontSize: "0.78rem", fontWeight: 800, marginBottom: "0.15rem" }}>{type.label}</div>
 <div style={{ fontSize: "0.65rem", opacity: 0.7, lineHeight: 1.4 }}>{type.desc}</div>
 </button>
 ))}
 </div>
 </div>

 {/* Waitlist banner */}
 {isWaitlist && (
 <div style={{ marginBottom: "1.75rem", padding: "1.25rem 1.5rem", border: "2px solid var(--primary)", borderRadius: "var(--radius)", background: "rgba(232,245,66,0.08)", display: "flex", gap: "1rem", alignItems: "flex-start" }}>
 <span style={{ fontSize: "1.75rem", flexShrink: 0 }}>🚀</span>
 <div>
 <div style={{ fontSize: "0.88rem", fontWeight: 900, color: "var(--text)", marginBottom: "0.3rem" }}>
 Join the Kyros Cloud Waitlist
 </div>
 <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", lineHeight: 1.7 }}>
 Kyros Cloud is our fully managed memory API — no infra, no setup, just plug in and go.
 Early waitlist members get <strong>priority access</strong>, <strong>discounted pricing</strong>, and the chance to shape the product roadmap directly.
 </div>
 </div>
 </div>
 )}

 {/* Form */}
 {formState === "success" ? (
 <div
 style={{
 padding: "3rem 2rem",
 border: S.border,
 borderRadius: "var(--radius)",
 background: "var(--bg-alt)",
 textAlign: "center",
 boxShadow: S.shadowLg,
 }}
 >
 <div style={{ fontSize: "3rem", marginBottom: "1rem" }}></div>
 <h2 style={{ fontSize: "1.4rem", fontWeight: 900, letterSpacing: "-0.03em", margin: "0 0 0.75rem" }}>
 Your email app is opening!
 </h2>
 <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", lineHeight: 1.7, margin: "0 0 1.5rem", maxWidth: "40ch", marginLeft: "auto", marginRight: "auto" }}>
 Your message is pre-filled in your email client addressed to{" "}
 <strong>kyros.494@gmail.com</strong>. Just hit Send and we&apos;ll get back to you within 24 hours.
 </p>
 <button
 onClick={() => { setFormState("idle"); setName(""); setEmail(""); setCompany(""); setMessage(""); }}
 style={{ padding: "0.75rem 1.5rem", border: S.border, borderRadius: 8, background: "var(--text)", color: "var(--bg)", fontWeight: 800, fontSize: "0.85rem", cursor: "pointer", fontFamily: "var(--font-mono)" }}
 >
 Send Another Message
 </button>
 </div>
 ) : (
 <form
 onSubmit={handleSubmit}
 style={{
 border: S.border,
 borderRadius: "var(--radius)",
 background: "var(--bg)",
 overflow: "hidden",
 boxShadow: S.shadow,
 }}
 >
 {/* Form header */}
 <div style={{ padding: "1.25rem 1.75rem", borderBottom: S.border, background: "var(--bg-dark)", display: "flex", alignItems: "center", gap: "0.75rem" }}>
 <span style={{ fontSize: "1.1rem" }}>{selectedType.icon}</span>
 <div>
 <div style={{ fontSize: "0.85rem", fontWeight: 900, color: "var(--text-on-dark)" }}>{selectedType.label}</div>
 <div style={{ fontSize: "0.68rem", color: "rgba(249,247,242,0.45)", fontFamily: "var(--font-mono)" }}>→ kyros.494@gmail.com</div>
 </div>
 </div>

 <div style={{ padding: "1.75rem", display: "flex", flexDirection: "column", gap: "1.25rem" }}>
 {/* Name + Email row */}
 <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
 <div>
 <label style={{ display: "block", fontSize: "0.7rem", fontWeight: 800, fontFamily: "var(--font-mono)", color: "var(--text)", textTransform: "uppercase" as const, letterSpacing: "0.08em", marginBottom: "0.5rem" }}>
 Full Name *
 </label>
 <input
 type="text"
 required
 value={name}
 onChange={(e) => setName(e.target.value)}
 placeholder="Alex Johnson"
 style={{ width: "100%", padding: "0.75rem 1rem", border: S.border, borderRadius: 8, background: "var(--bg-alt)", color: "var(--text)", fontSize: "0.875rem", outline: "none", fontFamily: "var(--font-sans)", boxSizing: "border-box" as const }}
 />
 </div>
 <div>
 <label style={{ display: "block", fontSize: "0.7rem", fontWeight: 800, fontFamily: "var(--font-mono)", color: "var(--text)", textTransform: "uppercase" as const, letterSpacing: "0.08em", marginBottom: "0.5rem" }}>
 Email Address *
 </label>
 <input
 type="email"
 required
 value={email}
 onChange={(e) => setEmail(e.target.value)}
 placeholder="alex@yourcompany.com"
 style={{ width: "100%", padding: "0.75rem 1rem", border: S.border, borderRadius: 8, background: "var(--bg-alt)", color: "var(--text)", fontSize: "0.875rem", outline: "none", fontFamily: "var(--font-sans)", boxSizing: "border-box" as const }}
 />
 </div>
 </div>

 {/* Company */}
 <div>
 <label style={{ display: "block", fontSize: "0.7rem", fontWeight: 800, fontFamily: "var(--font-mono)", color: "var(--text)", textTransform: "uppercase" as const, letterSpacing: "0.08em", marginBottom: "0.5rem" }}>
 Company / Organization <span style={{ fontWeight: 400, opacity: 0.5 }}>(optional)</span>
 </label>
 <input
 type="text"
 value={company}
 onChange={(e) => setCompany(e.target.value)}
 placeholder="Acme Corp, Independent Developer, etc."
 style={{ width: "100%", padding: "0.75rem 1rem", border: S.border, borderRadius: 8, background: "var(--bg-alt)", color: "var(--text)", fontSize: "0.875rem", outline: "none", fontFamily: "var(--font-sans)", boxSizing: "border-box" as const }}
 />
 </div>

 {/* Message */}
 <div>
 <label style={{ display: "block", fontSize: "0.7rem", fontWeight: 800, fontFamily: "var(--font-mono)", color: "var(--text)", textTransform: "uppercase" as const, letterSpacing: "0.08em", marginBottom: "0.5rem" }}>
 {isWaitlist ? "Tell us about your use case *" : "Your Message *"}
 </label>
 <textarea
 required
 value={message}
 onChange={(e) => setMessage(e.target.value)}
 rows={6}
 placeholder={
 isWaitlist
 ? "Describe what you're building and how you plan to use Kyros Cloud. This helps us prioritize the right features and reach out with the most relevant updates..."
 : inquiryType === "enterprise"
 ? "Describe your team size, use case, expected memory volume, and any specific compliance or deployment requirements..."
 : inquiryType === "bug"
 ? "Describe the bug: what you expected to happen, what actually happened, and steps to reproduce..."
 : "What would you like to discuss?"
 }
 style={{ width: "100%", padding: "0.875rem 1rem", border: S.border, borderRadius: 8, background: "var(--bg-alt)", color: "var(--text)", fontSize: "0.875rem", outline: "none", fontFamily: "var(--font-sans)", resize: "vertical", lineHeight: 1.7, boxSizing: "border-box" as const }}
 />
 </div>

 {/* Submit */}
 <button
 type="submit"
 disabled={formState === "sending" || !name.trim() || !email.trim() || !message.trim()}
 style={{
 padding: "1rem 2rem",
 border: S.border,
 borderRadius: 10,
 background: (!name.trim() || !email.trim() || !message.trim()) ? "var(--bg-alt)" : isWaitlist ? "var(--primary)" : "var(--text)",
 color: (!name.trim() || !email.trim() || !message.trim()) ? "var(--text-muted)" : isWaitlist ? "var(--text)" : "var(--bg)",
 fontWeight: 900,
 fontSize: "0.95rem",
 cursor: (!name.trim() || !email.trim() || !message.trim()) ? "not-allowed" : "pointer",
 boxShadow: (!name.trim() || !email.trim() || !message.trim()) ? "none" : S.shadow,
 transition: "all 0.15s",
 display: "flex",
 alignItems: "center",
 justifyContent: "center",
 gap: "0.625rem",
 fontFamily: "var(--font-mono)",
 }}
 >
 {formState === "sending" ? (
 <>Opening your email client…</>
 ) : isWaitlist ? (
 <>🚀 Join the Cloud Waitlist →</>
 ) : (
 <> Send Message →</>
 )}
 </button>

 <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", margin: 0, textAlign: "center" as const, fontFamily: "var(--font-mono)" }}>
 Opens your email client pre-filled · Sends directly to kyros.494@gmail.com
 </p>
 </div>
 </form>
 )}
 </div>

 {/* ─── Right Sidebar ──────────────────────────── */}
 <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>

 {/* Cloud Waitlist CTA */}
 <div
 style={{
 border: "2px solid var(--primary)",
 borderRadius: "var(--radius)",
 background: "var(--bg-dark)",
 overflow: "hidden",
 boxShadow: S.shadowLg,
 }}
 >
 <div style={{ padding: "0.875rem 1.5rem", borderBottom: "1px solid rgba(232,245,66,0.2)", background: "rgba(232,245,66,0.08)" }}>
 <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", fontWeight: 800, textTransform: "uppercase" as const, letterSpacing: "0.12em", color: "var(--primary)" }}>
 Coming Soon — Kyros Cloud
 </span>
 </div>
 <div style={{ padding: "1.5rem" }}>
 <h3 style={{ fontSize: "1.05rem", fontWeight: 900, color: "var(--text-on-dark)", margin: "0 0 0.875rem", letterSpacing: "-0.02em", lineHeight: 1.3 }}>
 Managed memory API.<br />No infra. Just plug in.
 </h3>
 <ul style={{ listStyle: "none", margin: "0 0 1.25rem", padding: 0, display: "flex", flexDirection: "column", gap: "0.625rem" }}>
 {[
 "Hosted API with 99.9% uptime SLA",
 "Auto-scaling vector storage",
 "Dashboard + usage analytics",
 "One-click SDK setup",
 "Priority support channel",
 "Early access pricing for waitlist",
 ].map((item) => (
 <li key={item} style={{ display: "flex", alignItems: "flex-start", gap: "0.625rem", fontSize: "0.78rem", color: "rgba(249,247,242,0.7)", lineHeight: 1.5 }}>
 <span style={{ color: "var(--primary)", fontWeight: 900, flexShrink: 0, marginTop: "0.05rem" }}></span>
 {item}
 </li>
 ))}
 </ul>
 <button
 onClick={() => setInquiryType("waitlist")}
 style={{ width: "100%", padding: "0.875rem", border: "2px solid var(--primary)", borderRadius: 8, background: "var(--primary)", color: "var(--text)", fontWeight: 900, fontSize: "0.875rem", cursor: "pointer", fontFamily: "var(--font-mono)", boxShadow: "3px 3px 0 rgba(232,245,66,0.4)" }}
 >
 🚀 Join Waitlist →
 </button>
 </div>
 </div>

 {/* Direct contact */}
 <div style={{ border: S.border, borderRadius: "var(--radius)", background: "var(--bg)", padding: "1.5rem", boxShadow: S.shadow }}>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.12em", color: "var(--text-muted)", marginBottom: "1rem" }}>
 Direct Contact
 </div>
 <div style={{ display: "flex", flexDirection: "column", gap: "0.875rem" }}>
 <a
 href="mailto:kyros.494@gmail.com"
 style={{ display: "flex", alignItems: "center", gap: "0.875rem", padding: "0.875rem 1rem", border: S.border, borderRadius: 8, background: "var(--bg-alt)", textDecoration: "none", color: "var(--text)", transition: "transform 0.15s, box-shadow 0.15s", boxShadow: S.shadow }}
 onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.transform = "translate(-2px,-2px)"; (e.currentTarget as HTMLElement).style.boxShadow = S.shadowLg; }}
 onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.transform = "none"; (e.currentTarget as HTMLElement).style.boxShadow = S.shadow; }}
 >
 <span style={{ fontSize: "1.25rem" }}></span>
 <div>
 <div style={{ fontSize: "0.72rem", fontWeight: 800, color: "var(--text)", marginBottom: "0.15rem" }}>Email</div>
 <div style={{ fontSize: "0.72rem", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>kyros.494@gmail.com</div>
 </div>
 </a>
 <a
 href="https://x.com/kyros_494"
 target="_blank"
 rel="noopener noreferrer"
 style={{ display: "flex", alignItems: "center", gap: "0.875rem", padding: "0.875rem 1rem", border: S.border, borderRadius: 8, background: "var(--bg-alt)", textDecoration: "none", color: "var(--text)", transition: "transform 0.15s, box-shadow 0.15s", boxShadow: S.shadow }}
 onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.transform = "translate(-2px,-2px)"; (e.currentTarget as HTMLElement).style.boxShadow = S.shadowLg; }}
 onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.transform = "none"; (e.currentTarget as HTMLElement).style.boxShadow = S.shadow; }}
 >
 <span style={{ fontSize: "1.25rem" }}>𝕏</span>
 <div>
 <div style={{ fontSize: "0.72rem", fontWeight: 800, color: "var(--text)", marginBottom: "0.15rem" }}>Twitter / X</div>
 <div style={{ fontSize: "0.72rem", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>@kyros_494</div>
 </div>
 </a>
 <a
 href="https://github.com/Kyros-494/kyros-ai"
 target="_blank"
 rel="noopener noreferrer"
 style={{ display: "flex", alignItems: "center", gap: "0.875rem", padding: "0.875rem 1rem", border: S.border, borderRadius: 8, background: "var(--bg-alt)", textDecoration: "none", color: "var(--text)", transition: "transform 0.15s, box-shadow 0.15s", boxShadow: S.shadow }}
 onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.transform = "translate(-2px,-2px)"; (e.currentTarget as HTMLElement).style.boxShadow = S.shadowLg; }}
 onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.transform = "none"; (e.currentTarget as HTMLElement).style.boxShadow = S.shadow; }}
 >
 <span style={{ fontSize: "1.25rem" }}>⌥</span>
 <div>
 <div style={{ fontSize: "0.72rem", fontWeight: 800, color: "var(--text)", marginBottom: "0.15rem" }}>GitHub</div>
 <div style={{ fontSize: "0.72rem", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>Kyros-494/kyros-ai</div>
 </div>
 </a>
 </div>
 </div>

 {/* FAQ */}
 <div style={{ border: S.border, borderRadius: "var(--radius)", background: "var(--bg-alt)", padding: "1.5rem", boxShadow: S.shadow }}>
 <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.12em", color: "var(--text-muted)", marginBottom: "1rem" }}>
 Quick Answers
 </div>
 <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
 {[
 { q: "Is Kyros free?", a: "The self-hosted version (GitHub) is Apache 2.0 licensed and completely free. Cloud pricing TBD for waitlist members." },
 { q: "When does Cloud launch?", a: "Very soon!!! Waitlist members get priority access." },
 { q: "Do you offer enterprise support?", a: "Yes select Enterprise Inquiry and describe your needs. We offer custom SLAs and dedicated support." },
 ].map((faq) => (
 <div key={faq.q} style={{ paddingBottom: "1rem", borderBottom: S.borderLight }}>
 <div style={{ fontSize: "0.8rem", fontWeight: 800, color: "var(--text)", marginBottom: "0.35rem" }}>{faq.q}</div>
 <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", lineHeight: 1.65 }}>{faq.a}</div>
 </div>
 ))}
 </div>
 </div>
 </div>
 </div>
 </section>
 </div>
 );
}
