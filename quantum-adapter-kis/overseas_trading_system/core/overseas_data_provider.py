"""
해외주식 데이터 제공자
KIS API를 통한 해외주식 실시간 데이터 수집
환율 정보, 거래시간 관리 포함
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone
from typing import Optional, Dict, List
import requests

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from overseas_trading_system.core.overseas_data_types import (
    OverseasMarketData, ExchangeRate, ExchangeType, TradingSession,
    TradingHours, DEFAULT_EXCHANGES, TRADING_HOURS_MAP
)


class OverseasDataProvider:
    """해외주식 실시간 데이터 제공자"""

    def __init__(self):
        self.logger = logging.getLogger("overseas_data_provider")
        self.base_url = "http://localhost:8000"
        self.exchange_map = DEFAULT_EXCHANGES
        self.trading_hours = TRADING_HOURS_MAP

        # 환율 캐시
        self.exchange_rate_cache: Optional[ExchangeRate] = None
        self.rate_update_interval = 60  # 1분마다 환율 업데이트

    async def get_realtime_price(self, symbol: str) -> Optional[OverseasMarketData]:
        """실시간 해외주식 가격 조회"""
        try:
            exchange = self.exchange_map.get(symbol, ExchangeType.NAS)

            # KIS API 호출
            url = f"{self.base_url}/overseas/{exchange.value}/price/{symbol}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                output = data.get('output', {})

                # 현재 환율 조회
                exchange_rate = await self.get_exchange_rate()

                # 거래시간 확인
                trading_hours = self.trading_hours.get(exchange, TradingHours(exchange))
                current_session = trading_hours.get_current_session()

                # OverseasMarketData 생성
                market_data = OverseasMarketData(
                    symbol=symbol,
                    exchange=exchange,
                    timestamp=datetime.now(),
                    current_price=float(output.get('last', 0)),
                    open_price=float(output.get('open', 0)),
                    high_price=float(output.get('high', 0)),
                    low_price=float(output.get('low', 0)),
                    previous_close=float(output.get('base', 0)),
                    volume=int(output.get('tvol', 0)),
                    change=float(output.get('diff', 0)),
                    change_percent=float(output.get('rate', 0)),
                    trading_session=current_session,
                    exchange_rate=exchange_rate
                )

                self.logger.info(f"실시간 데이터 조회 성공: {symbol} ${market_data.current_price}")
                return market_data

            else:
                self.logger.error(f"KIS API 호출 실패 [{symbol}]: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"실시간 데이터 조회 오류 [{symbol}]: {e}")
            return None

    async def get_chart_data(self, symbol: str, period: str = "D", count: int = 100) -> List[OverseasMarketData]:
        """해외주식 차트 데이터 조회"""
        try:
            exchange = self.exchange_map.get(symbol, ExchangeType.NAS)

            # KIS API 호출
            url = f"{self.base_url}/overseas/{exchange.value}/chart/{symbol}"
            params = {
                'period': period,
                'count': count
            }
            response = requests.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                output = data.get('output', [])

                chart_data_list = []
                exchange_rate = await self.get_exchange_rate()

                for item in output:
                    chart_data = OverseasMarketData(
                        symbol=symbol,
                        exchange=exchange,
                        timestamp=datetime.strptime(item.get('stck_bsop_date', ''), '%Y%m%d'),
                        current_price=float(item.get('stck_clpr', 0)),
                        open_price=float(item.get('stck_oprc', 0)),
                        high_price=float(item.get('stck_hgpr', 0)),
                        low_price=float(item.get('stck_lwpr', 0)),
                        volume=int(item.get('cntg_vol', 0)),
                        exchange_rate=exchange_rate
                    )
                    chart_data_list.append(chart_data)

                self.logger.info(f"차트 데이터 조회 성공: {symbol} {len(chart_data_list)}개")
                return chart_data_list

            else:
                self.logger.error(f"차트 데이터 조회 실패 [{symbol}]: {response.status_code}")
                return []

        except Exception as e:
            self.logger.error(f"차트 데이터 조회 오류 [{symbol}]: {e}")
            return []

    async def get_exchange_rate(self, force_update: bool = False) -> Optional[ExchangeRate]:
        """USD/KRW 환율 조회 (캐시 지원)"""
        try:
            # 캐시된 환율이 있고 강제 업데이트가 아닌 경우
            if not force_update and self.exchange_rate_cache:
                cache_age = (datetime.now() - self.exchange_rate_cache.timestamp).seconds
                if cache_age < self.rate_update_interval:
                    return self.exchange_rate_cache

            # KIS API를 통한 환율 조회 (임시로 고정 환율 사용)
            # 실제로는 KIS API의 환율 조회 엔드포인트를 사용해야 함
            current_rate = 1310.0  # USD/KRW 임시 환율

            exchange_rate = ExchangeRate(
                base_currency="USD",
                quote_currency="KRW",
                rate=current_rate,
                timestamp=datetime.now()
            )

            self.exchange_rate_cache = exchange_rate
            self.logger.info(f"환율 업데이트: 1 USD = {current_rate} KRW")

            return exchange_rate

        except Exception as e:
            self.logger.error(f"환율 조회 오류: {e}")
            # 기본 환율 반환
            return ExchangeRate(rate=1300.0, timestamp=datetime.now())

    async def get_market_index(self, index_code: str, exchange: ExchangeType = ExchangeType.NAS) -> Optional[Dict]:
        """시장 지수 조회 (NASDAQ Composite, S&P 500 등)"""
        try:
            url = f"{self.base_url}/overseas/{exchange.value}/index/{index_code}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                output = data.get('output', {})

                index_data = {
                    'index_code': index_code,
                    'exchange': exchange,
                    'current_value': float(output.get('bstp_nmix_prpr', 0)),
                    'change': float(output.get('bstp_nmix_prdy_vrss', 0)),
                    'change_percent': float(output.get('prdy_vrss_sign', 0)),
                    'timestamp': datetime.now()
                }

                self.logger.info(f"지수 조회 성공: {index_code} {index_data['current_value']}")
                return index_data

            else:
                self.logger.error(f"지수 조회 실패 [{index_code}]: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"지수 조회 오류 [{index_code}]: {e}")
            return None

    def get_trading_session(self, exchange: ExchangeType) -> TradingSession:
        """현재 거래 세션 확인"""
        trading_hours = self.trading_hours.get(exchange, TradingHours(exchange))
        return trading_hours.get_current_session()

    def is_market_open(self, exchange: ExchangeType) -> bool:
        """시장 개장 여부"""
        session = self.get_trading_session(exchange)
        return session in [TradingSession.PRE_MARKET, TradingSession.REGULAR, TradingSession.AFTER_HOURS]

    async def get_popular_stocks(self, exchange: ExchangeType = ExchangeType.NAS, count: int = 10) -> List[Dict]:
        """인기 종목 조회"""
        try:
            # 임시로 주요 종목 리스트 반환
            popular_symbols = [
                "TSLA", "AAPL", "NVDA", "MSFT", "GOOGL",
                "AMZN", "META", "NFLX", "AMD", "INTC"
            ][:count]

            popular_stocks = []
            for symbol in popular_symbols:
                market_data = await self.get_realtime_price(symbol)
                if market_data:
                    popular_stocks.append({
                        'symbol': symbol,
                        'current_price': market_data.current_price,
                        'change_percent': market_data.change_percent,
                        'volume': market_data.volume
                    })

            return popular_stocks

        except Exception as e:
            self.logger.error(f"인기 종목 조회 오류: {e}")
            return []

    async def get_pre_market_data(self, symbol: str) -> Optional[Dict]:
        """프리마켓 데이터 조회"""
        try:
            # 프리마켓 전용 엔드포인트가 있다면 사용
            # 현재는 일반 가격 조회 사용
            market_data = await self.get_realtime_price(symbol)

            if market_data and market_data.trading_session == TradingSession.PRE_MARKET:
                return {
                    'symbol': symbol,
                    'pre_market_price': market_data.current_price,
                    'pre_market_change': market_data.change,
                    'pre_market_change_percent': market_data.change_percent,
                    'pre_market_volume': market_data.volume,
                    'timestamp': market_data.timestamp
                }

            return None

        except Exception as e:
            self.logger.error(f"프리마켓 데이터 조회 오류 [{symbol}]: {e}")
            return None

    async def get_after_hours_data(self, symbol: str) -> Optional[Dict]:
        """애프터아워스 데이터 조회"""
        try:
            # 애프터아워스 전용 엔드포인트가 있다면 사용
            market_data = await self.get_realtime_price(symbol)

            if market_data and market_data.trading_session == TradingSession.AFTER_HOURS:
                return {
                    'symbol': symbol,
                    'after_hours_price': market_data.current_price,
                    'after_hours_change': market_data.change,
                    'after_hours_change_percent': market_data.change_percent,
                    'after_hours_volume': market_data.volume,
                    'timestamp': market_data.timestamp
                }

            return None

        except Exception as e:
            self.logger.error(f"애프터아워스 데이터 조회 오류 [{symbol}]: {e}")
            return None

    async def health_check(self) -> bool:
        """KIS API 연결 상태 확인"""
        try:
            url = f"{self.base_url}/health"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Health check 실패: {e}")
            return False


# 테스트 함수
async def test_overseas_data_provider():
    """해외주식 데이터 제공자 테스트"""
    print("=== 해외주식 데이터 제공자 테스트 ===")

    provider = OverseasDataProvider()

    # 1. Tesla 실시간 가격 조회
    print("\n1. Tesla 실시간 가격 조회")
    tsla_data = await provider.get_realtime_price("TSLA")
    if tsla_data:
        print(f"TSLA: ${tsla_data.current_price:.2f} ({tsla_data.change_percent:+.2f}%)")
        print(f"원화: ₩{tsla_data.get_price_krw():,.0f}")
        print(f"거래세션: {tsla_data.trading_session.value}")

    # 2. 환율 조회
    print("\n2. 환율 조회")
    exchange_rate = await provider.get_exchange_rate()
    if exchange_rate:
        print(f"USD/KRW: {exchange_rate.rate:.2f}")

    # 3. 거래시간 확인
    print("\n3. 거래시간 확인")
    session = provider.get_trading_session(ExchangeType.NAS)
    is_open = provider.is_market_open(ExchangeType.NAS)
    print(f"현재 세션: {session.value}")
    print(f"시장 개장: {is_open}")

    # 4. 인기 종목 조회
    print("\n4. 인기 종목 조회")
    popular = await provider.get_popular_stocks(count=5)
    for stock in popular:
        print(f"{stock['symbol']}: ${stock['current_price']:.2f} ({stock['change_percent']:+.2f}%)")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_overseas_data_provider())