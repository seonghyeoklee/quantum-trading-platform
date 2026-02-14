"""자동매매 엔진 - 시작/중지/상태 관리"""

import asyncio
import logging
from datetime import date, datetime

from app.config import Settings, StrategyConfig, StrategyType
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
from app.trading.regime import MarketRegime, REGIME_KR, detect_current_regime
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

        # 리스크 관리 (SMA 크로스오버 전략용)
        self._entry_prices: dict[str, float] = {}      # 종목별 매수가
        self._buy_timestamps: dict[str, datetime] = {}  # 종목별 매수 시각
        self._peak_prices: dict[str, float] = {}        # 종목별 고점 (트레일링 스탑용)

        # 자동 국면 감지
        self._current_regime: MarketRegime | None = None
        self._regime_checked_date: date | None = None

    def get_status(self) -> TradingStatus:
        return TradingStatus(
            status=self._status,
            watch_symbols=self._watch_symbols,
            recent_signals=self._signals[-MAX_HISTORY:],
            recent_orders=self._orders[-MAX_HISTORY:],
            started_at=self._started_at,
            loop_count=self._loop_count,
            current_regime=self._current_regime.value if self._current_regime else None,
        )

    def get_strategy_config(self) -> StrategyConfig:
        """현재 전략 설정 조회"""
        cfg = self.settings.trading
        return StrategyConfig(
            strategy_type=cfg.strategy_type,
            short_ma_period=cfg.short_ma_period,
            long_ma_period=cfg.long_ma_period,
            use_advanced_strategy=cfg.use_advanced_strategy,
            rsi_period=cfg.rsi_period,
            rsi_overbought=cfg.rsi_overbought,
            rsi_oversold=cfg.rsi_oversold,
            volume_ma_period=cfg.volume_ma_period,
            obv_ma_period=cfg.obv_ma_period,
            stop_loss_pct=cfg.stop_loss_pct,
            max_holding_days=cfg.max_holding_days,
            bollinger_period=cfg.bollinger_period,
            bollinger_num_std=cfg.bollinger_num_std,
            bollinger_volume_filter=cfg.bollinger_volume_filter,
            use_minute_chart=cfg.use_minute_chart,
            minute_short_period=cfg.minute_short_period,
            minute_long_period=cfg.minute_long_period,
            trailing_stop_pct=cfg.trailing_stop_pct,
            capital_ratio=cfg.capital_ratio,
            auto_regime=cfg.auto_regime,
        )

    def update_strategy(self, config: StrategyConfig) -> None:
        """전략 설정 변경 (재시작 불필요). 다음 tick부터 적용."""
        cfg = self.settings.trading
        old_type = cfg.strategy_type

        cfg.strategy_type = config.strategy_type
        cfg.short_ma_period = config.short_ma_period
        cfg.long_ma_period = config.long_ma_period
        cfg.use_advanced_strategy = config.use_advanced_strategy
        cfg.rsi_period = config.rsi_period
        cfg.rsi_overbought = config.rsi_overbought
        cfg.rsi_oversold = config.rsi_oversold
        cfg.volume_ma_period = config.volume_ma_period
        cfg.obv_ma_period = config.obv_ma_period
        cfg.stop_loss_pct = config.stop_loss_pct
        cfg.max_holding_days = config.max_holding_days
        cfg.bollinger_period = config.bollinger_period
        cfg.bollinger_num_std = config.bollinger_num_std
        cfg.bollinger_volume_filter = config.bollinger_volume_filter
        cfg.use_minute_chart = config.use_minute_chart
        cfg.minute_short_period = config.minute_short_period
        cfg.minute_long_period = config.minute_long_period
        cfg.trailing_stop_pct = config.trailing_stop_pct
        cfg.capital_ratio = config.capital_ratio
        cfg.auto_regime = config.auto_regime

        # 전략 타입 변경 시 매수 정보 초기화 (기존 포지션 추적 무효화)
        if config.strategy_type != old_type:
            cleared = len(self._entry_prices)
            self._entry_prices.clear()
            self._buy_timestamps.clear()
            self._peak_prices.clear()
            if cleared > 0:
                logger.warning(
                    "전략 변경(%s→%s): 매수 추적 정보 %d건 초기화",
                    old_type.value, config.strategy_type.value, cleared,
                )

        logger.info(
            "전략 설정 변경: %s (SMA %d/%d, adv=%s, minute=%s)",
            config.strategy_type.value,
            config.short_ma_period, config.long_ma_period,
            config.use_advanced_strategy, config.use_minute_chart,
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
                self._entry_prices.pop(pos.symbol, None)
                self._buy_timestamps.pop(pos.symbol, None)
                self._peak_prices.pop(pos.symbol, None)
                closed += 1
        if closed > 0:
            logger.info("장 마감 강제 청산 완료: %d종목", closed)

    async def _evaluate_strategy(
        self, symbol: str, now: datetime
    ) -> TradingSignal:
        """전략 평가: 차트 조회 → 시그널 생성 → 로그"""
        cfg = self.settings.trading
        strategy_type = cfg.strategy_type

        if strategy_type == StrategyType.BOLLINGER:
            chart = await self.market.get_minute_chart(
                symbol, minutes=cfg.minute_chart_lookback
            )
            price_info = await self.market.get_current_price(symbol)
            vol_period = cfg.bollinger_volume_ma_period if cfg.bollinger_volume_filter else None
            result = evaluate_bollinger_signal(
                chart,
                period=cfg.bollinger_period,
                num_std=cfg.bollinger_num_std,
                volume_ma_period=vol_period,
            )
            logger.info(
                "[%s] %s | 현재가=%d, BB(%.0f/%.0f/%.0f), vol_ok=%s",
                symbol, result.signal.value, price_info.current_price,
                result.upper_band, result.middle_band, result.lower_band,
                result.volume_confirmed,
            )
            return TradingSignal(
                symbol=symbol,
                signal=result.signal,
                current_price=price_info.current_price,
                timestamp=now,
                upper_band=result.upper_band,
                middle_band=result.middle_band,
                lower_band=result.lower_band,
                volume_confirmed=result.volume_confirmed,
            )

        # SMA 크로스오버 전략
        if cfg.use_minute_chart:
            chart = await self.market.get_minute_chart(
                symbol, minutes=cfg.minute_chart_lookback
            )
            short_period = cfg.minute_short_period
            long_period = cfg.minute_long_period
        else:
            short_period = cfg.short_ma_period
            long_period = cfg.long_ma_period
            chart = await self.market.get_daily_chart(
                symbol, days=long_period + 10
            )
        price_info = await self.market.get_current_price(symbol)

        if cfg.use_advanced_strategy:
            result = evaluate_signal_with_filters(
                chart, short_period, long_period,
                rsi_period=cfg.rsi_period,
                rsi_overbought=cfg.rsi_overbought,
                rsi_oversold=cfg.rsi_oversold,
                volume_ma_period=cfg.volume_ma_period,
                obv_ma_period=cfg.obv_ma_period,
            )
            signal = TradingSignal(
                symbol=symbol,
                signal=result.signal,
                short_ma=result.short_ma,
                long_ma=result.long_ma,
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
            symbol, signal.signal.value, price_info.current_price,
            short_period, signal.short_ma, long_period, signal.long_ma,
        )
        return signal

    async def _detect_regime(self) -> MarketRegime | None:
        """기준 종목 일봉으로 현재 시장 국면 감지"""
        symbol = self.settings.trading.regime_reference_symbol
        chart = await self.market.get_daily_chart(symbol, days=130)
        if len(chart) < 120:
            logger.warning("국면 판별 데이터 부족: %d일 (최소 120일)", len(chart))
            return None
        closes = [float(c.close) for c in chart]
        info = detect_current_regime(closes)
        if info is None:
            return None
        return info.regime

    async def _check_and_switch_regime(self, now: datetime) -> None:
        """국면 감지 후 변경 시 최적 전략으로 자동 전환"""
        regime = await self._detect_regime()
        if regime is None:
            return

        old_regime = self._current_regime
        self._current_regime = regime

        if regime == old_regime:
            return

        logger.info(
            "국면 변경 감지: %s → %s",
            REGIME_KR.get(old_regime, "없음") if old_regime else "초기",
            REGIME_KR[regime],
        )

        # 국면별 전략 매핑 (히트맵 분석 결과 기반)
        if regime in (MarketRegime.STRONG_BULL, MarketRegime.BULL):
            config = StrategyConfig(
                strategy_type=StrategyType.SMA_CROSSOVER,
                use_advanced_strategy=True,
                stop_loss_pct=5.0,
                max_holding_days=20,
                auto_regime=True,
            )
        else:
            # sideways, bear, strong_bear → 볼린저
            config = StrategyConfig(
                strategy_type=StrategyType.BOLLINGER,
                auto_regime=True,
            )

        self.update_strategy(config)
        logger.info(
            "국면(%s) 기반 전략 전환: %s",
            REGIME_KR[regime], config.strategy_type.value,
        )

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

        # 자동 국면 감지 (하루 1회)
        cfg = self.settings.trading
        if cfg.auto_regime and self._regime_checked_date != now.date():
            await self._check_and_switch_regime(now)
            self._regime_checked_date = now.date()

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
                signal = await self._evaluate_strategy(symbol, now)
                self._signals.append(signal)

                # 고점 갱신 (보유 중인 종목)
                cfg = self.settings.trading
                if symbol in self._entry_prices:
                    self._peak_prices[symbol] = max(
                        self._peak_prices.get(symbol, 0), float(signal.current_price)
                    )

                # 트레일링 스탑 (전략 무관)
                if cfg.trailing_stop_pct > 0 and symbol in self._peak_prices:
                    peak = self._peak_prices[symbol]
                    if peak > 0:
                        drop_pct = (peak - signal.current_price) / peak * 100
                        if drop_pct >= cfg.trailing_stop_pct:
                            logger.info(
                                "[%s] 트레일링 스탑: 고점=%.0f, 현재가=%d, 하락=%.1f%%",
                                symbol, peak, signal.current_price, drop_pct,
                            )
                            await self._execute_sell(symbol, now)
                            continue

                # SMA 크로스오버: 리스크 체크 (stop-loss / max-holding)
                if cfg.strategy_type == StrategyType.SMA_CROSSOVER and symbol in self._entry_prices:
                    entry_price = self._entry_prices[symbol]
                    # stop-loss
                    if cfg.stop_loss_pct > 0:
                        loss_pct = (entry_price - signal.current_price) / entry_price * 100
                        if loss_pct >= cfg.stop_loss_pct:
                            logger.info(
                                "[%s] 손절 매도: 매수가=%.0f, 현재가=%d, 손실=%.1f%%",
                                symbol, entry_price, signal.current_price, loss_pct,
                            )
                            await self._execute_sell(symbol, now)
                            continue
                    # max-holding
                    if cfg.max_holding_days > 0 and symbol in self._buy_timestamps:
                        days_held = (now - self._buy_timestamps[symbol]).days
                        if days_held >= cfg.max_holding_days:
                            logger.info(
                                "[%s] 보유기간 초과 매도: %d일 보유 (한도 %d일)",
                                symbol, days_held, cfg.max_holding_days,
                            )
                            await self._execute_sell(symbol, now)
                            continue

                # 매매 실행 (데이트레이딩 제한 적용)
                if signal.signal == SignalType.BUY:
                    if current_hhmm >= self.settings.trading.no_new_buy_minute:
                        logger.info(
                            "[%s] %02d:%02d — 신규 매수 금지 시간",
                            symbol, now.hour, now.minute,
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
                            symbol, signal.current_price, now
                        )
                elif signal.signal == SignalType.SELL:
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
            positions, summary = await self.order.get_balance()
            for pos in positions:
                if pos.symbol == symbol and pos.quantity > 0:
                    logger.info(
                        "[%s] 이미 보유 중 (%d주) — 매수 생략", symbol, pos.quantity
                    )
                    return

            if current_price <= 0:
                return

            # 동적 수량 계산
            cfg = self.settings.trading
            if cfg.capital_ratio > 0:
                target = int(summary.deposit * cfg.capital_ratio)
            else:
                target = cfg.target_order_amount
            min_qty = cfg.min_quantity
            max_qty = cfg.max_quantity
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

            # 매수 성공 시 일일 거래 카운터 증가 + 매수 정보 기록
            if order_result.success:
                self._daily_trade_count[symbol] = (
                    self._daily_trade_count.get(symbol, 0) + 1
                )
                self._entry_prices[symbol] = float(current_price)
                self._buy_timestamps[symbol] = now
                self._peak_prices[symbol] = float(current_price)

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
                    # 매도 시 매수 정보 삭제
                    self._entry_prices.pop(symbol, None)
                    self._buy_timestamps.pop(symbol, None)
                    self._peak_prices.pop(symbol, None)
                    return

            logger.info("[%s] 보유 수량 없음 — 매도 생략", symbol)

