'use client';

import { useEffect, useRef, useState } from 'react';
import { Card, CardContent } from "@/components/ui/card";

export function TestChart() {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const addLog = (message: string) => {
    console.log(message);
    setLogs(prev => [...prev, message]);
  };

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Test the actual API
    import('lightweight-charts').then((LightweightCharts) => {
      if (!chartContainerRef.current) return;

      try {
        addLog('📦 Lightweight Charts 모듈 로딩됨');
        addLog('🔍 사용 가능한 함수들: ' + Object.keys(LightweightCharts).join(', '));
        
        // Test createChart
        if (typeof LightweightCharts.createChart === 'function') {
          addLog('✅ createChart 함수 발견');
          
          const chart = LightweightCharts.createChart(chartContainerRef.current, {
            width: 600,
            height: 300,
          });
          
          addLog('✅ Chart 객체 생성 성공');
          addLog('🔍 Chart 메소드들: ' + Object.getOwnPropertyNames(Object.getPrototypeOf(chart)).join(', '));
          
          // Test addCandlestickSeries
          if (typeof chart.addCandlestickSeries === 'function') {
            addLog('✅ addCandlestickSeries 메소드 발견');
            
            const series = chart.addCandlestickSeries({
              upColor: '#00ff00',
              downColor: '#ff0000',
            });
            
            addLog('✅ Candlestick series 생성 성공');
            addLog('🔍 Series 메소드들: ' + Object.getOwnPropertyNames(Object.getPrototypeOf(series)).join(', '));
            
            // Test data format
            const testData = [
              { time: '2023-01-01', open: 100, high: 110, low: 95, close: 105 },
              { time: '2023-01-02', open: 105, high: 115, low: 100, close: 108 },
            ];
            
            try {
              series.setData(testData);
              addLog('✅ 테스트 데이터 설정 성공');
              chart.timeScale().fitContent();
              addLog('✅ 차트 렌더링 완료');
            } catch (dataError) {
              addLog('❌ 데이터 설정 실패: ' + (dataError as Error).message);
            }
            
          } else {
            addLog('❌ addCandlestickSeries 메소드를 찾을 수 없음');
          }
          
        } else {
          addLog('❌ createChart 함수를 찾을 수 없음');
        }
        
        setIsLoading(false);
        
      } catch (error) {
        addLog('❌ 오류 발생: ' + (error as Error).message);
        setIsLoading(false);
      }
      
    }).catch((error) => {
      addLog('❌ 모듈 로딩 실패: ' + error.message);
      setIsLoading(false);
    });

  }, []);

  return (
    <Card className="w-full">
      <CardContent className="p-4">
        <h3 className="text-lg font-semibold mb-4">Lightweight Charts API 테스트</h3>
        
        {isLoading && <p className="text-blue-600">테스트 중...</p>}
        
        <div className="space-y-2 mb-4">
          {logs.map((log, index) => (
            <div key={index} className="text-sm font-mono bg-gray-100 p-2 rounded">
              {log}
            </div>
          ))}
        </div>
        
        <div 
          ref={chartContainerRef} 
          style={{ width: '100%', height: '300px', border: '1px solid #ccc' }}
        />
      </CardContent>
    </Card>
  );
}