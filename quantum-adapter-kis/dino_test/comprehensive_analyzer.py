#!/usr/bin/env python3
"""
종합 DINO 테스트 실행 및 저장 시스템

모든 DINO 분석을 수행하고 결과와 Raw 데이터를 데이터베이스에 저장합니다.
- 9개 분석 영역 실행
- 모든 Raw 데이터 수집 및 저장
- 하루 1회 분석 제한 (unique constraint)
- AI 응답 및 환경 정보 보존
"""

import logging
import psycopg2
import json
from datetime import datetime, date
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict

from .finance_data_collector import FinanceDataCollector
from .finance_scorer import DinoTestFinanceScorer
from .theme_analyzer import ThemeAnalyzer
from .material_analyzer import DinoTestMaterialAnalyzer
from .interest_coverage_analyzer import InterestCoverageAnalyzer
from .news_analyzer import NewsAnalyzer
from .event_analyzer import EventAnalyzer
from .positive_news_analyzer import PositiveNewsAnalyzer
from .technical_analyzer import DinoTestTechnicalAnalyzer
from .price_analyzer import DinoTestPriceAnalyzer

logger = logging.getLogger(__name__)

@dataclass
class ComprehensiveDinoResult:
    """종합 DINO 테스트 결과"""
    stock_code: str
    company_name: str
    user_id: int
    
    # 9개 분석 영역 점수
    finance_score: int = 0           # D001: 재무 분석 (0-5)
    technical_score: int = 0         # 기술적 분석 (0-5) - TODO
    price_score: int = 0            # 가격 분석 (0-5) - TODO
    material_score: int = 0         # D003: 소재 분석 (0-5)
    event_score: int = 0            # D001: 이벤트 분석 (0 or 1)
    theme_score: int = 0            # D002: 테마 분석 (0 or 1)
    positive_news_score: int = 0    # D008: 호재뉴스 도배 (-1, 0, 1)
    interest_coverage_score: int = 0 # D009: 이자보상배율 (0-5)
    
    analysis_date: date = None
    status: str = "PENDING"
    
    def __post_init__(self):
        if self.analysis_date is None:
            self.analysis_date = date.today()
    
    @property
    def total_score(self) -> int:
        """총 점수 계산"""
        return (self.finance_score + self.technical_score + self.price_score + 
                self.material_score + self.event_score + self.theme_score + 
                self.positive_news_score + self.interest_coverage_score)

@dataclass
class RawDataCollection:
    """Raw 데이터 수집 결과"""
    # 외부 API Raw 데이터
    news_raw_data: Optional[Dict] = None
    disclosure_raw_data: Optional[Dict] = None
    financial_raw_data: Optional[Dict] = None
    technical_raw_data: Optional[Dict] = None
    price_raw_data: Optional[Dict] = None
    material_raw_data: Optional[Dict] = None
    
    # AI 분석 응답 원문
    ai_theme_response: Optional[str] = None
    ai_news_response: Optional[str] = None
    ai_event_response: Optional[str] = None
    ai_positive_news_response: Optional[str] = None
    
    # 분석 환경 정보
    analysis_environment: Optional[Dict] = None
    ai_model_info: Optional[Dict] = None

class ComprehensiveDinoAnalyzer:
    """종합 DINO 테스트 분석기"""
    
    def __init__(self, db_host: str = "localhost", db_port: int = 5432, 
                 db_name: str = "quantum_trading", db_user: str = "quantum", 
                 db_password: str = "quantum123"):
        self.logger = logging.getLogger(__name__)
        
        # 데이터베이스 연결 설정
        self.db_config = {
            "host": db_host,
            "port": db_port,
            "database": db_name,
            "user": db_user,
            "password": db_password
        }
        
        # 개별 분석기 초기화 (필요할 때 동적 로드)
        self.finance_data_collector = None
        self.finance_scorer = None
        
        self.logger.info("✅ ComprehensiveDinoAnalyzer 초기화 완료")
    
    def check_existing_analysis(self, stock_code: str, analysis_date: date = None) -> bool:
        """기존 분석 존재 여부 확인 (하루 1회 제한)"""
        if analysis_date is None:
            analysis_date = date.today()
        
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) FROM dino_test_results 
                        WHERE stock_code = %s AND analysis_date = %s
                    """, (stock_code, analysis_date))
                    
                    count = cursor.fetchone()[0]
                    exists = count > 0
                    
                    if exists:
                        self.logger.warning(f"⚠️ {stock_code} 오늘 분석 이미 존재: {analysis_date}")
                    
                    return exists
                    
        except Exception as e:
            self.logger.error(f"기존 분석 확인 실패: {e}")
            return False
    
    def run_comprehensive_analysis(self, stock_code: str, company_name: str = None, 
                                 user_id: int = 1, force_rerun: bool = False) -> Optional[ComprehensiveDinoResult]:
        """종합 DINO 분석 실행"""
        
        search_name = company_name if company_name else stock_code
        self.logger.info(f"🚀 종합 DINO 분석 시작: {search_name} ({stock_code})")
        
        # 1. 기존 분석 확인 (강제 재실행이 아닌 경우)
        if not force_rerun and self.check_existing_analysis(stock_code):
            self.logger.info(f"⏭️ 오늘 이미 분석됨, 건너뜀: {stock_code}")
            return None
        
        # 2. 결과 및 Raw 데이터 객체 초기화
        result = ComprehensiveDinoResult(
            stock_code=stock_code,
            company_name=search_name,
            user_id=user_id,
            status="RUNNING"
        )
        
        raw_data = RawDataCollection()
        
        # 3. 분석 환경 정보 수집
        raw_data.analysis_environment = {
            "analysis_timestamp": datetime.now().isoformat(),
            "python_version": "3.13",
            "system": "quantum-adapter-kis",
            "analyzer_version": "1.0.0"
        }
        
        try:
            # 실제 분석기들을 사용한 종합 분석
            
            # 4. D002: 테마 분석 (AI 기반)
            self.logger.info("🎯 D002 테마 분석 실행중...")
            try:
                theme_analyzer = ThemeAnalyzer()
                theme_result = theme_analyzer.analyze_leading_theme(stock_code, search_name)
                if theme_result:
                    result.theme_score = theme_result.theme_score
                    raw_data.ai_theme_response = theme_result.analysis_summary
                    
                    # 테마 분석에 사용된 뉴스 데이터 수집 및 저장
                    theme_news_data = theme_analyzer.fetch_news_data(search_name, count=30)
                    news_links = []
                    for news in theme_news_data[:10]:  # 상위 10개 뉴스 링크만 저장
                        if news.get('link'):
                            news_links.append({
                                'title': news.get('title', '').replace('<b>', '').replace('</b>', ''),
                                'link': news.get('link'),
                                'pub_date': news.get('pubDate', ''),
                                'description': news.get('description', '')[:100] + '...' if news.get('description') else ''
                            })
                    
                    raw_data.news_raw_data = {
                        "theme_analysis": {
                            "detected_theme": theme_result.detected_theme,
                            "confidence_score": theme_result.confidence_score,
                            "is_leading_theme": theme_result.is_leading_theme,
                            "related_news_count": theme_result.related_news_count,
                            "analyzed_news_links": news_links
                        }
                    }
                    self.logger.info(f"✅ D002 테마 분석 완료: {result.theme_score}점, 테마: {theme_result.detected_theme}, 뉴스 {len(news_links)}건 링크 저장")
            except Exception as e:
                self.logger.warning(f"⚠️ D002 테마 분석 실패: {e}")
                result.theme_score = 0
            
            # 5. D009: 이자보상배율 분석
            self.logger.info("🏦 D009 이자보상배율 분석 실행중...")
            try:
                coverage_analyzer = InterestCoverageAnalyzer()
                coverage_result = coverage_analyzer.analyze_interest_coverage(stock_code, search_name)
                if coverage_result:
                    result.interest_coverage_score = coverage_result.coverage_score
                    raw_data.financial_raw_data = raw_data.financial_raw_data or {}
                    raw_data.financial_raw_data.update({
                        "interest_coverage": {
                            "coverage_ratio": coverage_result.interest_coverage_ratio,
                            "ebit": coverage_result.ebit,
                            "interest_expense": coverage_result.interest_expense,
                            "analysis_summary": coverage_result.analysis_summary
                        }
                    })
                    self.logger.info(f"✅ D009 이자보상배율 분석 완료: {result.interest_coverage_score}점")
            except Exception as e:
                self.logger.warning(f"⚠️ D009 이자보상배율 분석 실패: {e}")
                result.interest_coverage_score = 0
            
            # 6. D001: 이벤트 분석 (구체적 호재 임박)
            self.logger.info("📅 D001 이벤트 분석 실행중...")
            try:
                event_analyzer = EventAnalyzer()
                event_result = event_analyzer.analyze_imminent_events(stock_code, search_name)
                if event_result:
                    result.event_score = event_result.event_score
                    raw_data.ai_event_response = event_result.analysis_summary
                    
                    # 이벤트 분석에 사용된 뉴스 데이터 수집 및 저장
                    event_news_data = event_analyzer.fetch_news_data(search_name, count=20)
                    event_news_links = []
                    for news in event_news_data[:10]:  # 상위 10개 뉴스 링크 저장
                        if news.get('link'):
                            event_news_links.append({
                                'title': news.get('title', '').replace('<b>', '').replace('</b>', ''),
                                'link': news.get('link'),
                                'pub_date': news.get('pubDate', ''),
                                'description': news.get('description', '')[:100] + '...' if news.get('description') else ''
                            })
                    
                    raw_data.disclosure_raw_data = {
                        "imminent_events": {
                            "events_count": event_result.imminent_events_count,
                            "detected_events": event_result.detected_events,
                            "total_sources": event_result.total_sources,
                            "analyzed_news_links": event_news_links
                        }
                    }
                    self.logger.info(f"✅ D001 이벤트 분석 완료: {result.event_score}점, 뉴스 {len(event_news_links)}건 링크 저장")
            except Exception as e:
                self.logger.warning(f"⚠️ D001 이벤트 분석 실패: {e}")
                result.event_score = 0
            
            # 7. D008: 호재뉴스 도배 분석
            self.logger.info("📈 D008 호재뉴스 도배 분석 실행중...")
            try:
                positive_analyzer = PositiveNewsAnalyzer()
                positive_result = positive_analyzer.analyze_positive_news_flooding(stock_code, search_name)
                if positive_result:
                    result.positive_news_score = positive_result.flooding_score
                    raw_data.ai_positive_news_response = positive_result.analysis_summary
                    
                    # 호재뉴스 분석에 사용된 뉴스 데이터 수집 및 저장
                    positive_news_data = positive_analyzer.fetch_news_data(search_name, count=30)
                    positive_news_links = []
                    for news in positive_news_data[:15]:  # 상위 15개 뉴스 링크 저장 (호재뉴스 분석은 더 많이 저장)
                        if news.get('link'):
                            positive_news_links.append({
                                'title': news.get('title', '').replace('<b>', '').replace('</b>', ''),
                                'link': news.get('link'),
                                'pub_date': news.get('pubDate', ''),
                                'description': news.get('description', '')[:100] + '...' if news.get('description') else ''
                            })
                    
                    raw_data.news_raw_data = raw_data.news_raw_data or {}
                    raw_data.news_raw_data.update({
                        "positive_news_analysis": {
                            "positive_ratio": positive_result.positive_ratio,
                            "hype_score": positive_result.hype_score,
                            "positive_keywords": positive_result.positive_keywords_found,
                            "hype_expressions": positive_result.hype_expressions,
                            "analyzed_news_links": positive_news_links
                        }
                    })
                    self.logger.info(f"✅ D008 호재뉴스 분석 완료: {result.positive_news_score}점, 뉴스 {len(positive_news_links)}건 링크 저장")
            except Exception as e:
                self.logger.warning(f"⚠️ D008 호재뉴스 분석 실패: {e}")
                result.positive_news_score = 0
            
            # 8. 기존 DINO 테스트 분석기들 호출 (실제 API 호출)
            self.logger.info("📊 기존 DINO 분석기들 실행중...")
            
            # D001 재무분석 - HTTP API 호출
            try:
                import requests
                response = requests.get(f"http://localhost:8000/dino-test/finance/{stock_code}", timeout=30)
                if response.status_code == 200:
                    finance_data = response.json()
                    result.finance_score = finance_data.get('total_score', 0)
                    raw_data.financial_raw_data = raw_data.financial_raw_data or {}
                    raw_data.financial_raw_data.update({
                        "finance_analysis": finance_data.get('raw_data', {}),
                        "score_details": finance_data.get('score_details', {}),
                        "total_score": finance_data.get('total_score', 0)
                    })
                    self.logger.info(f"✅ D001 재무 분석 완료: {result.finance_score}점")
                else:
                    self.logger.warning(f"⚠️ D001 재무 분석 API 실패: {response.status_code}")
                    result.finance_score = 0
            except Exception as e:
                self.logger.warning(f"⚠️ D001 재무 분석 호출 실패: {e}")
                result.finance_score = 0
            
            # D003 소재분석 - HTTP API 호출
            try:
                response = requests.get(f"http://localhost:8000/dino-test/material/{stock_code}", timeout=30)
                if response.status_code == 200:
                    material_data = response.json()
                    result.material_score = material_data.get('total_score', 0)
                    raw_data.material_raw_data = {
                        "material_analysis": material_data.get('raw_data', {}),
                        "score_details": material_data.get('score_details', {}),
                        "total_score": material_data.get('total_score', 0)
                    }
                    self.logger.info(f"✅ D003 소재 분석 완료: {result.material_score}점")
                else:
                    self.logger.warning(f"⚠️ D003 소재 분석 API 실패: {response.status_code}")
                    result.material_score = 0
            except Exception as e:
                self.logger.warning(f"⚠️ D003 소재 분석 호출 실패: {e}")
                result.material_score = 0
            
            # 기술적 분석 - HTTP API 호출
            try:
                response = requests.get(f"http://localhost:8000/dino-test/technical/{stock_code}", timeout=30)
                if response.status_code == 200:
                    technical_data = response.json()
                    result.technical_score = technical_data.get('total_score', 0)
                    raw_data.technical_raw_data = {
                        "technical_analysis": technical_data.get('raw_data', {}),
                        "score_details": technical_data.get('score_details', {}),
                        "total_score": technical_data.get('total_score', 0)
                    }
                    self.logger.info(f"✅ 기술적 분석 완료: {result.technical_score}점")
                else:
                    self.logger.warning(f"⚠️ 기술적 분석 API 실패: {response.status_code}")
                    result.technical_score = 0
            except Exception as e:
                self.logger.warning(f"⚠️ 기술적 분석 호출 실패: {e}")
                result.technical_score = 0
            
            # 가격 분석 - HTTP API 호출
            try:
                response = requests.get(f"http://localhost:8000/dino-test/price/{stock_code}", timeout=30)
                if response.status_code == 200:
                    price_data = response.json()
                    result.price_score = price_data.get('total_score', 0)
                    raw_data.price_raw_data = {
                        "price_analysis": price_data.get('raw_data', {}),
                        "score_details": price_data.get('score_details', {}),
                        "total_score": price_data.get('total_score', 0)
                    }
                    self.logger.info(f"✅ 가격 분석 완료: {result.price_score}점")
                else:
                    self.logger.warning(f"⚠️ 가격 분석 API 실패: {response.status_code}")
                    result.price_score = 0
            except Exception as e:
                self.logger.warning(f"⚠️ 가격 분석 호출 실패: {e}")
                result.price_score = 0
            
            # AI 모델 정보 수집 (실제 환경 반영)
            raw_data.ai_model_info = {
                "primary_provider": "anthropic_claude",
                "fallback_provider": "openai_gpt", 
                "model_versions": {
                    "claude": "haiku-3",
                    "openai": "gpt-3.5-turbo"
                },
                "real_analysis": True
            }
            
            self.logger.info(f"✅ 실제 분석기 호출 완료 - 총점: {result.total_score}점")
            
            # 11. 분석 상태 업데이트
            result.status = "COMPLETED"
            total = result.total_score
            
            self.logger.info(f"🎉 종합 DINO 분석 완료: {search_name} - 총점 {total}점")
            
            # 12. 데이터베이스 저장
            saved_id = self.save_to_database(result, raw_data)
            if saved_id:
                self.logger.info(f"💾 데이터베이스 저장 완료: ID {saved_id}")
                return result
            else:
                self.logger.error("❌ 데이터베이스 저장 실패")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ 종합 분석 실패 - {stock_code}: {e}")
            result.status = "FAILED"
            return None
    
    def save_to_database(self, result: ComprehensiveDinoResult, raw_data: RawDataCollection) -> Optional[int]:
        """분석 결과와 Raw 데이터를 데이터베이스에 저장"""
        
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    # 1. DINO 테스트 결과 저장
                    cursor.execute("""
                        INSERT INTO dino_test_results (
                            stock_code, company_name, user_id,
                            finance_score, technical_score, price_score, material_score,
                            event_score, theme_score, positive_news_score, interest_coverage_score,
                            analysis_date, status
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING id
                    """, (
                        result.stock_code, result.company_name, result.user_id,
                        result.finance_score, result.technical_score, result.price_score, result.material_score,
                        result.event_score, result.theme_score, result.positive_news_score, result.interest_coverage_score,
                        result.analysis_date, result.status
                    ))
                    
                    dino_result_id = cursor.fetchone()[0]
                    
                    # 2. Raw 데이터 저장
                    cursor.execute("""
                        INSERT INTO dino_test_raw_data (
                            dino_test_result_id,
                            news_raw_data, disclosure_raw_data, financial_raw_data,
                            technical_raw_data, price_raw_data, material_raw_data,
                            ai_theme_response, ai_news_response, ai_event_response, ai_positive_news_response,
                            analysis_environment, ai_model_info
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        dino_result_id,
                        json.dumps(raw_data.news_raw_data) if raw_data.news_raw_data else None,
                        json.dumps(raw_data.disclosure_raw_data) if raw_data.disclosure_raw_data else None,
                        json.dumps(raw_data.financial_raw_data) if raw_data.financial_raw_data else None,
                        json.dumps(raw_data.technical_raw_data) if raw_data.technical_raw_data else None,
                        json.dumps(raw_data.price_raw_data) if raw_data.price_raw_data else None,
                        json.dumps(raw_data.material_raw_data) if raw_data.material_raw_data else None,
                        raw_data.ai_theme_response,
                        raw_data.ai_news_response,
                        raw_data.ai_event_response,
                        raw_data.ai_positive_news_response,
                        json.dumps(raw_data.analysis_environment) if raw_data.analysis_environment else None,
                        json.dumps(raw_data.ai_model_info) if raw_data.ai_model_info else None
                    ))
                    
                    conn.commit()
                    self.logger.info(f"✅ 데이터베이스 저장 완료: dino_test_results.id = {dino_result_id}")
                    return dino_result_id
                    
        except psycopg2.IntegrityError as e:
            if "uk_dino_test_daily" in str(e):
                self.logger.warning(f"⚠️ 오늘 이미 분석된 종목: {result.stock_code}")
                return None
            else:
                self.logger.error(f"데이터베이스 무결성 오류: {e}")
                return None
        except Exception as e:
            self.logger.error(f"데이터베이스 저장 실패: {e}")
            return None
    
    def get_analysis_results(self, stock_code: str = None, analysis_date: date = None, 
                           limit: int = 100) -> List[Dict]:
        """분석 결과 조회"""
        
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    query = """
                        SELECT 
                            stock_code, company_name, 
                            finance_score, technical_score, price_score, material_score,
                            event_score, theme_score, positive_news_score, interest_coverage_score,
                            total_score, analysis_grade,
                            analysis_date, created_at, status
                        FROM dino_test_results 
                        WHERE 1=1
                    """
                    params = []
                    
                    if stock_code:
                        query += " AND stock_code = %s"
                        params.append(stock_code)
                    
                    if analysis_date:
                        query += " AND analysis_date = %s"
                        params.append(analysis_date)
                    
                    query += " ORDER BY created_at DESC LIMIT %s"
                    params.append(limit)
                    
                    cursor.execute(query, params)
                    
                    columns = [desc[0] for desc in cursor.description]
                    results = []
                    
                    for row in cursor.fetchall():
                        result = dict(zip(columns, row))
                        # 날짜 객체를 문자열로 변환
                        if result.get('analysis_date'):
                            result['analysis_date'] = result['analysis_date'].isoformat()
                        if result.get('created_at'):
                            result['created_at'] = result['created_at'].isoformat()
                        results.append(result)
                    
                    return results
                    
        except Exception as e:
            self.logger.error(f"분석 결과 조회 실패: {e}")
            return []

if __name__ == "__main__":
    # 테스트 코드
    logging.basicConfig(level=logging.INFO)
    
    analyzer = ComprehensiveDinoAnalyzer()
    
    # 삼성전자 종합 분석 테스트
    result = analyzer.run_comprehensive_analysis("005930", "삼성전자", force_rerun=True)
    
    if result:
        print(f"\n🎉 {result.company_name} ({result.stock_code}) 종합 DINO 분석 결과")
        print(f"📊 D001 재무분석: {result.finance_score}점")
        print(f"🎯 D002 테마분석: {result.theme_score}점")
        print(f"💰 D003 소재분석: {result.material_score}점")
        print(f"📅 D001 이벤트분석: {result.event_score}점")
        print(f"📈 D008 호재뉴스: {result.positive_news_score}점")
        print(f"🏦 D009 이자보상배율: {result.interest_coverage_score}점")
        print(f"🏆 총점: {result.total_score}점")
        print(f"📅 분석일: {result.analysis_date}")
        print(f"✅ 상태: {result.status}")
    else:
        print("❌ 분석 실패")