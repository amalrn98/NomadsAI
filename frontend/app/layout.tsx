import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NomadsAI - AI-Powered Travel Intelligence",
  description: "Travel planning and destination research powered by Google Gemini.",
  keywords: ["AI travel", "travel planning", "business travel", "Google Gemini", "travel intelligence"],
  authors: [{ name: "NomadsAI Team" }],
  openGraph: {
    title: "NomadsAI - AI-Powered Travel Intelligence",
    description: "Travel planning powered by Google Gemini",
    type: "website",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "NomadsAI - AI-Powered Travel Intelligence",
    description: "Enterprise-grade travel planning powered by NVIDIA's advanced AI",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background font-sans antialiased">
        {children}
      </body>
    </html>
  );
}