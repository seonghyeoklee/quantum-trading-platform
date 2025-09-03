'use client';

import { Card, CardContent } from "@/components/ui/card";

export function TextChart() {
  return (
    <Card className="w-full h-[400px]">
      <CardContent className="p-6 h-full flex flex-col items-center justify-center">
        <div className="text-center space-y-4">
          <h3 className="text-2xl font-bold text-primary">📈 주식 차트</h3>
          <div className="space-y-2 text-lg">
            <p>삼성전자 (005930)</p>
            <p className="text-3xl font-bold">69,000원</p>
            <p className="text-red-600">+1,500원 (+2.22%)</p>
          </div>
          <div className="mt-8 text-sm text-muted-foreground">
            <p>📊 차트 라이브러리 로딩중...</p>
            <p>실제 차트가 곧 표시됩니다</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}