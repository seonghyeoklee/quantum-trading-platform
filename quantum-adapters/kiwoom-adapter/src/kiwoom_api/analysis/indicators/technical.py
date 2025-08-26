"""
기술적 지표 계산 모듈

RSI, OBV, 이동평균선 등 기술적 분석 지표들을 계산합니다.
"""

from typing import List
import pandas as pd


def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """
    RSI (Relative Strength Index) 계산
    
    Args:
        prices: 종가 리스트 (최신 데이터가 마지막)
        period: RSI 계산 기간 (기본 14일)
    
    Returns:
        RSI 값 (0-100 범위)
    """
    if len(prices) < period + 1:
        raise ValueError(f"RSI 계산을 위해서는 최소 {period + 1}개의 가격 데이터가 필요합니다.")
    
    # pandas Series로 변환
    price_series = pd.Series(prices)
    
    # 가격 변화량 계산
    delta = price_series.diff()
    
    # 상승분과 하락분 분리
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    
    # 초기 평균 계산 (첫 번째 기간)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # 이후 기간들에 대한 지수 이동 평균 계산 (Wilder's smoothing)
    for i in range(period, len(prices)):
        avg_gain.iloc[i] = ((avg_gain.iloc[i-1] * (period - 1)) + gain.iloc[i]) / period
        avg_loss.iloc[i] = ((avg_loss.iloc[i-1] * (period - 1)) + loss.iloc[i]) / period
    
    # RS (Relative Strength) 계산
    rs = avg_gain / avg_loss
    
    # RSI 계산
    rsi = 100.0 - (100.0 / (1.0 + rs))
    
    # 최신 RSI 값 반환
    return round(float(rsi.iloc[-1]), 2)


def calculate_sma(prices: List[float], period: int) -> float:
    """
    단순이동평균(SMA) 계산
    
    Args:
        prices: 가격 리스트
        period: 이동평균 기간
    
    Returns:
        이동평균 값
    """
    if len(prices) < period:
        raise ValueError(f"SMA 계산을 위해서는 최소 {period}개의 데이터가 필요합니다.")
    
    return round(sum(prices[-period:]) / period, 2)


def calculate_obv(prices: List[float], volumes: List[int]) -> float:
    """
    OBV (On-Balance Volume) 계산
    
    Args:
        prices: 종가 리스트 (시간순 정렬, 최신 데이터가 마지막)
        volumes: 거래량 리스트 (시간순 정렬, 최신 거래량이 마지막)
    
    Returns:
        현재 OBV 값 (누적 거래량)
    """
    if len(prices) != len(volumes) or len(prices) < 2:
        raise ValueError("OBV 계산을 위해서는 가격과 거래량 데이터가 같은 길이이고 최소 2개 이상이어야 합니다.")
    
    obv = 0
    for i in range(1, len(prices)):
        if prices[i] > prices[i-1]:
            obv += volumes[i]  # 상승일 때 거래량 더함
        elif prices[i] < prices[i-1]:
            obv -= volumes[i]  # 하락일 때 거래량 뺌
        # 같으면 변화 없음 (obv 그대로 유지)
    
    return obv


def calculate_ema(prices: List[float], period: int) -> float:
    """
    지수이동평균(EMA) 계산
    
    Args:
        prices: 가격 리스트 (시간순 정렬)
        period: 이동평균 기간
    
    Returns:
        EMA 값
    """
    if len(prices) < period:
        raise ValueError(f"EMA 계산을 위해서는 최소 {period}개의 데이터가 필요합니다.")
    
    # 초기값은 SMA로 설정
    ema = sum(prices[:period]) / period
    multiplier = 2.0 / (period + 1)
    
    # EMA 계산
    for i in range(period, len(prices)):
        ema = (prices[i] * multiplier) + (ema * (1 - multiplier))
    
    return round(ema, 2)


# 테스트용 함수
def test_rsi_calculation():
    """RSI 계산 테스트"""
    # 테스트 데이터 (실제 주가 패턴 시뮬레이션)
    test_prices = [
        44.00, 44.25, 44.50, 43.75, 44.50, 44.00, 44.25, 44.75, 45.00, 45.25,
        45.50, 45.25, 45.00, 44.50, 44.00, 44.25, 44.75, 45.50, 46.00, 46.25
    ]
    
    try:
        rsi = calculate_rsi(test_prices)
        print(f"테스트 RSI 값: {rsi}")
        print(f"RSI 해석: {'과매수' if rsi > 70 else '과매도' if rsi < 30 else '중립'}")
        return rsi
    except Exception as e:
        print(f"RSI 계산 오류: {e}")
        return None


if __name__ == "__main__":
    # 테스트 실행
    test_rsi_calculation()