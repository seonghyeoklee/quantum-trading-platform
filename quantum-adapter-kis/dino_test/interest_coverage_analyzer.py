#!/usr/bin/env python3
"""
D009: 이자보상배율 분석기

재무제표 데이터를 분석하여 이자보상배율을 계산합니다.
- 이자보상배율 = EBIT / 이자비용
- 이자보상배율 < 1.0: -1점 (위험)
- 이자보상배율 ≥ 1.0: 0점 (정상)

EBIT(Earnings Before Interest and Taxes): 세전영업이익
이자비용: 연간 이자 지급액
"""

import logging
import requests
import os
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class InterestCoverageResult:
    """이자보상배율 분석 결과"""
    company_name: str
    stock_code: str
    ebit: Optional[float]                    # EBIT (세전영업이익, 억원)
    interest_expense: Optional[float]        # 이자비용 (억원)
    interest_coverage_ratio: Optional[float] # 이자보상배율
    coverage_score: int                      # 점수 (-1 또는 0)
    analysis_summary: str                    # 분석 요약
    fiscal_year: Optional[str]               # 회계연도
    data_quality: str                        # 데이터 품질 (GOOD, FAIR, POOR)

class InterestCoverageAnalyzer:
    """이자보상배율 분석기"""
    
    def __init__(self, external_api_base_url: str = "http://external-api.quantum-trading.com:8001"):
        self.base_url = external_api_base_url
        self.logger = logging.getLogger(__name__)
        
        # KIS API 기본 URL (내부적으로 사용)
        self.kis_base_url = "http://localhost:8000"
    
    def fetch_financial_data(self, stock_code: str) -> Optional[Dict]:
        """KIS API를 통해 재무제표 데이터 수집"""
        try:
            # KIS API의 재무제표 데이터 엔드포인트 호출
            url = f"{self.kis_base_url}/dino-test/finance/{stock_code}"
            
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.logger.info(f"재무 데이터 수집 완료: {stock_code}")
                    return data
                else:
                    self.logger.warning(f"재무 데이터 수집 실패: {stock_code} - {data.get('message', 'Unknown error')}")
                    return None
            else:
                self.logger.error(f"재무 데이터 API 호출 실패: {stock_code} - HTTP {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"재무 데이터 수집 오류 - {stock_code}: {e}")
            return None
    
    def extract_ebit_and_interest(self, financial_data: Dict) -> Tuple[Optional[float], Optional[float], str, str]:
        """재무 데이터에서 EBIT과 이자비용 추출"""
        try:
            ebit = None
            interest_expense = None
            fiscal_year = "Unknown"
            data_quality = "POOR"
            
            # 재무 데이터가 있는지 확인
            if not financial_data or not financial_data.get("success"):
                return None, None, fiscal_year, "NO_DATA"
            
            # 재무제표 원시 데이터 확인
            raw_data = financial_data.get("raw_financial_data", {})
            financial_ratios = financial_data.get("financial_ratios", {})
            
            # 1. 영업이익 (Operating Income) 찾기 - EBIT 대용
            # KIS API에서 제공하는 영업이익을 EBIT로 사용
            operating_income_fields = [
                "operating_income", "영업이익", "영업수익", 
                "ebit", "EBIT", "세전영업이익"
            ]
            
            for field in operating_income_fields:
                if field in raw_data and raw_data[field] is not None:
                    try:
                        ebit = float(raw_data[field])
                        data_quality = "GOOD"
                        break
                    except (ValueError, TypeError):
                        continue
            
            # 2. 이자비용 찾기
            interest_fields = [
                "interest_expense", "이자비용", "이자지급액",
                "금융비용", "financial_cost", "borrowing_cost"
            ]
            
            for field in interest_fields:
                if field in raw_data and raw_data[field] is not None:
                    try:
                        interest_expense = float(raw_data[field])
                        if data_quality != "GOOD":
                            data_quality = "FAIR"
                        break
                    except (ValueError, TypeError):
                        continue
            
            # 3. 회계연도 정보
            fiscal_year = raw_data.get("fiscal_year", raw_data.get("year", "2024"))
            
            # 4. 데이터 품질 최종 판정
            if ebit is not None and interest_expense is not None:
                data_quality = "GOOD"
            elif ebit is not None or interest_expense is not None:
                data_quality = "FAIR"
            else:
                data_quality = "POOR"
            
            self.logger.info(f"재무 데이터 추출 완료 - EBIT: {ebit}, 이자비용: {interest_expense}, 품질: {data_quality}")
            
            return ebit, interest_expense, str(fiscal_year), data_quality
            
        except Exception as e:
            self.logger.error(f"재무 데이터 추출 오류: {e}")
            return None, None, "Unknown", "ERROR"
    
    def calculate_interest_coverage_ratio(self, ebit: Optional[float], interest_expense: Optional[float]) -> Tuple[Optional[float], int, str]:
        """이자보상배율 계산 및 점수 산출"""
        try:
            if ebit is None or interest_expense is None:
                return None, 0, "재무 데이터 부족으로 계산 불가"
            
            # 이자비용이 0이거나 음수인 경우 (부채가 없는 경우)
            if interest_expense <= 0:
                return float('inf'), 0, "이자비용 없음 (무차입 경영)"
            
            # 이자보상배율 계산
            coverage_ratio = ebit / interest_expense
            
            # 점수 계산
            if coverage_ratio < 1.0:
                score = -1
                status = f"위험 (이자보상배율: {coverage_ratio:.2f})"
            else:
                score = 0
                status = f"정상 (이자보상배율: {coverage_ratio:.2f})"
            
            self.logger.info(f"이자보상배율 계산 완료: {coverage_ratio:.2f}, 점수: {score}")
            
            return coverage_ratio, score, status
            
        except Exception as e:
            self.logger.error(f"이자보상배율 계산 오류: {e}")
            return None, 0, f"계산 오류: {str(e)}"
    
    def analyze_interest_coverage(self, stock_code: str, company_name: str = None) -> Optional[InterestCoverageResult]:
        """D009: 이자보상배율 분석"""
        
        search_keyword = company_name if company_name else stock_code
        
        self.logger.info(f"=== {search_keyword} ({stock_code}) D009 이자보상배율 분석 시작 ===")
        
        try:
            # 1. 재무제표 데이터 수집
            financial_data = self.fetch_financial_data(stock_code)
            
            if not financial_data:
                self.logger.warning(f"재무 데이터를 가져올 수 없음: {stock_code}")
                return InterestCoverageResult(
                    company_name=search_keyword,
                    stock_code=stock_code,
                    ebit=None,
                    interest_expense=None,
                    interest_coverage_ratio=None,
                    coverage_score=0,
                    analysis_summary="재무 데이터 수집 실패",
                    fiscal_year=None,
                    data_quality="NO_DATA"
                )
            
            # 2. EBIT과 이자비용 추출
            ebit, interest_expense, fiscal_year, data_quality = self.extract_ebit_and_interest(financial_data)
            
            # 3. 이자보상배율 계산
            coverage_ratio, score, status = self.calculate_interest_coverage_ratio(ebit, interest_expense)
            
            # 4. 결과 생성
            result = InterestCoverageResult(
                company_name=search_keyword,
                stock_code=stock_code,
                ebit=ebit,
                interest_expense=interest_expense,
                interest_coverage_ratio=coverage_ratio,
                coverage_score=score,
                analysis_summary=status,
                fiscal_year=fiscal_year,
                data_quality=data_quality
            )
            
            self.logger.info(f"D009 이자보상배율 분석 완료 - {search_keyword}: {status}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"D009 이자보상배율 분석 실패 - {stock_code}: {e}")
            return None

if __name__ == "__main__":
    # 테스트 코드
    logging.basicConfig(level=logging.INFO)
    
    analyzer = InterestCoverageAnalyzer()
    result = analyzer.analyze_interest_coverage("005930", "삼성전자")
    
    if result:
        print(f"\n💰 {result.company_name} ({result.stock_code}) D009 이자보상배율 분석 결과")
        print(f"회계연도: {result.fiscal_year}")
        print(f"EBIT: {result.ebit if result.ebit else 'N/A'}억원")
        print(f"이자비용: {result.interest_expense if result.interest_expense else 'N/A'}억원")
        
        if result.interest_coverage_ratio is not None:
            if result.interest_coverage_ratio == float('inf'):
                print(f"이자보상배율: 무한대 (무차입)")
            else:
                print(f"이자보상배율: {result.interest_coverage_ratio:.2f}")
        else:
            print(f"이자보상배율: 계산 불가")
        
        if result.coverage_score == -1:
            impact_text = "🔴 위험 (-1점)"
        else:
            impact_text = "🟢 정상 (0점)"
        
        print(f"D009 점수: {impact_text}")
        print(f"데이터 품질: {result.data_quality}")
        print(f"분석 요약: {result.analysis_summary}")
    else:
        print("❌ 이자보상배율 분석 결과를 가져올 수 없습니다.")