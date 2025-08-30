'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  getStockList, 
  getProgramTradeTop50, 
  getKiwoomToken, 
  checkKiwoomHealth,
  KiwoomApiResponse 
} from '@/lib/api/kiwoom-direct';

export default function KiwoomDirectExample() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleApiCall = async (apiCall: () => Promise<KiwoomApiResponse | any>, description: string) => {
    setLoading(true);
    setError(null);
    setResult(null);
    
    try {
      const response = await apiCall();
      setResult({ description, response });
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>키움 어댑터 직접 호출 테스트</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex gap-2 flex-wrap">
              <Button 
                onClick={() => handleApiCall(
                  () => checkKiwoomHealth(),
                  '헬스체크'
                )}
                disabled={loading}
              >
                헬스체크
              </Button>
              
              <Button 
                onClick={() => handleApiCall(
                  () => getKiwoomToken(),
                  '토큰 발급 (fn_au10001)'
                )}
                disabled={loading}
              >
                토큰 발급
              </Button>
              
              <Button 
                onClick={() => handleApiCall(
                  () => getStockList({ mrkt_tp: '0' }),
                  '코스피 종목 리스트 (fn_ka10099)'
                )}
                disabled={loading}
              >
                코스피 종목 리스트
              </Button>
              
              <Button 
                onClick={() => handleApiCall(
                  () => getProgramTradeTop50({
                    trde_upper_tp: '2', // 순매수상위
                    amt_qty_tp: '1',    // 금액
                    mrkt_tp: 'P00101',  // 코스피
                    stex_tp: '1'        // KRX
                  }),
                  '프로그램 거래 Top50 (fn_ka90003)'
                )}
                disabled={loading}
              >
                프로그램 거래 Top50
              </Button>
            </div>

            {loading && (
              <div className="text-center py-4">
                <div className="animate-spin inline-block w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                <p className="mt-2 text-sm text-gray-600">API 호출 중...</p>
              </div>
            )}

            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-800 font-medium">오류 발생:</p>
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}

            {result && (
              <div className="space-y-2">
                <h3 className="font-medium text-lg">{result.description} 결과:</h3>
                <pre className="bg-gray-100 p-4 rounded-lg text-xs overflow-auto max-h-96">
                  {JSON.stringify(result.response, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}