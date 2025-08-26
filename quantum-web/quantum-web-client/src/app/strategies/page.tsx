'use client';

import { useState, useMemo } from 'react';
import { useAuth } from "@/contexts/AuthContext";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import Header from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import StrategyCard from "@/components/strategies/StrategyCard";
import { 
  TradingStrategy,
  StrategyCategory,
  STRATEGY_CATEGORIES 
} from "@/lib/types/strategy-types";
import { technicalAnalysisStrategies } from "@/lib/data/technical-strategies";
import { 
  Search,
  Filter,
  Star,
  TrendingUp,
  BarChart3,
  Calculator,
  Bot,
  Lightbulb,
  Zap,
  Target
} from "lucide-react";

function StrategiesPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<StrategyCategory | 'all'>('all');
  const [selectedStatus, setSelectedStatus] = useState<'all' | 'active' | 'inactive' | 'testing'>('all');
  const [showOnlyFavorites, setShowOnlyFavorites] = useState(false);
  const [showOnlyPopular, setShowOnlyPopular] = useState(false);

  // 현재는 기술적 분석 전략만 사용하지만, 향후 다른 카테고리 전략들도 합칠 수 있도록 구조화
  const allStrategies: TradingStrategy[] = [
    ...technicalAnalysisStrategies
  ];

  // 필터링된 전략 목록
  const filteredStrategies = useMemo(() => {
    let strategies = allStrategies;

    // 검색어 필터링
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      strategies = strategies.filter(strategy =>
        strategy.name.toLowerCase().includes(query) ||
        strategy.description.toLowerCase().includes(query) ||
        strategy.tags.some(tag => tag.toLowerCase().includes(query))
      );
    }

    // 카테고리 필터링
    if (selectedCategory !== 'all') {
      strategies = strategies.filter(strategy => strategy.category === selectedCategory);
    }

    // 상태 필터링
    if (selectedStatus !== 'all') {
      strategies = strategies.filter(strategy => strategy.status === selectedStatus);
    }

    // 즐겨찾기 필터링
    if (showOnlyFavorites) {
      strategies = strategies.filter(strategy => strategy.isFavorite);
    }

    // 인기 전략 필터링
    if (showOnlyPopular) {
      strategies = strategies.filter(strategy => strategy.isPopular);
    }

    return strategies;
  }, [searchQuery, selectedCategory, selectedStatus, showOnlyFavorites, showOnlyPopular, allStrategies]);

  // 전략 상태 변경 핸들러
  const handleStrategyStatusChange = (strategyId: string, newStatus: 'active' | 'inactive') => {
    console.log(`Strategy ${strategyId} status changed to: ${newStatus}`);
    // TODO: 실제 상태 변경 로직 구현
  };

  // 즐겨찾기 토글 핸들러
  const handleFavoriteToggle = (strategyId: string) => {
    console.log(`Strategy ${strategyId} favorite toggled`);
    // TODO: 실제 즐겨찾기 상태 변경 로직 구현
  };

  // 전략 상세보기 핸들러
  const handleViewDetails = (strategyId: string) => {
    console.log(`View details for strategy: ${strategyId}`);
    // TODO: 상세 페이지로 라우팅
    window.location.href = `/strategies/${strategyId}`;
  };

  // 전략 설정 핸들러
  const handleSettings = (strategyId: string) => {
    console.log(`Open settings for strategy: ${strategyId}`);
    // TODO: 설정 모달 또는 페이지 오픈
  };

  // 필터 리셋
  const resetFilters = () => {
    setSearchQuery('');
    setSelectedCategory('all');
    setSelectedStatus('all');
    setShowOnlyFavorites(false);
    setShowOnlyPopular(false);
  };

  // 카테고리별 통계
  const categoryStats = useMemo(() => {
    const stats: Record<string, number> = { all: allStrategies.length };
    allStrategies.forEach(strategy => {
      stats[strategy.category] = (stats[strategy.category] || 0) + 1;
    });
    return stats;
  }, [allStrategies]);

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <div className="container mx-auto px-4 py-6 max-w-7xl">
        {/* 페이지 헤더 */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-4">
            <Bot className="w-8 h-8 text-primary" />
            <h1 className="text-3xl font-bold">자동매매 전략</h1>
          </div>
          <p className="text-muted-foreground">
            다양한 자동매매 전략을 활용하여 체계적이고 효율적인 투자를 시작하세요.
          </p>
        </div>

        {/* 검색 및 필터 섹션 */}
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="space-y-4">
              {/* 검색바 */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="전략명, 설명, 태그로 검색..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>

              {/* 필터 옵션 */}
              <div className="flex flex-wrap gap-4 items-center">
                <div className="flex items-center space-x-2">
                  <Filter className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm font-medium">필터:</span>
                </div>

                {/* 카테고리 필터 */}
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant={selectedCategory === 'all' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedCategory('all')}
                    className="text-xs"
                  >
                    전체 ({categoryStats.all})
                  </Button>
                  {Object.entries(STRATEGY_CATEGORIES).map(([key, info]) => (
                    <Button
                      key={key}
                      variant={selectedCategory === key ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setSelectedCategory(key as StrategyCategory)}
                      className="text-xs"
                    >
                      {info.name} ({categoryStats[key] || 0})
                    </Button>
                  ))}
                </div>

                {/* 상태 필터 */}
                <div className="flex gap-2">
                  <Button
                    variant={selectedStatus === 'all' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedStatus('all')}
                    className="text-xs"
                  >
                    전체 상태
                  </Button>
                  <Button
                    variant={selectedStatus === 'active' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedStatus('active')}
                    className="text-xs"
                  >
                    활성화
                  </Button>
                  <Button
                    variant={selectedStatus === 'inactive' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedStatus('inactive')}
                    className="text-xs"
                  >
                    비활성화
                  </Button>
                </div>

                {/* 기타 필터 */}
                <div className="flex gap-2">
                  <Button
                    variant={showOnlyPopular ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setShowOnlyPopular(!showOnlyPopular)}
                    className="text-xs"
                  >
                    <Star className="w-3 h-3 mr-1" />
                    인기 전략만
                  </Button>
                  <Button
                    variant={showOnlyFavorites ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setShowOnlyFavorites(!showOnlyFavorites)}
                    className="text-xs"
                  >
                    즐겨찾기만
                  </Button>
                </div>

                {/* 필터 리셋 */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={resetFilters}
                  className="text-xs"
                >
                  필터 초기화
                </Button>
              </div>

              {/* 검색 결과 개수 */}
              <div className="text-sm text-muted-foreground">
                총 {filteredStrategies.length}개의 전략이 검색되었습니다.
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 전략 목록 */}
        <div className="space-y-6">
          {filteredStrategies.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <div className="text-muted-foreground">
                  <Target className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium mb-2">검색 결과가 없습니다</p>
                  <p className="text-sm">다른 검색어를 시도하거나 필터를 조정해보세요.</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="grid lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {filteredStrategies.map((strategy) => (
                <StrategyCard
                  key={strategy.id}
                  strategy={strategy}
                  onStatusChange={handleStrategyStatusChange}
                  onFavoriteToggle={handleFavoriteToggle}
                  onViewDetails={handleViewDetails}
                  onSettings={handleSettings}
                />
              ))}
            </div>
          )}
        </div>

        {/* 도움말 섹션 */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle className="text-lg flex items-center">
              <Lightbulb className="w-5 h-5 mr-2" />
              자동매매 전략 사용법
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-6 text-sm">
              <div>
                <h4 className="font-medium mb-2 flex items-center">
                  <Zap className="w-4 h-4 mr-1" />
                  전략 활성화
                </h4>
                <ul className="space-y-1 text-muted-foreground">
                  <li>• 전략 카드에서 스위치를 통해 활성화/비활성화</li>
                  <li>• 활성화된 전략만 실시간 신호 생성</li>
                  <li>• 여러 전략을 동시에 활성화 가능</li>
                  <li>• 테스팅 상태인 전략은 페이퍼 트레이딩만</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium mb-2 flex items-center">
                  <BarChart3 className="w-4 h-4 mr-1" />
                  백테스팅 활용
                </h4>
                <ul className="space-y-1 text-muted-foreground">
                  <li>• 과거 데이터로 전략 성과 미리 확인</li>
                  <li>• 파라미터 조정으로 최적화 가능</li>
                  <li>• 샤프비율과 MDD로 위험도 평가</li>
                  <li>• 실전 투자 전 반드시 백테스팅 수행</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium mb-2 flex items-center">
                  <TrendingUp className="w-4 h-4 mr-1" />
                  전략 선택 가이드
                </h4>
                <ul className="space-y-1 text-muted-foreground">
                  <li>• 초급자: 이동평균, RSI 등 단순한 전략</li>
                  <li>• 중급자: 복합 지표 활용 전략</li>
                  <li>• 고급자: 다이버전스, 복합 조건 전략</li>
                  <li>• 시장 상황에 따른 전략 조합 권장</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium mb-2 flex items-center">
                  <Calculator className="w-4 h-4 mr-1" />
                  위험 관리
                </h4>
                <ul className="space-y-1 text-muted-foreground">
                  <li>• 손절/익절 비율을 반드시 설정</li>
                  <li>• 총 투자 자금의 일정 비율만 투입</li>
                  <li>• 여러 전략 분산으로 위험 분산</li>
                  <li>• 정기적인 성과 점검과 전략 조정</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function ProtectedStrategiesPage() {
  return (
    <ProtectedRoute>
      <StrategiesPage />
    </ProtectedRoute>
  );
}