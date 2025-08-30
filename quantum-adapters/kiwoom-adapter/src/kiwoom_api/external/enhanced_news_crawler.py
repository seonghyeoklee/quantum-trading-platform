"""
개선된 뉴스 수집기 - 네이버 뉴스 검색 API 사용

기존 HTML 크롤링 방식을 네이버 공식 뉴스 검색 API로 대체
robots.txt를 준수하는 합법적인 뉴스 데이터 수집
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Handle both relative and absolute imports for different execution contexts
try:
    from .naver_news_client import NaverNewsClient
    from ..config.settings import settings
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from kiwoom_api.external.naver_news_client import NaverNewsClient
    from kiwoom_api.config.settings import settings


class EnhancedNewsCrawler:
    """네이버 뉴스 검색 API 기반 뉴스 수집기"""
    
    def __init__(self):
        """네이버 뉴스 검색 API 클라이언트 초기화"""
        # 네이버 API 클라이언트 초기화
        self.news_client = NaverNewsClient(
            client_id=settings.NAVER_CLIENT_ID,
            client_secret=settings.NAVER_CLIENT_SECRET
        )
        
        # 종목별 검색 키워드 매핑 (기존과 동일)
        self.keywords_map = {
            "005930": ["삼성전자", "삼성", "반도체", "SEC", "Samsung"],
            "000660": ["SK하이닉스", "SK", "하이닉스", "메모리", "Hynix"], 
            "035420": ["NAVER", "네이버", "검색", "플랫폼"],
            "207940": ["삼성바이오로직스", "바이오", "제약", "CMO"],
            "068270": ["셀트리온", "바이오", "제약", "항체"]
        }
    
    async def get_comprehensive_news(self, stock_code: str, stock_name: str = "") -> Dict[str, Any]:
        """
        네이버 뉴스 검색 API를 통한 종목 관련 뉴스 수집
        
        Args:
            stock_code: 종목코드 (예: '005930')
            stock_name: 종목명 (예: '삼성전자')
            
        Returns:
            종합 뉴스 분석 결과 (기존 format과 동일)
        """
        
        print(f"[네이버 뉴스 API] {stock_code} ({stock_name}) 뉴스 검색 시작...")
        
        # 검색 키워드 생성
        search_keywords = self._build_search_query(stock_code, stock_name)
        
        try:
            # 네이버 뉴스 검색 API 호출
            api_response = await self.news_client.search_news(
                query=search_keywords,
                display=30,  # 더 많은 뉴스 조회
                sort="date"  # 최신순
            )
            
            if not api_response.get("items"):
                print(f"  → 검색 결과 없음 (총 {api_response.get('total', 0)}건)")
                return self._empty_result(stock_code, stock_name)
            
            # API 응답을 기존 형식으로 변환
            result = self.news_client.convert_to_enhanced_format(
                api_response, stock_code, stock_name
            )
            
            print(f"  → 총 {api_response.get('total', 0)}건 중 {len(result['articles'])}건 수집")
            print(f"[네이버 뉴스 API] 뉴스 수집 완료")
            
            return result
            
        except Exception as e:
            print(f"❌ 네이버 뉴스 API 오류: {str(e)}")
            return self._empty_result(stock_code, stock_name, error=str(e))
    
    def _build_search_query(self, stock_code: str, stock_name: str) -> str:
        """종목별 검색 쿼리 생성"""
        # 기본 키워드
        keywords = []
        
        # 종목명 추가
        if stock_name:
            keywords.append(stock_name)
        
        # 종목코드 추가
        keywords.append(stock_code)
        
        # 매핑된 키워드 추가
        mapped_keywords = self.keywords_map.get(stock_code, [])
        keywords.extend(mapped_keywords[:3])  # 상위 3개만
        
        # OR 조건으로 연결 (네이버 API는 띄어쓰기가 OR 역할)
        query = " OR ".join(set(keywords))  # 중복 제거
        
        print(f"  검색 키워드: {query}")
        return query
    
    def _empty_result(self, stock_code: str, stock_name: str, error: str = None) -> Dict[str, Any]:
        """빈 결과 반환 (기존 형식 호환)"""
        return {
            "articles": [],
            "total_count": 0,
            "category_stats": {"네이버뉴스API": 0},
            "sentiment_summary": {"positive": 0, "neutral": 0, "negative": 0, "overall": "중립"},
            "key_themes": [],
            "stock_code": stock_code,
            "stock_name": stock_name,
            "collected_at": datetime.now().isoformat(),
            "error": error
        }
    
    # 기존 메서드들 (호환성을 위해 유지)
    def _analyze_sentiment(self, title: str) -> str:
        """감성 분석 (NaverNewsClient로 위임)"""
        return self.news_client.analyze_sentiment(title)
    
    def _calculate_sentiment_summary(self, news_list: List[Dict]) -> Dict[str, Any]:
        """감성 분석 요약 (NaverNewsClient로 위임)"""
        return self.news_client._calculate_sentiment_summary(news_list)
    
    def _extract_content_preview(self, link_element, soup) -> str:
        """뉴스 내용 미리보기 (더 이상 사용하지 않음)"""
        return "네이버 뉴스 API를 통해 요약 제공"
    
    def _extract_key_themes(self, news_list: List[Dict]) -> List[str]:
        """주요 테마 추출 (NaverNewsClient로 위임)"""
        return self.news_client._extract_key_themes(news_list)


# 테스트 함수 (기존과 동일)
async def test_enhanced_crawler():
    crawler = EnhancedNewsCrawler()
    result = await crawler.get_comprehensive_news('005930', '삼성전자')
    return result


if __name__ == "__main__":
    # 직접 실행 시 테스트
    result = asyncio.run(test_enhanced_crawler())
    print(f"\n최종 결과: {result['total_count']}건의 뉴스 수집")
    print(f"카테고리별 통계: {result['category_stats']}")
    print(f"감성 분석: {result['sentiment_summary']}")
    print(f"주요 테마: {result['key_themes']}")
    
    if result.get('articles'):
        first_article = result['articles'][0]
        print(f"\n첫 번째 기사:")
        print(f"  제목: {first_article.get('title', '')}")
        print(f"  링크: {first_article.get('link', '')}")
        print(f"  내용: {first_article.get('content', '')[:100]}...")