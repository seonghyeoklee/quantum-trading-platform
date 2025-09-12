'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Clock,
  Database,
  BarChart3,
  TrendingUp,
  Activity
} from 'lucide-react';
import DinoAnalysisVisualization from './DinoAnalysisVisualization';
import { fetchComprehensiveDinoData, checkDinoApiHealth } from '@/lib/dino-api-client';
import { parseDinoRawData, DinoRawData, DinoAnalysisData } from '@/lib/dino-data-parser';

interface DinoTestViewerProps {
  stockCode?: string;
  companyName?: string;
}

export default function DinoTestViewer({ 
  stockCode = '005930', 
  companyName = '삼성전자' 
}: DinoTestViewerProps) {
  const [loading, setLoading] = useState(false);
  const [apiHealthy, setApiHealthy] = useState(false);
  const [rawData, setRawData] = useState<DinoRawData | null>(null);
  const [parsedData, setParsedData] = useState<DinoAnalysisData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // API 헬스체크
  useEffect(() => {
    const checkHealth = async () => {
      const healthy = await checkDinoApiHealth();
      setApiHealthy(healthy);
      console.log('DINO API Health:', healthy);
    };
    
    checkHealth();
    const interval = setInterval(checkHealth, 30000); // 30초마다 헬스체크
    
    return () => clearInterval(interval);
  }, []);

  // 실제 DINO 데이터 가져오기 및 파싱
  const fetchAndParseData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log(`Starting DINO data fetch for ${stockCode} (${companyName})`);
      
      // 1. 종합 DINO 데이터 수집
      const comprehensive = await fetchComprehensiveDinoData(stockCode);
      setRawData(comprehensive);
      console.log('Raw data fetched:', comprehensive);
      
      // 2. 파싱하여 시각화용 데이터로 변환
      const parsed = parseDinoRawData(comprehensive);
      setParsedData(parsed);
      console.log('Parsed data:', parsed);
      
      if (parsed) {
        setLastUpdated(new Date());
        console.log(`✅ DINO 분석 완료: ${stockCode} - 총점 ${parsed.평가점수.총점}점`);
      } else {
        setError('데이터 파싱에 실패했습니다.');
      }
      
    } catch (error) {
      console.error('DINO test error:', error);
      setError(error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // 초기 로드
  useEffect(() => {
    if (apiHealthy) {
      fetchAndParseData();
    }
  }, [stockCode, apiHealthy]);

  const getHealthStatusIcon = () => {
    if (apiHealthy) return <CheckCircle className="w-4 h-4 text-green-600" />;
    return <XCircle className="w-4 h-4 text-red-600" />;
  };

  const getHealthStatusText = () => {
    return apiHealthy ? 'API 연결됨' : 'API 연결 실패';
  };

  return (
    <div className="space-y-6">
      {/* 제어 패널 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              DINO 실시간 테스트 뷰어
            </div>
            <div className="flex items-center gap-2">
              {getHealthStatusIcon()}
              <Badge variant={apiHealthy ? "default" : "destructive"} className="text-xs">
                {getHealthStatusText()}
              </Badge>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-lg font-semibold">{companyName}</div>
              <div className="text-sm text-gray-600">{stockCode}</div>
              {lastUpdated && (
                <div className="text-xs text-gray-500 mt-1">
                  마지막 업데이트: {lastUpdated.toLocaleString()}
                </div>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button 
                onClick={fetchAndParseData} 
                disabled={loading || !apiHealthy}
                size="sm"
                className="flex items-center gap-2"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                {loading ? '분석 중...' : '새로고침'}
              </Button>
            </div>
          </div>

          {loading && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Clock className="w-4 h-4 animate-pulse" />
              DINO API에서 데이터를 가져오는 중입니다...
              <Progress value={undefined} className="flex-1 h-2" />
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-50 rounded-lg border border-red-200">
              <AlertCircle className="w-4 h-4 text-red-600" />
              <span className="text-sm text-red-700">{error}</span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 데이터 상태 정보 */}
      {rawData && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="w-5 h-5" />
              데이터 수집 상태
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4" />
                <span className="text-sm">재무분석</span>
                {rawData.financeData?.success ? 
                  <CheckCircle className="w-4 h-4 text-green-600" /> : 
                  <XCircle className="w-4 h-4 text-red-600" />
                }
              </div>
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4" />
                <span className="text-sm">기술분석</span>
                {rawData.technicalData?.success ? 
                  <CheckCircle className="w-4 h-4 text-green-600" /> : 
                  <XCircle className="w-4 h-4 text-red-600" />
                }
              </div>
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                <span className="text-sm">가격분석</span>
                {rawData.priceData?.success ? 
                  <CheckCircle className="w-4 h-4 text-green-600" /> : 
                  <XCircle className="w-4 h-4 text-red-600" />
                }
              </div>
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4" />
                <span className="text-sm">소재분석</span>
                {rawData.materialData?.success ? 
                  <CheckCircle className="w-4 h-4 text-green-600" /> : 
                  <XCircle className="w-4 h-4 text-red-600" />
                }
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 시각화 결과 */}
      {parsedData ? (
        <DinoAnalysisVisualization data={parsedData} />
      ) : !loading && !error && (
        <Card>
          <CardContent className="text-center py-8">
            <div className="text-gray-500 mb-2">분석 데이터를 가져오려면 새로고침 버튼을 클릭하세요</div>
            <div className="text-sm text-gray-400">
              {apiHealthy ? 'API 연결이 정상입니다' : 'API 연결을 확인해주세요'}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 디버깅용 Raw 데이터 (개발 모드에서만 표시) */}
      {process.env.NODE_ENV === 'development' && rawData && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Raw Data (개발 모드)</CardTitle>
          </CardHeader>
          <CardContent>
            <details className="cursor-pointer">
              <summary className="text-xs text-gray-600 hover:text-gray-800">
                원시 데이터 보기 (클릭하여 펼치기)
              </summary>
              <pre className="mt-2 p-2 bg-gray-50 rounded border text-xs overflow-auto max-h-48">
                {JSON.stringify(rawData, null, 2)}
              </pre>
            </details>
          </CardContent>
        </Card>
      )}
    </div>
  );
}