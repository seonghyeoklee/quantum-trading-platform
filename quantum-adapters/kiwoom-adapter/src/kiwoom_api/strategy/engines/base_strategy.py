"""
전략 기본 추상 클래스

모든 자동매매 전략이 상속받아야 하는 기본 클래스
"""

import sys
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from decimal import Decimal

# Handle both relative and absolute imports for different execution contexts
try:
    from ..models.trading_signal import TradingSignal, SignalType, SignalStrength
    from ..models.strategy_config import StrategyConfig
    from ...utils.rate_limiter import get_rate_limiter
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from kiwoom_api.strategy.models.trading_signal import TradingSignal, SignalType, SignalStrength
    from kiwoom_api.strategy.models.strategy_config import StrategyConfig
    from kiwoom_api.utils.rate_limiter import get_rate_limiter


class BaseStrategy(ABC):
    """
    전략 기본 추상 클래스
    
    모든 자동매매 전략이 상속받아야 하는 기본 인터페이스를 정의합니다.
    키움증권 API 연동, Rate Limiting, 오류 처리 등의 공통 기능을 제공합니다.
    """
    
    def __init__(self, config: StrategyConfig):
        """
        전략 초기화
        
        Args:
            config: 전략 설정 객체
        """
        self.config = config
        self.name = config.strategy_name
        self.enabled = config.enabled
        
        # 검증
        self._validate_config()
        
    def _validate_config(self) -> None:
        """전략 설정 검증"""
        if not self.config.target_symbols:
            raise ValueError("대상 종목이 설정되지 않았습니다.")
        
        if self.config.min_confidence < 0.0 or self.config.min_confidence > 1.0:
            raise ValueError("최소 신뢰도는 0.0과 1.0 사이여야 합니다.")
        
        if self.config.execution_interval < 10:
            raise ValueError("실행 주기는 최소 10초 이상이어야 합니다.")
    
    @abstractmethod
    async def analyze(self, symbol: str) -> Optional[TradingSignal]:
        """
        종목 분석 및 매매신호 생성
        
        Args:
            symbol: 종목코드 (6자리)
            
        Returns:
            TradingSignal 객체 또는 None (신호 없음)
        """
        pass
    
    @abstractmethod
    async def should_buy(self, symbol: str, data: Dict) -> bool:
        """
        매수 조건 확인
        
        Args:
            symbol: 종목코드
            data: 분석 데이터 딕셔너리
            
        Returns:
            매수해야 하면 True, 아니면 False
        """
        pass
    
    @abstractmethod
    async def should_sell(self, symbol: str, data: Dict) -> bool:
        """
        매도 조건 확인
        
        Args:
            symbol: 종목코드
            data: 분석 데이터 딕셔너리
            
        Returns:
            매도해야 하면 True, 아니면 False
        """
        pass
    
    async def get_chart_data(self, symbol: str, days: int = 30) -> Optional[Dict]:
        """
        키움 API를 통한 실제 차트 데이터 조회
        
        Args:
            symbol: 종목코드 (6자리)
            days: 조회할 일수
            
        Returns:
            차트 데이터 딕셔너리 또는 None (오류 시)
        """
        try:
            # 키움 차트 데이터 API 호출
            from ...functions.chart import fn_ka10081
            
            # Rate Limiter 적용하여 키움 API 호출
            rate_limiter = await get_rate_limiter()
            
            # 조회 종료일 (오늘)
            end_date = datetime.now().strftime("%Y%m%d")
            
            # 차트 데이터 요청 함수 정의
            async def _get_chart_data():
                try:
                    # fn_ka10081: 국내주식 시세(일봉) API 호출
                    result = await fn_ka10081(
                        data={
                            "stk_cd": symbol,           # 종목코드
                            "base_dt": end_date,        # 기준일자
                            "upd_stkpc_tp": "1",        # 수정주가타입 (1:수정주가)
                            "per_tp": "D",              # 기간타입 (D:일봉)
                            "cnt": str(min(days, 100))  # 조회건수 (최대 100)
                        },
                        cont_yn="N"  # 연속조회여부
                    )
                    
                    if result and result.get('Code') == 200 and result.get('Body'):
                        body = result['Body']
                        output = body.get('output', [])
                        
                        if not output:
                            print(f"차트 데이터가 없습니다: {symbol}")
                            return None
                        
                        # 데이터 파싱
                        prices = []
                        volumes = []
                        dates = []
                        opens = []
                        highs = []
                        lows = []
                        
                        for item in output:
                            # 가격 데이터 (문자열을 float로 변환)
                            try:
                                open_price = float(item.get('stck_oprc', '0'))
                                high_price = float(item.get('stck_hgpr', '0'))
                                low_price = float(item.get('stck_lwpr', '0'))
                                close_price = float(item.get('stck_clpr', '0'))
                                volume = int(item.get('acml_vol', '0'))
                                date_str = item.get('stck_bsop_date', '')
                                
                                if close_price > 0:  # 유효한 가격 데이터만
                                    opens.append(open_price)
                                    highs.append(high_price)
                                    lows.append(low_price)
                                    prices.append(close_price)
                                    volumes.append(volume)
                                    
                                    # 날짜 파싱 (YYYYMMDD 형식)
                                    if date_str and len(date_str) == 8:
                                        date_obj = datetime.strptime(date_str, '%Y%m%d')
                                        dates.append(date_obj)
                                    else:
                                        dates.append(datetime.now() - timedelta(days=len(dates)))
                                        
                            except (ValueError, TypeError) as e:
                                print(f"데이터 파싱 오류: {item}, 오류: {e}")
                                continue
                        
                        if not prices:
                            print(f"유효한 차트 데이터가 없습니다: {symbol}")
                            return None
                        
                        # 데이터 역순 정렬 (과거 -> 현재 순서)
                        prices.reverse()
                        volumes.reverse()
                        dates.reverse()
                        opens.reverse()
                        highs.reverse()
                        lows.reverse()
                        
                        return {
                            "symbol": symbol,
                            "prices": prices,           # 종가
                            "opens": opens,             # 시가
                            "highs": highs,             # 고가
                            "lows": lows,               # 저가
                            "volumes": volumes,         # 거래량
                            "dates": dates,             # 날짜
                            "data_count": len(prices),
                            "latest_price": prices[-1] if prices else 0,
                            "retrieved_at": datetime.now()
                        }
                    else:
                        print(f"키움 API 호출 실패: {result}")
                        return None
                        
                except Exception as api_error:
                    print(f"키움 API 호출 중 오류: {api_error}")
                    # API 오류 시 None 반환 (실제 데이터만 사용)
                    return None
            
            # Rate limiting과 재시도 로직이 적용된 API 호출
            result = await rate_limiter.execute_with_retry(
                f'chart_data_{symbol}', 
                _get_chart_data
            )
            
            return result
            
        except Exception as e:
            print(f"차트 데이터 조회 실패 - 종목: {symbol}, 오류: {e}")
            # 오류 시 None 반환 (실제 데이터만 사용)
            return None
    
    
    def calculate_confidence(self, signal_strength: float, market_condition: str = "normal") -> float:
        """
        신호 신뢰도 계산
        
        Args:
            signal_strength: 신호 강도 (0.0-1.0)
            market_condition: 시장 상황 ("bull", "bear", "normal")
            
        Returns:
            계산된 신뢰도 (0.0-1.0)
        """
        base_confidence = signal_strength
        
        # 시장 상황에 따른 신뢰도 조정
        market_multiplier = {
            "bull": 1.1,      # 상승장에서는 매수 신호 신뢰도 증가
            "bear": 0.9,      # 하락장에서는 신뢰도 감소
            "normal": 1.0     # 보통 시장
        }.get(market_condition, 1.0)
        
        confidence = min(base_confidence * market_multiplier, 1.0)
        return round(confidence, 3)
    
    def create_signal(
        self, 
        symbol: str, 
        signal_type: SignalType, 
        current_price: Decimal,
        confidence: float,
        reason: str,
        strength: SignalStrength = SignalStrength.MODERATE,
        target_price: Optional[Decimal] = None,
        stop_loss: Optional[Decimal] = None
    ) -> TradingSignal:
        """
        매매신호 객체 생성
        
        Args:
            symbol: 종목코드
            signal_type: 신호 타입 (BUY, SELL, HOLD, CLOSE)
            current_price: 현재가
            confidence: 신뢰도
            reason: 신호 발생 이유
            strength: 신호 강도
            target_price: 목표가 (선택)
            stop_loss: 손절가 (선택)
            
        Returns:
            TradingSignal 객체
        """
        # 손절가/익절가 자동 계산 (설정되지 않은 경우)
        if signal_type == SignalType.BUY:
            if not stop_loss:
                stop_loss = current_price * (1 - Decimal(str(self.config.stop_loss_ratio)))
            if not target_price:
                target_price = current_price * (1 + Decimal(str(self.config.take_profit_ratio)))
        elif signal_type == SignalType.SELL:
            if not stop_loss:
                stop_loss = current_price * (1 + Decimal(str(self.config.stop_loss_ratio)))
            if not target_price:
                target_price = current_price * (1 - Decimal(str(self.config.take_profit_ratio)))
        
        return TradingSignal(
            strategy_name=self.name,
            symbol=symbol,
            signal_type=signal_type,
            strength=strength,
            current_price=current_price,
            target_price=target_price,
            stop_loss=stop_loss,
            confidence=confidence,
            reason=reason,
            timestamp=datetime.now(),
            valid_until=datetime.now() + timedelta(minutes=30)  # 30분 유효
        )
    
    def is_market_hours(self) -> bool:
        """
        장중 시간 확인
        
        Returns:
            장중이면 True, 장외시간이면 False
        """
        now = datetime.now()
        
        # 주말 확인 (토요일=5, 일요일=6)
        if now.weekday() >= 5:
            return False
        
        # 평일 장중 시간 확인 (9:00 ~ 15:30)
        market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        return market_open <= now <= market_close
    
    def should_execute_signal(self, signal: TradingSignal) -> bool:
        """
        신호를 실행해야 하는지 판단
        
        Args:
            signal: 매매신호 객체
            
        Returns:
            실행해야 하면 True, 아니면 False
        """
        # 기본 검증
        if not signal.should_execute(self.config.min_confidence):
            return False
        
        # 장중 시간 확인 (모의투자가 아닌 경우)
        if not self.config.dry_run and not self.is_market_hours():
            return False
        
        # 전략이 비활성화된 경우
        if not self.enabled:
            return False
        
        return True
    
    def get_strategy_info(self) -> Dict:
        """
        전략 정보 반환
        
        Returns:
            전략 정보 딕셔너리
        """
        return {
            "name": self.name,
            "type": self.config.strategy_type.value,
            "enabled": self.enabled,
            "target_symbols": self.config.target_symbols,
            "risk_level": self.config.risk_level.value,
            "execution_interval": self.config.execution_interval,
            "min_confidence": self.config.min_confidence,
            "dry_run": self.config.dry_run
        }