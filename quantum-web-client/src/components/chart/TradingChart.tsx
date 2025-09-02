'use client';

import { Card, CardContent } from "@/components/ui/card";
import { TrendingUp, Activity } from "lucide-react";

export function TradingChart() {
  return (
    <Card className="w-full h-[400px] bg-gradient-to-r from-background to-muted/20">
      <CardContent className="p-6 h-full flex flex-col items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="relative">
            <TrendingUp className="w-16 h-16 text-primary animate-pulse" />
            <Activity className="w-6 h-6 text-muted-foreground absolute -bottom-1 -right-1" />
          </div>
          
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-foreground">
              Trading Chart
            </h3>
            <p className="text-sm text-muted-foreground max-w-sm">
              실시간 차트 데이터를 표시할 영역입니다.
              백엔드 API와 연동 후 실제 차트가 표시됩니다.
            </p>
          </div>
          
          <div className="flex gap-2 text-xs text-muted-foreground">
            <span className="px-2 py-1 bg-muted rounded">실시간 데이터</span>
            <span className="px-2 py-1 bg-muted rounded">차트 분석</span>
            <span className="px-2 py-1 bg-muted rounded">기술 지표</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}