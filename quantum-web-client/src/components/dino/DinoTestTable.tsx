'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  RefreshCw, 
  Play, 
  Eye,
  TrendingUp,
  TrendingDown,
  Minus,
  ChevronRight,
  ChevronDown,
  AlertTriangle
} from 'lucide-react';
import { useState, useEffect } from 'react';
import DinoTestTableMobile from './DinoTestTableMobile';

// DINO 테스트 영역 타입 정의
interface DinoTestArea {
  key: string;
  name: string;
  description: string;
  icon: any;
  maxScore: number;
  minScore?: number;
  category: string;
}

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

interface DinoTestTableProps {
  testAreas: DinoTestArea[];
  testStates: Record<string, TestExecutionState>;
  runningTests: Set<string>;
  onRunTest: (testKey: string) => void;
  onStopTest: (testKey: string) => void;
  onViewDetails: (testKey: string) => void;
}

export default function DinoTestTable({ 
  testAreas, 
  testStates, 
  runningTests, 
  onRunTest, 
  onStopTest, 
  onViewDetails 
}: DinoTestTableProps) {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [isMobile, setIsMobile] = useState(false);

  // 모바일 화면 감지
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // 점수에 따른 색상 및 스타일 반환
  const getScoreStyle = (score: number, maxScore: number, minScore = 0) => {
    const range = maxScore - minScore;
    const normalizedScore = (score - minScore) / range;
    
    if (normalizedScore >= 0.8) {
      return {
        bgColor: 'bg-green-100',
        textColor: 'text-green-800',
        borderColor: 'border-green-200',
        icon: <TrendingUp className="w-4 h-4" />
      };
    } else if (normalizedScore >= 0.6) {
      return {
        bgColor: 'bg-blue-100',
        textColor: 'text-blue-800',
        borderColor: 'border-blue-200',
        icon: <TrendingUp className="w-4 h-4" />
      };
    } else if (normalizedScore >= 0.4) {
      return {
        bgColor: 'bg-yellow-100',
        textColor: 'text-yellow-800',
        borderColor: 'border-yellow-200',
        icon: <Minus className="w-4 h-4" />
      };
    } else if (normalizedScore >= 0.2) {
      return {
        bgColor: 'bg-orange-100',
        textColor: 'text-orange-800',
        borderColor: 'border-orange-200',
        icon: <TrendingDown className="w-4 h-4" />
      };
    } else {
      return {
        bgColor: 'bg-red-100',
        textColor: 'text-red-800',
        borderColor: 'border-red-200',
        icon: <TrendingDown className="w-4 h-4" />
      };
    }
  };

  // 상태별 배지 반환
  const getStatusBadge = (status: TestExecutionState['status']) => {
    switch (status) {
      case 'running':
        return (
          <Badge variant="default" className="bg-blue-100 text-blue-800">
            <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
            실행중
          </Badge>
        );
      case 'completed':
        return (
          <Badge variant="default" className="bg-green-100 text-green-800">
            <CheckCircle className="w-3 h-3 mr-1" />
            완료
          </Badge>
        );
      case 'failed':
        return (
          <Badge variant="destructive">
            <XCircle className="w-3 h-3 mr-1" />
            실패
          </Badge>
        );
      default:
        return (
          <Badge variant="secondary">
            <Clock className="w-3 h-3 mr-1" />
            대기
          </Badge>
        );
    }
  };

  // 카테고리별 색상
  const getCategoryColor = (category: string) => {
    const colors = {
      'financial': 'text-blue-600',
      'technical': 'text-purple-600',
      'fundamental': 'text-green-600',
      'news': 'text-orange-600'
    };
    return colors[category as keyof typeof colors] || 'text-gray-600';
  };

  // 행 확장/축소 토글
  const toggleRowExpansion = (testKey: string) => {
    setExpandedRows(prev => {
      const newSet = new Set(prev);
      if (newSet.has(testKey)) {
        newSet.delete(testKey);
      } else {
        newSet.add(testKey);
      }
      return newSet;
    });
  };

  // 모바일에서는 모바일용 컴포넌트 사용
  if (isMobile) {
    return (
      <div>
        <div className="mb-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-600 rounded"></div>
            DINO 테스트 결과
            <Badge variant="outline" className="text-xs">
              {testAreas.length}개
            </Badge>
          </h3>
        </div>
        <DinoTestTableMobile 
          testAreas={testAreas}
          testStates={testStates}
          runningTests={runningTests}
          onRunTest={onRunTest}
          onStopTest={onStopTest}
          onViewDetails={onViewDetails}
        />
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <div className="w-5 h-5 bg-blue-600 rounded"></div>
          DINO 테스트 결과표
          <Badge variant="outline" className="ml-2">
            {testAreas.length}개 테스트
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50">
                <TableHead className="w-8"></TableHead>
                <TableHead className="font-semibold">테스트명</TableHead>
                <TableHead className="font-semibold text-center">카테고리</TableHead>
                <TableHead className="font-semibold text-center">점수</TableHead>
                <TableHead className="font-semibold text-center">상태</TableHead>
                <TableHead className="font-semibold text-center">실행시간</TableHead>
                <TableHead className="font-semibold text-center">액션</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {testAreas.map((area) => {
                const IconComponent = area.icon;
                const testState = testStates[area.key];
                const isRunning = runningTests.has(area.key);
                const isExpanded = expandedRows.has(area.key);
                const score = testState?.result?.score ?? 0;
                const scoreStyle = getScoreStyle(score, area.maxScore, area.minScore);

                return (
                  <>
                    <TableRow 
                      key={area.key} 
                      className="hover:bg-gray-50 transition-colors cursor-pointer"
                      onClick={() => toggleRowExpansion(area.key)}
                    >
                      {/* 확장 화살표 */}
                      <TableCell className="text-center">
                        {testState?.result?.details ? (
                          isExpanded ? (
                            <ChevronDown className="w-4 h-4 text-gray-400" />
                          ) : (
                            <ChevronRight className="w-4 h-4 text-gray-400" />
                          )
                        ) : null}
                      </TableCell>

                      {/* 테스트명 */}
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <IconComponent className="w-5 h-5 text-primary" />
                          <div>
                            <div className="font-medium">{area.name}</div>
                            <div className="text-sm text-muted-foreground">{area.description}</div>
                          </div>
                        </div>
                      </TableCell>

                      {/* 카테고리 */}
                      <TableCell className="text-center">
                        <Badge variant="outline" className={getCategoryColor(area.category)}>
                          {area.category}
                        </Badge>
                      </TableCell>

                      {/* 점수 */}
                      <TableCell className="text-center">
                        {testState?.status === 'completed' && testState.result ? (
                          <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-lg border ${scoreStyle.bgColor} ${scoreStyle.textColor} ${scoreStyle.borderColor}`}>
                            {scoreStyle.icon}
                            <span className="font-bold text-lg">
                              {score}
                            </span>
                            <span className="text-sm">
                              / {area.maxScore}
                            </span>
                          </div>
                        ) : (
                          <div className="text-gray-400 text-sm">
                            - / {area.maxScore}
                          </div>
                        )}
                      </TableCell>

                      {/* 상태 */}
                      <TableCell className="text-center">
                        {getStatusBadge(testState?.status || 'idle')}
                      </TableCell>

                      {/* 실행시간 */}
                      <TableCell className="text-center">
                        {testState?.duration ? (
                          <span className="text-sm font-mono">
                            {(testState.duration / 1000).toFixed(1)}초
                          </span>
                        ) : testState?.startTime && testState?.status === 'running' ? (
                          <span className="text-sm font-mono text-blue-600">
                            실행중...
                          </span>
                        ) : (
                          <span className="text-gray-400 text-sm">-</span>
                        )}
                      </TableCell>

                      {/* 액션 */}
                      <TableCell className="text-center" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-center gap-1">
                          {isRunning ? (
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => onStopTest(area.key)}
                              className="h-8 px-2"
                            >
                              중지
                            </Button>
                          ) : (
                            <Button
                              size="sm"
                              onClick={() => onRunTest(area.key)}
                              disabled={runningTests.size > 0 && !isRunning}
                              className="h-8 px-2"
                            >
                              <Play className="w-3 h-3 mr-1" />
                              실행
                            </Button>
                          )}
                          
                          {testState?.result?.details && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => onViewDetails(area.key)}
                              className="h-8 px-2"
                            >
                              <Eye className="w-3 h-3" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>

                    {/* 확장된 세부 정보 행 */}
                    {isExpanded && testState?.result?.details && (
                      <TableRow>
                        <TableCell colSpan={7} className="bg-gradient-to-r from-blue-50 to-indigo-50 p-0">
                          <div className="p-6 border-t">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                              {/* 실행 정보 */}
                              <div className="bg-white rounded-lg p-4 border border-blue-100 shadow-sm">
                                <h4 className="font-semibold text-base text-blue-800 mb-3 flex items-center gap-2">
                                  <Clock className="w-4 h-4" />
                                  실행 정보
                                </h4>
                                <div className="space-y-2.5 text-sm">
                                  <div className="flex justify-between items-center">
                                    <span className="text-gray-600">시작 시간</span>
                                    <span className="font-medium text-gray-800">
                                      {testState.startTime?.toLocaleTimeString()}
                                    </span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-gray-600">종료 시간</span>
                                    <span className="font-medium text-gray-800">
                                      {testState.endTime?.toLocaleTimeString()}
                                    </span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-gray-600">소요 시간</span>
                                    <span className="font-bold text-blue-600">
                                      {testState.duration ? `${(testState.duration / 1000).toFixed(1)}초` : '-'}
                                    </span>
                                  </div>
                                </div>
                              </div>

                              {/* 점수 세부사항 */}
                              <div className="bg-white rounded-lg p-4 border border-green-100 shadow-sm">
                                <h4 className="font-semibold text-base text-green-800 mb-3 flex items-center gap-2">
                                  <TrendingUp className="w-4 h-4" />
                                  성과 분석
                                </h4>
                                <div className="space-y-2.5 text-sm">
                                  <div className="flex justify-between items-center">
                                    <span className="text-gray-600">획득 점수</span>
                                    <span className="font-bold text-green-600 text-lg">
                                      {score}점
                                    </span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-gray-600">최대 점수</span>
                                    <span className="font-medium text-gray-800">
                                      {area.maxScore}점
                                    </span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-gray-600">달성률</span>
                                    <div className="flex items-center gap-2">
                                      <span className="font-bold text-green-600">
                                        {((score / area.maxScore) * 100).toFixed(1)}%
                                      </span>
                                      <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                                        <div 
                                          className="h-full bg-green-500 rounded-full transition-all"
                                          style={{ width: `${((score / area.maxScore) * 100)}%` }}
                                        />
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              </div>

                              {/* 분석 상태 */}
                              <div className="bg-white rounded-lg p-4 border border-purple-100 shadow-sm">
                                <h4 className="font-semibold text-base text-purple-800 mb-3 flex items-center gap-2">
                                  <CheckCircle className="w-4 h-4" />
                                  분석 상태
                                </h4>
                                <div className="space-y-2.5 text-sm">
                                  <div className="flex justify-between items-center">
                                    <span className="text-gray-600">데이터 소스</span>
                                    <span className="font-medium text-purple-600">
                                      DB 저장 결과
                                    </span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-gray-600">분석 상태</span>
                                    <div className="flex items-center gap-1">
                                      <CheckCircle className="w-3 h-3 text-green-600" />
                                      <span className="font-medium text-green-600">
                                        완료
                                      </span>
                                    </div>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-gray-600">카테고리</span>
                                    <span className="font-medium text-gray-800">
                                      {area.category}
                                    </span>
                                  </div>
                                  {testState.status === 'running' && testState.logs && testState.logs.length > 0 && (
                                    <div className="mt-3">
                                      <div className="text-xs text-gray-500 mb-2">실시간 로그:</div>
                                      <div className="bg-gray-900 rounded-md p-2 max-h-16 overflow-y-auto">
                                        {testState.logs.slice(-2).map((log, index) => (
                                          <div key={index} className="text-green-400 text-xs font-mono leading-relaxed mb-1 last:mb-0">
                                            <span className="text-gray-500">$ </span>
                                            {log}
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </>
                );
              })}
            </TableBody>
          </Table>
        </div>
        
        {/* 테이블 하단 요약 */}
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {Object.values(testStates).reduce((sum, state) => sum + (state.result?.score || 0), 0)}
              </div>
              <div className="text-gray-600">총점</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {Object.values(testStates).filter(state => state.status === 'completed').length}
              </div>
              <div className="text-gray-600">완료된 테스트</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {runningTests.size}
              </div>
              <div className="text-gray-600">실행중 테스트</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {Math.round((Object.values(testStates).filter(state => state.status === 'completed').length / testAreas.length) * 100)}%
              </div>
              <div className="text-gray-600">진행률</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}