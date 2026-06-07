import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "https://kyros-494.github.io/kyros-ai"),
  title: "Kyros — Persistent Memory for AI Agents",
  description:
    "Open-source memory operating system for AI agents. Episodic, semantic, and procedural memory with Ebbinghaus decay, Merkle integrity proofs, and zero-code proxy injection.",
  keywords: ["AI memory", "agent memory", "LLM memory", "persistent memory", "open source"],
  openGraph: {
    title: "Kyros — Persistent Memory for AI Agents",
    description:
      "Open-source memory operating system for AI agents with episodic, semantic, and procedural memory structures.",
    type: "website",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Kyros — The Memory OS for AI Agents",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Kyros — Persistent Memory for AI Agents",
    description: "Open-source memory operating system for AI agents.",
    images: ["/og-image.png"],
  },
  icons: {
    icon: "/favicon.ico",
    apple: "/apple-touch-icon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-slate-900 text-slate-100 font-sans">
        <Navbar />
        <main className="flex-1 flex flex-col">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
