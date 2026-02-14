"""자동매매 엔진 - 시작/중지/상태 관리"""

import asyncio
import logging
from datetime import date, datetime

from app.config import Settings, StrategyType
from app.kis.auth import KISAuth
from app.kis.client import KISClient
from app.kis.market import KISMarketClient
from app.kis.order import KISOrderClient
from app.models import (
    EngineStatus,
    OrderResult,
    SignalType,
    TradingSignal,
    TradingStatus,
)
from app.trading.calendar import is_market_open, is_trading_day
from app.trading.strategy import (
    evaluate_bollinger_signal,
    evaluate_signal,
    evaluate_signal_with_filters,
)

logger = logging.getLogger(__name__)

# 최대 시그널/주문 이력 보관 개수
MAX_HISTORY = 50


class TradingEngine:
    def __init__(self, settings: Settings):
        self.settings = settings

        # 공유 HTTP 클라이언트
        self._client = KISClient(timeout=settings.kis.timeout)

        self.auth = KISAuth(settings.kis, self._client)
        self.market = KISMarketClient(self.auth)
        self.order = KISOrderClient(self.auth)

        self._status = EngineStatus.STOPPED
        self._task: asyncio.Task | None = None
        self._watch_symbols: list[str] = []
        self._signals: list[TradingSignal] = []
        self._orders: list[OrderResult] = []
        self._started_at: datetime | None = None
        self._loop_count: int = 0

        # 종목별 주문 잠금 (잔고 확인 → 주문 실행 원자성 보장)
        self._order_locks: dict[str, asyncio.Lock] = {}

        # 에러 복구
        self._consecutive_errors: int = 0

        # 일일 거래 카운터 (데이트레이딩)
        self._daily_trade_count: dict[str, int] = {}  # symbol → 당일 매수 횟수
        self._trade_count_date: date | None = None  # 카운터 기준일

    def get_status(self) -> TradingStatus:
        return TradingStatus(
            status=self._status,
            watch_symbols=self._watch_symbols,
            recent_signals=self._signals[-MAX_HISTORY:],
            recent_orders=self._orders[-MAX_HISTORY:],
            started_at=self._started_at,
            loop_count=self._loop_count,
        )

    async def start(self, symbols: list[str] | None = None) -> None:
        if self._status == EngineStatus.RUNNING:
            logger.warning("엔진이 이미 실행 중입니다.")
            return

        # 재시작 시 HTTP 클라이언트 재생성
        if self._client.is_closed:
            self._client = KISClient(timeout=self.settings.kis.timeout)
            self.auth._client = self._client

        self._watch_symbols = symbols or self.settings.trading.watch_symbols
        self._consecutive_errors = 0

        # 시작 시 잔고 조회로 연결 상태 확인 (실패 시 시작 차단 + 리소스 정리)
        try:
            await self.order.get_balance()  # 연결 검증 (반환값 무시)
        except Exception:
            await self._client.close()
            raise
        logger.info("KIS API 연결 확인 완료")

        self._status = EngineStatus.RUNNING
        self._started_at = datetime.now()
        self._loop_count = 0
        logger.info("자동매매 시작: %s", self._watch_symbols)

        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        if self._status == EngineStatus.STOPPED:
            return

        self._status = EngineStatus.STOPPED
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        # HTTP 클라이언트 정리
        await self._client.close()
        logger.info("자동매매 중지")

    async def _run_loop(self) -> None:
        interval = self.settings.trading.trading_interval
        try:
            while self._status == EngineStatus.RUNNING:
                try:
                    await self._tick()
                    self._loop_count += 1
                    # 성공 시 에러 카운터 리셋
                    self._consecutive_errors = 0
                except Exception:
                    logger.exception("매매 루프 tick 오류")
                    self._consecutive_errors += 1
                    max_errors = self.settings.trading.max_consecutive_errors
                    if self._consecutive_errors >= max_errors:
                        logger.warning(
                            "연속 %d회 오류 — 엔진 정지", self._consecutive_errors
                        )
                        self._status = EngineStatus.STOPPED
                        break

                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("매매 루프 취소됨")

    def _reset_daily_counter_if_needed(self, today: date) -> None:
        """날짜 변경 시 카운터 초기화"""
        if self._trade_count_date != today:
            self._daily_trade_count.clear()
            self._trade_count_date = today

    def _can_buy(self, symbol: str) -> bool:
        """종목당 일일 매수 횟수 제한 확인"""
        max_trades = self.settings.trading.max_daily_trades
        return self._daily_trade_count.get(symbol, 0) < max_trades

    def _is_active_window(self, hhmm: int) -> bool:
        """현재 시각이 활성 매매 시간대인지 확인"""
        windows = self.settings.trading.active_trading_windows
        if not windows:
            return True  # 빈 리스트면 전 구간 매매
        return any(start <= hhmm < end for start, end in windows)

    async def _force_close_all(self, now: datetime) -> None:
        """보유 중인 모든 포지션 강제 매도 (장 마감 전)"""
        positions, _ = await self.order.get_balance()
        closed = 0
        for pos in positions:
            if pos.quantity > 0:
                result = await self.order.sell(pos.symbol, pos.quantity)
                order_result = OrderResult(
                    symbol=pos.symbol,
                    side="sell",
                    quantity=pos.quantity,
                    order_no=result.get("order_no", ""),
                    message=result.get("message", ""),
                    success=result.get("success", False),
                    timestamp=now,
                )
                self._orders.append(order_result)
                closed += 1
        if closed > 0:
            logger.info("장 마감 강제 청산 완료: %d종목", closed)

    async def _tick(self) -> None:
        """한 사이클 실행: 시세 조회 → 전략 판단 → 주문"""
        now = datetime.now()

        # 매매일/장시간 체크
        if not is_market_open(now):
            if not is_trading_day(now.date()):
                logger.debug("매매일 아님: %s", now.strftime("%Y-%m-%d (%a)"))
            else:
                logger.debug("장 시간 외: %s", now.strftime("%H:%M:%S"))
            return

        # 일일 카운터 초기화
        self._reset_daily_counter_if_needed(now.date())

        current_hhmm = now.hour * 100 + now.minute

        # 장 마감 청산: force_close_minute 이후 보유 포지션 전량 매도
        if current_hhmm >= self.settings.trading.force_close_minute:
            await self._force_close_all(now)
            return

        # 활성 매매 시간대 체크
        if not self._is_active_window(current_hhmm):
            logger.debug("비활성 시간대: %02d:%02d", now.hour, now.minute)
            return

        fail_count = 0
        for symbol in self._watch_symbols:
            try:
                strategy_type = self.settings.trading.strategy_type

                if strategy_type == StrategyType.BOLLINGER:
                    # 볼린저밴드 전략: 항상 분봉 사용
                    chart = await self.market.get_minute_chart(
                        symbol,
                        minutes=self.settings.trading.minute_chart_lookback,
                    )
                    price_info = await self.market.get_current_price(symbol)

                    result = evaluate_bollinger_signal(
                        chart,
                        period=self.settings.trading.bollinger_period,
                        num_std=self.settings.trading.bollinger_num_std,
                    )
                    signal_type = result.signal
                    signal = TradingSignal(
                        symbol=symbol,
                        signal=signal_type,
                        current_price=price_info.current_price,
                        timestamp=now,
                        upper_band=result.upper_band,
                        middle_band=result.middle_band,
                        lower_band=result.lower_band,
                    )

                    logger.info(
                        "[%s] %s | 현재가=%d, BB(%.0f/%.0f/%.0f)",
                        symbol,
                        signal_type.value,
                        price_info.current_price,
                        result.upper_band,
                        result.middle_band,
                        result.lower_band,
                    )

                else:
                    # SMA 크로스오버 전략 (기존 로직)
                    if self.settings.trading.use_minute_chart:
                        chart = await self.market.get_minute_chart(
                            symbol,
                            minutes=self.settings.trading.minute_chart_lookback,
                        )
                        short_period = self.settings.trading.minute_short_period
                        long_period = self.settings.trading.minute_long_period
                    else:
                        short_period = self.settings.trading.short_ma_period
                        long_period = self.settings.trading.long_ma_period
                        chart = await self.market.get_daily_chart(
                            symbol, days=long_period + 10
                        )
                    price_info = await self.market.get_current_price(symbol)

                    if self.settings.trading.use_advanced_strategy:
                        result = evaluate_signal_with_filters(
                            chart,
                            short_period,
                            long_period,
                            rsi_period=self.settings.trading.rsi_period,
                            rsi_overbought=self.settings.trading.rsi_overbought,
                            rsi_oversold=self.settings.trading.rsi_oversold,
                            volume_ma_period=self.settings.trading.volume_ma_period,
                            obv_ma_period=self.settings.trading.obv_ma_period,
                        )
                        signal_type = result.signal
                        short_ma = result.short_ma
                        long_ma = result.long_ma

                        signal = TradingSignal(
                            symbol=symbol,
                            signal=signal_type,
                            short_ma=short_ma,
                            long_ma=long_ma,
                            current_price=price_info.current_price,
                            timestamp=now,
                            rsi=result.rsi,
                            volume_confirmed=result.volume_confirmed,
                            obv_confirmed=result.obv_confirmed,
                            raw_signal=result.raw_signal,
                        )
                    else:
                        signal_type, short_ma, long_ma = evaluate_signal(
                            chart, short_period, long_period
                        )

                        signal = TradingSignal(
                            symbol=symbol,
                            signal=signal_type,
                            short_ma=short_ma,
                            long_ma=long_ma,
                            current_price=price_info.current_price,
                            timestamp=now,
                        )

                    logger.info(
                        "[%s] %s | 현재가=%d, SMA%d=%.0f, SMA%d=%.0f",
                        symbol,
                        signal_type.value,
                        price_info.current_price,
                        short_period,
                        short_ma,
                        long_period,
                        long_ma,
                    )

                self._signals.append(signal)

                # 매매 실행 (데이트레이딩 제한 적용)
                if signal_type == SignalType.BUY:
                    # 15:00 이후 신규 매수 금지
                    if current_hhmm >= self.settings.trading.no_new_buy_minute:
                        logger.info(
                            "[%s] %02d:%02d — 신규 매수 금지 시간",
                            symbol,
                            now.hour,
                            now.minute,
                        )
                    elif not self._can_buy(symbol):
                        logger.info(
                            "[%s] 일일 매수 한도 초과 (%d/%d)",
                            symbol,
                            self._daily_trade_count.get(symbol, 0),
                            self.settings.trading.max_daily_trades,
                        )
                    else:
                        await self._execute_buy(
                            symbol, price_info.current_price, now
                        )
                elif signal_type == SignalType.SELL:
                    await self._execute_sell(symbol, now)

            except Exception:
                logger.exception("[%s] 처리 중 오류", symbol)
                fail_count += 1

        # 1개라도 실패하면 예외를 올려 _run_loop 에러 카운터에 반영
        if fail_count > 0:
            raise RuntimeError(
                f"종목 처리 실패: {fail_count}/{len(self._watch_symbols)}개"
            )

    def _get_order_lock(self, symbol: str) -> asyncio.Lock:
        """종목별 주문 Lock 반환 (없으면 생성)"""
        if symbol not in self._order_locks:
            self._order_locks[symbol] = asyncio.Lock()
        return self._order_locks[symbol]

    async def _execute_buy(
        self, symbol: str, current_price: int, now: datetime
    ) -> None:
        """매수 주문 (잔고 확인 → 동적 수량 계산 → 주문을 Lock으로 원자적 실행)"""
        async with self._get_order_lock(symbol):
            positions, _ = await self.order.get_balance()
            for pos in positions:
                if pos.symbol == symbol and pos.quantity > 0:
                    logger.info(
                        "[%s] 이미 보유 중 (%d주) — 매수 생략", symbol, pos.quantity
                    )
                    return

            if current_price <= 0:
                return

            # 동적 수량 계산: 목표금액 / 현재가, min~max 범위 내
            target = self.settings.trading.target_order_amount
            min_qty = self.settings.trading.min_quantity
            max_qty = self.settings.trading.max_quantity
            quantity = max(min_qty, min(target // current_price, max_qty))

            result = await self.order.buy(symbol, quantity)

            order_result = OrderResult(
                symbol=symbol,
                side="buy",
                quantity=quantity,
                order_no=result.get("order_no", ""),
                message=result.get("message", ""),
                success=result.get("success", False),
                timestamp=now,
            )
            self._orders.append(order_result)

            # 매수 성공 시 일일 거래 카운터 증가
            if order_result.success:
                self._daily_trade_count[symbol] = (
                    self._daily_trade_count.get(symbol, 0) + 1
                )

    async def _execute_sell(self, symbol: str, now: datetime) -> None:
        """보유 종목 전량 매도 (잔고 확인 → 주문을 Lock으로 원자적 실행)"""
        async with self._get_order_lock(symbol):
            positions, _ = await self.order.get_balance()
            for pos in positions:
                if pos.symbol == symbol and pos.quantity > 0:
                    result = await self.order.sell(symbol, pos.quantity)

                    order_result = OrderResult(
                        symbol=symbol,
                        side="sell",
                        quantity=pos.quantity,
                        order_no=result.get("order_no", ""),
                        message=result.get("message", ""),
                        success=result.get("success", False),
                        timestamp=now,
                    )
                    self._orders.append(order_result)
                    return

            logger.info("[%s] 보유 수량 없음 — 매도 생략", symbol)

