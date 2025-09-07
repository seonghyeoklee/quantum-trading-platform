'use client';

import dynamic from 'next/dynamic';

const HolidayCalendar = dynamic(
  () => import('./holiday-calendar'),
  { 
    ssr: false,
    loading: () => (
      <div className="bg-gradient-to-br from-card to-card/50 border border-border/50 rounded-2xl shadow-2xl backdrop-blur-sm overflow-hidden">
        <div className="p-8">
          <div className="flex items-center justify-center space-x-4">
            <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
            <div className="text-lg font-medium text-muted-foreground">달력을 불러오는 중...</div>
          </div>
        </div>
      </div>
    )
  }
);

interface ClientCalendarProps {
  className?: string;
}

export default function ClientCalendar({ className }: ClientCalendarProps) {
  return <HolidayCalendar className={className} />;
}