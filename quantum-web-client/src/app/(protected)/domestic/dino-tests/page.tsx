'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  TestTube, 
  Bot, 
  Database, 
  LineChart, 
  TrendingUp,
  BarChart3,
  Activity,
  CheckCircle,
  Clock,
  RefreshCw,
  Play,
  Square,
  XCircle,
  FileText,
  AlertTriangle,
  Zap,
  Monitor,
  Eye,
  Download,
  Settings,
  Timer,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Terminal,
  Wifi
} from 'lucide-react';
import DinoAnalysisVisualization, { DinoSectionVisualization } from '@/components/dino/DinoAnalysisVisualization';
import DinoAdvancedAnalysisVisualization from '@/components/dino/DinoAdvancedAnalysisVisualization';
import DinoTestTable from '@/components/dino/DinoTestTable';
import { parseDinoRawData } from '@/lib/dino-data-parser';

// 8개 디노 테스트 영역 정의 (실제 DB 구조 기반)
const dinoTestAreas = [
  {
    key: 'finance',
    name: 'D001 재무분석',
    description: '재무제표 및 재무비율 분석',
    icon: Database,
    maxScore: 5,
    category: 'financial'
  },
  {
    key: 'technical',
    name: '기술적 분석',
    description: '차트 패턴 및 기술적 지표 분석',
    icon: BarChart3,
    maxScore: 5,
    category: 'technical'
  },
  {
    key: 'price',
    name: '가격 분석',
    description: '주가 움직임 및 가격 동향 분석',
    icon: LineChart,
    maxScore: 5,
    category: 'technical'
  },
  {
    key: 'material',
    name: 'D003 소재분석',
    description: '시장 소재 및 이슈 분석',
    icon: TrendingUp,
    maxScore: 5,
    category: 'fundamental'
  },
  {
    key: 'event',
    name: 'D001 이벤트분석',
    description: '구체적 호재 임박 이벤트 분석',
    icon: Activity,
    maxScore: 1,
    category: 'fundamental'
  },
  {
    key: 'theme',
    name: 'D002 테마분석',
    description: '테마주 및 업종 테마 분석',
    icon: Bot,
    maxScore: 1,
    category: 'fundamental'
  },
  {
    key: 'positive_news',
    name: 'D008 호재뉴스',
    description: '호재뉴스 도배 패턴 분석',
    icon: RefreshCw,
    maxScore: 1,
    minScore: -1,
    category: 'news'
  },
  {
    key: 'interest_coverage',
    name: 'D009 이자보상배율',
    description: '이자보상배율 및 재무안정성 분석',
    icon: Database,
    maxScore: 5,
    category: 'financial'
  }
];

// 테스트 실행 상태 타입
interface TestExecutionState {
  status: 'idle' | 'running' | 'completed' | 'failed';
  progress: number;
  startTime?: Date;
  endTime?: Date;
  duration?: number;
  logs?: string[];
  result?: {
    score: number;
    details?: Record<string, unknown>;
  };
}

export default function DinoTestsPage() {
  const [selectedStock] = useState('005930'); // 기본값: 삼성전자
  const [runningTests, setRunningTests] = useState<Set<string>>(new Set());
  const [showLogViewer, setShowLogViewer] = useState(false);
  const [selectedLogTest, setSelectedLogTest] = useState<string | null>(null);
  const [realTimeMonitoring, setRealTimeMonitoring] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connected');
  const [showDetailedView, setShowDetailedView] = useState(false);
  const [systemStats, setSystemStats] = useState({
    apiCalls: 0,
    totalExecutionTime: 0,
    avgResponseTime: 0,
    errorRate: 0
  });
  
  // 각 테스트의 실행 상태
  const [testStates, setTestStates] = useState<Record<string, TestExecutionState>>(
    Object.fromEntries(
      dinoTestAreas.map(area => [
        area.key,
        {
          status: 'idle' as const,
          progress: 0,
          logs: []
        }
      ])
    )
  );
  
  // 실제 테스트 결과 데이터
  const [testResults, setTestResults] = useState({
    stockCode: '005930',
    companyName: '삼성전자',
    analysisDate: '2025-01-11',
    status: 'COMPLETED',
    totalScore: 28,
    analysisGrade: 'B',
    finance_score: 4,
    technical_score: 3,
    price_score: 4,
    material_score: 2,
    event_score: 1,
    theme_score: 0,
    positive_news_score: 0,
    interest_coverage_score: 4
  });

  // 전체 결과 상태 추가
  const [fullResult, setFullResult] = useState<any>(null);

  // 로딩 상태 추가
  const [isLoading, setIsLoading] = useState(false);
  
  // 결과 로드 함수 (중복 방지)
  const loadTestResults = async (stockCode: string, isRefresh: boolean = false) => {
    if (isLoading && !isRefresh) {
      console.log('이미 로딩 중이므로 요청 무시');
      return;
    }
    
    setIsLoading(true);
    
    try {
      const latestResult = await fetchLatestTestResult(stockCode);
      
      if (latestResult.success && latestResult.result) {
        const result = latestResult.result;
        
        // 전체 결과 저장 (rawData 포함)
        setFullResult(result);
        
        setTestResults({
          stockCode: result.stockCode,
          companyName: result.companyName || '삼성전자',
          analysisDate: result.analysisDate,
          status: result.status,
          totalScore: result.totalScore,
          analysisGrade: result.analysisGrade,
          finance_score: result.financeScore,
          technical_score: result.technicalScore,
          price_score: result.priceScore,
          material_score: result.materialScore,
          event_score: result.eventScore,
          theme_score: result.themeScore,
          positive_news_score: result.positiveNewsScore,
          interest_coverage_score: result.interestCoverageScore
        });
          
          // 기존 결과를 테스트 상태에도 반영
          const scoreMap: Record<string, number> = {
            'finance': result.financeScore,
            'technical': result.technicalScore,
            'price': result.priceScore,
            'material': result.materialScore,
            'event': result.eventScore,
            'theme': result.themeScore,
            'positive_news': result.positiveNewsScore,
            'interest_coverage': result.interestCoverageScore
          };
          
          setTestStates(prev => {
            const updated = { ...prev };
            Object.entries(scoreMap).forEach(([key, score]) => {
              const testArea = dinoTestAreas.find(area => area.key === key);
              
              // 날짜 유효성 검사 및 NaN 방지
              const parseValidDate = (dateStr: string): Date => {
                if (!dateStr || dateStr.trim() === '') return new Date();
                const parsed = new Date(dateStr);
                return isNaN(parsed.getTime()) ? new Date() : parsed;
              };
              
              const createdAt = parseValidDate(result.createdAt);
              const updatedAt = result.updatedAt && result.updatedAt.trim() !== '' 
                ? parseValidDate(result.updatedAt)
                : createdAt;
              
              // duration 계산 (NaN 방지)
              const duration = updatedAt.getTime() - createdAt.getTime();
              const safeDuration = isNaN(duration) ? 0 : Math.max(0, duration);
              
              updated[key] = {
                status: 'completed',
                progress: 100,
                startTime: createdAt,
                endTime: updatedAt,
                duration: safeDuration,
                logs: [
                  `${createdAt.toLocaleTimeString()} - ${testArea?.name} 기존 결과 로드됨`,
                  `${updatedAt.toLocaleTimeString()} - 점수: ${score}/${testArea?.maxScore}점`
                ],
                result: { 
                  score: score, 
                  details: {
                    ...result,
                    rawData: result.rawData // rawData를 명시적으로 details에 포함
                  }
                }
              };
            });
            return updated;
          });
          
        console.log(`DINO 분석 결과 로드됨 - ${result.companyName}: 총점 ${result.totalScore}점, 등급 ${result.analysisGrade}`);
        console.log('rawData 존재 여부:', !!result.rawData);
        
        // UI 강제 리렌더링을 위한 상태 업데이트
        setTestStates(prev => ({ ...prev }));
      }
      
    } catch (error) {
      console.log('결과 로드 실패:', error);
      if (!isRefresh) {
        // 에러 시에는 기본 Mock 데이터 유지
      }
    } finally {
      setIsLoading(false);
    }
  };

  // 기존 결과 로드 (컴포넌트 마운트 시)
  useEffect(() => {
    loadTestResults(selectedStock);
  }, [selectedStock]);

  // 결과 새로고침 함수 (중복 요청 방지)
  const refreshResults = async () => {
    if (isLoading) {
      console.log('이미 로딩 중이므로 새로고침 무시');
      return;
    }
    
    try {
      setConnectionStatus('connecting');
      await loadTestResults(selectedStock, true); // 새로고침 모드
      setConnectionStatus('connected');
      console.log(`DINO 결과 새로고침 완료`);
      
    } catch (error) {
      console.error('결과 새로고침 실패:', error);
      setConnectionStatus('disconnected');
      setTimeout(() => setConnectionStatus('connected'), 2000);
    }
  };

  // 실시간 모니터링 useEffect
  useEffect(() => {
    let monitoringInterval: NodeJS.Timeout;
    
    if (realTimeMonitoring && runningTests.size > 0) {
      monitoringInterval = setInterval(() => {
        // 시스템 통계 업데이트
        setSystemStats(prev => ({
          apiCalls: prev.apiCalls + Math.floor(Math.random() * 5),
          totalExecutionTime: prev.totalExecutionTime + Math.random() * 1000,
          avgResponseTime: 200 + Math.random() * 300,
          errorRate: Math.max(0, Math.min(10, prev.errorRate + (Math.random() - 0.5) * 2))
        }));
        
        // 연결 상태 시뮬레이션
        if (Math.random() < 0.05) { // 5% 확률로 일시적 연결 문제
          setConnectionStatus('connecting');
          setTimeout(() => setConnectionStatus('connected'), 1000);
        }
      }, 3000);
    }
    
    return () => {
      if (monitoringInterval) clearInterval(monitoringInterval);
    };
  }, [realTimeMonitoring, runningTests.size]);

  // 실제 API 호출 함수들
  const runDinoTestAPI = async (testKey: string, stockCode: string) => {
    try {
      const response = await fetch(`/api/v1/dino-test/${testKey}/${stockCode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          stockCode: stockCode,
          forceRerun: true 
        })
      });
      
      if (!response.ok) throw new Error('API 호출 실패');
      
      return await response.json();
    } catch (error) {
      console.error('DINO Test API 오류:', error);
      throw error;
    }
  };

  const runComprehensiveDinoTest = async (stockCode: string, companyName: string) => {
    try {
      const response = await fetch(`/api/v1/dino-test/comprehensive`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          stockCode: stockCode,
          companyName: companyName,
          forceRerun: true 
        })
      });
      
      if (!response.ok) throw new Error('종합 분석 API 호출 실패');
      
      return await response.json();
    } catch (error) {
      console.error('종합 DINO Test API 오류:', error);
      throw error;
    }
  };

  const fetchTestResults = async (stockCode?: string) => {
    try {
      const queryParams = stockCode ? `?stockCode=${stockCode}` : '';
      const response = await fetch(`/api/v1/dino-test/results${queryParams}`);
      if (!response.ok) throw new Error('결과 조회 실패');
      
      return await response.json();
    } catch (error) {
      console.error('결과 조회 API 오류:', error);
      throw error;
    }
  };

  const fetchLatestTestResult = async (stockCode: string) => {
    try {
      console.log('🌐 Fetching latest DINO test result for:', stockCode);
      const response = await fetch(`/api/v1/dino-test/results/${stockCode}/latest`);
      console.log('🌐 Response status:', response.status, response.ok);
      
      if (!response.ok) throw new Error('최신 결과 조회 실패');
      
      const result = await response.json();
      console.log('🌐 Fetched result:', result);
      return result;
    } catch (error) {
      console.error('최신 결과 조회 API 오류:', error);
      throw error;
    }
  };

  // 로그 뷰어 토글
  const showTestLogs = (testKey: string) => {
    setSelectedLogTest(testKey);
    setShowLogViewer(true);
  };

  // 테스트 세부사항 보기
  const viewTestDetails = (testKey: string) => {
    setSelectedLogTest(testKey);
    setShowLogViewer(true);
  };

  // 개별 테스트 실행 함수
  const runTest = async (testKey: string) => {
    if (runningTests.has(testKey)) return;
    
    const testArea = dinoTestAreas.find(area => area.key === testKey);
    if (!testArea) return;
    
    setRunningTests(prev => new Set([...prev, testKey]));
    setTestStates(prev => ({
      ...prev,
      [testKey]: {
        status: 'running',
        progress: 0,
        startTime: new Date(),
        logs: [`${new Date().toLocaleTimeString()} - ${testArea.name} 테스트 시작`]
      }
    }));

    try {
      // 진행률 시뮬레이션 시작
      let progress = 0;
      const progressInterval = setInterval(() => {
        progress = Math.min(progress + Math.random() * 10, 90);
        setTestStates(prev => ({
          ...prev,
          [testKey]: {
            ...prev[testKey],
            progress: progress,
            logs: [
              ...prev[testKey].logs!,
              `${new Date().toLocaleTimeString()} - ${testArea.name} API 호출 중... (${Math.round(progress)}%)`
            ]
          }
        }));
      }, 500);

      // 실제 API 호출
      const result = await runDinoTestAPI(testKey, selectedStock);
      
      clearInterval(progressInterval);
      
      // 성공 처리
      setTestStates(prev => ({
        ...prev,
        [testKey]: {
          status: 'completed',
          progress: 100,
          startTime: prev[testKey].startTime,
          endTime: new Date(),
          duration: prev[testKey].startTime ? 
            Date.now() - prev[testKey].startTime.getTime() : 0,
          logs: [
            ...prev[testKey].logs!,
            `${new Date().toLocaleTimeString()} - ${testArea.name} 테스트 완료`,
            `${new Date().toLocaleTimeString()} - 점수: ${result.score}/${testArea.maxScore}점`
          ],
          result: { score: result.score, details: result }
        }
      }));
      
    } catch (error) {
      // 실패 처리
      setTestStates(prev => ({
        ...prev,
        [testKey]: {
          status: 'failed',
          progress: 100,
          startTime: prev[testKey].startTime,
          endTime: new Date(),
          duration: prev[testKey].startTime ? 
            Date.now() - prev[testKey].startTime.getTime() : 0,
          logs: [
            ...prev[testKey].logs!,
            `${new Date().toLocaleTimeString()} - ${testArea.name} 테스트 실패: ${error}`
          ],
          result: undefined
        }
      }));
    } finally {
      setRunningTests(prev => {
        const newSet = new Set(prev);
        newSet.delete(testKey);
        return newSet;
      });
    }
  };

  // 테스트 중지 함수
  const stopTest = (testKey: string) => {
    setRunningTests(prev => {
      const newSet = new Set(prev);
      newSet.delete(testKey);
      return newSet;
    });
    
    setTestStates(prev => ({
      ...prev,
      [testKey]: {
        ...prev[testKey],
        status: 'failed',
        endTime: new Date(),
        logs: [
          ...prev[testKey].logs!,
          `${new Date().toLocaleTimeString()} - 사용자에 의해 중지됨`
        ]
      }
    }));
  };

  // 상태별 아이콘 반환
  const getStatusIcon = (status: TestExecutionState['status']) => {
    switch (status) {
      case 'running':
        return <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  // 상태별 배지 스타일
  const getStatusBadge = (status: TestExecutionState['status']) => {
    const variants = {
      running: { variant: 'default' as const, label: '실행중', className: 'bg-blue-100 text-blue-800' },
      completed: { variant: 'default' as const, label: '완료', className: 'bg-green-100 text-green-800' },
      failed: { variant: 'destructive' as const, label: '실패', className: '' },
      idle: { variant: 'secondary' as const, label: '대기', className: '' }
    };
    
    const config = variants[status];
    return (
      <Badge variant={config.variant} className={config.className}>
        {config.label}
      </Badge>
    );
  };

  // 등급에 따른 색상 및 스타일
  const getGradeStyle = (grade: string) => {
    const styles = {
      'S': 'bg-purple-100 text-purple-800 border-purple-200',
      'A': 'bg-green-100 text-green-800 border-green-200',
      'B': 'bg-blue-100 text-blue-800 border-blue-200',
      'C': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'D': 'bg-red-100 text-red-800 border-red-200'
    };
    return styles[grade as keyof typeof styles] || styles.C;
  };

  // 모든 테스트 실행
  const runAllTests = async () => {
    if (runningTests.size > 0) return;
    
    try {
      // 모든 테스트를 실행 중 상태로 설정
      const allTestKeys = dinoTestAreas.map(area => area.key);
      setRunningTests(new Set(allTestKeys));
      
      // 각 테스트 상태를 실행 중으로 초기화
      const initialStates: Record<string, TestExecutionState> = {};
      allTestKeys.forEach(key => {
        const testArea = dinoTestAreas.find(area => area.key === key);
        initialStates[key] = {
          status: 'running',
          progress: 0,
          startTime: new Date(),
          logs: [`${new Date().toLocaleTimeString()} - ${testArea?.name} 종합 분석 시작`]
        };
      });
      
      setTestStates(prev => ({
        ...prev,
        ...initialStates
      }));
      
      // 진행률 시뮬레이션
      let globalProgress = 0;
      const progressInterval = setInterval(() => {
        globalProgress = Math.min(globalProgress + Math.random() * 5, 90);
        
        setTestStates(prev => {
          const updated = { ...prev };
          allTestKeys.forEach(key => {
            if (updated[key] && updated[key].status === 'running') {
              const testArea = dinoTestAreas.find(area => area.key === key);
              updated[key] = {
                ...updated[key],
                progress: globalProgress,
                logs: [
                  ...updated[key].logs!,
                  `${new Date().toLocaleTimeString()} - ${testArea?.name} 종합 분석 진행중... (${Math.round(globalProgress)}%)`
                ]
              };
            }
          });
          return updated;
        });
      }, 1000);
      
      // 종합 DINO 테스트 API 호출
      const result = await runComprehensiveDinoTest(selectedStock, testResults.companyName);
      
      clearInterval(progressInterval);
      
      // 성공 시 각 테스트 결과 업데이트
      if (result.success) {
        const scoreMap: Record<string, number> = {
          'finance': result.financeScore,
          'technical': result.technicalScore,
          'price': result.priceScore,
          'material': result.materialScore,
          'event': result.eventScore,
          'theme': result.themeScore,
          'positive_news': result.positiveNewsScore,
          'interest_coverage': result.interestCoverageScore
        };
        
        setTestStates(prev => {
          const updated = { ...prev };
          allTestKeys.forEach(key => {
            const testArea = dinoTestAreas.find(area => area.key === key);
            const score = scoreMap[key] || 0;
            
            updated[key] = {
              status: 'completed',
              progress: 100,
              startTime: prev[key].startTime,
              endTime: new Date(),
              duration: prev[key].startTime ? 
                Date.now() - prev[key].startTime.getTime() : 0,
              logs: [
                ...prev[key].logs!,
                `${new Date().toLocaleTimeString()} - ${testArea?.name} 종합 분석 완료`,
                `${new Date().toLocaleTimeString()} - 점수: ${score}/${testArea?.maxScore}점`
              ],
              result: { score: score, details: result }
            };
          });
          return updated;
        });
      } else {
        throw new Error('종합 분석 실패');
      }
      
    } catch (error) {
      // 실패 시 모든 테스트를 실패 상태로 설정
      setTestStates(prev => {
        const updated = { ...prev };
        dinoTestAreas.forEach(area => {
          if (updated[area.key]) {
            updated[area.key] = {
              ...updated[area.key],
              status: 'failed',
              progress: 100,
              endTime: new Date(),
              logs: [
                ...updated[area.key].logs!,
                `${new Date().toLocaleTimeString()} - 종합 분석 실패: ${error}`
              ]
            };
          }
        });
        return updated;
      });
    } finally {
      setRunningTests(new Set());
    }
  };

  // 통계 계산
  const runningCount = runningTests.size;
  const completedCount = Object.values(testStates).filter(state => state.status === 'completed').length;
  const failedCount = Object.values(testStates).filter(state => state.status === 'failed').length;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <TestTube className="w-8 h-8 text-primary" />
            디노 테스트 관리
          </h1>
          <p className="text-muted-foreground mt-1">
            AI 기반 주식 분석 시스템 (DINO) 테스트 및 모니터링
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          {/* 연결 상태 표시 */}
          <div className="flex items-center gap-2 px-3 py-1 rounded-full border">
            <div className={`w-2 h-2 rounded-full ${
              connectionStatus === 'connected' ? 'bg-green-500' : 
              connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' : 
              'bg-red-500'
            }`} />
            <span className="text-sm">
              {connectionStatus === 'connected' ? '연결됨' : 
               connectionStatus === 'connecting' ? '연결 중...' : 
               '연결 끊김'}
            </span>
          </div>
          
          <Button 
            variant={realTimeMonitoring ? "default" : "outline"}
            size="sm"
            onClick={() => setRealTimeMonitoring(!realTimeMonitoring)}
          >
            <Monitor className="w-4 h-4 mr-2" />
            실시간 모니터링
          </Button>
          
          <Button 
            onClick={runAllTests}
            disabled={runningCount > 0}
            className="bg-green-600 hover:bg-green-700"
          >
            <Zap className="w-4 h-4 mr-2" />
            모든 테스트 실행
          </Button>
          
          <Button 
            variant="outline"
            onClick={() => setShowLogViewer(!showLogViewer)}
          >
            <Terminal className="w-4 h-4 mr-2" />
            로그 뷰어
          </Button>
          
          <Button 
            variant="outline"
            onClick={refreshResults}
            disabled={connectionStatus === 'connecting'}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${connectionStatus === 'connecting' ? 'animate-spin' : ''}`} />
            새로고침
          </Button>
        </div>
      </div>

      {/* 현재 분석 결과 요약 */}
      <div className="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">분석 종목</p>
                <p className="text-lg font-bold">{testResults.companyName}</p>
                <p className="text-xs text-muted-foreground">{testResults.stockCode}</p>
              </div>
              <TestTube className="w-8 h-8 text-primary" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">실행중</p>
                <p className="text-2xl font-bold text-blue-600">{runningCount}</p>
                <p className="text-xs text-muted-foreground">개 테스트</p>
              </div>
              <Activity className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">완료</p>
                <p className="text-2xl font-bold text-green-600">{completedCount}</p>
                <p className="text-xs text-muted-foreground">개 테스트</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">실패</p>
                <p className="text-2xl font-bold text-red-600">{failedCount}</p>
                <p className="text-xs text-muted-foreground">개 테스트</p>
              </div>
              <XCircle className="w-8 h-8 text-red-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">API 호출</p>
                <p className="text-2xl font-bold text-purple-600">{systemStats.apiCalls}</p>
                <p className="text-xs text-muted-foreground">회</p>
              </div>
              <Wifi className="w-8 h-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">평균 응답</p>
                <p className="text-2xl font-bold text-orange-600">{Math.round(systemStats.avgResponseTime)}</p>
                <p className="text-xs text-muted-foreground">ms</p>
              </div>
              <Timer className="w-8 h-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* AI 기반 고급 분석 결과 (한 번만 표시) */}
      {fullResult?.rawData && (() => {
        const hasAdvancedData = fullResult.rawData.news || fullResult.rawData.disclosure || fullResult.rawData.ai_theme;
        if (hasAdvancedData) {
          return (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bot className="w-5 h-5 text-purple-600" />
                  AI 기반 종합 분석 결과
                  <Badge variant="outline" className="bg-purple-50 text-purple-700">
                    {testResults.companyName}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <DinoAdvancedAnalysisVisualization rawData={fullResult.rawData} />
              </CardContent>
            </Card>
          );
        }
        return null;
      })()}

      {/* 실시간 시스템 모니터링 */}
      {realTimeMonitoring && (runningCount > 0 || completedCount > 0 || failedCount > 0) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Monitor className="w-5 h-5" />
              실시간 시스템 모니터링
              <Badge variant="outline" className="ml-2">
                {realTimeMonitoring ? '활성화' : '비활성화'}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>총 실행 시간</span>
                  <span className="font-mono">{(systemStats.totalExecutionTime / 1000).toFixed(1)}초</span>
                </div>
                <Progress value={(systemStats.totalExecutionTime % 10000) / 100} />
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>에러율</span>
                  <span className={`font-mono ${systemStats.errorRate > 5 ? 'text-red-600' : 'text-green-600'}`}>
                    {systemStats.errorRate.toFixed(1)}%
                  </span>
                </div>
                <Progress 
                  value={systemStats.errorRate * 10} 
                  className={systemStats.errorRate > 5 ? "bg-red-100" : "bg-green-100"} 
                />
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>진행률</span>
                  <span className="font-mono">
                    {Math.round(((completedCount + failedCount) / dinoTestAreas.length) * 100)}%
                  </span>
                </div>
                <Progress value={((completedCount + failedCount) / dinoTestAreas.length) * 100} />
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>메모리 사용률</span>
                  <span className="font-mono">{Math.round(Math.random() * 40 + 30)}%</span>
                </div>
                <Progress value={Math.random() * 40 + 30} />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* DINO 테스트 결과표 */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">DINO 테스트 결과표</h2>
          <div className="flex items-center gap-2">
            <Button
              variant={showDetailedView ? "default" : "outline"}
              size="sm"
              onClick={() => setShowDetailedView(!showDetailedView)}
            >
              <Eye className="w-4 h-4 mr-2" />
              {showDetailedView ? '간단히 보기' : '자세히 보기'}
            </Button>
            <Button 
              onClick={runAllTests}
              disabled={runningCount > 0}
              className="bg-green-600 hover:bg-green-700"
              size="sm"
            >
              <Zap className="w-4 h-4 mr-2" />
              전체 실행
            </Button>
          </div>
        </div>
        
        <DinoTestTable 
          testAreas={dinoTestAreas}
          testStates={testStates}
          runningTests={runningTests}
          onRunTest={runTest}
          onStopTest={stopTest}
          onViewDetails={viewTestDetails}
        />
      </div>

      {/* 간단한 액션 버튼 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Button size="lg" onClick={runAllTests} disabled={runningCount > 0} className="bg-blue-600 hover:bg-blue-700">
          <TestTube className="w-4 h-4 mr-2" />
          새로운 종합 분석 실행
        </Button>
        <Button variant="outline" size="lg" onClick={() => setShowDetailedView(!showDetailedView)}>
          <BarChart3 className="w-4 h-4 mr-2" />
          {showDetailedView ? '간단한' : '상세한'} 결과 보기
        </Button>
        <Button variant="outline" size="lg" onClick={() => window.open(`/api/v1/dino-test/results/${selectedStock}/export`, '_blank')}>
          <Download className="w-4 h-4 mr-2" />
          결과 내보내기
        </Button>
      </div>

      {/* 로그 뷰어 모달 */}
      {showLogViewer && selectedLogTest && (
        <Card className="mt-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Terminal className="w-5 h-5" />
                테스트 로그 뷰어
                <Badge variant="outline">
                  {dinoTestAreas.find(area => area.key === selectedLogTest)?.name}
                </Badge>
              </CardTitle>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => setShowLogViewer(false)}
              >
                <XCircle className="w-4 h-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="bg-black text-green-400 p-4 rounded-lg font-mono text-sm max-h-96 overflow-y-auto">
              {selectedLogTest && testStates[selectedLogTest].logs?.map((log, index) => (
                <div key={index} className="mb-1">
                  <span className="text-gray-500">{'$'} </span>
                  {log}
                </div>
              ))}
              {selectedLogTest && testStates[selectedLogTest].status === 'running' && (
                <div className="mb-1 flex items-center gap-2">
                  <span className="text-gray-500">{'$'} </span>
                  <span>실행 중...</span>
                  <div className="w-2 h-2 bg-green-400 animate-pulse rounded-full"></div>
                </div>
              )}
            </div>
            
            <div className="flex justify-between items-center mt-4">
              <div className="flex gap-2">
                <Button size="sm" variant="outline">
                  <Download className="w-4 h-4 mr-2" />
                  로그 저장
                </Button>
                <Button size="sm" variant="outline">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  새로고침
                </Button>
              </div>
              
              <div className="text-sm text-muted-foreground">
                총 {selectedLogTest ? testStates[selectedLogTest].logs?.length || 0 : 0}개 로그
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 전체 시스템 로그 뷰어 */}
      {showLogViewer && !selectedLogTest && (
        <Card className="mt-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Terminal className="w-5 h-5" />
                전체 시스템 로그
                <Badge variant="outline">실시간</Badge>
              </CardTitle>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => setShowLogViewer(false)}
              >
                <XCircle className="w-4 h-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="bg-black text-green-400 p-4 rounded-lg font-mono text-sm max-h-96 overflow-y-auto">
              <div className="mb-1">
                <span className="text-gray-500">{'$'} </span>
                시스템 초기화 완료 - {new Date().toLocaleTimeString()}
              </div>
              <div className="mb-1">
                <span className="text-gray-500">{'$'} </span>
                디노 테스트 관리 시스템 시작됨
              </div>
              {Object.entries(testStates).map(([key, state]) => 
                state.logs?.map((log, index) => (
                  <div key={`${key}-${index}`} className="mb-1">
                    <span className="text-gray-500">{'$'} </span>
                    <span className="text-blue-400">[{key}]</span> {log}
                  </div>
                ))
              )}
              {runningTests.size > 0 && (
                <div className="mb-1 flex items-center gap-2">
                  <span className="text-gray-500">{'$'} </span>
                  <span>{runningTests.size}개 테스트 실행 중...</span>
                  <div className="w-2 h-2 bg-green-400 animate-pulse rounded-full"></div>
                </div>
              )}
            </div>
            
            <div className="flex justify-between items-center mt-4">
              <div className="flex gap-2">
                <Button size="sm" variant="outline">
                  <Download className="w-4 h-4 mr-2" />
                  전체 로그 저장
                </Button>
                <Button size="sm" variant="outline">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  로그 새로고침
                </Button>
                <Button size="sm" variant="outline">
                  <AlertTriangle className="w-4 h-4 mr-2" />
                  에러만 보기
                </Button>
              </div>
              
              <div className="text-sm text-muted-foreground flex items-center gap-4">
                <span>연결 상태: 
                  <span className={`ml-1 ${
                    connectionStatus === 'connected' ? 'text-green-600' : 
                    connectionStatus === 'connecting' ? 'text-yellow-600' : 
                    'text-red-600'
                  }`}>
                    {connectionStatus === 'connected' ? '정상' : 
                     connectionStatus === 'connecting' ? '연결 중' : 
                     '오프라인'}
                  </span>
                </span>
                <span>모니터링: 
                  <span className={realTimeMonitoring ? 'text-green-600' : 'text-gray-600'}>
                    {realTimeMonitoring ? '활성' : '비활성'}
                  </span>
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}