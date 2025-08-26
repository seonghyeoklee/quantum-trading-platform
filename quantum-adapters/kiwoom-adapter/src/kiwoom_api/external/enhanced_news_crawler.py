"""
개선된 네이버 금융 뉴스 크롤러
모든 카테고리를 통합하여 종목별 맞춤형 뉴스를 수집합니다.
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import Dict, List, Any
from datetime import datetime


class EnhancedNewsCrawler:
    """개선된 네이버 금융 뉴스 크롤러"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.timeout = httpx.Timeout(10.0)
    
    async def get_comprehensive_news(self, stock_code: str, stock_name: str = "") -> Dict[str, Any]:
        """
        네이버 금융 뉴스 전체 카테고리에서 종목 관련 뉴스 수집
        
        Args:
            stock_code: 종목코드 (예: '005930')
            stock_name: 종목명 (예: '삼성전자')
            
        Returns:
            종합 뉴스 분석 결과
        """
        
        # 네이버 금융 뉴스 전체 카테고리
        categories = {
            '주요뉴스': 'https://finance.naver.com/news/mainnews.naver',
            '실시간속보': 'https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258', 
            '많이본뉴스': 'https://finance.naver.com/news/news_list.naver?mode=RANK',
            '시황전망': 'https://finance.naver.com/news/news_list.naver?mode=LSS3D&section_id=101&section_id2=258&section_id3=401',
            '기업분석': 'https://finance.naver.com/news/news_list.naver?mode=LSS3D&section_id=101&section_id2=258&section_id3=402',
            '해외증권': 'https://finance.naver.com/news/news_list.naver?mode=LSS3D&section_id=101&section_id2=258&section_id3=403',
            '채권파생': 'https://finance.naver.com/news/news_list.naver?mode=LSS3D&section_id=101&section_id2=258&section_id3=404'
        }
        
        # 종목별 키워드 매핑
        keywords_map = {
            "005930": ["삼성전자", "삼성", "반도체", "SEC", "Samsung"],
            "000660": ["SK하이닉스", "SK", "하이닉스", "메모리", "Hynix"], 
            "035420": ["NAVER", "네이버", "검색", "플랫폼"],
            "207940": ["삼성바이오로직스", "바이오", "제약", "CMO"],
            "068270": ["셀트리온", "바이오", "제약", "항체"]
        }
        
        search_keywords = keywords_map.get(stock_code, [stock_name]) if stock_name else [stock_code]
        
        all_news = []
        category_stats = {}
        
        for category_name, url in categories.items():
            try:
                print(f"[{category_name}] 크롤링 중...")
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, headers=self.headers)
                    
                    if response.status_code == 200:
                        # 네이버는 euc-kr 인코딩 사용
                        response.encoding = 'euc-kr'
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # 뉴스 링크 추출
                        news_links = soup.find_all('a', href=True)
                        category_news = []
                        
                        for link in news_links:
                            href = link.get('href', '')
                            title = link.text.strip()
                            
                            # 뉴스 기사 링크 패턴 확인
                            is_news_link = (
                                'newsView' in href or 'news_read' in href or 
                                '/news/' in href or 'article' in href
                            )
                            
                            if is_news_link and title and len(title) > 5:
                                # 키워드 매칭
                                if any(keyword.lower() in title.lower() for keyword in search_keywords):
                                    
                                    # URL 정규화
                                    full_url = f"https://finance.naver.com{href}" if href.startswith('/') else href
                                    
                                    # 감성 분석 (간단한 키워드 기반)
                                    sentiment = self._analyze_sentiment(title)
                                    
                                    news_item = {
                                        "title": title,
                                        "url": full_url,
                                        "date": datetime.now().strftime("%Y-%m-%d"),
                                        "source": f"네이버금융-{category_name}",
                                        "sentiment": sentiment,
                                        "category": category_name,
                                        "summary": title[:100]
                                    }
                                    
                                    category_news.append(news_item)
                                    all_news.append(news_item)
                                    
                                    # 카테고리별 최대 5개까지
                                    if len(category_news) >= 5:
                                        break
                        
                        category_stats[category_name] = len(category_news)
                        print(f"  → {len(category_news)}건 발견")
                        
            except Exception as e:
                print(f"  ❌ 에러: {e}")
                category_stats[category_name] = 0
        
        # 감성 분석 통계
        sentiment_summary = self._calculate_sentiment_summary(all_news)
        
        # 주요 테마 추출
        key_themes = self._extract_key_themes(all_news)
        
        result = {
            "articles": all_news,
            "total_count": len(all_news),
            "category_stats": category_stats,
            "sentiment_summary": sentiment_summary,
            "key_themes": key_themes,
            "stock_code": stock_code,
            "stock_name": stock_name,
            "collected_at": datetime.now().isoformat()
        }
        
        print(f"\n=== 총 {len(all_news)}건의 관련 뉴스 수집 완료 ===")
        return result
    
    def _analyze_sentiment(self, title: str) -> str:
        """간단한 감성 분석"""
        positive_keywords = [
            '상승', '호재', '개선', '성장', '증가', '확대', '투자', '계약', '수주', 
            '상한가', '급등', '기대', '전망', '좋은', '우수', '성공', '발표'
        ]
        
        negative_keywords = [
            '하락', '악재', '감소', '축소', '리스크', '우려', '하한가', '급락', 
            '손실', '적자', '부진', '어려움', '문제', '위기', '실망', '부정'
        ]
        
        title_lower = title.lower()
        
        positive_count = sum(1 for keyword in positive_keywords if keyword in title_lower)
        negative_count = sum(1 for keyword in negative_keywords if keyword in title_lower)
        
        if positive_count > negative_count:
            return "긍정"
        elif negative_count > positive_count:
            return "부정"
        else:
            return "중립"
    
    def _calculate_sentiment_summary(self, news_list: List[Dict]) -> Dict[str, Any]:
        """감성 분석 요약 통계"""
        if not news_list:
            return {"positive": 0, "neutral": 0, "negative": 0, "overall": "중립"}
        
        sentiment_count = {"긍정": 0, "중립": 0, "부정": 0}
        
        for news in news_list:
            sentiment = news.get('sentiment', '중립')
            sentiment_count[sentiment] = sentiment_count.get(sentiment, 0) + 1
        
        total = len(news_list)
        positive_ratio = sentiment_count["긍정"] / total
        negative_ratio = sentiment_count["부정"] / total
        
        if positive_ratio > 0.6:
            overall = "매우 긍정적"
        elif positive_ratio > 0.4:
            overall = "긍정적"
        elif negative_ratio > 0.6:
            overall = "매우 부정적"
        elif negative_ratio > 0.4:
            overall = "부정적"
        else:
            overall = "중립"
        
        return {
            "positive": sentiment_count["긍정"],
            "neutral": sentiment_count["중립"],
            "negative": sentiment_count["부정"],
            "overall": overall
        }
    
    def _extract_key_themes(self, news_list: List[Dict]) -> List[str]:
        """주요 테마 키워드 추출"""
        if not news_list:
            return []
        
        # 테마 키워드 카운팅
        theme_keywords = [
            '실적', '투자', '개발', '계약', '수주', '인수', '합병', 
            '상장', '증자', '배당', '신제품', '기술', '특허', '승인'
        ]
        
        theme_count = {}
        for news in news_list:
            title = news.get('title', '')
            for keyword in theme_keywords:
                if keyword in title:
                    theme_count[keyword] = theme_count.get(keyword, 0) + 1
        
        # 상위 3개 테마 반환
        sorted_themes = sorted(theme_count.items(), key=lambda x: x[1], reverse=True)
        return [theme for theme, count in sorted_themes[:3] if count > 0]


# 테스트 함수
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