"""
네이버 뉴스 검색 API 클라이언트

네이버 개발자 센터의 뉴스 검색 API를 사용하여
합법적으로 뉴스 데이터를 수집하는 클라이언트
"""

import asyncio
import httpx
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from urllib.parse import quote


class NaverNewsClient:
    """네이버 뉴스 검색 API 클라이언트"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://openapi.naver.com/v1/search/news.json"
        
        self.headers = {
            'X-Naver-Client-Id': self.client_id,
            'X-Naver-Client-Secret': self.client_secret,
            'User-Agent': 'Kiwoom-Adapter/1.0'
        }
        self.timeout = httpx.Timeout(15.0)
    
    async def search_news(
        self, 
        query: str, 
        display: int = 20, 
        start: int = 1, 
        sort: str = "date"
    ) -> Dict[str, Any]:
        """
        네이버 뉴스 검색 API 호출
        
        Args:
            query: 검색어 (UTF-8 인코딩)
            display: 결과 개수 (1~100, 기본값: 20)
            start: 검색 시작 위치 (1~1000, 기본값: 1)
            sort: 정렬 방식 ("sim": 정확도순, "date": 날짜순)
            
        Returns:
            검색 결과 딕셔너리
        """
        try:
            # URL 인코딩
            encoded_query = quote(query, safe='', encoding='utf-8')
            
            params = {
                "query": encoded_query,
                "display": min(display, 100),
                "start": max(1, start),
                "sort": sort if sort in ["sim", "date"] else "date"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.base_url,
                    params=params,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 403:
                    print(f"❌ 네이버 API 권한 오류 (403): API 설정을 확인하세요")
                    return {"items": [], "total": 0, "start": start, "display": display}
                elif response.status_code == 400:
                    print(f"❌ 네이버 API 요청 오류 (400): {response.text}")
                    return {"items": [], "total": 0, "start": start, "display": display}
                else:
                    print(f"❌ 네이버 API 오류 ({response.status_code}): {response.text}")
                    return {"items": [], "total": 0, "start": start, "display": display}
                    
        except httpx.TimeoutException:
            print(f"❌ 네이버 API 타임아웃: {query}")
            return {"items": [], "total": 0, "start": start, "display": display}
        except Exception as e:
            print(f"❌ 네이버 API 호출 오류: {str(e)}")
            return {"items": [], "total": 0, "start": start, "display": display}
    
    def clean_html_tags(self, text: str) -> str:
        """HTML 태그 제거"""
        if not text:
            return ""
        # <b> 태그와 기타 HTML 태그 제거
        clean_text = re.sub(r'<[^>]+>', '', text)
        # HTML 엔티티 처리
        clean_text = clean_text.replace('&lt;', '<').replace('&gt;', '>')
        clean_text = clean_text.replace('&amp;', '&').replace('&quot;', '"')
        clean_text = clean_text.replace('&apos;', "'")
        return clean_text.strip()
    
    def parse_pubdate(self, pubdate: str) -> str:
        """네이버 API pubDate를 YYYY-MM-DD 형식으로 변환"""
        try:
            # "Mon, 26 Sep 2016 07:50:00 +0900" -> "2016-09-26"
            dt = datetime.strptime(pubdate, "%a, %d %b %Y %H:%M:%S %z")
            return dt.strftime("%Y-%m-%d")
        except:
            # 파싱 실패 시 현재 날짜 반환
            return datetime.now().strftime("%Y-%m-%d")
    
    def analyze_sentiment(self, title: str, description: str = "") -> str:
        """간단한 감정 분석 (기존 로직 재사용)"""
        text = f"{title} {description}".lower()
        
        positive_keywords = [
            '상승', '호재', '개선', '성장', '증가', '확대', '투자', '계약', '수주', 
            '상한가', '급등', '기대', '전망', '좋은', '우수', '성공', '발표',
            '긍정', '플러스', '상향', '돌파', '신고가'
        ]
        
        negative_keywords = [
            '하락', '악재', '감소', '축소', '리스크', '우려', '하한가', '급락', 
            '손실', '적자', '부진', '어려움', '문제', '위기', '실망', '부정',
            '마이너스', '하향', '폭락', '신저가'
        ]
        
        positive_count = sum(1 for keyword in positive_keywords if keyword in text)
        negative_count = sum(1 for keyword in negative_keywords if keyword in text)
        
        if positive_count > negative_count:
            return "긍정"
        elif negative_count > positive_count:
            return "부정"
        else:
            return "중립"
    
    def convert_to_enhanced_format(
        self, 
        api_response: Dict[str, Any], 
        stock_code: str, 
        stock_name: str
    ) -> Dict[str, Any]:
        """
        네이버 API 응답을 기존 enhanced_news_crawler 형식으로 변환
        """
        items = api_response.get("items", [])
        total = api_response.get("total", 0)
        
        articles = []
        category_stats = {"네이버뉴스API": len(items)}
        
        for item in items:
            # HTML 태그 제거
            clean_title = self.clean_html_tags(item.get("title", ""))
            clean_description = self.clean_html_tags(item.get("description", ""))
            
            # 날짜 파싱
            pub_date = self.parse_pubdate(item.get("pubDate", ""))
            
            # 감정 분석
            sentiment = self.analyze_sentiment(clean_title, clean_description)
            
            article = {
                "title": clean_title,
                "url": item.get("originallink", item.get("link", "")),
                "link": item.get("link", item.get("originallink", "")),
                "content": clean_description,
                "summary": clean_description[:100] + "..." if len(clean_description) > 100 else clean_description,
                "date": pub_date,
                "source": "네이버뉴스API",
                "sentiment": sentiment,
                "category": "검색결과"
            }
            
            articles.append(article)
        
        # 감성 분석 통계 계산
        sentiment_summary = self._calculate_sentiment_summary(articles)
        
        # 주요 테마 추출
        key_themes = self._extract_key_themes(articles)
        
        return {
            "articles": articles,
            "total_count": len(articles),
            "category_stats": category_stats,
            "sentiment_summary": sentiment_summary,
            "key_themes": key_themes,
            "stock_code": stock_code,
            "stock_name": stock_name,
            "collected_at": datetime.now().isoformat(),
            "api_total": total  # API에서 반환한 총 결과 수
        }
    
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
        
        theme_keywords = [
            '실적', '투자', '개발', '계약', '수주', '인수', '합병', 
            '상장', '증자', '배당', '신제품', '기술', '특허', '승인',
            '매출', '영업이익', '순이익', '성장', '확장'
        ]
        
        theme_count = {}
        for news in news_list:
            title = news.get('title', '')
            content = news.get('content', '')
            text = f"{title} {content}"
            
            for keyword in theme_keywords:
                if keyword in text:
                    theme_count[keyword] = theme_count.get(keyword, 0) + 1
        
        # 상위 3개 테마 반환
        sorted_themes = sorted(theme_count.items(), key=lambda x: x[1], reverse=True)
        return [theme for theme, count in sorted_themes[:3] if count > 0]


# 테스트 함수
async def test_naver_news_client():
    """네이버 뉴스 API 클라이언트 테스트"""
    client = NaverNewsClient(
        client_id="oarxsFogkVekumlQyzJW",
        client_secret="SlqG6Cl4h2"
    )
    
    # 삼성전자 뉴스 검색 테스트
    query = "삼성전자 OR 005930"
    result = await client.search_news(query, display=5)
    
    if result.get("items"):
        print(f"✅ 네이버 뉴스 API 테스트 성공")
        print(f"📊 총 {result.get('total', 0)}건 중 {len(result.get('items', []))}건 조회")
        
        first_item = result["items"][0]
        print(f"🗞️ 첫 번째 뉴스: {client.clean_html_tags(first_item.get('title', ''))}")
        
        # enhanced 형식 변환 테스트
        enhanced_result = client.convert_to_enhanced_format(result, "005930", "삼성전자")
        print(f"🔄 변환 결과: {len(enhanced_result['articles'])}건 변환 완료")
        
        return enhanced_result
    else:
        print(f"❌ 네이버 뉴스 API 테스트 실패")
        print(f"📄 응답: {result}")
        return None


if __name__ == "__main__":
    # 직접 실행 시 테스트
    result = asyncio.run(test_naver_news_client())
    if result:
        print(f"\n최종 결과:")
        print(f"- 총 뉴스: {result['total_count']}건")
        print(f"- 감성 분석: {result['sentiment_summary']}")
        print(f"- 주요 테마: {result['key_themes']}")