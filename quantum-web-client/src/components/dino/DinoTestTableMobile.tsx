'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
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
  Square
} from 'lucide-react';
import { useState } from 'react';

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

interface DinoTestTableMobileProps {
  testAreas: DinoTestArea[];
  testStates: Record<string, TestExecutionState>;
  runningTests: Set<string>;
  onRunTest: (testKey: string) => void;
  onStopTest: (testKey: string) => void;
  onViewDetails: (testKey: string) => void;
}

export default function DinoTestTableMobile({ 
  testAreas, 
  testStates, 
  runningTests, 
  onRunTest, 
  onStopTest, 
  onViewDetails 
}: DinoTestTableMobileProps) {
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set());

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
      'financial': 'text-blue-600 bg-blue-50',
      'technical': 'text-purple-600 bg-purple-50',
      'fundamental': 'text-green-600 bg-green-50',
      'news': 'text-orange-600 bg-orange-50'
    };
    return colors[category as keyof typeof colors] || 'text-gray-600 bg-gray-50';
  };

  // 카드 확장/축소 토글
  const toggleCardExpansion = (testKey: string) => {
    setExpandedCards(prev => {
      const newSet = new Set(prev);
      if (newSet.has(testKey)) {
        newSet.delete(testKey);
      } else {
        newSet.add(testKey);
      }
      return newSet;
    });
  };

  return (
    <div className="space-y-3">
      {/* 모바일용 요약 카드 */}
      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50">
        <CardContent className="p-4">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {Object.values(testStates).reduce((sum, state) => sum + (state.result?.score || 0), 0)}
              </div>
              <div className="text-xs text-gray-600">총점</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">
                {Object.values(testStates).filter(state => state.status === 'completed').length}
              </div>
              <div className="text-xs text-gray-600">완료</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {runningTests.size}
              </div>
              <div className="text-xs text-gray-600">실행중</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 테스트 카드들 */}
      {testAreas.map((area) => {
        const IconComponent = area.icon;
        const testState = testStates[area.key];
        const isRunning = runningTests.has(area.key);
        const isExpanded = expandedCards.has(area.key);
        const score = testState?.result?.score ?? 0;
        const scoreStyle = getScoreStyle(score, area.maxScore, area.minScore);

        return (
          <Card key={area.key} className="overflow-hidden">
            <CardContent className="p-0">
              {/* 메인 정보 */}
              <div 
                className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => toggleCardExpansion(area.key)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1">
                    <IconComponent className="w-5 h-5 text-primary flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <div className="font-medium text-sm truncate">{area.name}</div>
                      <div className="text-xs text-gray-600 truncate">{area.description}</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {testState?.result?.details && (
                      isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-gray-400" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-gray-400" />
                      )
                    )}
                  </div>
                </div>

                {/* 점수 및 상태 */}
                <div className="mt-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={`text-xs px-2 py-1 rounded-full ${getCategoryColor(area.category)}`}>
                      {area.category}
                    </div>
                    {getStatusBadge(testState?.status || 'idle')}
                  </div>
                  
                  <div className="text-right">
                    {testState?.status === 'completed' && testState.result ? (
                      <div className={`inline-flex items-center gap-1 px-2 py-1 rounded border text-xs ${scoreStyle.bgColor} ${scoreStyle.textColor} ${scoreStyle.borderColor}`}>
                        {scoreStyle.icon}
                        <span className="font-bold">{score}</span>
                        <span>/{area.maxScore}</span>
                      </div>
                    ) : (
                      <div className="text-gray-400 text-xs">-/{area.maxScore}</div>
                    )}
                  </div>
                </div>
              </div>

              {/* 액션 버튼 영역 */}
              <div className="px-4 pb-4 border-t bg-gray-50">
                <div className="flex items-center gap-2 pt-3">
                  {isRunning ? (
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={(e) => {
                        e.stopPropagation();
                        onStopTest(area.key);
                      }}
                      className="flex-1 h-8"
                    >
                      <Square className="w-3 h-3 mr-1" />
                      중지
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onRunTest(area.key);
                      }}
                      disabled={runningTests.size > 0 && !isRunning}
                      className="flex-1 h-8"
                    >
                      <Play className="w-3 h-3 mr-1" />
                      실행
                    </Button>
                  )}
                  
                  {testState?.result?.details && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={(e) => {
                        e.stopPropagation();
                        onViewDetails(area.key);
                      }}
                      className="h-8 px-3"
                    >
                      <Eye className="w-3 h-3" />
                    </Button>
                  )}

                  {testState?.duration && (
                    <div className="text-xs text-gray-500 ml-auto">
                      {(testState.duration / 1000).toFixed(1)}초
                    </div>
                  )}
                </div>
              </div>

              {/* 확장된 세부 정보 */}
              {isExpanded && testState?.result?.details && (
                <div className="border-t bg-gradient-to-r from-blue-50 to-indigo-50">
                  <div className="p-4 space-y-4">
                    {/* 성과 요약 */}
                    <div className="bg-white rounded-lg p-3 border border-green-100 shadow-sm">
                      <div className="flex items-center gap-2 mb-3">
                        <TrendingUp className="w-4 h-4 text-green-600" />
                        <span className="font-semibold text-sm text-green-800">성과 요약</span>
                      </div>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div className="text-center p-2 bg-green-50 rounded border">
                          <div className="text-lg font-bold text-green-600">{score}</div>
                          <div className="text-xs text-gray-600">획득점수</div>
                        </div>
                        <div className="text-center p-2 bg-blue-50 rounded border">
                          <div className="text-lg font-bold text-blue-600">
                            {((score / area.maxScore) * 100).toFixed(0)}%
                          </div>
                          <div className="text-xs text-gray-600">달성률</div>
                        </div>
                      </div>
                      {/* 진행률 바 */}
                      <div className="mt-3">
                        <div className="flex justify-between text-xs text-gray-600 mb-1">
                          <span>진행 상황</span>
                          <span>{score}/{area.maxScore}점</span>
                        </div>
                        <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-green-400 to-green-600 rounded-full transition-all duration-300"
                            style={{ width: `${((score / area.maxScore) * 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* 실행 정보 */}
                    <div className="bg-white rounded-lg p-3 border border-blue-100 shadow-sm">
                      <div className="flex items-center gap-2 mb-3">
                        <Clock className="w-4 h-4 text-blue-600" />
                        <span className="font-semibold text-sm text-blue-800">실행 정보</span>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">시작</span>
                          <span className="font-medium text-gray-800">
                            {testState.startTime?.toLocaleTimeString()}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">종료</span>
                          <span className="font-medium text-gray-800">
                            {testState.endTime?.toLocaleTimeString()}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">소요시간</span>
                          <span className="font-bold text-blue-600">
                            {testState.duration ? `${(testState.duration / 1000).toFixed(1)}초` : '-'}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    {/* 분석 정보 */}
                    <div className="bg-white rounded-lg p-3 border border-purple-100 shadow-sm">
                      <div className="flex items-center gap-2 mb-3">
                        <CheckCircle className="w-4 h-4 text-purple-600" />
                        <span className="font-semibold text-sm text-purple-800">분석 정보</span>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">데이터 소스</span>
                          <span className="font-medium text-purple-600 text-xs">
                            DB 저장결과
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">카테고리</span>
                          <span className="font-medium text-gray-800 text-xs">
                            {area.category}
                          </span>
                        </div>
                        {testState.status === 'running' && testState.logs && testState.logs.length > 0 && (
                          <div className="mt-2">
                            <div className="text-xs text-gray-500 mb-1">실시간 로그:</div>
                            <div className="bg-gray-900 rounded-md p-2 max-h-16 overflow-y-auto">
                              {testState.logs.slice(-1).map((log, index) => (
                                <div key={index} className="text-green-400 text-xs font-mono leading-relaxed">
                                  <span className="text-gray-500">$ </span>
                                  <span className="break-words">{log}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}