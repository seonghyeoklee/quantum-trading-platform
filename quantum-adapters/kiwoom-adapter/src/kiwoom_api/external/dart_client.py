"""
DART API 클라이언트 모듈

DART(Data Analysis, Retrieval and Transfer System) API를 통해
재무제표, 공시정보 등을 수집하는 클라이언트입니다.
"""

import httpx
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import os
from pathlib import Path

# Handle both relative and absolute imports for different execution contexts
try:
    from ..config.settings import settings
except ImportError:
    import sys
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from kiwoom_api.config.settings import settings

class DARTReportType(Enum):
    """DART 보고서 타입"""
    # 정기보고서
    ANNUAL = "11011"  # 사업보고서
    HALF_YEAR = "11012"  # 반기보고서
    QUARTER = "11013"  # 분기보고서
    QUARTER_1 = "11014"  # 1분기보고서
    QUARTER_3 = "11015"  # 3분기보고서
    
    # 주요사항보고서
    MAJOR_DECISION = "B001"  # 주요경영사항
    INVESTMENT = "B002"  # 투자판단관련
    
    # 실적공시
    PROVISIONAL = "D001"  # 잠정실적
    FAIR_DISCLOSURE = "D002"  # 공정공시
    EARNINGS_FORECAST = "D003"  # 실적예측

class DARTFinancialAccount(Enum):
    """주요 재무계정 코드"""
    # 재무상태표
    TOTAL_ASSETS = "ifrs-full_Assets"  # 자산총계
    TOTAL_EQUITY = "ifrs-full_Equity"  # 자본총계
    TOTAL_LIABILITIES = "ifrs-full_Liabilities"  # 부채총계
    RETAINED_EARNINGS = "ifrs-full_RetainedEarnings"  # 이익잉여금
    CAPITAL_STOCK = "ifrs-full_IssuedCapital"  # 자본금
    
    # 손익계산서
    REVENUE = "ifrs-full_Revenue"  # 매출액
    OPERATING_PROFIT = "dart_OperatingIncomeLoss"  # 영업이익
    NET_INCOME = "ifrs-full_ProfitLoss"  # 당기순이익
    INTEREST_EXPENSE = "ifrs-full_InterestExpense"  # 이자비용
    
    # 현금흐름표
    OPERATING_CASH_FLOW = "ifrs-full_CashFlowsFromUsedInOperatingActivities"  # 영업현금흐름


class DARTClient:
    """DART API 클라이언트"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: DART API 인증키 (환경변수 DART_API_KEY로도 설정 가능)
        """
        self.api_key = api_key or settings.DART_API_KEY or os.getenv("DART_API_KEY")
        if not self.api_key:
            raise ValueError("DART API key is required. Set DART_API_KEY environment variable or pass api_key parameter.")
        
        self.base_url = "https://opendart.fss.or.kr/api"
        self.timeout = httpx.Timeout(30.0)
        
    async def get_corp_code(self, stock_code: str) -> Optional[str]:
        """
        종목코드로 기업코드 조회
        
        Args:
            stock_code: 6자리 종목코드 (예: "005930")
            
        Returns:
            8자리 기업코드 (예: "00126380")
        """
        # 기업코드 맵핑 테이블 (실제로는 DART에서 제공하는 고유번호 파일을 다운로드해야 함)
        # 여기서는 주요 기업만 하드코딩
        corp_code_map = {
            "005930": "00126380",  # 삼성전자
            "000660": "00164779",  # SK하이닉스
            "005380": "00126186",  # 현대차
            "035420": "00159320",  # NAVER
            "000270": "00139649",  # 기아
            "051910": "00231848",  # LG화학
            "006400": "00127219",  # 삼성SDI
            "035720": "00160980",  # 카카오
            "028260": "00148064",  # 삼성물산
            "105560": "00547709",  # KB금융
        }
        
        return corp_code_map.get(stock_code)
    
    async def get_financial_statement(self, 
                                     stock_code: str,
                                     year: int,
                                     quarter: str = "11013") -> Dict[str, Any]:
        """
        재무제표 조회
        
        Args:
            stock_code: 종목코드
            year: 조회년도
            quarter: 보고서 타입 (11011=사업보고서, 11013=1분기, 11012=반기, 11014=3분기)
            
        Returns:
            재무제표 데이터
        """
        corp_code = await self.get_corp_code(stock_code)
        if not corp_code:
            return {}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # 단일회사 재무정보 API
            response = await client.get(
                f"{self.base_url}/fnlttSinglAcnt.json",
                params={
                    "crtfc_key": self.api_key,
                    "corp_code": corp_code,
                    "bsns_year": str(year),
                    "reprt_code": quarter
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "000":
                    return self._parse_financial_data(data.get("list", []))
            
            return {}
    
    def _parse_financial_data(self, raw_data: List[Dict]) -> Dict[str, Any]:
        """
        재무데이터 파싱 및 주요 지표 계산
        
        Args:
            raw_data: DART API 원시 데이터
            
        Returns:
            계산된 재무 지표
        """
        financial_data = {}
        
        # 계정과목별 데이터 추출
        for item in raw_data:
            account_nm = item.get("account_nm", "")
            thstrm_amount = item.get("thstrm_amount", "0")  # 당기
            frmtrm_amount = item.get("frmtrm_amount", "0")  # 전기
            
            # 숫자 변환 (천원 단위)
            try:
                current = float(thstrm_amount.replace(",", "")) if thstrm_amount else 0
                previous = float(frmtrm_amount.replace(",", "")) if frmtrm_amount else 0
            except:
                current = previous = 0
            
            # 주요 계정 매핑
            if "매출액" in account_nm or "수익" in account_nm:
                financial_data["revenue_current"] = current
                financial_data["revenue_previous"] = previous
            elif "영업이익" in account_nm or "영업손익" in account_nm:
                financial_data["operating_profit_current"] = current
                financial_data["operating_profit_previous"] = previous
            elif "당기순이익" in account_nm:
                financial_data["net_income"] = current
            elif "이익잉여금" in account_nm or "이익잉여" in account_nm:
                financial_data["retained_earnings"] = current
            elif "자본금" in account_nm:
                financial_data["capital_stock"] = current
            elif "자산총계" in account_nm:
                financial_data["total_assets"] = current
            elif "부채총계" in account_nm:
                financial_data["total_liabilities"] = current
            elif "자본총계" in account_nm:
                financial_data["total_equity"] = current
            elif "이자비용" in account_nm:
                financial_data["interest_expense"] = current
        
        # 유보율 계산
        if financial_data.get("retained_earnings") and financial_data.get("capital_stock"):
            financial_data["retention_ratio"] = (
                financial_data["retained_earnings"] / financial_data["capital_stock"] * 100
            )
        
        # 부채비율 계산
        if financial_data.get("total_liabilities") and financial_data.get("total_equity"):
            financial_data["debt_ratio"] = (
                financial_data["total_liabilities"] / financial_data["total_equity"] * 100
            )
        
        # 이자보상배율 계산
        if financial_data.get("operating_profit_current") and financial_data.get("interest_expense"):
            financial_data["interest_coverage_ratio"] = (
                financial_data["operating_profit_current"] / financial_data["interest_expense"]
            )
        
        # 영업이익률 계산
        if financial_data.get("operating_profit_current") and financial_data.get("revenue_current"):
            financial_data["operating_margin"] = (
                financial_data["operating_profit_current"] / financial_data["revenue_current"] * 100
            )
        
        # ROE 계산
        if financial_data.get("net_income") and financial_data.get("total_equity"):
            financial_data["roe"] = (
                financial_data["net_income"] / financial_data["total_equity"] * 100
            )
        
        # ROA 계산
        if financial_data.get("net_income") and financial_data.get("total_assets"):
            financial_data["roa"] = (
                financial_data["net_income"] / financial_data["total_assets"] * 100
            )
        
        return financial_data
    
    async def get_disclosures(self, 
                            stock_code: str,
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        공시 정보 조회
        
        Args:
            stock_code: 종목코드
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
            
        Returns:
            공시 리스트
        """
        corp_code = await self.get_corp_code(stock_code)
        if not corp_code:
            return []
        
        # 기본값: 최근 3개월
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/list.json",
                params={
                    "crtfc_key": self.api_key,
                    "corp_code": corp_code,
                    "bgn_de": start_date,
                    "end_de": end_date,
                    "page_count": "100"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "000":
                    return self._analyze_disclosures(data.get("list", []))
            
            return []
    
    def _analyze_disclosures(self, disclosures: List[Dict]) -> List[Dict[str, Any]]:
        """
        공시 분석 및 분류
        
        Args:
            disclosures: 공시 리스트
            
        Returns:
            분석된 공시 정보
        """
        analyzed = []
        
        for disclosure in disclosures:
            report_nm = disclosure.get("report_nm", "")
            rcept_dt = disclosure.get("rcept_dt", "")
            
            # 공시 유형 분류
            disclosure_type = "기타"
            sentiment = "중립"
            
            # 불성실 공시 체크
            if "정정" in report_nm or "지연" in report_nm or "불성실" in report_nm:
                disclosure_type = "불성실공시"
                sentiment = "부정"
            
            # 실적 공시 체크
            elif "실적" in report_nm or "매출" in report_nm:
                disclosure_type = "실적공시"
                if "증가" in report_nm or "호조" in report_nm or "개선" in report_nm:
                    sentiment = "긍정"
                elif "감소" in report_nm or "부진" in report_nm or "악화" in report_nm:
                    sentiment = "부정"
            
            # 배당 공시 체크
            elif "배당" in report_nm:
                disclosure_type = "배당공시"
                sentiment = "긍정"
            
            # 주요 경영사항
            elif "계약" in report_nm or "투자" in report_nm or "인수" in report_nm:
                disclosure_type = "경영사항"
                if "체결" in report_nm or "확정" in report_nm:
                    sentiment = "긍정"
                elif "해지" in report_nm or "취소" in report_nm:
                    sentiment = "부정"
            
            analyzed.append({
                "date": rcept_dt,
                "title": report_nm,
                "type": disclosure_type,
                "sentiment": sentiment,
                "rcept_no": disclosure.get("rcept_no", ""),
                "corp_name": disclosure.get("corp_name", "")
            })
        
        return analyzed
    
    async def get_dividend_info(self, stock_code: str, year: int) -> Dict[str, Any]:
        """
        배당 정보 조회
        
        Args:
            stock_code: 종목코드
            year: 조회년도
            
        Returns:
            배당 정보
        """
        corp_code = await self.get_corp_code(stock_code)
        if not corp_code:
            return {}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/alotMatter.json",
                params={
                    "crtfc_key": self.api_key,
                    "corp_code": corp_code,
                    "bsns_year": str(year),
                    "reprt_code": "11011"  # 사업보고서
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "000" and data.get("list"):
                    dividend_data = data["list"][0]
                    return {
                        "dividend_rate": float(dividend_data.get("thstrm_dividend_rate", "0")),
                        "dividend_per_share": float(dividend_data.get("thstrm", "0")),
                        "dividend_yield": self._calculate_dividend_yield(
                            dividend_data.get("thstrm", "0"),
                            stock_code
                        )
                    }
            
            return {}
    
    def _calculate_dividend_yield(self, dividend_per_share: str, stock_code: str) -> float:
        """
        배당수익률 계산 (실제로는 현재 주가가 필요함)
        
        Args:
            dividend_per_share: 주당 배당금
            stock_code: 종목코드
            
        Returns:
            배당수익률 (%)
        """
        # TODO: 현재 주가를 가져와서 계산
        # 임시로 2% 반환
        return 2.0
    
    async def check_earnings_surprise(self, 
                                     stock_code: str,
                                     threshold: float = 10.0) -> Dict[str, Any]:
        """
        어닝서프라이즈 체크
        
        Args:
            stock_code: 종목코드
            threshold: 서프라이즈 기준 (%, 기본 10%)
            
        Returns:
            어닝서프라이즈 정보
        """
        # 최근 실적 공시 조회
        disclosures = await self.get_disclosures(
            stock_code,
            start_date=(datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        )
        
        earnings_disclosures = [
            d for d in disclosures 
            if d["type"] == "실적공시" and "잠정" in d["title"]
        ]
        
        if earnings_disclosures:
            # 실제로는 공시 상세 내용을 파싱해서 전년 대비 증감률을 계산해야 함
            # 여기서는 간단히 시뮬레이션
            latest = earnings_disclosures[0]
            
            # 긍정적 키워드 체크
            if any(word in latest["title"] for word in ["증가", "호조", "개선", "흑자전환"]):
                return {
                    "has_surprise": True,
                    "type": "positive",
                    "date": latest["date"],
                    "title": latest["title"],
                    "estimated_change": 15.0  # 임시값
                }
        
        return {
            "has_surprise": False,
            "type": "none",
            "estimated_change": 0.0
        }


# 사용 예시
async def example_usage():
    """DART API 사용 예시"""
    
    # 환경변수에 DART_API_KEY 설정 필요
    client = DARTClient()
    
    # 삼성전자 재무정보 조회
    financial_data = await client.get_financial_statement("005930", 2024, "11013")
    print(f"유보율: {financial_data.get('retention_ratio', 0):.2f}%")
    print(f"부채비율: {financial_data.get('debt_ratio', 0):.2f}%")
    print(f"이자보상배율: {financial_data.get('interest_coverage_ratio', 0):.2f}")
    
    # 공시 정보 조회
    disclosures = await client.get_disclosures("005930")
    for disclosure in disclosures[:5]:
        print(f"{disclosure['date']}: {disclosure['title']} ({disclosure['sentiment']})")
    
    # 어닝서프라이즈 체크
    surprise = await client.check_earnings_surprise("005930")
    if surprise["has_surprise"]:
        print(f"어닝서프라이즈 발생: {surprise['title']}")
    
    # 배당 정보 조회
    dividend = await client.get_dividend_info("005930", 2023)
    print(f"배당수익률: {dividend.get('dividend_yield', 0):.2f}%")


if __name__ == "__main__":
    asyncio.run(example_usage())