#!/usr/bin/env python3
"""
AI 기반 뉴스 분석기

뉴스 제목과 내용을 AI로 분석하여 악재/호재를 판단합니다.
- 악재뉴스 (대형 클레임, 계약취소, 리콜 등): -1점
- 중립뉴스: 0점  
- 호재뉴스 (대형 계약, 신제품 출시, 실적 개선 등): +1점
"""

import logging
import requests
import os
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from .ai_client import get_ai_client

logger = logging.getLogger(__name__)

@dataclass
class NewsAnalysisResult:
    """뉴스 분석 결과"""
    company_name: str
    stock_code: str
    total_news_count: int
    positive_news_count: int  # 호재 뉴스 수
    negative_news_count: int  # 악재 뉴스 수  
    neutral_news_count: int   # 중립 뉴스 수
    sentiment_score: float    # 감정 점수 (-1.0 ~ +1.0)
    material_impact: int      # 재료 영향도 점수 (-1, 0, +1)
    key_topics: List[str]     # 주요 토픽들
    analysis_summary: str     # 분석 요약

class NewsAnalyzer:
    """AI 기반 뉴스 분석기"""
    
    def __init__(self, external_api_base_url: str = "http://external-api.quantum-trading.com:8001"):
        self.base_url = external_api_base_url
        self.logger = logging.getLogger(__name__)
        
        # 통합 AI 클라이언트 초기화
        self.ai_client = get_ai_client()
        self.ai_available = self.ai_client.is_available()
        
        if self.ai_available:
            providers = self.ai_client.get_available_providers()
            self.logger.info(f"✅ AI 클라이언트 초기화 완료: {', '.join(providers)}")
        else:
            self.logger.warning("⚠️ 사용 가능한 AI API가 없어서 키워드 분석만 사용")
        
        # 악재/호재 키워드 사전
        self.negative_keywords = [
            "클레임", "리콜", "결함", "중단", "취소", "소송", "분쟁", "조사", "제재", "규제",
            "손실", "적자", "하락", "감소", "악화", "위험", "문제", "사고", "파업", "노조",
            "부채", "채무불이행", "파산", "폐업", "철수", "중단", "지연", "실패"
        ]
        
        self.positive_keywords = [
            "계약", "수주", "협력", "파트너십", "투자", "인수", "합병", "출시", "개발", "혁신",
            "성장", "증가", "상승", "개선", "흑자", "이익", "매출", "확대", "진출", "성공",
            "수상", "인증", "승인", "선정", "채택", "도입", "런칭", "오픈"
        ]
    
    def fetch_news_data(self, company_keyword: str, count: int = 20) -> Optional[List[Dict]]:
        """External API로 뉴스 데이터 수집"""
        try:
            url = f"{self.base_url}/news/financial/{company_keyword}"
            params = {"count": count}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            items = data.get("items", [])
            
            self.logger.info(f"뉴스 수집 완료: {company_keyword} - {len(items)}건")
            return items
            
        except Exception as e:
            self.logger.error(f"뉴스 데이터 수집 실패 - {company_keyword}: {e}")
            return None
    
    def analyze_with_ai(self, news_list: List[Dict]) -> Dict:
        """AI를 이용한 뉴스 감정 분석 (Claude 우선, OpenAI 폴백)"""
        if not self.ai_available or not news_list:
            return {"sentiment_score": 0.0, "material_impact": 0, "analysis_summary": "AI 분석 불가"}
        
        try:
            # 뉴스 제목들을 하나의 텍스트로 조합
            news_titles = []
            for news in news_list[:10]:  # 최대 10개만 분석 (토큰 절약)
                title = news.get("title", "").replace("<b>", "").replace("</b>", "")
                news_titles.append(title)
            
            news_text = "\n".join([f"{i+1}. {title}" for i, title in enumerate(news_titles)])
            
            # AI 프롬프트 구성
            system_prompt = "당신은 한국 증시 전문 애널리스트입니다. 뉴스를 분석하여 투자 관점에서 평가합니다."
            
            user_prompt = f"""
다음 뉴스 제목들을 분석하여 해당 기업에 대한 투자 관점에서 평가해주세요.

뉴스 제목들:
{news_text}

분석 기준:
1. 악재뉴스: 대형 클레임, 계약취소, 리콜, 손실, 소송, 규제 등 (-1점)
2. 중립뉴스: 일반적인 시장 상황, 단순 보고 등 (0점)  
3. 호재뉴스: 대형 계약, 신제품 출시, 실적 개선, 파트너십 등 (+1점)

다음 JSON 형식으로 응답해주세요:
{{
    "sentiment_score": -1.0~1.0 사이의 감정 점수,
    "material_impact": -1, 0, 1 중 하나의 재료 영향도,
    "positive_count": 호재 뉴스 개수,
    "negative_count": 악재 뉴스 개수,
    "neutral_count": 중립 뉴스 개수,
    "key_topics": ["주요 토픽1", "주요 토픽2"],
    "analysis_summary": "100자 이내 분석 요약"
}}
            """
            
            # AI API 호출
            result_text = self.ai_client.analyze_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=500
            )
            
            if not result_text:
                self.logger.warning("AI API 호출 실패, 키워드 분석으로 폴백")
                return self._fallback_analysis(news_list)
            
            # JSON 파싱 시도
            result = self.ai_client.parse_json_response(result_text)
            if result:
                self.logger.info(f"✅ AI 뉴스 분석 성공: {result.get('analysis_summary', 'N/A')}")
                return result
            else:
                self.logger.warning(f"JSON 파싱 실패, 원본 응답: {result_text[:200]}...")
                return self._fallback_analysis(news_list)
                
        except Exception as e:
            self.logger.error(f"AI API 호출 실패: {e}")
            return self._fallback_analysis(news_list)
    
    def _fallback_analysis(self, news_list: List[Dict]) -> Dict:
        """AI 분석 실패 시 키워드 기반 폴백 분석 (개선됨)"""
        if not news_list:
            return {"sentiment_score": 0.0, "material_impact": 0, "positive_count": 0, 
                   "negative_count": 0, "neutral_count": 0, "key_topics": [], 
                   "analysis_summary": "분석할 뉴스가 없음"}
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        topics = set()
        
        # 감정 분석된 뉴스들 (디버깅용)
        analyzed_news = []
        
        for news in news_list:
            title = news.get("title", "").replace("<b>", "").replace("</b>", "")
            description = news.get("description", "")
            full_text = f"{title} {description}"
            
            # 대소문자 무관 키워드 매칭
            pos_matches = sum(1 for kw in self.positive_keywords if kw in full_text)
            neg_matches = sum(1 for kw in self.negative_keywords if kw in full_text)
            
            # 추가적인 휴리스틱 분석
            # 주가 상승/하락 관련
            if any(word in full_text for word in ["상승", "오름", "급등", "강세", "뛰", "+", "최고"]):
                pos_matches += 1
            if any(word in full_text for word in ["하락", "떨어", "급락", "약세", "-", "최저"]):
                neg_matches += 1
            
            # 실적 관련  
            if any(word in full_text for word in ["매출 증가", "이익 증가", "실적 개선", "흑자"]):
                pos_matches += 2  # 가중치
            if any(word in full_text for word in ["매출 감소", "손실", "적자", "실적 악화"]):
                neg_matches += 2  # 가중치
            
            # 분류 결정
            sentiment = "중립"
            if neg_matches > pos_matches and neg_matches > 0:
                negative_count += 1
                sentiment = "악재"
            elif pos_matches > neg_matches and pos_matches > 0:
                positive_count += 1
                sentiment = "호재"
            else:
                neutral_count += 1
            
            analyzed_news.append({
                "title": title[:50] + "..." if len(title) > 50 else title,
                "sentiment": sentiment,
                "pos_score": pos_matches,
                "neg_score": neg_matches
            })
            
            # 토픽 추출 (더 정확하게)
            if any(word in full_text for word in ["주가", "주식", "시세", "거래"]):
                topics.add("주가동향")
            if any(word in full_text for word in ["반도체", "메모리", "칩", "HBM"]):
                topics.add("반도체")  
            if any(word in full_text for word in ["AI", "인공지능", "머신러닝"]):
                topics.add("AI/인공지능")
            if any(word in full_text for word in ["계약", "수주", "협력", "파트너십"]):
                topics.add("계약/협력")
            if any(word in full_text for word in ["신제품", "출시", "런칭", "개발"]):
                topics.add("신제품")
            if any(word in full_text for word in ["실적", "매출", "영업이익", "분기"]):
                topics.add("실적/재무")
            if any(word in full_text for word in ["경쟁", "라이벌", "시장점유율"]):
                topics.add("경쟁동향")
        
        # 감정 점수 계산
        total = positive_count + negative_count + neutral_count
        if total > 0:
            sentiment_score = (positive_count - negative_count) / total
        else:
            sentiment_score = 0.0
        
        # 재료 영향도 판정
        if negative_count >= 3:  # 악재 뉴스 3건 이상
            material_impact = -1
        elif positive_count >= 3:  # 호재 뉴스 3건 이상
            material_impact = 1
        else:
            material_impact = 0
        
        return {
            "sentiment_score": sentiment_score,
            "material_impact": material_impact,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "key_topics": list(topics)[:5],  # 최대 5개
            "analysis_summary": f"키워드 분석: 호재 {positive_count}건, 악재 {negative_count}건"
        }
    
    def analyze_news_sentiment(self, stock_code: str, company_name: str = None) -> Optional[NewsAnalysisResult]:
        """종목의 뉴스 감정 분석"""
        
        # 기업명이 없으면 종목코드로 검색
        search_keyword = company_name if company_name else stock_code
        
        self.logger.info(f"=== {search_keyword} ({stock_code}) 뉴스 감정 분석 시작 ===")
        
        try:
            # 1. 뉴스 데이터 수집
            news_data = self.fetch_news_data(search_keyword, count=20)
            if not news_data:
                self.logger.warning(f"뉴스 데이터가 없음: {search_keyword}")
                return None
            
            # 2. AI 분석 수행
            ai_result = self.analyze_with_ai(news_data)
            
            # 3. 분석 결과 생성
            result = NewsAnalysisResult(
                company_name=search_keyword,
                stock_code=stock_code,
                total_news_count=len(news_data),
                positive_news_count=ai_result.get("positive_count", 0),
                negative_news_count=ai_result.get("negative_count", 0),
                neutral_news_count=ai_result.get("neutral_count", 0),
                sentiment_score=ai_result.get("sentiment_score", 0.0),
                material_impact=ai_result.get("material_impact", 0),
                key_topics=ai_result.get("key_topics", []),
                analysis_summary=ai_result.get("analysis_summary", "")
            )
            
            self.logger.info(f"뉴스 분석 완료 - {search_keyword}: "
                            f"감정점수 {result.sentiment_score:.2f}, 재료영향 {result.material_impact}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"뉴스 감정 분석 실패 - {stock_code}: {e}")
            return None

if __name__ == "__main__":
    # 테스트 코드
    logging.basicConfig(level=logging.INFO)
    
    analyzer = NewsAnalyzer()
    result = analyzer.analyze_news_sentiment("005930", "삼성전자")
    
    if result:
        print(f"\n📰 {result.company_name} ({result.stock_code}) 뉴스 분석 결과")
        print(f"전체 뉴스: {result.total_news_count}건")
        print(f"호재: {result.positive_news_count}건 | 악재: {result.negative_news_count}건 | 중립: {result.neutral_news_count}건")
        print(f"감정 점수: {result.sentiment_score:.3f} (-1.0 ~ +1.0)")
        
        if result.material_impact == 1:
            impact_text = "🟢 호재 (+1점)"
        elif result.material_impact == -1:
            impact_text = "🔴 악재 (-1점)"
        else:
            impact_text = "⚪ 중립 (0점)"
        
        print(f"재료 영향도: {impact_text}")
        
        if result.key_topics:
            print(f"주요 토픽: {', '.join(result.key_topics)}")
        
        print(f"분석 요약: {result.analysis_summary}")