'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Newspaper, 
  Bot, 
  Calendar,
  ExternalLink,
  Users,
  Award,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  MessageSquare,
  Zap,
  Target,
  ChevronDown
} from 'lucide-react';

// 기본 타입 정의
interface NewsItem {
  link: string;
  title: string;
  pub_date: string;
  description: string;
}

interface ImminentEvent {
  source: string;
  event_type: string;
  description: string;
  date_mention: string;
  urgency_score: number;
}

// API에서 오는 rawData 구조
interface DinoAdvancedRawData {
  news?: {
    theme_analysis?: {
      detected_theme: string;
      confidence_score: number;
      is_leading_theme: boolean;
      related_news_count: number;
      analyzed_news_links: NewsItem[];
    };
    positive_news_analysis?: {
      hype_score: number;
      positive_ratio: number;
      hype_expressions: string[];
      positive_keywords: string[];
      analyzed_news_links: NewsItem[];
    };
  };
  disclosure?: {
    imminent_events?: {
      events_count: number;
      total_sources: number;
      detected_events: ImminentEvent[];
      analyzed_news_links: NewsItem[];
    };
  };
  ai_theme?: string;
  ai_event?: string;
  ai_positive_news?: string;
}

interface DinoAdvancedAnalysisVisualizationProps {
  rawData: DinoAdvancedRawData;
}

// 날짜 포맷팅
const formatDate = (dateStr: string): string => {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ko-KR', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return dateStr;
  }
};

// 중복 제거된 뉴스 링크 추출
const extractUniqueNewsLinks = (rawData: DinoAdvancedRawData): NewsItem[] => {
  const allLinks: NewsItem[] = [];
  const seenLinks = new Set<string>();

  // 각 소스에서 뉴스 링크 수집
  const sources = [
    rawData.news?.theme_analysis?.analyzed_news_links || [],
    rawData.news?.positive_news_analysis?.analyzed_news_links || [],
    rawData.disclosure?.imminent_events?.analyzed_news_links || []
  ];

  sources.forEach(links => {
    links.forEach(link => {
      if (!seenLinks.has(link.link)) {
        seenLinks.add(link.link);
        allLinks.push(link);
      }
    });
  });

  // 날짜순 정렬 (최신순)
  return allLinks.sort((a, b) => new Date(b.pub_date).getTime() - new Date(a.pub_date).getTime());
};


// 통합 AI 분석 요약 컴포넌트
const IntegratedAIAnalysis = ({ rawData }: { rawData: DinoAdvancedRawData }) => {
  const hasTheme = rawData.ai_theme && rawData.ai_theme.length > 10;
  const hasEvent = rawData.ai_event && rawData.ai_event !== "키워드 분석: 6개 이벤트 감지";
  const hasPositiveNews = rawData.ai_positive_news && rawData.ai_positive_news.length > 10;
  
  // AI 분석이 하나도 없으면 표시하지 않음
  if (!hasTheme && !hasEvent && !hasPositiveNews) return null;

  return (
    <div className="p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200">
      <div className="flex items-center gap-2 mb-3">
        <Bot className="w-5 h-5 text-purple-600" />
        <span className="font-semibold text-purple-800">AI 종합 분석</span>
        <Badge variant="outline" className="bg-purple-100 text-purple-700">
          통합 요약
        </Badge>
      </div>

      <div className="space-y-3">
        {hasTheme && (
          <div className="bg-white p-3 rounded border">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-800">테마 분석</span>
            </div>
            <p className="text-sm text-blue-700 leading-relaxed">
              {rawData.ai_theme}
            </p>
          </div>
        )}

        {hasPositiveNews && (
          <div className="bg-white p-3 rounded border">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-4 h-4 text-orange-600" />
              <span className="text-sm font-medium text-orange-800">뉴스 신뢰성 분석</span>
            </div>
            <p className="text-sm text-orange-700 leading-relaxed">
              {rawData.ai_positive_news}
            </p>
          </div>
        )}

        {hasEvent && (
          <div className="bg-white p-3 rounded border">
            <div className="flex items-center gap-2 mb-2">
              <Calendar className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium text-green-800">이벤트 분석</span>
            </div>
            <p className="text-sm text-green-700 leading-relaxed">
              {rawData.ai_event}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

// 메인 컴포넌트 - 중복 제거 및 통합 표시
export default function DinoAdvancedAnalysisVisualization({ rawData }: DinoAdvancedAnalysisVisualizationProps) {
  const hasAdvancedData = rawData?.news || rawData?.disclosure || rawData?.ai_theme;
  
  if (!hasAdvancedData) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <div className="flex flex-col items-center gap-2">
            <MessageSquare className="w-8 h-8 text-gray-400" />
            <div className="text-sm text-gray-600">고급 분석 데이터가 없습니다</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // 중복 제거된 뉴스 링크 추출
  const uniqueNewsLinks = extractUniqueNewsLinks(rawData);

  return (
    <div className="space-y-4">
      {/* 헤더 */}
      <div className="flex items-center gap-2">
        <BarChart3 className="w-5 h-5" />
        <h3 className="text-lg font-semibold">AI 기반 고급 분석</h3>
        <Badge variant="outline" className="bg-purple-50 text-purple-700">
          {uniqueNewsLinks.length}개 뉴스 분석
        </Badge>
      </div>

      {/* 통합 AI 분석 - 중복 제거된 형태 */}
      <IntegratedAIAnalysis rawData={rawData} />

      {/* 수치 데이터 - 간결한 형태 */}
      {(rawData.news?.theme_analysis || rawData.news?.positive_news_analysis || rawData.disclosure?.imminent_events) && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {rawData.news?.theme_analysis && (
            <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center gap-2 mb-2">
                <Target className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-800">테마 감지</span>
              </div>
              <div className="text-lg font-bold text-blue-700 mb-1">
                {rawData.news.theme_analysis.detected_theme}
              </div>
              <div className="text-xs text-blue-600">
                신뢰도: {(rawData.news.theme_analysis.confidence_score * 100).toFixed(0)}% | 
                뉴스: {rawData.news.theme_analysis.related_news_count}개
              </div>
            </div>
          )}

          {rawData.news?.positive_news_analysis && (
            <div className="p-3 bg-orange-50 rounded-lg border border-orange-200">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="w-4 h-4 text-orange-600" />
                <span className="text-sm font-medium text-orange-800">뉴스 분석</span>
              </div>
              <div className="text-lg font-bold text-orange-700 mb-1">
                과장도: {(rawData.news.positive_news_analysis.hype_score * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-orange-600">
                긍정비율: {(rawData.news.positive_news_analysis.positive_ratio * 100).toFixed(0)}%
              </div>
            </div>
          )}

          {rawData.disclosure?.imminent_events && (
            <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
              <div className="flex items-center gap-2 mb-2">
                <Calendar className="w-4 h-4 text-purple-600" />
                <span className="text-sm font-medium text-purple-800">이벤트 감지</span>
              </div>
              <div className="text-lg font-bold text-purple-700 mb-1">
                {rawData.disclosure.imminent_events.events_count}개 이벤트
              </div>
              <div className="text-xs text-purple-600">
                분석소스: {rawData.disclosure.imminent_events.total_sources}개
              </div>
            </div>
          )}
        </div>
      )}

      {/* 뉴스 링크 - 접기/펼치기 가능한 형태 */}
      {uniqueNewsLinks.length > 0 && (
        <details className="border rounded-lg">
          <summary className="p-4 cursor-pointer hover:bg-gray-50 flex items-center gap-2">
            <Newspaper className="w-4 h-4" />
            <span className="font-medium">관련 뉴스 {uniqueNewsLinks.length}개 보기</span>
            <ChevronDown className="w-4 h-4 ml-auto" />
          </summary>
          <div className="p-4 border-t bg-gray-50">
            <div className="space-y-3">
              {uniqueNewsLinks.slice(0, 5).map((news, index) => (
                <div key={index} className="flex items-start gap-3 p-3 bg-white rounded border hover:shadow-sm transition-shadow">
                  <div className="flex-1">
                    <div className="text-sm font-medium line-clamp-2 mb-1">
                      {news.title}
                    </div>
                    <div className="text-xs text-gray-500 mb-1">
                      {formatDate(news.pub_date)}
                    </div>
                    <div className="text-xs text-gray-600 line-clamp-2">
                      {news.description}
                    </div>
                  </div>
                  <a
                    href={news.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-1 text-gray-400 hover:text-blue-600 transition-colors flex-shrink-0"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              ))}
              {uniqueNewsLinks.length > 5 && (
                <div className="text-center text-sm text-gray-500">
                  +{uniqueNewsLinks.length - 5}개 더 있음
                </div>
              )}
            </div>
          </div>
        </details>
      )}
    </div>
  );
}