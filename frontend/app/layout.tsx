import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "RanOutOfTokens Dashboard",
  description: "Agentic self-healing incident operations",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
