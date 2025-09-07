import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import "react-calendar/dist/Calendar.css";
import { ThemeProvider } from "@/components/theme-provider";
import { MarketProvider } from "@/contexts/MarketContext";
import { AuthProvider } from "@/contexts/AuthContext";
import { TradingModeProvider } from "@/contexts/TradingModeContext";
import Header from "@/components/layout/Header";

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
  description: "Professional algorithmic trading platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  console.log('🔥 Layout이 렌더링되고 있습니다');
  
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen bg-background text-foreground font-sans`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <AuthProvider>
            <TradingModeProvider>
              <MarketProvider>
                <Header />
                {children}
              </MarketProvider>
            </TradingModeProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}