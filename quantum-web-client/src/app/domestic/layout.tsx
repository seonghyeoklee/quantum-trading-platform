'use client';

import { ReactNode } from 'react';

interface DomesticLayoutProps {
  children: ReactNode;
}

export default function DomesticLayout({ children }: DomesticLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      {/* 메인 컨텐츠 - 전체 폭 활용 */}
      <main className="w-full px-4 sm:px-6 py-4 sm:py-6">
        {children}
      </main>
    </div>
  );
}