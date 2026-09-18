import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "MediSense AI",
  description: "Intelligent healthcare prediction and personalized health assistant",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
