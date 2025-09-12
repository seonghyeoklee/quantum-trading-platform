'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { TestTube, Activity, Search } from 'lucide-react';
import DinoTestViewer from '@/components/dino/DinoTestViewer';

// 테스트용 주요 종목 목록
const TEST_STOCKS = [
  { code: '005930', name: '삼성전자' },
  { code: '000660', name: 'SK하이닉스' },
  { code: '035420', name: 'NAVER' },
  { code: '005380', name: '현대차' },
  { code: '006400', name: '삼성SDI' },
  { code: '207940', name: '삼성바이오로직스' },
  { code: '035900', name: 'JYP Ent.' },
  { code: '003670', name: '포스코퓨처엠' }
];

export default function DinoTestPage() {
  const [selectedStock, setSelectedStock] = useState(TEST_STOCKS[0]);
  const [customStockCode, setCustomStockCode] = useState('');
  const [customCompanyName, setCustomCompanyName] = useState('');

  const handleStockSelect = (stock: typeof TEST_STOCKS[0]) => {
    setSelectedStock(stock);
    setCustomStockCode('');
    setCustomCompanyName('');
  };

  const handleCustomStockSubmit = () => {
    if (customStockCode.trim()) {
      const customStock = {
        code: customStockCode.trim(),
        name: customCompanyName.trim() || customStockCode.trim()
      };
      setSelectedStock(customStock);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* 페이지 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <TestTube className="w-8 h-8 text-blue-600" />
            DINO 시각화 테스트
          </h1>
          <p className="text-gray-600 mt-1">
            실제 DINO API 데이터를 사용한 시각화 컴포넌트 테스트
          </p>
        </div>
        <Badge variant="secondary" className="text-sm">
          <Activity className="w-4 h-4 mr-1" />
          실시간 데이터
        </Badge>
      </div>

      {/* 종목 선택 패널 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">테스트 종목 선택</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* 미리 정의된 종목 목록 */}
            <div>
              <h3 className="text-sm font-medium mb-2">주요 종목</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {TEST_STOCKS.map((stock) => (
                  <Button
                    key={stock.code}
                    variant={selectedStock.code === stock.code ? "default" : "outline"}
                    size="sm"
                    onClick={() => handleStockSelect(stock)}
                    className="flex flex-col items-start p-3 h-auto"
                  >
                    <div className="font-medium">{stock.name}</div>
                    <div className="text-xs opacity-70">{stock.code}</div>
                  </Button>
                ))}
              </div>
            </div>

            {/* 커스텀 종목 입력 */}
            <div>
              <h3 className="text-sm font-medium mb-2">직접 입력</h3>
              <div className="flex gap-2">
                <Input
                  placeholder="종목코드 (예: 005930)"
                  value={customStockCode}
                  onChange={(e) => setCustomStockCode(e.target.value)}
                  maxLength={6}
                  className="flex-1"
                />
                <Input
                  placeholder="회사명 (선택사항)"
                  value={customCompanyName}
                  onChange={(e) => setCustomCompanyName(e.target.value)}
                  className="flex-1"
                />
                <Button 
                  onClick={handleCustomStockSubmit}
                  disabled={!customStockCode.trim()}
                  className="flex items-center gap-2"
                >
                  <Search className="w-4 h-4" />
                  분석
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 현재 선택된 종목 표시 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {selectedStock.name}
              </div>
              <div className="text-lg text-gray-600">
                {selectedStock.code}
              </div>
            </div>
            <Badge variant="outline" className="px-3 py-1">
              분석 대상
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* DINO 테스트 뷰어 */}
      <DinoTestViewer 
        stockCode={selectedStock.code}
        companyName={selectedStock.name}
        key={`${selectedStock.code}-${Date.now()}`} // 종목 변경시 컴포넌트 재마운트
      />

      {/* 사용법 안내 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">사용법 안내</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-2">
          <div className="flex items-start gap-2">
            <Badge variant="outline" className="mt-0.5">1</Badge>
            <div>
              <strong>종목 선택:</strong> 위의 주요 종목 버튼을 클릭하거나 직접 종목코드를 입력합니다.
            </div>
          </div>
          <div className="flex items-start gap-2">
            <Badge variant="outline" className="mt-0.5">2</Badge>
            <div>
              <strong>데이터 로드:</strong> 새로고침 버튼을 클릭하면 실제 DINO API에서 데이터를 가져옵니다.
            </div>
          </div>
          <div className="flex items-start gap-2">
            <Badge variant="outline" className="mt-0.5">3</Badge>
            <div>
              <strong>시각화 확인:</strong> 재무, 기술, 가격, 재료 분석 결과가 차트와 표로 표시됩니다.
            </div>
          </div>
          <div className="flex items-start gap-2">
            <Badge variant="outline" className="mt-0.5">4</Badge>
            <div>
              <strong>실시간 모니터링:</strong> API 연결 상태와 데이터 수집 상태를 실시간으로 확인할 수 있습니다.
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}