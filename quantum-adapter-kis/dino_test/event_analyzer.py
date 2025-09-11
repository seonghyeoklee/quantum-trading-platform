#!/usr/bin/env python3
"""
D001: 구체화된 이벤트/호재 임박 분석기

뉴스와 공시에서 구체적인 날짜가 명시된 호재성 이벤트를 감지합니다.
- 신제품 출시
- 실적 발표/IR
- 계약 체결/파트너십
- 승인/인증 관련
- 기타 호재성 이벤트

구체적인 날짜가 포함된 호재 이벤트 발견 시 +1점
"""

import logging
import requests
import openai
import os
import re
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class EventAnalysisResult:
    """이벤트 분석 결과"""
    company_name: str
    stock_code: str
    total_sources: int          # 분석한 뉴스+공시 수
    imminent_events_count: int  # 임박한 호재 이벤트 수
    event_score: int           # 이벤트 점수 (0 또는 1)
    detected_events: List[Dict] # 감지된 이벤트 목록
    analysis_summary: str      # 분석 요약

@dataclass 
class DetectedEvent:
    """감지된 이벤트"""
    event_type: str       # 이벤트 유형 (신제품, 실적발표, 계약, 승인 등)
    description: str      # 이벤트 설명
    date_mention: str     # 날짜 언급 부분
    source: str          # 출처 (뉴스 또는 공시)
    title: str           # 제목
    urgency_score: float # 임박성 점수 (0-1)

class EventAnalyzer:
    """구체화된 이벤트/호재 임박 분석기"""
    
    def __init__(self, external_api_base_url: str = "http://external-api.quantum-trading.com:8001"):
        self.base_url = external_api_base_url
        self.logger = logging.getLogger(__name__)
        
        # OpenAI API 키 설정
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            openai.api_key = openai_api_key
            self.openai_available = True
            self.logger.info("✅ OpenAI API 키 설정 완료")
        else:
            self.openai_available = False
            self.logger.warning("⚠️ OpenAI API 키가 없어서 AI 분석 비활성화")
        
        # 호재성 이벤트 키워드 정의
        self.positive_event_keywords = {
            "신제품_출시": ["출시", "런칭", "론칭", "공개", "발표", "선보", "데뷔", "오픈", "런치"],
            "실적_IR": ["실적", "어닝", "컨퍼런스콜", "IR", "투자자", "설명회", "발표회", "보고서"],
            "계약_파트너십": ["계약", "수주", "파트너십", "협력", "MOU", "양해각서", "제휴", "합작"],
            "승인_인증": ["승인", "허가", "인증", "특허", "라이센스", "등록", "통과", "취득"],
            "투자_M&A": ["투자", "인수", "합병", "지분", "출자", "펀딩", "자금조달"],
            "기타_호재": ["수상", "선정", "채택", "도입", "확장", "진출", "성장", "개선"]
        }
        
        # 날짜 패턴 정규표현식 (한국어)
        self.date_patterns = [
            r'\d{4}년\s*\d{1,2}월',           # 2025년 3월
            r'\d{1,2}월\s*\d{1,2}일',         # 3월 15일
            r'다음\s*(주|달|월|분기|년)',      # 다음 주/달/월/분기/년
            r'이번\s*(주|달|월|분기|년)',      # 이번 주/달/월/분기/년
            r'곧|임박|예정|계획|준비',         # 곧, 임박, 예정, 계획
            r'\d{1,2}일\s*예정',             # 15일 예정
            r'\d{1,2}월\s*중',               # 3월 중
            r'\d+분기',                      # 1분기, 2분기
            r'연내|올해|내년',               # 연내, 올해, 내년
            r'\d{1,2}월말|월초',            # 3월말, 월초
        ]
    
    def fetch_news_data(self, company_keyword: str, count: int = 20) -> List[Dict]:
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
    
    def fetch_disclosure_data(self, stock_code: str) -> List[Dict]:
        """External API로 공시 데이터 수집"""
        try:
            # 종목코드 -> 기업코드 매핑 (주요 종목만)
            stock_to_corp_mapping = {
                "005930": "00126380",  # 삼성전자
                "000660": "00164779",  # SK하이닉스
                "035720": "00401731",  # 카카오
                "051910": "00154449",  # LG화학
                "003550": "00164742"   # LG
            }
            
            corp_code = stock_to_corp_mapping.get(stock_code)
            if not corp_code:
                self.logger.warning(f"기업코드 매핑 없음: {stock_code}")
                return []
            
            url = f"{self.base_url}/disclosure/company/{corp_code}"
            params = {"days": 30, "count": 20}  # 최근 30일간 공시
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            items = data.get("disclosures", [])
            
            self.logger.info(f"공시 데이터 수집 완료: {stock_code} - {len(items)}건")
            return items
            
        except Exception as e:
            self.logger.error(f"공시 데이터 수집 실패 - {stock_code}: {e}")
            return []
    
    def extract_date_mentions(self, text: str) -> List[str]:
        """텍스트에서 날짜 언급 추출"""
        date_mentions = []
        
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            date_mentions.extend(matches)
        
        return list(set(date_mentions))  # 중복 제거
    
    def analyze_with_openai(self, news_data: List[Dict], disclosure_data: List[Dict]) -> Dict:
        """OpenAI를 활용한 이벤트 분석"""
        if not self.openai_available:
            return self._fallback_analysis(news_data, disclosure_data)
        
        try:
            # 뉴스와 공시 제목들을 조합
            all_texts = []
            
            # 뉴스 데이터 추가
            for news in news_data[:10]:
                title = news.get("title", "").replace("<b>", "").replace("</b>", "")
                description = news.get("description", "")
                all_texts.append(f"[뉴스] {title} - {description}")
            
            # 공시 데이터 추가
            for disclosure in disclosure_data[:10]:
                title = disclosure.get("report_nm", "")
                all_texts.append(f"[공시] {title}")
            
            if not all_texts:
                return {"event_score": 0, "events": [], "analysis_summary": "분석할 데이터 없음"}
            
            combined_text = "\n".join(all_texts)
            
            # GPT 프롬프트 구성
            prompt = f"""
다음은 한국 상장기업의 최근 뉴스와 공시 내용입니다. 

텍스트:
{combined_text}

다음 기준으로 구체화된 호재 이벤트를 찾아 분석해주세요:

1. 구체적인 날짜나 시기가 명시된 호재성 이벤트
   - 신제품/서비스 출시 예정
   - 실적 발표/IR 행사 
   - 계약 체결/파트너십
   - 승인/인증 취득
   - 투자/M&A 관련
   
2. 분석 기준:
   - 구체적 날짜 언급 + 호재성 내용 = 점수 부여
   - 막연한 표현("향후", "언젠가")은 제외
   - 악재나 중립적 내용은 제외

JSON 형식으로 응답:
{{
    "event_score": 0 또는 1 (구체적 호재 이벤트 있으면 1점),
    "events_count": 감지된 이벤트 수,
    "detected_events": [
        {{
            "event_type": "이벤트 유형",
            "description": "이벤트 설명",
            "date_mention": "날짜 언급 부분",
            "urgency_score": 0.0-1.0
        }}
    ],
    "analysis_summary": "분석 요약"
}}
            """
            
            # OpenAI API 호출
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 한국 증시 전문 애널리스트입니다. 구체적인 날짜가 명시된 호재 이벤트를 정확히 식별합니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # JSON 파싱
            import json
            try:
                result = json.loads(result_text)
                self.logger.info(f"✅ OpenAI 이벤트 분석 성공: {result.get('analysis_summary', 'N/A')}")
                return result
            except json.JSONDecodeError:
                self.logger.warning(f"JSON 파싱 실패, 원본 응답: {result_text}")
                return self._fallback_analysis(news_data, disclosure_data)
                
        except Exception as e:
            self.logger.error(f"OpenAI API 호출 실패: {e}")
            return self._fallback_analysis(news_data, disclosure_data)
    
    def _fallback_analysis(self, news_data: List[Dict], disclosure_data: List[Dict]) -> Dict:
        """AI 분석 실패 시 키워드 기반 폴백 분석"""
        detected_events = []
        
        # 뉴스 분석
        for news in news_data:
            title = news.get("title", "").replace("<b>", "").replace("</b>", "")
            description = news.get("description", "")
            full_text = f"{title} {description}"
            
            # 날짜 패턴 확인
            date_mentions = self.extract_date_mentions(full_text)
            if not date_mentions:
                continue
            
            # 호재성 이벤트 키워드 확인
            for event_type, keywords in self.positive_event_keywords.items():
                for keyword in keywords:
                    if keyword in full_text:
                        detected_events.append({
                            "event_type": event_type,
                            "description": title[:100],
                            "date_mention": ", ".join(date_mentions),
                            "source": "뉴스",
                            "urgency_score": 0.7
                        })
                        break
        
        # 공시 분석
        for disclosure in disclosure_data:
            title = disclosure.get("report_nm", "")
            
            # 날짜 패턴 확인
            date_mentions = self.extract_date_mentions(title)
            if not date_mentions:
                continue
            
            # 호재성 이벤트 키워드 확인
            for event_type, keywords in self.positive_event_keywords.items():
                for keyword in keywords:
                    if keyword in title:
                        detected_events.append({
                            "event_type": event_type,
                            "description": title,
                            "date_mention": ", ".join(date_mentions),
                            "source": "공시",
                            "urgency_score": 0.8
                        })
                        break
        
        # 점수 계산
        event_score = 1 if detected_events else 0
        
        return {
            "event_score": event_score,
            "events_count": len(detected_events),
            "detected_events": detected_events,
            "analysis_summary": f"키워드 분석: {len(detected_events)}개 이벤트 감지"
        }
    
    def analyze_imminent_events(self, stock_code: str, company_name: str = None) -> Optional[EventAnalysisResult]:
        """D001: 구체화된 이벤트/호재 임박 분석"""
        
        search_keyword = company_name if company_name else stock_code
        
        self.logger.info(f"=== {search_keyword} ({stock_code}) D001 이벤트 분석 시작 ===")
        
        try:
            # 1. 뉴스 및 공시 데이터 수집
            news_data = self.fetch_news_data(search_keyword, count=20)
            disclosure_data = self.fetch_disclosure_data(stock_code)
            
            if not news_data and not disclosure_data:
                self.logger.warning(f"분석할 데이터가 없음: {search_keyword}")
                return None
            
            # 2. 이벤트 분석 수행
            ai_result = self.analyze_with_openai(news_data, disclosure_data)
            
            # 3. 결과 생성
            result = EventAnalysisResult(
                company_name=search_keyword,
                stock_code=stock_code,
                total_sources=len(news_data) + len(disclosure_data),
                imminent_events_count=ai_result.get("events_count", 0),
                event_score=ai_result.get("event_score", 0),
                detected_events=ai_result.get("detected_events", []),
                analysis_summary=ai_result.get("analysis_summary", "")
            )
            
            self.logger.info(f"D001 이벤트 분석 완료 - {search_keyword}: "
                            f"점수 {result.event_score}, 이벤트 {result.imminent_events_count}개")
            
            return result
            
        except Exception as e:
            self.logger.error(f"D001 이벤트 분석 실패 - {stock_code}: {e}")
            return None

if __name__ == "__main__":
    # 테스트 코드
    logging.basicConfig(level=logging.INFO)
    
    analyzer = EventAnalyzer()
    result = analyzer.analyze_imminent_events("005930", "삼성전자")
    
    if result:
        print(f"\n📅 {result.company_name} ({result.stock_code}) D001 이벤트 분석 결과")
        print(f"분석 소스: {result.total_sources}건 (뉴스+공시)")
        print(f"임박 이벤트: {result.imminent_events_count}개")
        print(f"D001 점수: {result.event_score}점")
        
        if result.detected_events:
            print(f"\n감지된 이벤트:")
            for i, event in enumerate(result.detected_events, 1):
                print(f"{i}. [{event['event_type']}] {event['description']}")
                print(f"   날짜: {event['date_mention']} | 출처: {event['source']}")
        
        print(f"\n분석 요약: {result.analysis_summary}")