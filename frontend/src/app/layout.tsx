import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MVP-MISTRAL RAG",
  description: "Multi-Tenant Document Intelligence & RAG SaaS",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="it">
      <body className="min-h-screen bg-gray-50 dark:bg-gray-950">
        {children}
      </body>
    </html>
  );
}
