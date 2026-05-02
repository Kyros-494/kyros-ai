import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "https://kyros.ai"),
  title: "Kyros — Persistent Memory for AI Agents",
  description:
    "Open-source memory operating system for AI agents. Episodic, semantic, and procedural memory with Ebbinghaus decay, Merkle integrity proofs, and zero-code proxy injection.",
  keywords: ["AI memory", "agent memory", "LLM memory", "persistent memory", "open source"],
  openGraph: {
    title: "Kyros — Persistent Memory for AI Agents",
    description:
      "Open-source memory OS for AI agents. 100% Precision@5, 37ms avg latency, 99% fewer tokens than Mem0.",
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
    description: "Open-source memory OS for AI agents.",
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
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
