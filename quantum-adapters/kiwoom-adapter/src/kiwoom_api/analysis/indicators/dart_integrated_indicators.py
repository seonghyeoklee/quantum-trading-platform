"""
DART API 통합 재무지표 수집 모듈

기존 Kiwoom API 데이터에 DART API의 상세 재무정보를 통합하여
Google Sheets VLOOKUP 계산에 필요한 모든 데이터를 제공합니다.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio

# Handle both relative and absolute imports
try:
    from ...external.dart_client import DARTClient
    from .financial_indicators import FinancialDataCollector
    from ..core.vlookup_calculator import VLOOKUPCalculator
    from ..core.area_scorers import AreaScorer
except ImportError:
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from kiwoom_api.external.dart_client import DARTClient
    from kiwoom_api.analysis.indicators.financial_indicators import FinancialDataCollector
    from kiwoom_api.analysis.core.vlookup_calculator import VLOOKUPCalculator
    from kiwoom_api.analysis.core.area_scorers import AreaScorer


class DARTIntegratedDataCollector:
    """DART API 통합 데이터 수집기"""
    
    def __init__(self, dart_api_key: Optional[str] = None):
        """
        Args:
            dart_api_key: DART API 키 (환경변수로도 설정 가능)
        """
        self.kiwoom_collector = FinancialDataCollector()
        self.dart_client = DARTClient(api_key=dart_api_key)
        self.vlookup_calc = VLOOKUPCalculator()
        self.area_scorer = AreaScorer()
        
    async def get_comprehensive_financial_data(self, stock_code: str) -> Dict[str, Any]:
        """
        Kiwoom + DART 통합 재무 데이터 수집
        
        Args:
            stock_code: 6자리 종목코드
            
        Returns:
            통합된 재무 데이터
        """
        # 병렬로 데이터 수집
        tasks = [
            self.kiwoom_collector.get_stock_basic_info(stock_code),
            self.kiwoom_collector.get_historical_data(stock_code),
            self._get_dart_financial_data(stock_code),
            self._get_dart_disclosure_analysis(stock_code)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 통합
        kiwoom_basic = results[0] if not isinstance(results[0], Exception) else {}
        kiwoom_historical = results[1] if not isinstance(results[1], Exception) else {}
        dart_financial = results[2] if not isinstance(results[2], Exception) else {}
        dart_disclosure = results[3] if not isinstance(results[3], Exception) else {}
        
        # 데이터 병합
        integrated_data = {
            **kiwoom_basic,
            **kiwoom_historical,
            **dart_financial,
            **dart_disclosure,
            "data_sources": {
                "kiwoom": ["basic_info", "historical_prices", "trading_volume"],
                "dart": ["financial_statements", "disclosures", "dividend_info"],
                "calculated": ["technical_indicators", "valuation_scores"]
            }
        }
        
        # VLOOKUP 계산에 필요한 형식으로 변환
        return self._transform_for_vlookup(integrated_data)
    
    async def _get_dart_financial_data(self, stock_code: str) -> Dict[str, Any]:
        """
        DART에서 재무제표 데이터 수집
        
        Args:
            stock_code: 종목코드
            
        Returns:
            재무 데이터
        """
        try:
            current_year = datetime.now().year
            
            # 최근 분기 보고서 조회
            financial_data = await self.dart_client.get_financial_statement(
                stock_code, 
                current_year, 
                "11013"  # 1분기 보고서
            )
            
            # 전년도 데이터도 조회
            previous_year_data = await self.dart_client.get_financial_statement(
                stock_code,
                current_year - 1,
                "11011"  # 사업보고서
            )
            
            # 배당 정보 조회
            dividend_info = await self.dart_client.get_dividend_info(
                stock_code,
                current_year - 1
            )
            
            return {
                "dart_financial": {
                    # 재무 영역 데이터
                    "retention_ratio": financial_data.get("retention_ratio", 0),
                    "debt_ratio": financial_data.get("debt_ratio", 0),
                    "interest_coverage_ratio": financial_data.get("interest_coverage_ratio", 0),
                    "operating_margin": financial_data.get("operating_margin", 0),
                    "roe": financial_data.get("roe", 0),
                    "roa": financial_data.get("roa", 0),
                    
                    # 전년 대비 데이터
                    "revenue_current": financial_data.get("revenue_current", 0),
                    "revenue_previous": previous_year_data.get("revenue_current", 0),
                    "operating_profit_current": financial_data.get("operating_profit_current", 0),
                    "operating_profit_previous": previous_year_data.get("operating_profit_current", 0),
                    
                    # 배당 정보
                    "dividend_yield": dividend_info.get("dividend_yield", 0),
                    "dividend_per_share": dividend_info.get("dividend_per_share", 0)
                }
            }
        except Exception as e:
            print(f"DART 재무 데이터 수집 실패: {e}")
            return {"dart_financial": {}}
    
    async def _get_dart_disclosure_analysis(self, stock_code: str) -> Dict[str, Any]:
        """
        DART 공시 분석
        
        Args:
            stock_code: 종목코드
            
        Returns:
            공시 분석 결과
        """
        try:
            # 최근 3개월 공시 조회
            disclosures = await self.dart_client.get_disclosures(stock_code)
            
            # 어닝서프라이즈 체크
            earnings_surprise = await self.dart_client.check_earnings_surprise(stock_code)
            
            # 공시 분석
            disclosure_analysis = {
                "total_disclosures": len(disclosures),
                "unfaithful_disclosures": 0,
                "positive_disclosures": 0,
                "negative_disclosures": 0,
                "has_earnings_surprise": earnings_surprise.get("has_surprise", False)
            }
            
            # 공시 유형별 카운트
            for disclosure in disclosures:
                if disclosure["type"] == "불성실공시":
                    disclosure_analysis["unfaithful_disclosures"] += 1
                elif disclosure["sentiment"] == "긍정":
                    disclosure_analysis["positive_disclosures"] += 1
                elif disclosure["sentiment"] == "부정":
                    disclosure_analysis["negative_disclosures"] += 1
            
            # 최근 주요 공시
            recent_major_disclosures = [
                d for d in disclosures[:10]
                if d["type"] in ["실적공시", "경영사항", "배당공시"]
            ]
            
            return {
                "dart_disclosure": disclosure_analysis,
                "recent_disclosures": recent_major_disclosures[:5]
            }
            
        except Exception as e:
            print(f"DART 공시 분석 실패: {e}")
            return {"dart_disclosure": {}, "recent_disclosures": []}
    
    def _transform_for_vlookup(self, integrated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        통합 데이터를 VLOOKUP 계산 형식으로 변환
        
        Args:
            integrated_data: 통합된 원시 데이터
            
        Returns:
            VLOOKUP 계산용 데이터
        """
        dart_financial = integrated_data.get("dart_financial", {})
        dart_disclosure = integrated_data.get("dart_disclosure", {})
        
        # Google Sheets D열 데이터 매핑
        vlookup_data = {
            # D23-D28: 재무 데이터 (DART에서 정확한 값 제공)
            "D23": dart_financial.get("revenue_previous", 0),  # 전년 매출
            "D24": dart_financial.get("revenue_current", 0),   # 당년 매출
            "D25": dart_financial.get("operating_profit_current", 0),  # 당년 영업이익
            "D26": dart_financial.get("operating_margin", 0),  # 영업이익률
            "D27": dart_financial.get("retention_ratio", 0),   # 유보율 (DART 정확값)
            "D28": dart_financial.get("debt_ratio", 0),        # 부채비율 (DART 정확값)
            
            # D30-D32: 기술 데이터 (Kiwoom 계산)
            "D30": integrated_data.get("obv_condition", False),  # OBV 조건
            "D31": integrated_data.get("investor_sentiment", 50),  # 투자심리도
            "D32": integrated_data.get("rsi_14", 50),  # RSI
            
            # D35: 가격 데이터
            "D35": integrated_data.get("position_vs_52week", 0),  # 52주 대비 위치
            
            # D38-D46: 재료 데이터 (DART + 수동입력 필요)
            "D38": dart_disclosure.get("has_earnings_surprise", False),  # 호재 임박
            "D39": False,  # 주도 테마 (수동 입력 필요)
            "D40": integrated_data.get("institutional_holding_change", 0),  # 기관 수급
            "D41": dart_financial.get("dividend_yield", 0),  # 배당수익률 (DART)
            "D42": dart_disclosure.get("has_earnings_surprise", False),  # 어닝서프라이즈
            "D43": dart_disclosure.get("unfaithful_disclosures", 0) > 0,  # 불성실 공시
            "D44": dart_disclosure.get("negative_disclosures", 0) > 2,  # 악재뉴스
            "D45": dart_disclosure.get("positive_disclosures", 0) > 5,  # 호재뉴스 도배
            "D46": dart_financial.get("interest_coverage_ratio", 999),  # 이자보상배율 (DART)
            
            # 메타 정보
            "stock_code": integrated_data.get("stock_code", stock_code),
            "stock_name": integrated_data.get("stock_name", ""),
            "data_timestamp": datetime.now().isoformat(),
            "data_sources": integrated_data.get("data_sources", {})
        }
        
        return vlookup_data
    
    async def calculate_scores_with_dart(self, stock_code: str) -> Dict[str, Any]:
        """
        DART 데이터를 포함한 완전한 점수 계산
        
        Args:
            stock_code: 종목코드
            
        Returns:
            4개 영역 점수 및 종합 분석
        """
        # 통합 데이터 수집
        vlookup_data = await self.get_comprehensive_financial_data(stock_code)
        
        # 개별 점수 계산
        scores = {}
        
        # 재무 영역 점수 계산
        scores["sales"] = self.vlookup_calc.calculate_sales_score(
            vlookup_data["D24"], vlookup_data["D23"]
        )
        scores["operating_profit"] = self.vlookup_calc.calculate_operating_profit_score(
            vlookup_data["D25"], vlookup_data.get("D24_previous", 0)
        )
        scores["operating_margin"] = self.vlookup_calc.calculate_operating_margin_score(
            vlookup_data["D26"]
        )
        scores["retention_ratio"] = self.vlookup_calc.calculate_retention_ratio_score(
            vlookup_data["D27"]
        )
        scores["debt_ratio"] = self.vlookup_calc.calculate_debt_ratio_score(
            vlookup_data["D28"]
        )
        
        # 기술 영역 점수 계산
        scores["obv"] = self.vlookup_calc.calculate_obv_score(vlookup_data["D30"])
        scores["sentiment"] = self.vlookup_calc.calculate_sentiment_score(vlookup_data["D31"])
        scores["rsi"] = self.vlookup_calc.calculate_rsi_score(vlookup_data["D32"])
        
        # 가격 영역 점수 계산
        scores["price_position"] = self.vlookup_calc.calculate_price_position_score(
            vlookup_data["D35"]
        )
        
        # 재료 영역 점수 계산
        scores["event"] = self.vlookup_calc.calculate_event_score(vlookup_data["D38"])
        scores["theme"] = self.vlookup_calc.calculate_theme_score(vlookup_data["D39"])
        scores["institutional"] = self.vlookup_calc.calculate_institutional_score(
            vlookup_data["D40"]
        )
        scores["dividend"] = self.vlookup_calc.calculate_dividend_score(vlookup_data["D41"])
        scores["earnings_surprise"] = self.vlookup_calc.calculate_earnings_surprise_score(
            vlookup_data["D42"]
        )
        scores["unfaithful_disclosure"] = self.vlookup_calc.calculate_unfaithful_disclosure_score(
            vlookup_data["D43"]
        )
        scores["bad_news"] = self.vlookup_calc.calculate_bad_news_score(vlookup_data["D44"])
        scores["good_news_spam"] = self.vlookup_calc.calculate_good_news_spam_score(
            vlookup_data["D45"]
        )
        scores["interest_coverage"] = self.vlookup_calc.calculate_interest_coverage_score(
            vlookup_data["D46"]
        )
        
        # 영역별 종합 점수 계산
        area_scores = {
            "financial": self.area_scorer.calculate_financial_score(
                scores["sales"],
                scores["operating_profit"],
                scores["operating_margin"],
                scores["retention_ratio"],
                scores["debt_ratio"]
            ),
            "technical": self.area_scorer.calculate_technical_score(
                scores["obv"],
                scores["sentiment"],
                scores["rsi"]
            ),
            "price": self.area_scorer.calculate_price_score(
                scores["price_position"]
            ),
            "material": self.area_scorer.calculate_material_score(
                scores["event"],
                scores["theme"],
                scores["institutional"],
                scores["dividend"],
                scores["earnings_surprise"],
                scores["unfaithful_disclosure"],
                scores["bad_news"],
                scores["good_news_spam"],
                scores["interest_coverage"]
            )
        }
        
        # 종합 결과 반환
        return {
            "stock_code": stock_code,
            "stock_name": vlookup_data.get("stock_name", ""),
            "individual_scores": scores,
            "area_scores": area_scores,
            "raw_data": vlookup_data,
            "data_quality": {
                "dart_data_available": bool(vlookup_data.get("D27")),  # 유보율이 있으면 DART 성공
                "kiwoom_data_available": bool(vlookup_data.get("stock_name")),
                "calculation_timestamp": datetime.now().isoformat()
            }
        }


# 사용 예시
async def example_dart_integration():
    """DART 통합 데이터 수집 예시"""
    
    # DART_API_KEY 환경변수 설정 필요
    collector = DARTIntegratedDataCollector()
    
    # 삼성전자 완전 분석
    result = await collector.calculate_scores_with_dart("005930")
    
    print("=== DART 통합 분석 결과 ===")
    print(f"종목: {result['stock_name']} ({result['stock_code']})")
    print("\n영역별 점수:")
    for area_name, area_data in result['area_scores'].items():
        print(f"  {area_data['area']}: {area_data['total_score']}/5점")
    
    print("\n데이터 품질:")
    print(f"  DART 데이터: {'✅' if result['data_quality']['dart_data_available'] else '❌'}")
    print(f"  Kiwoom 데이터: {'✅' if result['data_quality']['kiwoom_data_available'] else '❌'}")


if __name__ == "__main__":
    asyncio.run(example_dart_integration())