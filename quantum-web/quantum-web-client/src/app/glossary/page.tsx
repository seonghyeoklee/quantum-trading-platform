'use client';

import { useState, useMemo, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { useAuth } from "@/contexts/AuthContext";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import Header from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  getAllTerms, 
  getTermCategories,
  getDifficultyOptions,
  findTermById,
  FinancialTerm 
} from "@/lib/data/financial-terms";
import { 
  Search,
  BookOpen,
  Filter,
  Tag,
  GraduationCap,
  ExternalLink,
  Lightbulb
} from "lucide-react";

function GlossaryPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedDifficulty, setSelectedDifficulty] = useState('all');
  const [expandedTerm, setExpandedTerm] = useState<string | null>(null);
  
  const searchParams = useSearchParams();
  const termFromUrl = searchParams?.get('term');

  // URL의 term 파라미터로 지정된 용어가 있으면 자동 확장
  useEffect(() => {
    if (termFromUrl) {
      const term = findTermById(termFromUrl);
      if (term) {
        setExpandedTerm(termFromUrl);
        setSearchQuery(term.term); // 검색어에도 설정
      }
    }
  }, [termFromUrl]);

  const allTerms = getAllTerms();
  const categories = getTermCategories();
  const difficulties = getDifficultyOptions();

  // 필터링된 용어 목록
  const filteredTerms = useMemo(() => {
    let terms = allTerms;

    // 검색어 필터링
    if (searchQuery.trim()) {
      terms = terms.filter(term => 
        term.term.toLowerCase().includes(searchQuery.toLowerCase()) ||
        term.definition.toLowerCase().includes(searchQuery.toLowerCase()) ||
        term.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        term.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      );
    }

    // 카테고리 필터링
    if (selectedCategory !== 'all') {
      terms = terms.filter(term => term.category === selectedCategory);
    }

    // 난이도 필터링
    if (selectedDifficulty !== 'all') {
      terms = terms.filter(term => term.difficulty === selectedDifficulty);
    }

    return terms.sort((a, b) => a.term.localeCompare(b.term, 'ko-KR'));
  }, [searchQuery, selectedCategory, selectedDifficulty, allTerms]);

  // 카테고리별 색상
  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      'valuation': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      'profitability': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      'financial_health': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      'market': 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
      'trading': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      'general': 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
    };
    return colors[category] || colors['general'];
  };

  // 난이도별 색상
  const getDifficultyColor = (difficulty: string) => {
    const colors: Record<string, string> = {
      'beginner': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      'intermediate': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      'advanced': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    };
    return colors[difficulty] || colors['beginner'];
  };

  // 난이도 텍스트
  const getDifficultyText = (difficulty: string) => {
    const texts: Record<string, string> = {
      'beginner': '초급',
      'intermediate': '중급',
      'advanced': '고급',
    };
    return texts[difficulty] || '기본';
  };

  // 카테고리 텍스트
  const getCategoryText = (category: string) => {
    const texts: Record<string, string> = {
      'valuation': '가치평가',
      'profitability': '수익성',
      'financial_health': '재무건전성',
      'market': '시장지표',
      'trading': '거래',
      'general': '일반',
    };
    return texts[category] || category;
  };

  // 필터 리셋
  const resetFilters = () => {
    setSearchQuery('');
    setSelectedCategory('all');
    setSelectedDifficulty('all');
    setExpandedTerm(null);
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <div className="container mx-auto px-4 py-6 max-w-6xl">
        {/* 페이지 헤더 */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-4">
            <BookOpen className="w-8 h-8 text-primary" />
            <h1 className="text-3xl font-bold">금융 용어 사전</h1>
          </div>
          <p className="text-muted-foreground">
            주식 투자와 금융 분석에 필요한 핵심 용어들을 쉽게 찾아보세요.
          </p>
        </div>

        {/* 검색 및 필터 영역 */}
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="space-y-4">
              {/* 검색바 */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="용어, 정의, 태그로 검색..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>

              {/* 필터 */}
              <div className="flex flex-wrap gap-4 items-center">
                <div className="flex items-center space-x-2">
                  <Filter className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm font-medium">필터:</span>
                </div>

                {/* 카테고리 필터 */}
                <div className="flex items-center space-x-2">
                  <Tag className="w-4 h-4 text-muted-foreground" />
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="text-sm border border-input rounded-md px-2 py-1 bg-background"
                  >
                    <option value="all">모든 카테고리</option>
                    {categories.map(category => (
                      <option key={category} value={category}>
                        {getCategoryText(category)}
                      </option>
                    ))}
                  </select>
                </div>

                {/* 난이도 필터 */}
                <div className="flex items-center space-x-2">
                  <GraduationCap className="w-4 h-4 text-muted-foreground" />
                  <select
                    value={selectedDifficulty}
                    onChange={(e) => setSelectedDifficulty(e.target.value)}
                    className="text-sm border border-input rounded-md px-2 py-1 bg-background"
                  >
                    <option value="all">모든 난이도</option>
                    {difficulties.map(difficulty => (
                      <option key={difficulty} value={difficulty}>
                        {getDifficultyText(difficulty)}
                      </option>
                    ))}
                  </select>
                </div>

                {/* 필터 리셋 */}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={resetFilters}
                  className="text-xs"
                >
                  필터 초기화
                </Button>
              </div>

              {/* 검색 결과 개수 */}
              <div className="text-sm text-muted-foreground">
                총 {filteredTerms.length}개의 용어가 검색되었습니다.
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 용어 목록 */}
        <div className="space-y-4">
          {filteredTerms.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <div className="text-muted-foreground">
                  <BookOpen className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium mb-2">검색 결과가 없습니다</p>
                  <p className="text-sm">다른 검색어를 시도하거나 필터를 조정해보세요.</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            filteredTerms.map((term) => (
              <Card key={term.id} className="overflow-hidden">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="flex items-center space-x-3">
                        <span className="text-xl">{term.term}</span>
                        <Badge className={getCategoryColor(term.category)}>
                          {getCategoryText(term.category)}
                        </Badge>
                        <Badge className={getDifficultyColor(term.difficulty)}>
                          {getDifficultyText(term.difficulty)}
                        </Badge>
                      </CardTitle>
                      <p className="text-primary font-medium mt-2">
                        {term.definition}
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setExpandedTerm(
                        expandedTerm === term.id ? null : term.id
                      )}
                      className="ml-4"
                    >
                      {expandedTerm === term.id ? '접기' : '자세히'}
                    </Button>
                  </div>
                </CardHeader>

                <CardContent className="pt-0">
                  <div className="space-y-4">
                    {/* 기본 설명 */}
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {term.description}
                    </p>

                    {/* 확장 정보 */}
                    {expandedTerm === term.id && (
                      <div className="space-y-4 mt-4 p-4 bg-muted/50 rounded-lg">
                        {/* 공식 */}
                        {term.formula && (
                          <div>
                            <h4 className="font-medium text-sm mb-2 flex items-center">
                              <Lightbulb className="w-4 h-4 mr-2" />
                              공식
                            </h4>
                            <div className="font-mono text-sm bg-background p-3 rounded border">
                              {term.formula}
                            </div>
                          </div>
                        )}

                        {/* 예시 */}
                        {term.example && (
                          <div>
                            <h4 className="font-medium text-sm mb-2">예시</h4>
                            <div className="text-sm bg-blue-50 dark:bg-blue-950/20 p-3 rounded border border-blue-200 dark:border-blue-800">
                              {term.example}
                            </div>
                          </div>
                        )}

                        {/* 태그 */}
                        {term.tags.length > 0 && (
                          <div>
                            <h4 className="font-medium text-sm mb-2">관련 키워드</h4>
                            <div className="flex flex-wrap gap-2">
                              {term.tags.map(tag => (
                                <Badge 
                                  key={tag} 
                                  variant="secondary"
                                  className="text-xs"
                                >
                                  #{tag}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* 관련 링크 */}
                        <div className="pt-3 border-t border-border">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              const url = `/stock?term=${term.id}`;
                              window.open(url, '_blank');
                            }}
                            className="text-xs"
                          >
                            <ExternalLink className="w-3 h-3 mr-1" />
                            종목 정보에서 활용하기
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* 도움말 */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle className="text-lg flex items-center">
              <Lightbulb className="w-5 h-5 mr-2" />
              용어 사전 사용법
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4 text-sm">
              <div>
                <h4 className="font-medium mb-2">검색 및 필터</h4>
                <ul className="space-y-1 text-muted-foreground">
                  <li>• 용어명, 정의, 설명, 태그로 검색 가능</li>
                  <li>• 카테고리별로 용어를 분류하여 탐색</li>
                  <li>• 난이도별로 학습 단계에 맞춰 선택</li>
                  <li>• 필터 초기화로 전체 용어 다시 보기</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium mb-2">상세 정보</h4>
                <ul className="space-y-1 text-muted-foreground">
                  <li>• '자세히' 버튼으로 공식과 예시 확인</li>
                  <li>• 관련 키워드로 연관 개념 학습</li>
                  <li>• 종목 정보에서 실제 활용법 확인</li>
                  <li>• 주식 분석 도구와 연동하여 실습</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function ProtectedGlossaryPage() {
  return (
    <ProtectedRoute>
      <GlossaryPage />
    </ProtectedRoute>
  );
}