import HolidayCalendar from '@/components/kis/holiday-calendar';

export default function CalendarPage() {
  return (
    <div className="container mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          KIS 휴장일 달력
        </h1>
        <p className="text-gray-600">
          한국투자증권 API에서 제공하는 영업일/거래일/개장일/결제일 정보를 확인하세요.
        </p>
      </div>
      
      <HolidayCalendar className="max-w-4xl mx-auto" />
    </div>
  );
}