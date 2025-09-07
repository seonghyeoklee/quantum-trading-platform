import ClientCalendar from '@/components/kis/client-calendar';

export const metadata = {
  title: '트레이딩 캘린더 | Quantum Trading',
  description: '주식 거래를 위한 종합 캘린더 - 시장 운영일, 종목 이슈, 뉴스, 공시 정보 통합',
};

export default function DomesticCalendarPage() {
  return (
    <ClientCalendar />
  );
}