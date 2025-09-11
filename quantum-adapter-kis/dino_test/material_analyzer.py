"""
디노테스트 소재 영역 분석기

소재 영역 4개 지표를 평가하여 0~5점 범위에서 점수를 산출합니다:
1. 고배당 (2% 이상) (±1점)
2. 기관/외국인 수급 (최근 1~3개월, 상장주식수의 1% 이상) (±1점)
3. 어닝서프라이즈 (컨센서스 대비 10% 이상) (±1점) - 향후 구현
4. 기타 소재 항목들 (뉴스, 이벤트 등) - 향후 구현

총점 계산: MAX(0, MIN(5, 2 + SUM(개별점수들)))
"""

import logging
import pandas as pd
from typing import Optional, Dict, Any
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class MaterialData:
    """소재분석 데이터 구조"""
    # 배당 정보
    dividend_yield: Optional[float] = None          # 배당률 (%)
    
    # 기관/외국인 수급 정보
    institutional_ratio: Optional[float] = None     # 기관 보유 비율 (%)
    foreign_ratio: Optional[float] = None           # 외국인 보유 비율 (%)
    institutional_change_1m: Optional[float] = None # 기관 1개월 변화율 (%)
    foreign_change_1m: Optional[float] = None       # 외국인 1개월 변화율 (%)
    institutional_change_3m: Optional[float] = None # 기관 3개월 변화율 (%)
    foreign_change_3m: Optional[float] = None       # 외국인 3개월 변화율 (%)
    
    # 주식 정보
    listed_shares: Optional[int] = None             # 상장주식수
    
    # 추가 정보 (향후 확장)
    earnings_surprise: Optional[float] = None       # 어닝서프라이즈 (%)
    
    # 원시 데이터 저장
    raw_dividend_data: Optional[pd.DataFrame] = None
    raw_investor_data: Optional[pd.DataFrame] = None

@dataclass
class MaterialScoreDetail:
    """소재분석 점수 상세 내역"""
    dividend_score: int = 0                         # 고배당 점수 (0~1점)
    institutional_score: int = 0                    # 기관 수급 점수 (0~1점) 
    foreign_score: int = 0                          # 외국인 수급 점수 (0~1점)
    earnings_surprise_score: int = 0                # 어닝서프라이즈 점수 (0~1점)
    
    total_score: int = 0                            # 최종 점수 (0~5점)
    
    # 상세 계산 결과
    dividend_yield: Optional[float] = None          # 배당률 (%)
    institutional_ratio: Optional[float] = None     # 기관 보유 비율 (%)
    foreign_ratio: Optional[float] = None           # 외국인 보유 비율 (%)
    institutional_change: Optional[float] = None    # 기관 변화율 (%)
    foreign_change: Optional[float] = None          # 외국인 변화율 (%)
    
    # 상태 설명
    dividend_status: Optional[str] = None           # 배당 상태 설명
    institutional_status: Optional[str] = None      # 기관 수급 상태 설명
    foreign_status: Optional[str] = None            # 외국인 수급 상태 설명

class DinoTestMaterialAnalyzer:
    """디노테스트 소재 영역 분석기"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_dividend_score(self, material_data: MaterialData) -> tuple[int, Optional[float], Optional[str]]:
        """
        D004: 고배당 점수 계산 (0~1점)
        
        판단 기준:
        - 배당률 ≥ 2%: +1점 (고배당)
        - 배당률 < 2%: 0점 (일반)
        - 배당률 데이터 없음: 0점
        """
        if material_data.dividend_yield is None:
            self.logger.warning("배당률 계산을 위한 데이터 부족")
            return 0, None, "데이터 부족"
        
        dividend_yield = material_data.dividend_yield
        
        if dividend_yield >= 2.0:
            score = 1
            status = f"고배당 ({dividend_yield:.2f}%)"
        else:
            score = 0
            status = f"일반 배당 ({dividend_yield:.2f}%)"
        
        self.logger.info(f"배당률: {status}, 점수: +{score}")
        return score, dividend_yield, status
    
    def calculate_investor_supply_score(self, material_data: MaterialData) -> tuple[int, Optional[float], Optional[float], Optional[str]]:
        """
        D003: 기관/외국인 투자 수급 점수 계산 (0~1점)
        
        판단 기준:
        - 기관 또는 외국인 중 어느 하나라도 최근 1~3개월 내 1% 이상 매집: +1점
        - 그 외: 0점
        
        Returns:
            tuple: (총점, 기관변화율, 외국인변화율, 상태설명)
        """
        # 기관 수급 데이터 확인
        institutional_changes = []
        if material_data.institutional_change_1m is not None:
            institutional_changes.append(material_data.institutional_change_1m)
        if material_data.institutional_change_3m is not None:
            institutional_changes.append(material_data.institutional_change_3m)
        
        # 외국인 수급 데이터 확인  
        foreign_changes = []
        if material_data.foreign_change_1m is not None:
            foreign_changes.append(material_data.foreign_change_1m)
        if material_data.foreign_change_3m is not None:
            foreign_changes.append(material_data.foreign_change_3m)
        
        # 최대 변화율 계산
        max_institutional = max(institutional_changes) if institutional_changes else 0
        max_foreign = max(foreign_changes) if foreign_changes else 0
        
        # 데이터 부족 체크
        if not institutional_changes and not foreign_changes:
            self.logger.warning("기관/외국인 수급 계산을 위한 데이터 부족")
            return 0, None, None, "데이터 부족"
        
        # 점수 계산: 기관 또는 외국인 중 하나라도 1% 이상이면 1점
        if max_institutional >= 1.0 or max_foreign >= 1.0:
            score = 1
            if max_institutional >= 1.0 and max_foreign >= 1.0:
                status = f"기관+외국인 동반 매집 (기관:{max_institutional:.2f}%, 외국인:{max_foreign:.2f}%)"
            elif max_institutional >= 1.0:
                status = f"기관 매집 ({max_institutional:.2f}%)"
            else:
                status = f"외국인 매집 ({max_foreign:.2f}%)"
        else:
            score = 0
            status = f"기관/외국인 수급 중립 (기관:{max_institutional:.2f}%, 외국인:{max_foreign:.2f}%)"
        
        self.logger.info(f"D003 투자 수급: {status}, 점수: +{score}")
        return score, max_institutional, max_foreign, status
    
    def calculate_earnings_surprise_score(self, material_data: MaterialData) -> tuple[int, Optional[float], Optional[str]]:
        """
        D005: 어닝서프라이즈 점수 계산 (0~1점) - 향후 구현
        
        판단 기준:
        - 컨센서스 대비 10% 이상 초과: +1점
        - 그 외: 0점
        """
        if material_data.earnings_surprise is None:
            self.logger.info("어닝서프라이즈 데이터 없음 - 향후 구현 예정")
            return 0, None, "향후 구현"
        
        earnings_surprise = material_data.earnings_surprise
        
        if earnings_surprise >= 10.0:  # 컨센서스 대비 10% 이상 초과
            score = 1
            status = f"어닝서프라이즈 (+{earnings_surprise:.1f}%)"
        else:
            score = 0
            status = f"어닝서프라이즈 없음 ({earnings_surprise:.1f}%)"
        
        self.logger.info(f"어닝서프라이즈: {status}, 점수: +{score}")
        return score, earnings_surprise, status
    
    def calculate_total_material_score(self, material_data: MaterialData) -> MaterialScoreDetail:
        """
        디노테스트 소재 영역 최종 점수 계산
        
        소재 영역 주요 지표:
        1. 고배당 (2% 이상) (0~1점)
        2. 기관/외국인 수급 (1% 이상 매집) (0~1점) - 통합점수
        3. 어닝서프라이즈 (10% 이상) (0~1점) - 향후 구현
        
        총점 공식: MAX(0, MIN(5, 2 + SUM(개별점수들)))
        """
        self.logger.info("=== 디노테스트 소재 영역 점수 계산 시작 ===")
        
        # 고배당 점수 계산
        dividend_score, dividend_yield, dividend_status = self.calculate_dividend_score(material_data)
        
        # 기관/외국인 수급 점수 계산 (통합)
        investor_supply_score, institutional_change, foreign_change, investor_status = self.calculate_investor_supply_score(material_data)
        
        # 어닝서프라이즈 점수 계산 (향후 구현)
        earnings_surprise_score, earnings_surprise_val, earnings_surprise_status = self.calculate_earnings_surprise_score(material_data)
        
        # 총 점수 계산 (0~5점) - 공식: MAX(0,MIN(5,2+SUM(점수들)))
        individual_sum = dividend_score + investor_supply_score + earnings_surprise_score
        total_score = max(0, min(5, 2 + individual_sum))
        
        self.logger.info(f"소재 영역 총 점수: {total_score}/5점 (개별 합계: {individual_sum})")
        self.logger.info("=== 디노테스트 소재 영역 점수 계산 완료 ===")
        
        return MaterialScoreDetail(
            dividend_score=dividend_score,
            institutional_score=investor_supply_score,  # D003 통합점수
            foreign_score=0,  # D003에 통합되었으므로 0
            earnings_surprise_score=earnings_surprise_score,
            total_score=total_score,
            dividend_yield=dividend_yield,
            institutional_ratio=material_data.institutional_ratio,
            foreign_ratio=material_data.foreign_ratio,
            institutional_change=institutional_change,
            foreign_change=foreign_change,
            dividend_status=dividend_status,
            institutional_status=investor_status,  # D003 통합 상태
            foreign_status="D003에 통합됨"  # 통합 표시
        )