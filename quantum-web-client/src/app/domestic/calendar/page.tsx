import ClientCalendar from '@/components/kis/client-calendar';
import { Calendar, TrendingUp, Building2, Newspaper } from 'lucide-react';

export const metadata = {
  title: '트레이딩 캘린더 | Quantum Trading',
  description: '주식 거래를 위한 종합 캘린더 - 시장 운영일, 종목 이슈, 뉴스, 공시 정보 통합',
};

export default function DomesticCalendarPage() {
  return (
    <div className="space-y-8 w-full">
      {/* Professional Header */}
      <div className="flex items-center justify-between pb-6 border-b border-border">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            <Calendar className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-3xl font-bold text-foreground tracking-tight">
                트레이딩 캘린더
              </h1>
              <p className="text-sm text-muted-foreground mt-1">
                한국투자증권 거래일정 및 시장 운영 정보
              </p>
            </div>
          </div>
        </div>
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-primary/10 rounded-lg">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-sm font-medium text-primary">실시간 연동</span>
        </div>
      </div>
      
      {/* KIS 거래일 개념 설명 */}
      <div className="bg-gradient-to-br from-card to-muted/20 border border-border rounded-xl p-6 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 bg-gradient-to-br from-primary to-primary/80 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg">
            <Calendar className="w-6 h-6 text-primary-foreground" />
          </div>
          <div className="space-y-4 flex-1">
            <div>
              <h2 className="text-xl font-bold text-foreground mb-2">
                KIS 거래일정 캘린더
              </h2>
              <p className="text-muted-foreground leading-relaxed">
                한국투자증권 API 기준 4가지 업무일 구분을 통한 정확한 거래 계획 수립
              </p>
            </div>
            
            {/* KIS 업무일 구분 설명 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
              {/* 개장일 - 주문 가능일 */}
              <div className="flex items-center gap-3 p-3 bg-card border border-green-200/50 rounded-lg">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                </div>
                <div>
                  <div className="text-sm font-semibold text-green-700">개장일</div>
                  <div className="text-xs text-muted-foreground">주식 주문 가능</div>
                </div>
              </div>
              
              {/* 거래일 - 증권업무 가능 */}
              <div className="flex items-center gap-3 p-3 bg-card border border-blue-200/50 rounded-lg">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                </div>
                <div>
                  <div className="text-sm font-semibold text-blue-700">거래일</div>
                  <div className="text-xs text-muted-foreground">증권업무 가능</div>
                </div>
              </div>
              
              {/* 영업일 - 금융기관 업무 */}
              <div className="flex items-center gap-3 p-3 bg-card border border-cyan-200/50 rounded-lg">
                <div className="w-8 h-8 bg-cyan-100 rounded-lg flex items-center justify-center">
                  <div className="w-3 h-3 bg-cyan-500 rounded-full"></div>
                </div>
                <div>
                  <div className="text-sm font-semibold text-cyan-700">영업일</div>
                  <div className="text-xs text-muted-foreground">금융기관 업무</div>
                </div>
              </div>
              
              {/* 결제일 - 주식 인수/지불 */}
              <div className="flex items-center gap-3 p-3 bg-card border border-orange-200/50 rounded-lg">
                <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
                  <div className="w-3 h-3 bg-orange-400 rounded-full"></div>
                </div>
                <div>
                  <div className="text-sm font-semibold text-orange-700">결제일</div>
                  <div className="text-xs text-muted-foreground">주식 인수/지불</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <ClientCalendar />
    </div>
  );
}