"""
매매 신호 감지 모듈
골든크로스/데드크로스 및 기타 매매 신호 감지
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict
import pandas as pd
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SignalType(Enum):
    """매매 신호 타입"""
    GOLDEN_CROSS = "GOLDEN_CROSS"  # 골든크로스 (매수)
    DEAD_CROSS = "DEAD_CROSS"      # 데드크로스 (매도) 
    HOLD = "HOLD"                   # 보유/대기
    NONE = "NONE"                   # 신호 없음

class ConfidenceLevel(Enum):
    """신호 확신도"""
    CONFIRMED = "CONFIRMED"         # 3일 연속 확정
    TENTATIVE = "TENTATIVE"         # 임시 신호
    WEAK = "WEAK"                   # 약한 신호

@dataclass
class TradingSignal:
    """매매 신호 정보"""
    timestamp: datetime
    symbol: str
    symbol_name: str
    signal_type: SignalType
    confidence: ConfidenceLevel
    price: float
    sma5: float
    sma20: float
    confirmation_days: int
    spread_percent: float      # 이동평균선 간격 %
    volume_ratio: float        # 평균 거래량 대비 비율
    rsi: Optional[float]       # RSI 값
    strength: float           # 신호 강도 (0-100)
    reason: str              # 신호 발생 이유
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'symbol_name': self.symbol_name,
            'signal_type': self.signal_type.value,
            'confidence': self.confidence.value,
            'price': self.price,
            'sma5': self.sma5,
            'sma20': self.sma20,
            'confirmation_days': self.confirmation_days,
            'spread_percent': self.spread_percent,
            'volume_ratio': self.volume_ratio,
            'rsi': self.rsi,
            'strength': self.strength,
            'reason': self.reason
        }

class SignalDetector:
    """매매 신호 감지기"""
    
    def __init__(self, confirmation_days: int = 1):
        """
        Args:
            confirmation_days: 신호 확정을 위한 연속 일수 (백테스팅 결과 기반 최적화)
        """
        self.confirmation_days = confirmation_days
        self.signal_history: Dict[str, List[TradingSignal]] = {}
        
        # 백테스팅 결과 기반 종목별 최적 확정 기간 (2024.09.04 분석 결과)
        self.optimal_periods = {
            "005930": 7,  # 삼성전자: 7일 확정 (+0.14%)
            "035720": 1,  # 카카오: 1일 확정 (+0.17%)
            "009540": 7,  # HD한국조선해양: 7일 확정 (+1.17%)
            "012450": 2,  # 한화에어로스페이스: 2일 확정 (+0.49%)
            "010060": 7,  # OCI: 7일 확정 (-0.01%)
        }
        
        # 기본값: 대형주/안정주 → 7일, 중소형/테마주 → 2일
        self.default_period_large_cap = 7  # 대형주 기본값
        self.default_period_small_cap = 2  # 중소형주 기본값
    
    def get_optimal_confirmation_days(self, symbol: str) -> int:
        """
        종목별 최적 확정 기간 반환 (백테스팅 결과 기반)
        
        Args:
            symbol: 종목 코드
            
        Returns:
            최적 확정 기간 (일)
        """
        # 백테스팅 결과가 있는 종목은 최적 기간 사용
        if symbol in self.optimal_periods:
            return self.optimal_periods[symbol]
        
        # 대형주 판단 (시가총액 상위 종목들)
        large_cap_symbols = {
            "005930",  # 삼성전자
            "000660",  # SK하이닉스  
            "035420",  # NAVER
            "005490",  # POSCO홀딩스
            "051910",  # LG화학
            "006400",  # 삼성SDI
            "028260",  # 삼성물산
        }
        
        if symbol in large_cap_symbols:
            return self.default_period_large_cap
        else:
            return self.default_period_small_cap
        
    def detect_golden_cross(self, 
                           df: pd.DataFrame,
                           symbol: str,
                           symbol_name: str = "",
                           short_ma: str = 'sma5',
                           long_ma: str = 'sma20') -> Optional[TradingSignal]:
        """
        골든크로스/데드크로스 신호 감지
        
        Args:
            df: 기술적 지표가 계산된 데이터프레임
            symbol: 종목 코드
            symbol_name: 종목명
            short_ma: 단기 이동평균 컬럼명
            long_ma: 장기 이동평균 컬럼명
        
        Returns:
            감지된 신호 또는 None
        """
        # 필요한 컬럼 확인
        required = [short_ma, long_ma, 'close', 'volume', 'volume_sma20']
        if not all(col in df.columns for col in required):
            logger.warning(f"필요한 컬럼이 없습니다: {required}")
            return None
        
        # 종목별 최적 확정 기간 가져오기
        optimal_days = self.get_optimal_confirmation_days(symbol)
        
        # NaN 값 제거
        df_clean = df.dropna(subset=[short_ma, long_ma]).copy()
        
        if len(df_clean) < optimal_days + 1:
            return None
        
        # 크로스 포인트 찾기
        df_clean['cross_diff'] = df_clean[short_ma] - df_clean[long_ma]
        df_clean['cross_diff_prev'] = df_clean['cross_diff'].shift(1)
        
        # 최근 데이터만 확인
        latest_idx = df_clean.index[-1]
        latest = df_clean.iloc[-1]
        
        signal_type = None
        reason = ""
        
        # 골든크로스: 이전에는 음수였다가 현재 양수가 됨
        if latest['cross_diff_prev'] <= 0 and latest['cross_diff'] > 0:
            signal_type = SignalType.GOLDEN_CROSS
            reason = f"골든크로스 발생: {short_ma}({latest[short_ma]:.0f}) > {long_ma}({latest[long_ma]:.0f})"
            
        # 데드크로스: 이전에는 양수였다가 현재 음수가 됨  
        elif latest['cross_diff_prev'] >= 0 and latest['cross_diff'] < 0:
            signal_type = SignalType.DEAD_CROSS
            reason = f"데드크로스 발생: {short_ma}({latest[short_ma]:.0f}) < {long_ma}({latest[long_ma]:.0f})"
        
        if signal_type:
            # 확정 여부 확인 (종목별 최적 기간 사용)
            confirmation_days = self._count_confirmation_days(
                df_clean, latest_idx, signal_type, short_ma, long_ma, optimal_days
            )
            
            confidence = self._determine_confidence(confirmation_days, optimal_days)
            
            # 신호 강도 계산
            strength = self._calculate_signal_strength(
                latest, signal_type, confirmation_days, optimal_days
            )
            
            # 신호 생성
            signal = TradingSignal(
                timestamp=datetime.now(),
                symbol=symbol,
                symbol_name=symbol_name or symbol,
                signal_type=signal_type,
                confidence=confidence,
                price=latest['close'],
                sma5=latest[short_ma],
                sma20=latest[long_ma],
                confirmation_days=confirmation_days,
                spread_percent=abs(latest['cross_diff']) / latest[long_ma] * 100,
                volume_ratio=latest.get('volume_ratio', 1.0),
                rsi=latest.get('rsi', None),
                strength=strength,
                reason=reason
            )
            
            # 히스토리 저장
            if symbol not in self.signal_history:
                self.signal_history[symbol] = []
            self.signal_history[symbol].append(signal)
            
            return signal
        
        return None
    
    def _count_confirmation_days(self, 
                                df: pd.DataFrame,
                                idx: int,
                                signal_type: SignalType,
                                short_ma: str,
                                long_ma: str,
                                required_days: int) -> int:
        """연속 유지 일수 계산"""
        count = 0
        
        # 현재 인덱스부터 과거 방향으로 확인
        idx_pos = df.index.get_loc(idx)
        
        for i in range(min(required_days, idx_pos + 1)):
            check_idx = df.index[idx_pos - i]
            
            if signal_type == SignalType.GOLDEN_CROSS:
                if df.loc[check_idx, short_ma] > df.loc[check_idx, long_ma]:
                    count += 1
                else:
                    break
            else:  # DEAD_CROSS
                if df.loc[check_idx, short_ma] < df.loc[check_idx, long_ma]:
                    count += 1
                else:
                    break
        
        return count
    
    def _determine_confidence(self, confirmation_days: int, required_days: int) -> ConfidenceLevel:
        """확신도 결정"""
        if confirmation_days >= required_days:
            return ConfidenceLevel.CONFIRMED
        elif confirmation_days >= max(2, required_days // 2):
            return ConfidenceLevel.TENTATIVE
        else:
            return ConfidenceLevel.WEAK
    
    def _calculate_signal_strength(self, 
                                  row: pd.Series,
                                  signal_type: SignalType,
                                  confirmation_days: int,
                                  required_days: int) -> float:
        """
        신호 강도 계산 (0-100)
        
        고려 요소:
        - 확정 일수 (종목별 최적 기간 기준)
        - 거래량 비율
        - 이동평균선 간격
        - RSI (있는 경우)
        """
        strength = 0.0
        
        # 확정 일수 (최대 40점) - 종목별 최적 기간 대비 비율
        strength += min(confirmation_days / required_days * 40, 40)
        
        # 거래량 비율 (최대 30점)
        volume_ratio = row.get('volume_ratio', 1.0)
        if volume_ratio > 1.5:
            strength += 30
        elif volume_ratio > 1.2:
            strength += 20
        elif volume_ratio > 1.0:
            strength += 10
        
        # 이동평균선 간격 (최대 20점)
        spread = abs(row.get('sma5', 0) - row.get('sma20', 0)) / row.get('sma20', 1) * 100
        if spread > 3:
            strength += 20
        elif spread > 2:
            strength += 15
        elif spread > 1:
            strength += 10
        
        # RSI 고려 (최대 10점)
        rsi = row.get('rsi', 50)
        if pd.notna(rsi):
            if signal_type == SignalType.GOLDEN_CROSS:
                if 30 <= rsi <= 70:
                    strength += 10
                elif 20 <= rsi <= 80:
                    strength += 5
            else:  # DEAD_CROSS
                if 30 <= rsi <= 70:
                    strength += 10
                elif 20 <= rsi <= 80:
                    strength += 5
        
        return min(strength, 100)
    
    def check_additional_conditions(self, signal: TradingSignal) -> bool:
        """
        추가 조건 확인
        
        Args:
            signal: 매매 신호
        
        Returns:
            모든 추가 조건을 만족하면 True
        """
        conditions_met = []
        
        # 1. 거래량 조건 (평균 대비 80% 이상)
        if signal.volume_ratio >= 0.8:
            conditions_met.append("거래량 조건 충족")
        else:
            logger.info(f"거래량 부족: {signal.volume_ratio:.2f}x")
            return False
        
        # 2. 이동평균선 간격 (1% 이상)
        if signal.spread_percent >= 1.0:
            conditions_met.append("스프레드 조건 충족")
        else:
            logger.info(f"스프레드 부족: {signal.spread_percent:.2f}%")
            return False
        
        # 3. RSI 조건 (과매수/과매도 아님)
        if signal.rsi is not None:
            if 25 <= signal.rsi <= 75:
                conditions_met.append("RSI 정상 범위")
            else:
                logger.info(f"RSI 극단값: {signal.rsi:.1f}")
                return False
        
        logger.info(f"추가 조건 모두 충족: {', '.join(conditions_met)}")
        return True