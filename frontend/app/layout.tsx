import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DormMove AI",
  description: "Agentic move-in planning assistant for college students.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-cream text-espresso antialiased">
        {children}
      </body>
    </html>
  );
}
