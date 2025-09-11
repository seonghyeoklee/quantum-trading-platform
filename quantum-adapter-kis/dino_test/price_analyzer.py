"""
디노테스트 가격 영역 분석기

가격 영역 5개 지표를 평가하여 0~5점 범위에서 점수를 산출합니다:
1. 52주 최고가 대비 현재가 위치 (최대 +3점)
2. 52주 최저가 대비 현재가 위치 (최대 -3점)

총점 계산: MAX(0, MIN(5, 2 + SUM(최고가점수, 최저가점수)))
"""

import logging
import pandas as pd
from typing import Optional
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class PriceData:
    """가격분석 데이터 구조"""
    # 현재 가격 정보
    current_price: Optional[float] = None       # 현재가
    
    # 52주 가격 정보
    week_52_high: Optional[float] = None        # 52주 최고가
    week_52_low: Optional[float] = None         # 52주 최저가
    week_52_high_date: Optional[datetime] = None # 52주 최고가 달성일
    week_52_low_date: Optional[datetime] = None  # 52주 최저가 달성일
    
    # 차트 데이터 (52주 분석용)
    chart_data: Optional[pd.DataFrame] = None   # OHLCV 데이터

@dataclass
class PriceScoreDetail:
    """가격분석 점수 상세 내역"""
    high_ratio_score: int = 0                   # 최고가 대비 점수 (최대 +3점)
    low_ratio_score: int = 0                    # 최저가 대비 점수 (최대 -3점)
    
    total_score: int = 0                        # 최종 점수 (0~5점)
    
    # 상세 계산 결과
    high_ratio: Optional[float] = None          # 최고가 대비 비율 (%)
    low_ratio: Optional[float] = None           # 최저가 대비 비율 (%)
    current_price: Optional[float] = None       # 현재가
    week_52_high: Optional[float] = None        # 52주 최고가
    week_52_low: Optional[float] = None         # 52주 최저가
    high_ratio_status: Optional[str] = None     # 최고가 비율 상태 설명
    low_ratio_status: Optional[str] = None      # 최저가 비율 상태 설명

class DinoTestPriceAnalyzer:
    """디노테스트 가격 영역 분석기"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_52week_high_score(self, price_data: PriceData) -> tuple[int, Optional[float], Optional[str]]:
        """
        52주 최고가 대비 현재가 점수 계산 (최대 +3점)
        
        판단 기준:
        - (최고가-현재가)/최고가*100
        - -40% 이하: +3점 (현재가가 최고가의 60% 이상)
        - -30% 이하: +2점 (현재가가 최고가의 70% 이상)
        - -20% 이하: +1점 (현재가가 최고가의 80% 이상)
        - 그 외: 0점
        """
        if (price_data.current_price is None or 
            price_data.week_52_high is None):
            self.logger.warning("52주 최고가 계산을 위한 데이터 부족")
            return 0, None, "데이터 부족"
        
        if price_data.week_52_high == 0:
            self.logger.warning("52주 최고가가 0원")
            return 0, None, "최고가 오류"
        
        # 최고가 대비 비율 계산: (최고가-현재가)/최고가*100
        high_ratio = (price_data.week_52_high - price_data.current_price) / price_data.week_52_high * 100
        
        # 점수 계산 (음수로 나오므로 절대값으로 비교)
        if high_ratio <= -40:  # 현재가가 최고가의 140% 이상 (불가능하지만 방어코드)
            score = 3
            status = "최고가 크게 돌파 (매우 강함)"
        elif high_ratio <= -30:  # 현재가가 최고가의 130% 이상 (불가능하지만 방어코드)
            score = 3
            status = "최고가 돌파 (매우 강함)"  
        elif high_ratio <= -20:  # 현재가가 최고가의 120% 이상 (불가능하지만 방어코드)
            score = 2
            status = "최고가 근접 돌파 (강함)"
        elif high_ratio <= -10:  # 현재가가 최고가의 110% 이상 (불가능하지만 방어코드)
            score = 1
            status = "최고가 근접 (양호)"
        else:
            # 실제 로직: 현재가가 최고가보다 낮은 경우
            if abs(high_ratio) >= 40:  # 최고가 대비 40% 이상 하락
                score = 0
                status = "최고가 대비 큰 폭 하락 (약함)"
            elif abs(high_ratio) >= 30:  # 최고가 대비 30% 이상 하락
                score = 1
                status = "최고가 대비 하락 (보통)"
            elif abs(high_ratio) >= 20:  # 최고가 대비 20% 이상 하락  
                score = 2
                status = "최고가 대비 소폭 하락 (양호)"
            elif abs(high_ratio) >= 10:  # 최고가 대비 10% 이상 하락
                score = 3
                status = "최고가 근접 (우수)"
            else:  # 최고가 대비 10% 이내
                score = 3
                status = "최고가 근접 (매우 우수)"
        
        self.logger.info(f"52주 최고가: {status}, 비율: {high_ratio:.2f}%, 점수: +{score}")
        return score, high_ratio, status
    
    def calculate_52week_low_score(self, price_data: PriceData) -> tuple[int, Optional[float], Optional[str]]:
        """
        52주 최저가 대비 현재가 점수 계산 (최대 -3점)
        
        판단 기준:
        - (현재가-최저가)/최저가*100
        - +300% 이상: -3점 (최저가 대비 4배 이상)
        - +200% 이상: -2점 (최저가 대비 3배 이상)
        - +100% 이상: -1점 (최저가 대비 2배 이상)
        - 그 외: 0점
        """
        if (price_data.current_price is None or 
            price_data.week_52_low is None):
            self.logger.warning("52주 최저가 계산을 위한 데이터 부족")
            return 0, None, "데이터 부족"
        
        if price_data.week_52_low == 0:
            self.logger.warning("52주 최저가가 0원")
            return 0, None, "최저가 오류"
        
        # 최저가 대비 비율 계산: (현재가-최저가)/최저가*100
        low_ratio = (price_data.current_price - price_data.week_52_low) / price_data.week_52_low * 100
        
        # 점수 계산 (상승폭이 클수록 마이너스 점수)
        if low_ratio >= 300:  # 최저가 대비 300% 이상 상승 (4배)
            score = -3
            status = "최저가 대비 과도한 상승 (위험)"
        elif low_ratio >= 200:  # 최저가 대비 200% 이상 상승 (3배)
            score = -2
            status = "최저가 대비 큰 폭 상승 (주의)"
        elif low_ratio >= 100:  # 최저가 대비 100% 이상 상승 (2배)
            score = -1
            status = "최저가 대비 상당한 상승 (보통)"
        elif low_ratio >= 50:   # 최저가 대비 50% 이상 상승
            score = 0
            status = "최저가 대비 적정 상승 (양호)"
        else:  # 최저가 대비 50% 이내 상승
            score = 0
            status = "최저가 근접 (우수)"
        
        self.logger.info(f"52주 최저가: {status}, 비율: +{low_ratio:.2f}%, 점수: {score}")
        return score, low_ratio, status
    
    def calculate_52week_data_from_chart(self, chart_data: pd.DataFrame) -> tuple[Optional[float], Optional[float], Optional[datetime], Optional[datetime]]:
        """
        차트 데이터로부터 52주 최고가/최저가 계산
        
        Args:
            chart_data: OHLCV 데이터 (pandas DataFrame)
                       컬럼: date, open, high, low, close, volume
        
        Returns:
            tuple: (52주_최고가, 52주_최저가, 최고가_달성일, 최저가_달성일)
        """
        if chart_data is None or chart_data.empty:
            return None, None, None, None
        
        try:
            # 최근 252일(52주) 데이터만 사용
            recent_data = chart_data.tail(252) if len(chart_data) > 252 else chart_data
            
            # 52주 최고가/최저가 계산
            week_52_high = recent_data['high'].max()
            week_52_low = recent_data['low'].min()
            
            # 최고가/최저가 달성일 찾기
            high_date_idx = recent_data['high'].idxmax()
            low_date_idx = recent_data['low'].idxmin()
            
            high_date = recent_data.loc[high_date_idx, 'date']
            low_date = recent_data.loc[low_date_idx, 'date']
            
            self.logger.info(f"52주 최고가: {week_52_high:,}원 ({high_date.strftime('%Y-%m-%d')})")
            self.logger.info(f"52주 최저가: {week_52_low:,}원 ({low_date.strftime('%Y-%m-%d')})")
            
            return week_52_high, week_52_low, high_date, low_date
            
        except Exception as e:
            self.logger.error(f"52주 데이터 계산 실패: {e}")
            return None, None, None, None
    
    def calculate_total_price_score(self, price_data: PriceData) -> PriceScoreDetail:
        """
        디노테스트 가격 영역 최종 점수 계산
        
        가격 영역 2개 지표:
        1. 52주 최고가 대비 현재가 위치 (최대 +3점)
        2. 52주 최저가 대비 현재가 위치 (최대 -3점)
        
        총점 공식: MAX(0, MIN(5, 2 + SUM(최고가점수, 최저가점수)))
        """
        self.logger.info("=== 디노테스트 가격 영역 점수 계산 시작 ===")
        
        # 차트 데이터가 있으면 52주 데이터 계산
        if price_data.chart_data is not None:
            week_52_high, week_52_low, high_date, low_date = self.calculate_52week_data_from_chart(price_data.chart_data)
            if week_52_high is not None:
                price_data.week_52_high = week_52_high
                price_data.week_52_low = week_52_low
                price_data.week_52_high_date = high_date
                price_data.week_52_low_date = low_date
            
            # 현재가는 차트 데이터의 최신 종가
            if price_data.current_price is None and not price_data.chart_data.empty:
                price_data.current_price = price_data.chart_data['close'].iloc[-1]
        
        # 52주 최고가 대비 점수 계산
        high_score, high_ratio, high_status = self.calculate_52week_high_score(price_data)
        
        # 52주 최저가 대비 점수 계산  
        low_score, low_ratio, low_status = self.calculate_52week_low_score(price_data)
        
        # 총 점수 계산 (0~5점) - 공식: MAX(0,MIN(5,2+SUM(점수들)))
        individual_sum = high_score + low_score
        total_score = max(0, min(5, 2 + individual_sum))
        
        self.logger.info(f"가격 영역 총 점수: {total_score}/5점 (개별 합계: {individual_sum})")
        self.logger.info("=== 디노테스트 가격 영역 점수 계산 완료 ===")
        
        return PriceScoreDetail(
            high_ratio_score=high_score,
            low_ratio_score=low_score,
            total_score=total_score,
            high_ratio=high_ratio,
            low_ratio=low_ratio,
            current_price=price_data.current_price,
            week_52_high=price_data.week_52_high,
            week_52_low=price_data.week_52_low,
            high_ratio_status=high_status,
            low_ratio_status=low_status
        )