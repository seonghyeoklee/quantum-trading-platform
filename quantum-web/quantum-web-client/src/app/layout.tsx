import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { AuthProvider } from "@/contexts/AuthContext";
import { TradingModeProvider } from "@/contexts/TradingModeContext";
import TradingModeBodyClass from "@/components/layout/TradingModeBodyClass";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Quantum Trading Platform",
  description: "Professional algorithmic trading platform with real-time market data and advanced analytics",
  keywords: "trading, finance, stocks, algorithms, real-time, analytics",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen bg-background font-sans`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <AuthProvider>
            <TradingModeProvider>
              <TradingModeBodyClass />
              {children}
            </TradingModeProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
