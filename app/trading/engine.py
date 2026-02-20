"""자동매매 엔진 - 시작/중지/상태 관리"""

import asyncio
import logging
from datetime import date, datetime

from app.config import Settings, StrategyConfig, StrategyType
from app.kis.auth import KISAuth
from app.kis.client import KISClient
from app.kis.market import KISMarketClient
from app.kis.order import KISOrderClient
from app.kis.overseas_market import KISOverseasMarketClient
from app.kis.overseas_order import KISOverseasOrderClient
from app.models import (
    EngineStatus,
    EventType,
    MarketType,
    OrderResult,
    Position,
    SignalType,
    TradeEvent,
    TradingSignal,
    TradingStatus,
    detect_market_type,
)
from app.trading.calendar import is_market_open, is_trading_day, is_us_market_open
from app.trading.journal import TradingJournal
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
        self.us_market = KISOverseasMarketClient(self.auth)
        self.us_order = KISOverseasOrderClient(self.auth)

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

        # 활성 시장 (None=전체, DOMESTIC/US 개별)
        self._active_market: MarketType | None = None

        # 자동 국면 감지
        self._current_regime: MarketRegime | None = None
        self._regime_checked_date: date | None = None

        # 매매 저널
        self._journal = TradingJournal(log_dir=settings.trading.journal_dir)

    @property
    def journal(self) -> TradingJournal:
        return self._journal

    def _get_exchange(self, symbol: str) -> str | None:
        """US 심볼의 거래소 코드 반환 (설정 또는 기본 NAS)"""
        return self.settings.trading.us_symbol_exchanges.get(symbol, "NAS")

    def get_status(self) -> TradingStatus:
        return TradingStatus(
            status=self._status,
            watch_symbols=self._watch_symbols,
            recent_signals=self._signals[-MAX_HISTORY:],
            recent_orders=self._orders[-MAX_HISTORY:],
            started_at=self._started_at,
            loop_count=self._loop_count,
            current_regime=self._current_regime.value if self._current_regime else None,
            active_market=self._active_market.value if self._active_market else "all",
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
        self._journal.log_event(TradeEvent.engine_event(
            EventType.STRATEGY_CHANGE,
            f"{old_type.value} -> {config.strategy_type.value}",
        ))

    async def start(
        self,
        symbols: list[str] | None = None,
        market: MarketType | None = None,
    ) -> None:
        if self._status == EngineStatus.RUNNING:
            logger.warning("엔진이 이미 실행 중입니다.")
            return

        # 재시작 시 HTTP 클라이언트 재생성
        if self._client.is_closed:
            self._client = KISClient(timeout=self.settings.kis.timeout)
            self.auth._client = self._client

        # 종목 결정: symbols 명시 > market 기반 설정 > 전체 합산
        if symbols is not None:
            self._watch_symbols = symbols
        elif market == MarketType.DOMESTIC:
            self._watch_symbols = list(self.settings.trading.watch_symbols)
        elif market == MarketType.US:
            self._watch_symbols = list(self.settings.trading.us_watch_symbols)
        else:
            self._watch_symbols = (
                self.settings.trading.watch_symbols
                + self.settings.trading.us_watch_symbols
            )

        # market 필터: 명시된 경우 해당 시장 종목만 남김
        if symbols is not None and market is not None:
            self._watch_symbols = [
                s for s in self._watch_symbols
                if detect_market_type(s) == market
            ]

        if not self._watch_symbols:
            raise ValueError("감시할 종목이 없습니다.")

        self._active_market = market  # None이면 양쪽 모두
        self._consecutive_errors = 0

        # 시작 시 연결 상태 확인 (실패 시 시작 차단 + 리소스 정리)
        try:
            if market == MarketType.US:
                await self.us_order.get_balance()
            else:
                await self.order.get_balance()
        except Exception:
            await self._client.close()
            raise
        logger.info("KIS API 연결 확인 완료")

        # 보유 포지션 복원 (매수가/고점/매수시각)
        await self._restore_positions(market)

        self._status = EngineStatus.RUNNING
        self._started_at = datetime.now()
        self._loop_count = 0
        logger.info("자동매매 시작: %s", self._watch_symbols)
        self._journal.log_event(TradeEvent.engine_event(
            EventType.ENGINE_START,
            f"symbols={self._watch_symbols}",
            timestamp=self._started_at,
        ))

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
        self._journal.log_event(TradeEvent.engine_event(EventType.ENGINE_STOP))

        # 당일 이벤트가 있으면 일일 리포트 자동 생성
        today = date.today()
        if self._journal.read_events(today):
            self._journal.generate_daily_report(today)

    async def _restore_positions(
        self, market: MarketType | None = None
    ) -> None:
        """보유 포지션에서 매수가/고점/매수시각 복원 (재시작 시 초기화 방지)"""
        all_positions: list[Position] = []
        try:
            if market is None or market == MarketType.DOMESTIC:
                dom_pos, _ = await self.order.get_balance()
                all_positions.extend(dom_pos)
            if market is None or market == MarketType.US:
                us_pos, _ = await self.us_order.get_balance()
                all_positions.extend(us_pos)
        except Exception:
            logger.warning("포지션 복원 중 잔고 조회 실패 — 건너뜀", exc_info=True)
            return

        now = datetime.now()
        watch_set = set(self._watch_symbols)
        restored = 0

        for pos in all_positions:
            if pos.quantity <= 0 or pos.symbol not in watch_set:
                continue
            if pos.symbol in self._entry_prices:
                continue  # 이미 추적 중

            self._entry_prices[pos.symbol] = float(pos.avg_price)
            self._buy_timestamps[pos.symbol] = now
            peak = max(float(pos.avg_price), float(pos.current_price))
            self._peak_prices[pos.symbol] = peak
            restored += 1

            self._journal.log_event(TradeEvent.engine_event(
                EventType.STATE_RESTORE,
                f"{pos.symbol}: avg_price={pos.avg_price}, "
                f"current_price={pos.current_price}, qty={pos.quantity}",
                timestamp=now,
            ))

        if restored > 0:
            logger.info("보유 포지션 %d종목 매수 정보 복원 완료", restored)

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

    async def _force_close_all(
        self, now: datetime, market: MarketType | None = None
    ) -> None:
        """보유 중인 포지션 강제 매도 (장 마감 전). market 지정 시 해당 시장만."""
        all_positions: list = []
        if market is None or market == MarketType.DOMESTIC:
            dom_pos, _ = await self.order.get_balance()
            all_positions.extend(dom_pos)
        if market is None or market == MarketType.US:
            # 감시 종목에 US 심볼이 있을 때만 해외 잔고 조회
            has_us = any(
                detect_market_type(s) == MarketType.US for s in self._watch_symbols
            )
            if has_us:
                us_pos, _ = await self.us_order.get_balance()
                all_positions.extend(us_pos)

        closed = 0
        close_time = now.strftime("%H:%M")
        for pos in all_positions:
            if pos.quantity > 0:
                pos_mkt = detect_market_type(pos.symbol)
                if pos_mkt == MarketType.US:
                    exchange = self._get_exchange(pos.symbol)
                    result = await self.us_order.sell(pos.symbol, pos.quantity, exchange)
                else:
                    result = await self.order.sell(pos.symbol, pos.quantity)
                entry_price = self._entry_prices.get(pos.symbol, 0.0)
                detail = f"장 마감 강제 청산 ({close_time})"
                order_result = OrderResult(
                    symbol=pos.symbol,
                    side="sell",
                    quantity=pos.quantity,
                    order_no=result.get("order_no", ""),
                    message=result.get("message", ""),
                    success=result.get("success", False),
                    timestamp=now,
                    reason="force_close",
                    reason_detail=detail,
                )
                self._orders.append(order_result)
                self._journal.log_event(TradeEvent.from_order(
                    pos.symbol, "sell", pos.quantity, result,
                    "force_close", pos.current_price, entry_price,
                    event_type=EventType.FORCE_CLOSE, timestamp=now,
                    reason_detail=detail,
                ))
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
        mkt = detect_market_type(symbol)

        # 시장별 클라이언트 선택
        if mkt == MarketType.US:
            exchange = self._get_exchange(symbol)
            market_client = self.us_market
            _get_price = lambda: market_client.get_current_price(symbol, exchange)
            _get_minute = lambda mins: market_client.get_minute_chart(symbol, exchange, mins)
            _get_daily = lambda days: market_client.get_daily_chart(symbol, exchange, days)
        else:
            market_client = self.market
            _get_price = lambda: market_client.get_current_price(symbol)
            _get_minute = lambda mins: market_client.get_minute_chart(symbol, mins)
            _get_daily = lambda days: market_client.get_daily_chart(symbol, days)

        if strategy_type == StrategyType.BOLLINGER:
            chart = await _get_minute(cfg.minute_chart_lookback)
            price_info = await _get_price()
            vol_period = cfg.bollinger_volume_ma_period if cfg.bollinger_volume_filter else None
            result = evaluate_bollinger_signal(
                chart,
                period=cfg.bollinger_period,
                num_std=cfg.bollinger_num_std,
                volume_ma_period=vol_period,
                min_bandwidth=cfg.bollinger_min_bandwidth,
            )
            logger.info(
                "[%s] %s | 현재가=%.0f, BB(%.0f/%.0f/%.0f), vol_ok=%s | %s",
                symbol, result.signal.value, price_info.current_price,
                result.upper_band, result.middle_band, result.lower_band,
                result.volume_confirmed, result.reason_detail,
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
                reason_detail=result.reason_detail,
            )

        # SMA 크로스오버 전략
        if cfg.use_minute_chart:
            chart = await _get_minute(cfg.minute_chart_lookback)
            short_period = cfg.minute_short_period
            long_period = cfg.minute_long_period
        else:
            short_period = cfg.short_ma_period
            long_period = cfg.long_ma_period
            chart = await _get_daily(long_period + 10)
        price_info = await _get_price()

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
                reason_detail=result.reason_detail,
            )
        else:
            signal_type, short_ma, long_ma, reason_detail = evaluate_signal(
                chart, short_period, long_period
            )
            signal = TradingSignal(
                symbol=symbol,
                signal=signal_type,
                short_ma=short_ma,
                long_ma=long_ma,
                current_price=price_info.current_price,
                timestamp=now,
                reason_detail=reason_detail,
            )

        logger.info(
            "[%s] %s | 현재가=%.0f, SMA%d=%.0f, SMA%d=%.0f | %s",
            symbol, signal.signal.value, price_info.current_price,
            short_period, signal.short_ma, long_period, signal.long_ma,
            signal.reason_detail,
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

        old_kr = REGIME_KR.get(old_regime, "없음") if old_regime else "초기"
        new_kr = REGIME_KR[regime]
        logger.info("국면 변경 감지: %s → %s", old_kr, new_kr)
        self._journal.log_event(TradeEvent.engine_event(
            EventType.REGIME_CHANGE,
            f"{old_kr} -> {new_kr}",
            timestamp=now,
        ))

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

        # 활성 시장만 체크 (_active_market 기반)
        am = self._active_market
        kr_open = is_market_open(now) if am in (None, MarketType.DOMESTIC) else False
        us_open = is_us_market_open(now) if am in (None, MarketType.US) else False

        if not kr_open and not us_open:
            logger.debug("어느 시장도 열려있지 않음: %s", now.strftime("%H:%M:%S"))
            return

        # 일일 카운터 초기화
        self._reset_daily_counter_if_needed(now.date())

        # 자동 국면 감지 (하루 1회, 국내 장 시간에만)
        cfg = self.settings.trading
        if kr_open and cfg.auto_regime and self._regime_checked_date != now.date():
            await self._check_and_switch_regime(now)
            self._regime_checked_date = now.date()

        current_hhmm = now.hour * 100 + now.minute

        # 국내 장 마감 청산: force_close_minute 이후 국내 보유 포지션 전량 매도
        if kr_open and current_hhmm >= self.settings.trading.force_close_minute:
            await self._force_close_all(now, market=MarketType.DOMESTIC)
            kr_open = False  # 이번 tick에서 국내 종목 더 이상 처리 안 함

        fail_count = 0
        for symbol in self._watch_symbols:
            mkt = detect_market_type(symbol)

            # 해당 시장이 열려있지 않으면 스킵
            if mkt == MarketType.DOMESTIC and not kr_open:
                continue
            if mkt == MarketType.US and not us_open:
                continue

            # 국내 종목: 활성 매매 시간대 체크 (시세 조회 자체를 스킵)
            if mkt == MarketType.DOMESTIC and not self._is_active_window(current_hhmm):
                logger.debug("[%s] 비활성 시간대: %02d:%02d", symbol, now.hour, now.minute)
                continue

            try:
                signal = await self._evaluate_strategy(symbol, now)
                self._signals.append(signal)
                self._journal.log_event(TradeEvent.from_signal(signal))

                # 현재가 0 → 시세 이상: 매매 판단 스킵
                if signal.current_price <= 0:
                    logger.warning("[%s] 현재가 0 — 매매 판단 스킵", symbol)
                    continue

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
                            detail = (
                                f"트레일링 스탑: 고점 {peak:,.0f} → "
                                f"현재가 {signal.current_price:,.0f} "
                                f"(고점 대비 -{drop_pct:.1f}%)"
                            )
                            logger.info("[%s] %s", symbol, detail)
                            await self._execute_sell(
                                symbol, now,
                                reason="trailing_stop",
                                reason_detail=detail,
                            )
                            continue

                # SMA 크로스오버: 리스크 체크 (stop-loss / max-holding)
                if cfg.strategy_type == StrategyType.SMA_CROSSOVER:
                    entry_price = self._entry_prices.get(symbol, 0.0)
                    # stop-loss
                    if cfg.stop_loss_pct > 0 and entry_price > 0:
                        loss_pct = (entry_price - signal.current_price) / entry_price * 100
                        if loss_pct >= cfg.stop_loss_pct:
                            detail = (
                                f"손절 매도: 매수가 {entry_price:,.0f} → "
                                f"현재가 {signal.current_price:,.0f} "
                                f"(손실 -{loss_pct:.1f}%)"
                            )
                            logger.info("[%s] %s", symbol, detail)
                            await self._execute_sell(
                                symbol, now,
                                reason="stop_loss",
                                reason_detail=detail,
                            )
                            continue
                    # max-holding
                    if cfg.max_holding_days > 0 and symbol in self._buy_timestamps:
                        buy_ts = self._buy_timestamps[symbol]
                        days_held = (now - buy_ts).days
                        if days_held >= cfg.max_holding_days:
                            detail = (
                                f"보유기간 초과: 매수일 {buy_ts.strftime('%m/%d')} → "
                                f"현재 {now.strftime('%m/%d')} "
                                f"({days_held}일 보유, 한도 {cfg.max_holding_days}일)"
                            )
                            logger.info("[%s] %s", symbol, detail)
                            await self._execute_sell(
                                symbol, now,
                                reason="max_holding",
                                reason_detail=detail,
                            )
                            continue

                # 매매 실행 (데이트레이딩 제한은 국내 종목에만 적용)
                if signal.signal == SignalType.BUY:
                    if mkt == MarketType.DOMESTIC:
                        if current_hhmm >= self.settings.trading.no_new_buy_minute:
                            logger.info(
                                "[%s] %02d:%02d — 신규 매수 금지 시간",
                                symbol, now.hour, now.minute,
                            )
                            continue
                        if not self._can_buy(symbol):
                            logger.info(
                                "[%s] 일일 매수 한도 초과 (%d/%d)",
                                symbol,
                                self._daily_trade_count.get(symbol, 0),
                                self.settings.trading.max_daily_trades,
                            )
                            continue
                    await self._execute_buy(symbol, signal.current_price, now)
                elif signal.signal == SignalType.SELL:
                    await self._execute_sell(
                        symbol, now,
                        reason="signal",
                        reason_detail=signal.reason_detail,
                    )

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
        self, symbol: str, current_price: float, now: datetime
    ) -> None:
        """매수 주문 (잔고 확인 → 동적 수량 계산 → 주문을 Lock으로 원자적 실행)"""
        mkt = detect_market_type(symbol)

        async with self._get_order_lock(symbol):
            # 시장별 잔고 조회
            if mkt == MarketType.US:
                positions, summary = await self.us_order.get_balance()
            else:
                positions, summary = await self.order.get_balance()

            for pos in positions:
                if pos.symbol == symbol and pos.quantity > 0:
                    logger.info(
                        "[%s] 이미 보유 중 (%d주) — 매수 생략", symbol, pos.quantity
                    )
                    return

            if current_price <= 0:
                return

            # 동적 수량 계산 (국내/해외 분리, capital_ratio 공통 적용)
            cfg = self.settings.trading
            if mkt == MarketType.US:
                if cfg.capital_ratio > 0 and summary.deposit > 0:
                    target = summary.deposit * cfg.capital_ratio
                else:
                    target = cfg.us_target_order_amount
                min_qty = cfg.us_min_quantity
                max_qty = cfg.us_max_quantity
            else:
                if cfg.capital_ratio > 0:
                    target = int(summary.deposit * cfg.capital_ratio)
                else:
                    target = cfg.target_order_amount
                min_qty = cfg.min_quantity
                max_qty = cfg.max_quantity
            quantity = max(min_qty, min(int(target // current_price), max_qty))

            # 시장별 주문 실행
            if mkt == MarketType.US:
                exchange = self._get_exchange(symbol)
                result = await self.us_order.buy(symbol, quantity, exchange)
            else:
                result = await self.order.buy(symbol, quantity)

            order_result = OrderResult(
                symbol=symbol,
                side="buy",
                quantity=quantity,
                order_no=result.get("order_no", ""),
                message=result.get("message", ""),
                success=result.get("success", False),
                timestamp=now,
                reason="signal",
            )
            self._orders.append(order_result)
            self._journal.log_event(TradeEvent.from_order(
                symbol, "buy", quantity, result,
                "signal", current_price, current_price, timestamp=now,
            ))

            # 매수 성공 시 일일 거래 카운터 증가 + 매수 정보 기록
            if order_result.success:
                self._daily_trade_count[symbol] = (
                    self._daily_trade_count.get(symbol, 0) + 1
                )
                self._entry_prices[symbol] = float(current_price)
                self._buy_timestamps[symbol] = now
                self._peak_prices[symbol] = float(current_price)

    async def _execute_sell(
        self,
        symbol: str,
        now: datetime,
        reason: str = "signal",
        reason_detail: str = "",
    ) -> None:
        """보유 종목 전량 매도 (잔고 확인 → 주문을 Lock으로 원자적 실행)"""
        mkt = detect_market_type(symbol)

        async with self._get_order_lock(symbol):
            if mkt == MarketType.US:
                positions, _ = await self.us_order.get_balance()
            else:
                positions, _ = await self.order.get_balance()

            for pos in positions:
                if pos.symbol == symbol and pos.quantity > 0:
                    if mkt == MarketType.US:
                        exchange = self._get_exchange(symbol)
                        result = await self.us_order.sell(symbol, pos.quantity, exchange)
                    else:
                        result = await self.order.sell(symbol, pos.quantity)
                    entry_price = self._entry_prices.get(symbol, 0.0)

                    order_result = OrderResult(
                        symbol=symbol,
                        side="sell",
                        quantity=pos.quantity,
                        order_no=result.get("order_no", ""),
                        message=result.get("message", ""),
                        success=result.get("success", False),
                        timestamp=now,
                        reason=reason,
                        reason_detail=reason_detail,
                    )
                    self._orders.append(order_result)
                    self._journal.log_event(TradeEvent.from_order(
                        symbol, "sell", pos.quantity, result,
                        reason, pos.current_price, entry_price,
                        timestamp=now, reason_detail=reason_detail,
                    ))
                    # 매도 시 매수 정보 삭제
                    self._entry_prices.pop(symbol, None)
                    self._buy_timestamps.pop(symbol, None)
                    self._peak_prices.pop(symbol, None)
                    return

            logger.info("[%s] 보유 수량 없음 — 매도 생략", symbol)

