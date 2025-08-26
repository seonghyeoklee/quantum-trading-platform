"""
뉴스 크롤링 및 감성 분석 시스템

다양한 소스에서 뉴스를 수집하고 호재/악재를 판별하는 시스템입니다.
3가지 접근 방법을 제공:
1. 네이버 금융 크롤링 (무료, 제한적)
2. 뉴스 API 서비스 활용 (유료, 안정적)
3. RSS 피드 수집 (무료, 실시간)
"""

import httpx
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import re
import os
from bs4 import BeautifulSoup
import feedparser
import hashlib
import json


class NewsSource(Enum):
    """뉴스 소스 타입"""
    NAVER_FINANCE = "naver_finance"  # 네이버 금융
    DAUM_FINANCE = "daum_finance"   # 다음 금융
    RSS_FEED = "rss_feed"           # RSS 피드
    NEWS_API = "news_api"           # 뉴스 API (한국언론진흥재단 등)
    SOCIAL_MEDIA = "social_media"   # 소셜 미디어 (추가 가능)


class NewsSentiment(Enum):
    """뉴스 감성 분류"""
    VERY_POSITIVE = 2    # 매우 긍정 (강한 호재)
    POSITIVE = 1         # 긍정 (호재)
    NEUTRAL = 0          # 중립
    NEGATIVE = -1        # 부정 (악재)
    VERY_NEGATIVE = -2   # 매우 부정 (강한 악재)


class NewsCategory(Enum):
    """뉴스 카테고리"""
    EARNINGS = "실적"           # 실적 관련
    MA = "인수합병"             # M&A, 인수합병
    CONTRACT = "계약"           # 수주, 계약
    PRODUCT = "제품"            # 신제품, 출시
    REGULATION = "규제"         # 규제, 정책
    MANAGEMENT = "경영"         # 경영진 변동
    TECHNOLOGY = "기술"         # 기술 개발, 특허
    MARKET = "시황"            # 시장 동향
    ISSUE = "이슈"             # 사건, 사고
    DIVIDEND = "배당"          # 배당 관련


class NewsCrawler:
    """뉴스 크롤링 시스템"""
    
    def __init__(self):
        """초기화"""
        self.session_timeout = httpx.Timeout(10.0)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # 감성 분석용 키워드 사전
        self.positive_keywords = {
            "strong": ["신기록", "최고치", "급등", "대박", "흑자전환", "어닝서프라이즈", 
                      "목표가상향", "수주", "계약체결", "승인", "특허", "혁신", "돌파"],
            "moderate": ["상승", "증가", "호조", "개선", "회복", "성장", "확대", "강세",
                        "매수", "긍정", "기대", "전망", "호재", "수혜", "개발성공"]
        }
        
        self.negative_keywords = {
            "strong": ["폭락", "급락", "최악", "파산", "상장폐지", "횡령", "구속", 
                      "리콜", "대규모손실", "적자전환", "어닝쇼크", "목표가하향"],
            "moderate": ["하락", "감소", "부진", "악화", "위축", "축소", "약세",
                        "매도", "우려", "리스크", "불안", "악재", "피해", "실패"]
        }
        
        # 뉴스 카테고리 키워드
        self.category_keywords = {
            NewsCategory.EARNINGS: ["실적", "매출", "영업이익", "순이익", "적자", "흑자"],
            NewsCategory.MA: ["인수", "합병", "M&A", "매각", "지분", "인수합병"],
            NewsCategory.CONTRACT: ["수주", "계약", "공급", "납품", "체결", "수출"],
            NewsCategory.PRODUCT: ["신제품", "출시", "개발", "런칭", "신약", "임상"],
            NewsCategory.REGULATION: ["규제", "제재", "승인", "허가", "정책", "법안"],
            NewsCategory.MANAGEMENT: ["CEO", "대표", "사장", "임원", "인사", "사임"],
            NewsCategory.TECHNOLOGY: ["기술", "특허", "R&D", "연구", "개발", "혁신"],
            NewsCategory.MARKET: ["시황", "전망", "동향", "추세", "거래량", "수급"],
            NewsCategory.ISSUE: ["사고", "소송", "분쟁", "이슈", "논란", "스캔들"],
            NewsCategory.DIVIDEND: ["배당", "배당금", "현금배당", "주식배당", "무상증자"]
        }
    
    async def crawl_naver_finance(self, stock_code: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        네이버 금융에서 뉴스 크롤링
        
        Args:
            stock_code: 종목코드
            days: 수집 기간 (일)
            
        Returns:
            뉴스 리스트
        """
        news_list = []
        
        try:
            # 네이버 증권 뉴스 URL (시황전망 + 기업분석)
            urls = [
                "https://finance.naver.com/news/news_list.naver?mode=LSS3D&section_id=101&section_id2=258&section_id3=401",  # 시황전망
                "https://finance.naver.com/news/news_list.naver?mode=LSS3D&section_id=101&section_id2=258&section_id3=402"   # 기업분석
            ]
            
            for url in urls:
                async with httpx.AsyncClient(timeout=self.session_timeout) as client:
                    response = await client.get(url, headers=self.headers)
                    
                    if response.status_code == 200:
                        # 네이버는 euc-kr 인코딩 사용
                        response.encoding = 'euc-kr'
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # 뉴스 링크 추출
                        news_links = soup.find_all('a', href=True)
                        
                        for link in news_links:
                            href = link.get('href', '')
                            if 'newsView' in href or 'news_read' in href:
                                title = link.text.strip()
                                if title and len(title) > 5:
                                    # 종목명이 포함된 뉴스만 필터링
                                    if stock_code in title or stock_name in title:
                                        
                                        # URL 정규화
                                        if href.startswith('/'):
                                            full_url = f"https://finance.naver.com{href}"
                                        else:
                                            full_url = href
                        
                        if title_elem and date_elem:
                            title = title_elem.text.strip()
                            link = f"https://finance.naver.com{title_elem['href']}"
                            date_str = date_elem.text.strip()
                            source = source_elem.text.strip() if source_elem else "네이버금융"
                            
                            # 날짜 파싱
                            try:
                                news_date = datetime.strptime(date_str, "%Y.%m.%d %H:%M")
                            except:
                                news_date = datetime.now()
                            
                            # 기간 필터링
                            if news_date < datetime.now() - timedelta(days=days):
                                break
                            
                            # 뉴스 분석
                            sentiment = self._analyze_sentiment(title)
                            category = self._categorize_news(title)
                            
                            news_list.append({
                                "title": title,
                                "link": link,
                                "date": news_date.isoformat(),
                                "source": source,
                                "sentiment": sentiment.value,
                                "sentiment_label": sentiment.name,
                                "category": category.value if category else "기타",
                                "crawl_source": NewsSource.NAVER_FINANCE.value,
                                "stock_code": stock_code
                            })
            
        except Exception as e:
            print(f"네이버 금융 크롤링 실패: {e}")
        
        return news_list
    
    async def crawl_rss_feeds(self, stock_name: str, feeds: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        RSS 피드에서 뉴스 수집
        
        Args:
            stock_name: 종목명 (검색용)
            feeds: RSS 피드 URL 리스트
            
        Returns:
            뉴스 리스트
        """
        if not feeds:
            # 기본 RSS 피드 목록
            feeds = [
                "https://www.mk.co.kr/rss/30100041/",  # 매일경제 증권
                "https://www.hankyung.com/feed/finance",  # 한국경제 금융
                "https://rss.edaily.co.kr/stock_news.xml",  # 이데일리 증권
                "http://www.yonhapnews.co.kr/RSS/economy.xml"  # 연합뉴스 경제
            ]
        
        news_list = []
        
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:20]:  # 최근 20개만
                    title = entry.title
                    
                    # 종목명이 포함된 뉴스만 필터링
                    if stock_name not in title:
                        continue
                    
                    # 뉴스 분석
                    sentiment = self._analyze_sentiment(title)
                    category = self._categorize_news(title)
                    
                    news_list.append({
                        "title": title,
                        "link": entry.link,
                        "date": datetime(*entry.published_parsed[:6]).isoformat() if hasattr(entry, 'published_parsed') else datetime.now().isoformat(),
                        "source": feed.feed.title if hasattr(feed.feed, 'title') else "RSS",
                        "summary": entry.summary if hasattr(entry, 'summary') else "",
                        "sentiment": sentiment.value,
                        "sentiment_label": sentiment.name,
                        "category": category.value if category else "기타",
                        "crawl_source": NewsSource.RSS_FEED.value,
                        "stock_name": stock_name
                    })
                    
            except Exception as e:
                print(f"RSS 피드 수집 실패 ({feed_url}): {e}")
        
        return news_list
    
    async def crawl_bigkinds(self, stock_name: str, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        빅카인즈(한국언론진흥재단) API를 통한 뉴스 수집
        
        Args:
            stock_name: 종목명
            api_key: 빅카인즈 API 키
            
        Returns:
            뉴스 리스트
        """
        if not api_key:
            api_key = os.getenv("BIGKINDS_API_KEY")
            if not api_key:
                return []
        
        news_list = []
        
        try:
            # 빅카인즈 API 엔드포인트
            url = "https://www.bigkinds.or.kr/api/news/search.do"
            
            payload = {
                "access_key": api_key,
                "argument": {
                    "query": stock_name,
                    "published_at": {
                        "from": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                        "until": datetime.now().strftime("%Y-%m-%d")
                    },
                    "provider": ["경향신문", "국민일보", "매일경제", "한국경제"],
                    "category": ["경제", "증권"],
                    "sort": {"date": "desc"},
                    "return_from": 0,
                    "return_size": 30
                }
            }
            
            async with httpx.AsyncClient(timeout=self.session_timeout) as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for doc in data.get("return_object", {}).get("documents", []):
                        title = doc.get("title", "").replace("<![CDATA[", "").replace("]]>", "")
                        
                        # 뉴스 분석
                        sentiment = self._analyze_sentiment(title)
                        category = self._categorize_news(title)
                        
                        news_list.append({
                            "title": title,
                            "link": doc.get("news_url", ""),
                            "date": doc.get("published_at", ""),
                            "source": doc.get("provider", ""),
                            "summary": doc.get("summary", ""),
                            "sentiment": sentiment.value,
                            "sentiment_label": sentiment.name,
                            "category": category.value if category else "기타",
                            "crawl_source": NewsSource.NEWS_API.value,
                            "stock_name": stock_name,
                            "byline": doc.get("byline", "")
                        })
                        
        except Exception as e:
            print(f"빅카인즈 API 수집 실패: {e}")
        
        return news_list
    
    def _analyze_sentiment(self, text: str) -> NewsSentiment:
        """
        텍스트 감성 분석
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            감성 분류
        """
        text_lower = text.lower()
        
        # 점수 계산
        positive_score = 0
        negative_score = 0
        
        # 강한 긍정 키워드 체크
        for keyword in self.positive_keywords["strong"]:
            if keyword in text:
                positive_score += 2
        
        # 보통 긍정 키워드 체크
        for keyword in self.positive_keywords["moderate"]:
            if keyword in text:
                positive_score += 1
        
        # 강한 부정 키워드 체크
        for keyword in self.negative_keywords["strong"]:
            if keyword in text:
                negative_score += 2
        
        # 보통 부정 키워드 체크
        for keyword in self.negative_keywords["moderate"]:
            if keyword in text:
                negative_score += 1
        
        # 최종 점수 계산
        final_score = positive_score - negative_score
        
        # 감성 분류
        if final_score >= 3:
            return NewsSentiment.VERY_POSITIVE
        elif final_score >= 1:
            return NewsSentiment.POSITIVE
        elif final_score <= -3:
            return NewsSentiment.VERY_NEGATIVE
        elif final_score <= -1:
            return NewsSentiment.NEGATIVE
        else:
            return NewsSentiment.NEUTRAL
    
    def _categorize_news(self, text: str) -> Optional[NewsCategory]:
        """
        뉴스 카테고리 분류
        
        Args:
            text: 분류할 텍스트
            
        Returns:
            뉴스 카테고리
        """
        text_lower = text.lower()
        category_scores = {}
        
        # 각 카테고리별 점수 계산
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                category_scores[category] = score
        
        # 가장 높은 점수의 카테고리 반환
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return None
    
    async def get_comprehensive_news(self, 
                                   stock_code: str, 
                                   stock_name: str,
                                   use_api: bool = False,
                                   api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        종합 뉴스 수집 및 분석
        
        Args:
            stock_code: 종목코드
            stock_name: 종목명
            use_api: API 사용 여부
            api_key: API 키
            
        Returns:
            종합 뉴스 분석 결과
        """
        all_news = []
        
        # 1. 네이버 금융 크롤링
        naver_news = await self.crawl_naver_finance(stock_code)
        all_news.extend(naver_news)
        
        # 2. RSS 피드 수집
        rss_news = await self.crawl_rss_feeds(stock_name)
        all_news.extend(rss_news)
        
        # 3. API 사용 시
        if use_api and api_key:
            api_news = await self.crawl_bigkinds(stock_name, api_key)
            all_news.extend(api_news)
        
        # 중복 제거 (제목 해시 기반)
        unique_news = {}
        for news in all_news:
            title_hash = hashlib.md5(news["title"].encode()).hexdigest()
            if title_hash not in unique_news:
                unique_news[title_hash] = news
        
        news_list = list(unique_news.values())
        
        # 날짜순 정렬
        news_list.sort(key=lambda x: x["date"], reverse=True)
        
        # 통계 계산
        sentiment_stats = {
            "very_positive": 0,
            "positive": 0,
            "neutral": 0,
            "negative": 0,
            "very_negative": 0
        }
        
        category_stats = {}
        
        for news in news_list:
            # 감성 통계
            sentiment = news["sentiment"]
            if sentiment == 2:
                sentiment_stats["very_positive"] += 1
            elif sentiment == 1:
                sentiment_stats["positive"] += 1
            elif sentiment == 0:
                sentiment_stats["neutral"] += 1
            elif sentiment == -1:
                sentiment_stats["negative"] += 1
            elif sentiment == -2:
                sentiment_stats["very_negative"] += 1
            
            # 카테고리 통계
            category = news["category"]
            category_stats[category] = category_stats.get(category, 0) + 1
        
        # 전체 감성 점수 계산
        total_sentiment_score = (
            sentiment_stats["very_positive"] * 2 +
            sentiment_stats["positive"] * 1 +
            sentiment_stats["negative"] * -1 +
            sentiment_stats["very_negative"] * -2
        )
        
        # 호재/악재 판정 (Google Sheets D44, D45 매핑용)
        has_bad_news = sentiment_stats["negative"] + sentiment_stats["very_negative"] >= 3
        has_good_news_spam = sentiment_stats["positive"] + sentiment_stats["very_positive"] >= 5
        
        return {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "total_news": len(news_list),
            "sentiment_stats": sentiment_stats,
            "category_stats": category_stats,
            "total_sentiment_score": total_sentiment_score,
            "overall_sentiment": self._get_overall_sentiment(total_sentiment_score, len(news_list)),
            "has_bad_news": has_bad_news,  # D44 매핑
            "has_good_news_spam": has_good_news_spam,  # D45 매핑
            "recent_news": news_list[:10],  # 최근 10개
            "important_news": self._filter_important_news(news_list),
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def _get_overall_sentiment(self, score: int, total: int) -> str:
        """
        전체 감성 판정
        
        Args:
            score: 감성 점수 합계
            total: 전체 뉴스 수
            
        Returns:
            전체 감성 라벨
        """
        if total == 0:
            return "데이터없음"
        
        avg_score = score / total
        
        if avg_score >= 0.5:
            return "매우긍정"
        elif avg_score >= 0.2:
            return "긍정"
        elif avg_score <= -0.5:
            return "매우부정"
        elif avg_score <= -0.2:
            return "부정"
        else:
            return "중립"
    
    def _filter_important_news(self, news_list: List[Dict]) -> List[Dict]:
        """
        중요 뉴스 필터링
        
        Args:
            news_list: 전체 뉴스 리스트
            
        Returns:
            중요 뉴스 리스트
        """
        important = []
        
        for news in news_list:
            # 강한 감성의 뉴스만 선택
            if abs(news["sentiment"]) >= 2:
                important.append(news)
            # 주요 카테고리 뉴스
            elif news["category"] in ["실적", "인수합병", "규제", "배당"]:
                important.append(news)
        
        return important[:5]  # 최대 5개


# 사용 예시
async def example_news_crawling():
    """뉴스 크롤링 예시"""
    
    crawler = NewsCrawler()
    
    # 삼성전자 뉴스 수집
    result = await crawler.get_comprehensive_news(
        stock_code="005930",
        stock_name="삼성전자",
        use_api=False  # API 키가 있으면 True
    )
    
    print("=== 뉴스 분석 결과 ===")
    print(f"종목: {result['stock_name']} ({result['stock_code']})")
    print(f"총 뉴스 수: {result['total_news']}개")
    print(f"\n감성 분석:")
    for sentiment, count in result['sentiment_stats'].items():
        print(f"  {sentiment}: {count}개")
    print(f"\n전체 감성: {result['overall_sentiment']}")
    print(f"악재 뉴스 도배: {'예' if result['has_bad_news'] else '아니오'}")
    print(f"호재 뉴스 도배: {'예' if result['has_good_news_spam'] else '아니오'}")
    
    print(f"\n최근 주요 뉴스:")
    for news in result['important_news']:
        print(f"  [{news['sentiment_label']}] {news['title']}")


if __name__ == "__main__":
    asyncio.run(example_news_crawling())