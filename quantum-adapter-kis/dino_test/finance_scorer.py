"""
디노테스트 재무 영역 점수 계산기

재무 영역 5개 지표를 평가하여 0~5점 범위에서 점수를 산출합니다:
1. 매출액 증감 (±1점)
2. 영업이익 상태 (±2점) 
3. 영업이익률 (+1점)
4. 유보율 (±1점)
5. 부채비율 (±1점)

최종 점수: MAX(0, MIN(5, 2 + SUM(개별지표점수들)))
"""

import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass
from decimal import Decimal

logger = logging.getLogger(__name__)

@dataclass
class FinanceData:
    """재무 데이터 구조"""
    # 손익계산서 데이터
    current_revenue: Optional[Decimal] = None      # 당년 매출액
    previous_revenue: Optional[Decimal] = None     # 전년 매출액
    current_operating_profit: Optional[Decimal] = None   # 당년 영업이익
    previous_operating_profit: Optional[Decimal] = None  # 전년 영업이익
    
    # 대차대조표 데이터
    total_debt: Optional[Decimal] = None           # 총부채
    total_equity: Optional[Decimal] = None         # 자기자본
    retained_earnings: Optional[Decimal] = None    # 이익잉여금
    capital_stock: Optional[Decimal] = None        # 자본금
    
    # 계산된 비율 (API에서 직접 제공될 수도 있음)
    operating_margin: Optional[Decimal] = None     # 영업이익률
    retention_rate: Optional[Decimal] = None       # 유보율 (KIS API에서 직접 제공)
    
    # 데이터 기준 연월 (YYYYMM 형식)
    current_period: Optional[str] = None           # 당년 기준 연월
    previous_period: Optional[str] = None          # 전년 기준 연월

@dataclass
class FinanceScoreDetail:
    """재무 점수 상세 내역"""
    revenue_growth_score: int = 0                  # 매출액 증감 점수
    operating_profit_score: int = 0                # 영업이익 상태 점수
    operating_margin_score: int = 0                # 영업이익률 점수
    retained_earnings_ratio_score: int = 0         # 유보율 점수
    debt_ratio_score: int = 0                      # 부채비율 점수
    
    total_score: int = 0                           # 최종 점수 (0~5점)
    
    # 상세 계산 결과
    revenue_growth_rate: Optional[float] = None    # 매출 증가율 (%)
    operating_profit_transition: Optional[str] = None  # 영업이익 전환 상태
    operating_margin_rate: Optional[float] = None  # 영업이익률 (%)
    retained_earnings_ratio: Optional[float] = None # 유보율 (%)
    debt_ratio: Optional[float] = None             # 부채비율 (%)
    
    # 원본 데이터 (투명성을 위한 실제 계산 데이터)
    current_revenue: Optional[Decimal] = None      # 당년 매출액
    previous_revenue: Optional[Decimal] = None     # 전년 매출액
    current_operating_profit: Optional[Decimal] = None   # 당년 영업이익
    previous_operating_profit: Optional[Decimal] = None  # 전년 영업이익
    total_debt: Optional[Decimal] = None           # 총부채
    total_equity: Optional[Decimal] = None         # 자기자본
    retained_earnings: Optional[Decimal] = None    # 이익잉여금
    capital_stock: Optional[Decimal] = None        # 자본금
    
    # 데이터 기준 연월 (YYYYMM 형식)
    current_period: Optional[str] = None           # 당년 기준 연월
    previous_period: Optional[str] = None          # 전년 기준 연월

class DinoTestFinanceScorer:
    """디노테스트 재무 영역 점수 계산기"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_revenue_growth_score(self, finance_data: FinanceData) -> tuple[int, Optional[float]]:
        """
        매출액 증감 점수 계산 (±1점)
        
        규칙:
        - 전년 대비 매출 증가 10% 이상: +1점
        - 전년 대비 매출 감소: -1점  
        - 나머지 경우: 0점
        
        계산식: (당년 매출액 - 전년 매출액) / 전년 매출액 × 100
        """
        if not finance_data.current_revenue or not finance_data.previous_revenue:
            self.logger.warning("매출액 데이터 부족 - 점수 0점 처리")
            return 0, None
            
        if finance_data.previous_revenue == 0:
            self.logger.warning("전년 매출액이 0 - 점수 계산 불가")
            return 0, None
        
        growth_rate = float(
            (finance_data.current_revenue - finance_data.previous_revenue) / 
            finance_data.previous_revenue * 100
        )
        
        if growth_rate >= 10.0:
            score = 1
        elif growth_rate < 0:
            score = -1
        else:
            score = 0
            
        self.logger.info(f"매출액 증가율: {growth_rate:.2f}%, 점수: {score}")
        return score, growth_rate
    
    def calculate_operating_profit_score(self, finance_data: FinanceData) -> tuple[int, Optional[str]]:
        """
        영업이익 상태 점수 계산 (±2점)
        
        규칙:
        - 영업이익 흑자 전환 (전년 적자 → 당년 흑자): +1점
        - 영업이익 적자 전환 (전년 흑자 → 당년 적자): -1점
        - 영업이익 적자 지속 (전년 적자 → 당년 적자): -2점
        - 영업이익 흑자 지속: 0점
        """
        if finance_data.current_operating_profit is None or finance_data.previous_operating_profit is None:
            self.logger.warning("영업이익 데이터 부족 - 점수 0점 처리")
            return 0, None
        
        current_profitable = finance_data.current_operating_profit > 0
        previous_profitable = finance_data.previous_operating_profit > 0
        
        if not previous_profitable and current_profitable:
            # 적자 → 흑자 전환
            transition = "적자→흑자 전환"
            score = 1
        elif previous_profitable and not current_profitable:
            # 흑자 → 적자 전환
            transition = "흑자→적자 전환"
            score = -1
        elif not previous_profitable and not current_profitable:
            # 적자 지속
            transition = "적자 지속"
            score = -2
        else:
            # 흑자 지속
            transition = "흑자 지속"
            score = 0
        
        self.logger.info(f"영업이익 상태: {transition}, 점수: {score}")
        return score, transition
    
    def calculate_operating_margin_score(self, finance_data: FinanceData) -> tuple[int, Optional[float]]:
        """
        영업이익률 점수 계산 (+1점)
        
        규칙:
        - 영업이익률 10% 이상: +1점
        - 나머지 경우: 0점
        
        계산식: 영업이익 / 매출액 × 100
        """
        # 직접 제공된 영업이익률 사용
        if finance_data.operating_margin is not None:
            margin_rate = float(finance_data.operating_margin)
        # 손익계산서 데이터로 계산
        elif (finance_data.current_operating_profit is not None and 
              finance_data.current_revenue is not None and 
              finance_data.current_revenue > 0):
            margin_rate = float(finance_data.current_operating_profit / finance_data.current_revenue * 100)
        else:
            self.logger.warning("영업이익률 계산을 위한 데이터 부족 - 점수 0점 처리")
            return 0, None
        
        score = 1 if margin_rate >= 10.0 else 0
        
        self.logger.info(f"영업이익률: {margin_rate:.2f}%, 점수: {score}")
        return score, margin_rate
    
    def calculate_retained_earnings_ratio_score(self, finance_data: FinanceData) -> tuple[int, Optional[float]]:
        """
        유보율 점수 계산 (±1점)
        
        규칙:
        - 유보율 1,000% 이상: +1점
        - 유보율 300% 이하: -1점
        - 나머지 경우: 0점
        
        우선순위:
        1. KIS API에서 직접 제공된 유보율 사용 (retention_rate)
        2. 없으면 이익잉여금/자본금으로 계산
        """
        # KIS API에서 직접 제공된 유보율 사용
        if finance_data.retention_rate is not None:
            retention_ratio = float(finance_data.retention_rate)
        elif finance_data.retained_earnings and finance_data.capital_stock and finance_data.capital_stock != 0:
            # 이익잉여금/자본금으로 계산
            retention_ratio = float(finance_data.retained_earnings / finance_data.capital_stock * 100)
        else:
            self.logger.warning("유보율 계산을 위한 데이터 부족 - 점수 0점 처리")
            return 0, None
        
        if retention_ratio >= 1000.0:
            score = 1
        elif retention_ratio <= 300.0:
            score = -1
        else:
            score = 0
            
        self.logger.info(f"유보율: {retention_ratio:.2f}%, 점수: {score}")
        return score, retention_ratio
    
    def calculate_debt_ratio_score(self, finance_data: FinanceData) -> tuple[int, Optional[float]]:
        """
        부채비율 점수 계산 (±1점)
        
        규칙:
        - 부채비율 50% 이하: +1점
        - 부채비율 200% 이상: -1점
        - 나머지 경우: 0점
        
        계산식: 총부채 / 자기자본 × 100
        """
        if not finance_data.total_debt or not finance_data.total_equity:
            self.logger.warning("부채비율 계산을 위한 데이터 부족 - 점수 0점 처리")
            return 0, None
            
        if finance_data.total_equity == 0:
            self.logger.warning("자기자본이 0 - 부채비율 계산 불가")
            return 0, None
        
        debt_ratio = float(finance_data.total_debt / finance_data.total_equity * 100)
        
        if debt_ratio <= 50.0:
            score = 1
        elif debt_ratio >= 200.0:
            score = -1
        else:
            score = 0
            
        self.logger.info(f"부채비율: {debt_ratio:.2f}%, 점수: {score}")
        return score, debt_ratio
    
    def calculate_total_finance_score(self, finance_data: FinanceData) -> FinanceScoreDetail:
        """
        디노테스트 재무 영역 최종 점수 계산
        
        엑셀 수식: MAX(0, MIN(5, 2 + SUM(개별지표점수들)))
        """
        self.logger.info("=== 디노테스트 재무 영역 점수 계산 시작 ===")
        
        # 개별 지표 점수 계산
        revenue_score, revenue_growth = self.calculate_revenue_growth_score(finance_data)
        profit_score, profit_transition = self.calculate_operating_profit_score(finance_data)
        margin_score, margin_rate = self.calculate_operating_margin_score(finance_data)
        retention_score, retention_ratio = self.calculate_retained_earnings_ratio_score(finance_data)
        debt_score, debt_ratio = self.calculate_debt_ratio_score(finance_data)
        
        # 개별 점수 합계
        individual_scores_sum = revenue_score + profit_score + margin_score + retention_score + debt_score
        
        # 엑셀 수식 적용: MAX(0, MIN(5, 2 + SUM(개별점수들)))
        total_score = max(0, min(5, 2 + individual_scores_sum))
        
        self.logger.info(f"개별 점수 합계: {individual_scores_sum}, 최종 점수: {total_score}")
        self.logger.info("=== 디노테스트 재무 영역 점수 계산 완료 ===")
        
        return FinanceScoreDetail(
            revenue_growth_score=revenue_score,
            operating_profit_score=profit_score,
            operating_margin_score=margin_score,
            retained_earnings_ratio_score=retention_score,
            debt_ratio_score=debt_score,
            total_score=total_score,
            revenue_growth_rate=revenue_growth,
            operating_profit_transition=profit_transition,
            operating_margin_rate=margin_rate,
            retained_earnings_ratio=retention_ratio,
            debt_ratio=debt_ratio,
            # 원본 데이터 포함
            current_revenue=finance_data.current_revenue,
            previous_revenue=finance_data.previous_revenue,
            current_operating_profit=finance_data.current_operating_profit,
            previous_operating_profit=finance_data.previous_operating_profit,
            total_debt=finance_data.total_debt,
            total_equity=finance_data.total_equity,
            retained_earnings=finance_data.retained_earnings,
            capital_stock=finance_data.capital_stock,
            current_period=finance_data.current_period,
            previous_period=finance_data.previous_period
        )