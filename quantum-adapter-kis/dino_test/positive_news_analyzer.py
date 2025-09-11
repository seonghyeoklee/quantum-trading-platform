#!/usr/bin/env python3
"""
D008: 호재뉴스 도배 분석기

뉴스 제목과 내용을 AI로 분석하여 호재 뉴스의 집중도와 도배성을 판단합니다.
- 호재뉴스가 집중적으로 쏟아지는 경우 (도배): +1점
- 일반적인 뉴스 분포: 0점
- 악재가 더 많은 경우: -1점 (하지만 이는 D007에서 처리)

도배 판단 기준:
1. 호재 뉴스 비율 > 70%
2. 호재 뉴스 개수 ≥ 5개
3. 뉴스 제목의 과장성 표현 빈도
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
class PositiveNewsAnalysisResult:
    """호재뉴스 도배 분석 결과"""
    company_name: str
    stock_code: str
    total_news_count: int           # 전체 뉴스 수
    positive_news_count: int        # 호재 뉴스 수
    positive_ratio: float           # 호재 뉴스 비율 (0.0-1.0)
    hype_score: float              # 과장성 점수 (0.0-1.0)
    flooding_score: int            # 도배 점수 (-1, 0, 1)
    positive_keywords_found: List[str]  # 발견된 호재 키워드들
    hype_expressions: List[str]    # 과장 표현들
    analysis_summary: str          # 분석 요약

class PositiveNewsAnalyzer:
    """호재뉴스 도배 분석기"""
    
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
        
        # 호재성 키워드 정의 (기존 news_analyzer.py의 positive_keywords 확장)
        self.positive_keywords = [
            # 기본 호재
            "계약", "수주", "협력", "파트너십", "투자", "인수", "합병", "출시", "개발", "혁신",
            "성장", "증가", "상승", "개선", "흑자", "이익", "매출", "확대", "진출", "성공",
            "수상", "인증", "승인", "선정", "채택", "도입", "런칭", "오픈",
            
            # 과장 표현
            "급등", "폭등", "강세", "최고", "사상최대", "역대급", "급성장", "대박",
            "초대형", "메가", "슈퍼", "울트라", "최강", "압도적", "독보적",
            "혁명적", "획기적", "놀라운", "엄청난", "대단한", "최고급", "프리미엄",
            
            # 시장 관련
            "매수", "추천", "목표가", "상향", "긍정적", "호조", "부상", "주목",
            "기대", "전망", "유망", "잠재력", "기회", "모멘텀", "촉진", "가속화"
        ]
        
        # 과장성 표현 패턴
        self.hype_patterns = [
            "급등", "폭등", "대박", "사상최대", "역대급", "초대형", "메가", "슈퍼",
            "최강", "압도적", "독보적", "혁명적", "획기적", "놀라운", "엄청난",
            "!!!", "★", "☆", "♥", "◆", "■", "●", "▲", "↑", "☞"
        ]
    
    def fetch_news_data(self, company_keyword: str, count: int = 30) -> List[Dict]:
        """External API로 뉴스 데이터 수집"""
        try:
            url = f"{self.base_url}/news/financial/{company_keyword}"
            params = {"count": count}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            items = data.get("items", [])
            
            self.logger.info(f"뉴스 데이터 수집 완료: {company_keyword} - {len(items)}건")
            return items
            
        except Exception as e:
            self.logger.error(f"뉴스 데이터 수집 실패 - {company_keyword}: {e}")
            return []
    
    def analyze_with_ai(self, news_data: List[Dict], company_name: str) -> Dict:
        """AI를 활용한 호재뉴스 도배 분석 (Claude 우선, OpenAI 폴백)"""
        if not self.ai_available or not news_data:
            return self._fallback_analysis(news_data, company_name)
        
        try:
            # 뉴스 제목들을 조합
            news_titles = []
            for news in news_data[:15]:  # 최대 15개 뉴스 분석
                title = news.get("title", "").replace("<b>", "").replace("</b>", "")
                description = news.get("description", "")
                news_titles.append(f"{title} - {description[:100]}")
            
            if not news_titles:
                return {"flooding_score": 0, "positive_ratio": 0.0, "analysis_summary": "분석할 뉴스 없음"}
            
            news_text = "\n".join([f"{i+1}. {title}" for i, title in enumerate(news_titles)])
            
            # AI 프롬프트 구성
            system_prompt = "당신은 한국 증시 뉴스 전문 분석가입니다. 호재 뉴스의 도배성과 과장성을 정확히 판단합니다."
            
            user_prompt = f"""
다음은 {company_name}과 관련된 최근 뉴스입니다:

{news_text}

뉴스 분석 기준:
1. 호재뉴스 도배성 판단
   - 호재 뉴스 비율이 70% 이상이고 5건 이상인 경우 "도배"로 판단
   - 과장된 표현이 많이 사용된 경우 가중치 부여
   - 제목에 "급등", "대박", "사상최대" 등 과장 표현 확인

2. 점수 부여 기준:
   - 호재뉴스 도배 (70% 이상 + 5건 이상): +1점
   - 일반적인 뉴스 분포: 0점
   - 악재가 더 많은 경우: -1점

3. 과장성 분석:
   - 제목의 감정적, 과장적 표현 빈도 측정
   - 객관적 사실 vs 주관적 평가 비율

JSON 형식으로 응답:
{{
    "flooding_score": -1, 0, 또는 1,
    "positive_news_count": 호재 뉴스 개수,
    "total_news_count": 전체 뉴스 개수,
    "positive_ratio": 호재 뉴스 비율 (0.0-1.0),
    "hype_score": 과장성 점수 (0.0-1.0),
    "positive_keywords_found": ["발견된 호재 키워드들"],
    "hype_expressions": ["과장 표현들"],
    "analysis_summary": "분석 요약"
}}
            """
            
            # AI API 호출
            result_text = self.ai_client.analyze_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=800
            )
            
            if not result_text:
                self.logger.warning("AI API 호출 실패, 키워드 분석으로 폴백")
                return self._fallback_analysis(news_data, company_name)
            
            # JSON 파싱
            result = self.ai_client.parse_json_response(result_text)
            if result:
                self.logger.info(f"✅ AI 호재뉴스 분석 성공: {result.get('analysis_summary', 'N/A')}")
                return result
            else:
                self.logger.warning(f"JSON 파싱 실패, 원본 응답: {result_text[:200]}...")
                return self._fallback_analysis(news_data, company_name)
                
        except Exception as e:
            self.logger.error(f"AI API 호출 실패: {e}")
            return self._fallback_analysis(news_data, company_name)
    
    def _fallback_analysis(self, news_data: List[Dict], company_name: str) -> Dict:
        """AI 분석 실패 시 키워드 기반 폴백 분석"""
        if not news_data:
            return {
                "flooding_score": 0,
                "positive_news_count": 0,
                "total_news_count": 0,
                "positive_ratio": 0.0,
                "hype_score": 0.0,
                "positive_keywords_found": [],
                "hype_expressions": [],
                "analysis_summary": "분석할 뉴스가 없음"
            }
        
        positive_count = 0
        total_count = len(news_data)
        found_keywords = set()
        found_hype = set()
        
        for news in news_data:
            title = news.get("title", "").replace("<b>", "").replace("</b>", "")
            description = news.get("description", "")
            full_text = f"{title} {description}"
            
            # 호재 키워드 검사
            positive_matches = 0
            for keyword in self.positive_keywords:
                if keyword in full_text:
                    positive_matches += 1
                    found_keywords.add(keyword)
            
            # 과장 표현 검사
            for pattern in self.hype_patterns:
                if pattern in full_text:
                    found_hype.add(pattern)
            
            # 호재 뉴스 판정 (키워드 2개 이상)
            if positive_matches >= 2:
                positive_count += 1
        
        # 비율 계산
        positive_ratio = positive_count / total_count if total_count > 0 else 0.0
        
        # 과장성 점수 (과장 표현 빈도 기반)
        hype_score = min(1.0, len(found_hype) / 5.0)  # 최대 5개 기준으로 정규화
        
        # 도배 점수 판정
        if positive_ratio >= 0.7 and positive_count >= 5:
            flooding_score = 1  # 호재뉴스 도배
        elif positive_ratio <= 0.3 and positive_count <= 2:
            flooding_score = -1  # 악재 우세
        else:
            flooding_score = 0  # 중립
        
        return {
            "flooding_score": flooding_score,
            "positive_news_count": positive_count,
            "total_news_count": total_count,
            "positive_ratio": positive_ratio,
            "hype_score": hype_score,
            "positive_keywords_found": list(found_keywords)[:10],  # 최대 10개
            "hype_expressions": list(found_hype)[:5],  # 최대 5개
            "analysis_summary": f"키워드 분석: 호재 {positive_count}/{total_count}건 ({positive_ratio:.1%})"
        }
    
    def analyze_positive_news_flooding(self, stock_code: str, company_name: str = None) -> Optional[PositiveNewsAnalysisResult]:
        """D008: 호재뉴스 도배 분석"""
        
        search_keyword = company_name if company_name else stock_code
        
        self.logger.info(f"=== {search_keyword} ({stock_code}) D008 호재뉴스 도배 분석 시작 ===")
        
        try:
            # 1. 뉴스 데이터 수집
            news_data = self.fetch_news_data(search_keyword, count=30)
            
            if not news_data:
                self.logger.warning(f"분석할 뉴스 데이터가 없음: {search_keyword}")
                return None
            
            # 2. 호재뉴스 도배 분석 수행
            ai_result = self.analyze_with_ai(news_data, search_keyword)
            
            # 3. 결과 생성
            result = PositiveNewsAnalysisResult(
                company_name=search_keyword,
                stock_code=stock_code,
                total_news_count=ai_result.get("total_news_count", len(news_data)),
                positive_news_count=ai_result.get("positive_news_count", 0),
                positive_ratio=ai_result.get("positive_ratio", 0.0),
                hype_score=ai_result.get("hype_score", 0.0),
                flooding_score=ai_result.get("flooding_score", 0),
                positive_keywords_found=ai_result.get("positive_keywords_found", []),
                hype_expressions=ai_result.get("hype_expressions", []),
                analysis_summary=ai_result.get("analysis_summary", "")
            )
            
            self.logger.info(f"D008 호재뉴스 분석 완료 - {search_keyword}: "
                            f"점수 {result.flooding_score}, 호재비율 {result.positive_ratio:.1%}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"D008 호재뉴스 분석 실패 - {stock_code}: {e}")
            return None

if __name__ == "__main__":
    # 테스트 코드
    logging.basicConfig(level=logging.INFO)
    
    analyzer = PositiveNewsAnalyzer()
    result = analyzer.analyze_positive_news_flooding("005930", "삼성전자")
    
    if result:
        print(f"\n📈 {result.company_name} ({result.stock_code}) D008 호재뉴스 분석 결과")
        print(f"전체 뉴스: {result.total_news_count}건")
        print(f"호재 뉴스: {result.positive_news_count}건 ({result.positive_ratio:.1%})")
        print(f"과장성 점수: {result.hype_score:.2f}")
        
        if result.flooding_score == 1:
            impact_text = "🟢 호재뉴스 도배 (+1점)"
        elif result.flooding_score == -1:
            impact_text = "🔴 악재 우세 (-1점)"
        else:
            impact_text = "⚪ 중립 (0점)"
        
        print(f"D008 점수: {impact_text}")
        
        if result.positive_keywords_found:
            print(f"발견된 호재 키워드: {', '.join(result.positive_keywords_found[:5])}")
        
        if result.hype_expressions:
            print(f"과장 표현: {', '.join(result.hype_expressions)}")
        
        print(f"분석 요약: {result.analysis_summary}")