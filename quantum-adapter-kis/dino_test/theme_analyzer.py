#!/usr/bin/env python3
"""
D002: 확실한 주도 테마 분석기

뉴스와 시장 데이터를 분석하여 특정 종목이 확실한 주도 테마에 속하는지 판단합니다.
- 테마 집중도 분석
- 관련주 동반 움직임 확인  
- 시장 관심도 측정
- AI 기반 테마 판단

확실한 주도 테마로 판단되면 +1점
"""

import logging
import requests
import os
import re
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from .ai_client import get_ai_client

logger = logging.getLogger(__name__)

@dataclass
class ThemeAnalysisResult:
    """테마 분석 결과"""
    company_name: str
    stock_code: str
    is_leading_theme: bool          # 주도 테마 여부
    theme_score: int               # 테마 점수 (0 또는 1)
    detected_theme: str            # 감지된 테마명
    confidence_score: float        # 신뢰도 (0.0-1.0)
    theme_evidence: List[str]      # 테마 근거 목록
    related_news_count: int        # 관련 뉴스 수
    analysis_summary: str          # 분석 요약

class ThemeAnalyzer:
    """확실한 주도 테마 분석기"""
    
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
        
        # 주요 테마 키워드 정의 (2025년 기준)
        self.theme_keywords = {
            "AI/인공지능": [
                "AI", "인공지능", "ChatGPT", "LLM", "딥러닝", "머신러닝", "생성AI", 
                "GPT", "클로드", "미드저니", "오픈AI", "구글 바드", "AGI"
            ],
            "반도체": [
                "반도체", "메모리", "D램", "DRAM", "낸드", "NAND", "HBM", "시스템반도체",
                "파운드리", "웨이퍼", "칩셋", "AP", "GPU", "NPU", "TSMC"
            ],
            "방산": [
                "방산", "국방", "무기", "미사일", "전투기", "KF-21", "방위산업", 
                "군수", "레이더", "드론", "무인기", "국방예산", "NATO"
            ],
            "원자력": [
                "원자력", "원전", "소형모듈원자로", "SMR", "원자로", "핵발전", 
                "우라늄", "원전 수출", "APR1400", "한수원"
            ],
            "K-POP/엔터": [
                "K-POP", "케이팝", "BTS", "블랙핑크", "하이브", "SM", "JYP", "YG",
                "엔터테인먼트", "한류", "콘텐츠", "음원", "앨범"
            ],
            "2차전지": [
                "배터리", "전기차", "ESS", "양극재", "음극재", "분리막", "전해질",
                "리튬", "이차전지", "LFP", "NCM", "테슬라", "BYD"
            ],
            "바이오/의료": [
                "바이오", "제약", "신약", "백신", "항체", "유전자치료", "세포치료",
                "임상시험", "FDA", "식약처", "코로나", "치료제"
            ],
            "게임/메타버스": [
                "게임", "메타버스", "VR", "AR", "가상현실", "증강현실", "NFT",
                "블록체인", "크래프톤", "넥슨", "엔씨소프트", "미호요"
            ],
            "우주항공": [
                "우주", "항공", "위성", "발사체", "누리호", "한화시스템", "스페이스X",
                "위성통신", "GPS", "우주정거장"
            ],
            "친환경/ESG": [
                "친환경", "ESG", "탄소중립", "재생에너지", "태양광", "풍력",
                "수소", "그린뉴딜", "RE100", "탄소배출권"
            ]
        }
    
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
    
    def extract_theme_keywords(self, text: str) -> Dict[str, int]:
        """텍스트에서 테마 키워드 추출 및 빈도 계산"""
        theme_counts = {}
        
        # 대소문자 구분 없이 검색
        text_lower = text.lower()
        
        for theme_name, keywords in self.theme_keywords.items():
            count = 0
            for keyword in keywords:
                # 정확한 매칭을 위해 단어 경계 확인
                pattern = rf'\b{re.escape(keyword.lower())}\b'
                matches = re.findall(pattern, text_lower)
                count += len(matches)
            
            if count > 0:
                theme_counts[theme_name] = count
        
        return theme_counts
    
    def analyze_with_ai(self, news_data: List[Dict], company_name: str) -> Dict:
        """AI를 활용한 테마 분석 (Claude 우선, OpenAI 폴백)"""
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
                return {"is_leading_theme": False, "theme_score": 0, "analysis_summary": "분석할 뉴스 없음"}
            
            news_text = "\n".join([f"{i+1}. {title}" for i, title in enumerate(news_titles)])
            
            # 현재 주요 테마 목록을 프롬프트에 포함
            theme_list = ", ".join(self.theme_keywords.keys())
            
            # AI 프롬프트 구성
            system_prompt = "당신은 한국 증시의 테마주 전문 애널리스트입니다. 뉴스 분석을 통해 주도 테마를 정확히 판단합니다."
            
            user_prompt = f"""
다음은 {company_name}과 관련된 최근 뉴스입니다:

{news_text}

현재 주요 테마: {theme_list}

분석 기준:
1. 특정 테마에 대한 뉴스 집중도 (3건 이상 관련 뉴스)
2. 테마의 시장 주도성 (정부 정책, 글로벌 트렌드 연관성)
3. 지속적인 관심도 (단순 일회성이 아닌 지속적 이슈)
4. 기업의 테마 내 위상 (선도 기업 또는 핵심 기업 여부)

{company_name}이 확실한 주도 테마에 속하는지 판단해주세요.

JSON 형식으로 응답:
{{
    "is_leading_theme": true 또는 false,
    "detected_theme": "가장 연관성 높은 테마명",
    "confidence_score": 0.0-1.0 신뢰도,
    "theme_evidence": ["근거1", "근거2", "근거3"],
    "related_news_count": 관련 뉴스 수,
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
                self.logger.info(f"✅ AI 테마 분석 성공: {result.get('analysis_summary', 'N/A')}")
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
                "is_leading_theme": False,
                "detected_theme": "",
                "confidence_score": 0.0,
                "theme_evidence": [],
                "related_news_count": 0,
                "analysis_summary": "분석할 뉴스가 없음"
            }
        
        # 모든 뉴스 텍스트 결합
        all_text = ""
        for news in news_data:
            title = news.get("title", "").replace("<b>", "").replace("</b>", "")
            description = news.get("description", "")
            all_text += f"{title} {description} "
        
        # 테마별 키워드 빈도 분석
        theme_scores = self.extract_theme_keywords(all_text)
        
        if not theme_scores:
            return {
                "is_leading_theme": False,
                "detected_theme": "",
                "confidence_score": 0.0,
                "theme_evidence": [],
                "related_news_count": 0,
                "analysis_summary": "관련 테마를 찾을 수 없음"
            }
        
        # 가장 높은 점수의 테마 선택
        top_theme = max(theme_scores, key=theme_scores.get)
        top_score = theme_scores[top_theme]
        
        # 주도 테마 판정 기준: 키워드 3회 이상 + 뉴스 5건 이상
        is_leading = top_score >= 3 and len(news_data) >= 5
        confidence = min(0.9, (top_score / 10) + (len(news_data) / 20))
        
        evidence = [
            f"{top_theme} 키워드 {top_score}회 언급",
            f"관련 뉴스 {len(news_data)}건 확인",
            f"신뢰도 {confidence:.1%}"
        ]
        
        return {
            "is_leading_theme": is_leading,
            "detected_theme": top_theme,
            "confidence_score": confidence,
            "theme_evidence": evidence,
            "related_news_count": len(news_data),
            "analysis_summary": f"키워드 분석: {top_theme} 테마 {top_score}회 감지"
        }
    
    def analyze_leading_theme(self, stock_code: str, company_name: str = None) -> Optional[ThemeAnalysisResult]:
        """D002: 확실한 주도 테마 분석"""
        
        search_keyword = company_name if company_name else stock_code
        
        self.logger.info(f"=== {search_keyword} ({stock_code}) D002 주도 테마 분석 시작 ===")
        
        try:
            # 1. 뉴스 데이터 수집
            news_data = self.fetch_news_data(search_keyword, count=30)
            
            if not news_data:
                self.logger.warning(f"분석할 뉴스 데이터가 없음: {search_keyword}")
                return None
            
            # 2. 테마 분석 수행
            ai_result = self.analyze_with_ai(news_data, search_keyword)
            
            # 3. 결과 생성
            theme_score = 1 if ai_result.get("is_leading_theme", False) else 0
            
            result = ThemeAnalysisResult(
                company_name=search_keyword,
                stock_code=stock_code,
                is_leading_theme=ai_result.get("is_leading_theme", False),
                theme_score=theme_score,
                detected_theme=ai_result.get("detected_theme", ""),
                confidence_score=ai_result.get("confidence_score", 0.0),
                theme_evidence=ai_result.get("theme_evidence", []),
                related_news_count=ai_result.get("related_news_count", len(news_data)),
                analysis_summary=ai_result.get("analysis_summary", "")
            )
            
            self.logger.info(f"D002 테마 분석 완료 - {search_keyword}: "
                            f"점수 {result.theme_score}, 테마: {result.detected_theme}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"D002 테마 분석 실패 - {stock_code}: {e}")
            return None

if __name__ == "__main__":
    # 테스트 코드
    logging.basicConfig(level=logging.INFO)
    
    analyzer = ThemeAnalyzer()
    result = analyzer.analyze_leading_theme("005930", "삼성전자")
    
    if result:
        print(f"\n🎯 {result.company_name} ({result.stock_code}) D002 테마 분석 결과")
        print(f"주도 테마 여부: {'✅ YES' if result.is_leading_theme else '❌ NO'}")
        print(f"D002 점수: {result.theme_score}점")
        print(f"감지된 테마: {result.detected_theme}")
        print(f"신뢰도: {result.confidence_score:.1%}")
        print(f"관련 뉴스: {result.related_news_count}건")
        
        if result.theme_evidence:
            print(f"\n테마 근거:")
            for i, evidence in enumerate(result.theme_evidence, 1):
                print(f"{i}. {evidence}")
        
        print(f"\n분석 요약: {result.analysis_summary}")