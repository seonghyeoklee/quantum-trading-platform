"""자동매매 엔진 - 시작/중지/상태 관리"""

import asyncio
import logging
from datetime import date, datetime

from app.config import AllocationMode, Settings, StrategyConfig, StrategyType
from app.kis.auth import KISAuth
from app.kis.client import KISClient
from app.kis.market import KISMarketClient
from app.kis.order import KISOrderClient
from app.kis.overseas_market import KISOverseasMarketClient
from app.kis.overseas_order import KISOverseasOrderClient
from app.kis.volume_rank import KISVolumeRankClient
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
from app.trading.sector import ScannerPick, SectorScore, get_sector, score_sectors, select_leaders
from app.trading.strategy import (
    compute_atr,
    compute_sma,
    evaluate_bollinger_signal,
    evaluate_breakout_signal,
    evaluate_kama_signal,
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
        self.volume_rank = KISVolumeRankClient(self.auth)

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

        # 분할 매수 트렌치 카운터 (종목별 현재 트렌치 수)
        self._buy_tranche_count: dict[str, int] = {}

        # 매도 후 쿨다운 (종목별 마지막 매도 시각)
        self._sell_timestamps: dict[str, datetime] = {}

        # 활성 시장 (None=전체, DOMESTIC/US 개별)
        self._active_market: MarketType | None = None

        # 강제 청산 중복 방지
        self._force_close_done_date: date | None = None

        # 자동 국면 감지
        self._current_regime: MarketRegime | None = None
        self._regime_checked_date: date | None = None

        # 거래량 가중치 배분
        self._symbol_target_amounts: dict[str, float] = {}  # 종목별 목표금액
        self._volume_weights_date: date | None = None        # 마지막 계산일

        # 섹터 모멘텀 스캐너
        self._scanner_symbols: list[str] = []
        self._scanner_picks: list[ScannerPick] = []
        self._scanner_sector_scores: list[SectorScore] = []
        self._last_scan_time: datetime | None = None

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
            scanner_symbols=list(self._scanner_symbols),
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
            min_profit_pct=cfg.min_profit_pct,
            bollinger_period=cfg.bollinger_period,
            bollinger_num_std=cfg.bollinger_num_std,
            bollinger_volume_filter=cfg.bollinger_volume_filter,
            bollinger_min_bandwidth=cfg.bollinger_min_bandwidth,
            bollinger_min_profit_pct=cfg.bollinger_min_profit_pct,
            bollinger_min_sell_bandwidth=cfg.bollinger_min_sell_bandwidth,
            bollinger_use_middle_exit=cfg.bollinger_use_middle_exit,
            bollinger_obv_filter=cfg.bollinger_obv_filter,
            bollinger_obv_ma_period=cfg.bollinger_obv_ma_period,
            min_sma_gap_pct=cfg.min_sma_gap_pct,
            sell_cooldown_minutes=cfg.sell_cooldown_minutes,
            use_minute_chart=cfg.use_minute_chart,
            minute_short_period=cfg.minute_short_period,
            minute_long_period=cfg.minute_long_period,
            trailing_stop_pct=cfg.trailing_stop_pct,
            trailing_stop_grace_minutes=cfg.trailing_stop_grace_minutes,
            take_profit_pct=cfg.take_profit_pct,
            split_buy_count=cfg.split_buy_count,
            capital_ratio=cfg.capital_ratio,
            use_rsi_divergence=cfg.use_rsi_divergence,
            use_macd_filter=cfg.use_macd_filter,
            macd_fast=cfg.macd_fast,
            macd_slow=cfg.macd_slow,
            macd_signal=cfg.macd_signal,
            bollinger_use_engulfing=cfg.bollinger_use_engulfing,
            bollinger_use_double_pattern=cfg.bollinger_use_double_pattern,
            bollinger_rsi_period=cfg.bollinger_rsi_period,
            bollinger_rsi_overbought=cfg.bollinger_rsi_overbought,
            bollinger_rsi_oversold=cfg.bollinger_rsi_oversold,
            auto_regime=cfg.auto_regime,
            scanner_enabled=cfg.scanner_enabled,
            scanner_interval_minutes=cfg.scanner_interval_minutes,
            scanner_top_sectors=cfg.scanner_top_sectors,
            scanner_max_picks=cfg.scanner_max_picks,
            scanner_min_price=cfg.scanner_min_price,
            scanner_min_volume=cfg.scanner_min_volume,
            scanner_min_change_rate=cfg.scanner_min_change_rate,
            allocation_mode=cfg.allocation_mode,
            total_order_budget=cfg.total_order_budget,
            us_total_order_budget=cfg.us_total_order_budget,
            atr_stop_multiplier=cfg.atr_stop_multiplier,
            atr_trailing_multiplier=cfg.atr_trailing_multiplier,
            atr_period=cfg.atr_period,
            bandwidth_percentile=cfg.bandwidth_percentile,
            bandwidth_lookback=cfg.bandwidth_lookback,
            kama_er_period=cfg.kama_er_period,
            kama_fast_period=cfg.kama_fast_period,
            kama_slow_period=cfg.kama_slow_period,
            kama_signal_period=cfg.kama_signal_period,
            kama_volume_filter=cfg.kama_volume_filter,
            breakout_upper_period=cfg.breakout_upper_period,
            breakout_lower_period=cfg.breakout_lower_period,
            breakout_atr_filter=cfg.breakout_atr_filter,
            breakout_volume_filter=cfg.breakout_volume_filter,
            use_daily_trend_filter=cfg.use_daily_trend_filter,
            daily_trend_sma_period=cfg.daily_trend_sma_period,
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
        cfg.min_profit_pct = config.min_profit_pct
        cfg.bollinger_period = config.bollinger_period
        cfg.bollinger_num_std = config.bollinger_num_std
        cfg.bollinger_volume_filter = config.bollinger_volume_filter
        cfg.bollinger_min_bandwidth = config.bollinger_min_bandwidth
        cfg.bollinger_min_profit_pct = config.bollinger_min_profit_pct
        cfg.bollinger_min_sell_bandwidth = config.bollinger_min_sell_bandwidth
        cfg.bollinger_use_middle_exit = config.bollinger_use_middle_exit
        cfg.bollinger_obv_filter = config.bollinger_obv_filter
        cfg.bollinger_obv_ma_period = config.bollinger_obv_ma_period
        cfg.min_sma_gap_pct = config.min_sma_gap_pct
        cfg.sell_cooldown_minutes = config.sell_cooldown_minutes
        cfg.use_minute_chart = config.use_minute_chart
        cfg.minute_short_period = config.minute_short_period
        cfg.minute_long_period = config.minute_long_period
        cfg.trailing_stop_pct = config.trailing_stop_pct
        cfg.trailing_stop_grace_minutes = config.trailing_stop_grace_minutes
        cfg.take_profit_pct = config.take_profit_pct
        cfg.split_buy_count = config.split_buy_count
        cfg.capital_ratio = config.capital_ratio
        cfg.use_rsi_divergence = config.use_rsi_divergence
        cfg.use_macd_filter = config.use_macd_filter
        cfg.macd_fast = config.macd_fast
        cfg.macd_slow = config.macd_slow
        cfg.macd_signal = config.macd_signal
        cfg.bollinger_use_engulfing = config.bollinger_use_engulfing
        cfg.bollinger_use_double_pattern = config.bollinger_use_double_pattern
        cfg.bollinger_rsi_period = config.bollinger_rsi_period
        cfg.bollinger_rsi_overbought = config.bollinger_rsi_overbought
        cfg.bollinger_rsi_oversold = config.bollinger_rsi_oversold
        cfg.auto_regime = config.auto_regime
        cfg.scanner_enabled = config.scanner_enabled
        cfg.scanner_interval_minutes = config.scanner_interval_minutes
        cfg.scanner_top_sectors = config.scanner_top_sectors
        cfg.scanner_max_picks = config.scanner_max_picks
        cfg.scanner_min_price = config.scanner_min_price
        cfg.scanner_min_volume = config.scanner_min_volume
        cfg.scanner_min_change_rate = config.scanner_min_change_rate
        cfg.allocation_mode = config.allocation_mode
        cfg.total_order_budget = config.total_order_budget
        cfg.us_total_order_budget = config.us_total_order_budget
        cfg.atr_stop_multiplier = config.atr_stop_multiplier
        cfg.atr_trailing_multiplier = config.atr_trailing_multiplier
        cfg.atr_period = config.atr_period
        cfg.bandwidth_percentile = config.bandwidth_percentile
        cfg.bandwidth_lookback = config.bandwidth_lookback
        cfg.kama_er_period = config.kama_er_period
        cfg.kama_fast_period = config.kama_fast_period
        cfg.kama_slow_period = config.kama_slow_period
        cfg.kama_signal_period = config.kama_signal_period
        cfg.kama_volume_filter = config.kama_volume_filter
        cfg.breakout_upper_period = config.breakout_upper_period
        cfg.breakout_lower_period = config.breakout_lower_period
        cfg.breakout_atr_filter = config.breakout_atr_filter
        cfg.breakout_volume_filter = config.breakout_volume_filter
        cfg.use_daily_trend_filter = config.use_daily_trend_filter
        cfg.daily_trend_sma_period = config.daily_trend_sma_period

        # 전략 타입 변경 시 매수 정보 초기화 (기존 포지션 추적 무효화)
        if config.strategy_type != old_type:
            cleared = len(self._entry_prices)
            self._entry_prices.clear()
            self._buy_timestamps.clear()
            self._peak_prices.clear()
            self._buy_tranche_count.clear()
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

        # 거래량 가중치 계산 (volume_weighted 모드 시)
        await self._compute_volume_weights()

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
            # 기존 포지션은 분할매수 완료로 간주 (추가 매수 방지)
            self._buy_tranche_count[pos.symbol] = self.settings.trading.split_buy_count
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
            self._force_close_done_date = None

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
                    name=pos.name,
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
                # 매도 성공한 경우에만 추적 정보 제거
                if result.get("success", False):
                    self._entry_prices.pop(pos.symbol, None)
                    self._buy_timestamps.pop(pos.symbol, None)
                    self._peak_prices.pop(pos.symbol, None)
                    self._buy_tranche_count.pop(pos.symbol, None)
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

        # --- KAMA 전략 ---
        if strategy_type == StrategyType.KAMA:
            if cfg.use_minute_chart:
                chart = await _get_minute(cfg.minute_chart_lookback)
            else:
                chart = await _get_daily(cfg.kama_er_period + cfg.kama_signal_period + 20)
            price_info = await _get_price()
            result = evaluate_kama_signal(
                chart,
                er_period=cfg.kama_er_period,
                fast_period=cfg.kama_fast_period,
                slow_period=cfg.kama_slow_period,
                signal_period=cfg.kama_signal_period,
                volume_filter=cfg.kama_volume_filter,
                atr_period=cfg.atr_period,
            )
            logger.info(
                "[%s] %s | 현재가=%.0f, KAMA=%.1f, Signal=%.1f, ATR=%s | %s",
                symbol, result.signal.value, price_info.current_price,
                result.kama, result.signal_line,
                f"{result.atr:.1f}" if result.atr else "N/A",
                result.reason_detail,
            )
            signal = TradingSignal(
                symbol=symbol,
                name=price_info.name,
                signal=result.signal,
                short_ma=result.kama,
                long_ma=result.signal_line,
                current_price=price_info.current_price,
                timestamp=now,
                atr=result.atr,
                volume_confirmed=result.volume_confirmed,
                reason_detail=result.reason_detail,
            )
            return self._apply_daily_trend_filter(signal, cfg, _get_daily)

        # --- Breakout 전략 ---
        if strategy_type == StrategyType.BREAKOUT:
            if cfg.use_minute_chart:
                chart = await _get_minute(cfg.minute_chart_lookback)
            else:
                chart = await _get_daily(cfg.breakout_upper_period + 20)
            price_info = await _get_price()
            result = evaluate_breakout_signal(
                chart,
                upper_period=cfg.breakout_upper_period,
                lower_period=cfg.breakout_lower_period,
                atr_filter=cfg.breakout_atr_filter,
                atr_period=cfg.atr_period,
                volume_filter=cfg.breakout_volume_filter,
            )
            logger.info(
                "[%s] %s | 현재가=%.0f, CH(%.0f/%.0f), ATR=%s | %s",
                symbol, result.signal.value, price_info.current_price,
                result.upper_channel, result.lower_channel,
                f"{result.atr:.1f}" if result.atr else "N/A",
                result.reason_detail,
            )
            signal = TradingSignal(
                symbol=symbol,
                name=price_info.name,
                signal=result.signal,
                current_price=price_info.current_price,
                timestamp=now,
                atr=result.atr,
                volume_confirmed=result.volume_confirmed,
                reason_detail=result.reason_detail,
            )
            return self._apply_daily_trend_filter(signal, cfg, _get_daily)

        # --- Bollinger 전략 ---
        if strategy_type == StrategyType.BOLLINGER:
            chart = await _get_minute(cfg.minute_chart_lookback)
            price_info = await _get_price()
            vol_period = cfg.bollinger_volume_ma_period if cfg.bollinger_volume_filter else None
            obv_period = cfg.bollinger_obv_ma_period if cfg.bollinger_obv_filter else None
            # 중간밴드 이탈 매도: 보유 중인 경우에만 활성화
            middle_exit = cfg.bollinger_use_middle_exit and symbol in self._entry_prices
            result = evaluate_bollinger_signal(
                chart,
                period=cfg.bollinger_period,
                num_std=cfg.bollinger_num_std,
                volume_ma_period=vol_period,
                min_bandwidth=cfg.bollinger_min_bandwidth,
                min_sell_bandwidth=cfg.bollinger_min_sell_bandwidth,
                use_middle_exit=middle_exit,
                use_engulfing_filter=cfg.bollinger_use_engulfing,
                use_double_pattern=cfg.bollinger_use_double_pattern,
                rsi_period=cfg.bollinger_rsi_period,
                rsi_overbought=cfg.bollinger_rsi_overbought,
                rsi_oversold=cfg.bollinger_rsi_oversold,
                obv_ma_period=obv_period,
                bandwidth_percentile=cfg.bandwidth_percentile,
                bandwidth_lookback=cfg.bandwidth_lookback,
            )
            # ATR 계산 (동적 손절용)
            atr_values = compute_atr(chart, cfg.atr_period)
            current_atr = atr_values[-1] if atr_values else None
            logger.info(
                "[%s] %s | 현재가=%.0f, BB(%.0f/%.0f/%.0f), vol_ok=%s | %s",
                symbol, result.signal.value, price_info.current_price,
                result.upper_band, result.middle_band, result.lower_band,
                result.volume_confirmed, result.reason_detail,
            )
            signal = TradingSignal(
                symbol=symbol,
                name=price_info.name,
                signal=result.signal,
                current_price=price_info.current_price,
                timestamp=now,
                upper_band=result.upper_band,
                middle_band=result.middle_band,
                lower_band=result.lower_band,
                volume_confirmed=result.volume_confirmed,
                obv_confirmed=result.obv_confirmed,
                atr=current_atr,
                reason_detail=result.reason_detail,
            )
            return self._apply_daily_trend_filter(signal, cfg, _get_daily)

        # --- SMA 크로스오버 전략 ---
        if cfg.use_minute_chart:
            chart = await _get_minute(cfg.minute_chart_lookback)
            short_period = cfg.minute_short_period
            long_period = cfg.minute_long_period
        else:
            short_period = cfg.short_ma_period
            long_period = cfg.long_ma_period
            chart = await _get_daily(long_period + 10)
        price_info = await _get_price()

        # ATR 계산 (동적 손절용)
        atr_values = compute_atr(chart, cfg.atr_period)
        current_atr = atr_values[-1] if atr_values else None

        # 국면 정보 (regime-aware 필터용)
        regime_str = self._current_regime.value if self._current_regime else None

        if cfg.use_advanced_strategy:
            result = evaluate_signal_with_filters(
                chart, short_period, long_period,
                rsi_period=cfg.rsi_period,
                rsi_overbought=cfg.rsi_overbought,
                rsi_oversold=cfg.rsi_oversold,
                volume_ma_period=cfg.volume_ma_period,
                obv_ma_period=cfg.obv_ma_period,
                use_rsi_divergence=cfg.use_rsi_divergence,
                use_macd_filter=cfg.use_macd_filter,
                macd_fast=cfg.macd_fast,
                macd_slow=cfg.macd_slow,
                macd_signal=cfg.macd_signal,
                min_gap_pct=cfg.min_sma_gap_pct,
                regime=regime_str,
            )
            signal = TradingSignal(
                symbol=symbol,
                name=price_info.name,
                signal=result.signal,
                short_ma=result.short_ma,
                long_ma=result.long_ma,
                current_price=price_info.current_price,
                timestamp=now,
                rsi=result.rsi,
                volume_confirmed=result.volume_confirmed,
                obv_confirmed=result.obv_confirmed,
                raw_signal=result.raw_signal,
                atr=current_atr,
                reason_detail=result.reason_detail,
            )
        else:
            signal_type, short_ma, long_ma, reason_detail = evaluate_signal(
                chart, short_period, long_period,
                min_gap_pct=cfg.min_sma_gap_pct,
            )
            signal = TradingSignal(
                symbol=symbol,
                name=price_info.name,
                signal=signal_type,
                short_ma=short_ma,
                long_ma=long_ma,
                current_price=price_info.current_price,
                timestamp=now,
                atr=current_atr,
                reason_detail=reason_detail,
            )

        logger.info(
            "[%s] %s | 현재가=%.0f, SMA%d=%.0f, SMA%d=%.0f | %s",
            symbol, signal.signal.value, price_info.current_price,
            short_period, signal.short_ma, long_period, signal.long_ma,
            signal.reason_detail,
        )
        return self._apply_daily_trend_filter(signal, cfg, _get_daily)

    def _apply_daily_trend_filter(
        self, signal: TradingSignal, cfg, _get_daily
    ) -> TradingSignal:
        """멀티 타임프레임 필터: 일봉 SMA 아래이면 BUY → HOLD.

        동기 반환 — 일봉 데이터는 _tick에서 별도 호출해야 하므로
        이 메서드는 이미 캐시된 일봉 데이터가 있을 때만 작동한다.
        실제 비동기 일봉 조회는 _tick 레벨에서 수행.
        """
        # 동기 필터이므로 여기서는 self._daily_trend_blocked 플래그만 확인
        # 실제 구현은 _tick에서 비동기로 일봉 조회 후 판단
        return signal

    async def _check_daily_trend(
        self, symbol: str, signal: TradingSignal
    ) -> TradingSignal:
        """일봉 추세 필터 (BUY 시그널에만 적용).

        use_daily_trend_filter + use_minute_chart + BUY 시 일봉 SMA 아래이면 HOLD.
        """
        cfg = self.settings.trading
        if (
            not cfg.use_daily_trend_filter
            or not cfg.use_minute_chart
            or signal.signal != SignalType.BUY
        ):
            return signal

        mkt = detect_market_type(symbol)
        if mkt == MarketType.US:
            exchange = self._get_exchange(symbol)
            daily_chart = await self.us_market.get_daily_chart(
                symbol, exchange, cfg.daily_trend_sma_period + 5
            )
        else:
            daily_chart = await self.market.get_daily_chart(
                symbol, cfg.daily_trend_sma_period + 5
            )

        if len(daily_chart) < cfg.daily_trend_sma_period:
            return signal

        daily_closes = [float(c.close) for c in daily_chart]
        daily_sma = compute_sma(daily_closes, cfg.daily_trend_sma_period)
        sma_val = daily_sma[-1]
        if sma_val is not None and signal.current_price < sma_val:
            new_reason = (
                signal.reason_detail
                + f" → 일봉 SMA{cfg.daily_trend_sma_period} 하회"
                f"({signal.current_price:.0f} < {sma_val:.0f}) → HOLD"
            )
            return TradingSignal(
                symbol=signal.symbol,
                name=signal.name,
                signal=SignalType.HOLD,
                short_ma=signal.short_ma,
                long_ma=signal.long_ma,
                current_price=signal.current_price,
                timestamp=signal.timestamp,
                rsi=signal.rsi,
                volume_confirmed=signal.volume_confirmed,
                obv_confirmed=signal.obv_confirmed,
                raw_signal=signal.signal,
                upper_band=signal.upper_band,
                middle_band=signal.middle_band,
                lower_band=signal.lower_band,
                atr=signal.atr,
                reason_detail=new_reason,
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
        if regime == MarketRegime.STRONG_BULL:
            config = StrategyConfig(
                strategy_type=StrategyType.BREAKOUT,
                auto_regime=True,
            )
        elif regime == MarketRegime.BULL:
            config = StrategyConfig(
                strategy_type=StrategyType.KAMA,
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

    async def _run_scanner(self, now: datetime) -> None:
        """섹터 모멘텀 스캐너: 거래량 상위 종목 조회 → 섹터 스코어링 → 대장주 선정"""
        cfg = self.settings.trading
        if not cfg.scanner_enabled:
            return

        # 스캔 주기 체크
        if self._last_scan_time is not None:
            elapsed = (now - self._last_scan_time).total_seconds() / 60
            if elapsed < cfg.scanner_interval_minutes:
                return

        try:
            rank_items = await self.volume_rank.get_volume_ranking(top_n=30)
        except Exception:
            logger.warning("스캐너: 거래량순위 조회 실패", exc_info=True)
            return

        self._last_scan_time = now

        # 거래량 상위 종목 필터링 → 상위 N개 직접 선정
        filtered = [
            item for item in rank_items
            if item.current_price >= cfg.scanner_min_price
            and item.volume >= cfg.scanner_min_volume
            and item.change_rate >= cfg.scanner_min_change_rate
        ]
        top_picks = filtered[:cfg.scanner_max_picks]

        # 섹터 스코어링은 참고용으로만 유지
        sector_scores = score_sectors(
            rank_items,
            min_price=cfg.scanner_min_price,
            min_volume=cfg.scanner_min_volume,
            min_change_rate=cfg.scanner_min_change_rate,
        )
        self._scanner_sector_scores = sector_scores
        self._scanner_picks = [
            ScannerPick(
                symbol=item.symbol,
                name=item.name,
                sector=get_sector(item.symbol),
                score=float(item.volume),
                current_price=item.current_price,
                change_rate=item.change_rate,
                volume=item.volume,
            )
            for item in top_picks
        ]

        new_symbols = [item.symbol for item in top_picks]
        old_set = set(self._scanner_symbols)
        new_set = set(new_symbols)

        # 추가된 종목 로깅
        added = new_set - old_set
        for sym in added:
            item = next((i for i in top_picks if i.symbol == sym), None)
            detail = f"{sym} ({item.name}, {item.change_rate:+.1f}%, 거래량 {item.volume:,})" if item else sym
            logger.info("스캐너 종목 추가: %s", detail)
            self._journal.log_event(TradeEvent.engine_event(
                EventType.SCANNER_ADD, detail, timestamp=now,
            ))

        # 제거된 종목 로깅 + 추적 정보 정리
        removed = old_set - new_set
        for sym in removed:
            logger.info("스캐너 종목 제거: %s", sym)
            self._journal.log_event(TradeEvent.engine_event(
                EventType.SCANNER_REMOVE, sym, timestamp=now,
            ))
            # 추적 정보 정리 (보유 중이 아닌 경우만)
            if sym not in self._entry_prices:
                self._peak_prices.pop(sym, None)
                self._buy_timestamps.pop(sym, None)
                self._buy_tranche_count.pop(sym, None)
                self._sell_timestamps.pop(sym, None)

        self._scanner_symbols = list(new_symbols)

        # 스캔 결과 저널 기록
        pick_names = [f"{i.name}({i.change_rate:+.1f}%)" for i in top_picks]
        self._journal.log_event(TradeEvent.engine_event(
            EventType.SCANNER_SCAN,
            f"거래량 상위 {len(top_picks)}종목: {', '.join(pick_names)}",
            timestamp=now,
        ))

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

        # 거래량 가중치 갱신 (날짜 변경 시)
        if self._volume_weights_date != now.date():
            await self._compute_volume_weights()

        # 자동 국면 감지 (하루 1회, 국내 장 시간에만)
        cfg = self.settings.trading
        if kr_open and cfg.auto_regime and self._regime_checked_date != now.date():
            await self._check_and_switch_regime(now)
            self._regime_checked_date = now.date()

        current_hhmm = now.hour * 100 + now.minute

        # 섹터 모멘텀 스캐너 (국내 장 시간에만)
        if kr_open:
            await self._run_scanner(now)

        # 국내 장 마감 청산: force_close_minute 이후 국내 보유 포지션 전량 매도 (0=비활성)
        # 같은 날 이미 강제 청산 완료 시 재실행 방지
        if (
            kr_open
            and self.settings.trading.force_close_minute > 0
            and current_hhmm >= self.settings.trading.force_close_minute
            and self._force_close_done_date != now.date()
        ):
            await self._force_close_all(now, market=MarketType.DOMESTIC)
            self._force_close_done_date = now.date()
            kr_open = False  # 이번 tick에서 국내 종목 더 이상 처리 안 함

        # 매매 대상 결정
        # scanner_enabled=True: 스캔 종목 + 고정 워치리스트 + 보유 종목 (중복 제거)
        # scanner_enabled=False: 고정 워치리스트 (기존 동작)
        if cfg.scanner_enabled:
            held_symbols = list(self._entry_prices.keys())
            all_symbols = list(dict.fromkeys(
                self._scanner_symbols + list(self._watch_symbols) + held_symbols
            ))
        else:
            all_symbols = list(self._watch_symbols)

        fail_count = 0
        for symbol in all_symbols:
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

                # 일봉 추세 필터 (BUY 시그널에만, 비동기)
                signal = await self._check_daily_trend(symbol, signal)

                self._signals.append(signal)

                # 현재가 0 → 시세 이상: 매매 판단 스킵
                if signal.current_price <= 0:
                    logger.warning("[%s] 현재가 0 — 매매 판단 스킵", symbol)
                    continue

                self._journal.log_event(TradeEvent.from_signal(signal))

                # 고점 갱신 (보유 중인 종목)
                cfg = self.settings.trading
                if symbol in self._entry_prices:
                    self._peak_prices[symbol] = max(
                        self._peak_prices.get(symbol, 0), float(signal.current_price)
                    )

                # ATR 기반 트레일링 스탑 (atr_trailing_multiplier > 0이면 사용)
                if (
                    cfg.atr_trailing_multiplier > 0
                    and signal.atr is not None
                    and signal.atr > 0
                    and symbol in self._peak_prices
                ):
                    grace_ok = True
                    if cfg.trailing_stop_grace_minutes > 0 and symbol in self._buy_timestamps:
                        elapsed = (now - self._buy_timestamps[symbol]).total_seconds() / 60
                        if elapsed < cfg.trailing_stop_grace_minutes:
                            grace_ok = False
                    peak = self._peak_prices[symbol]
                    atr_trail_level = peak - signal.atr * cfg.atr_trailing_multiplier
                    if grace_ok and peak > 0 and signal.current_price <= atr_trail_level:
                        drop_pct = (peak - signal.current_price) / peak * 100
                        detail = (
                            f"ATR 트레일링 스탑: 고점 {peak:,.0f} → "
                            f"현재가 {signal.current_price:,.0f} "
                            f"(ATR×{cfg.atr_trailing_multiplier}={signal.atr * cfg.atr_trailing_multiplier:,.0f}, "
                            f"고점 대비 -{drop_pct:.1f}%)"
                        )
                        logger.info("[%s] %s", symbol, detail)
                        await self._execute_sell(
                            symbol, now,
                            reason="trailing_stop",
                            reason_detail=detail,
                        )
                        continue

                # 트레일링 스탑 (고정 %, ATR 트레일링 미사용 시 폴백)
                if cfg.trailing_stop_pct > 0 and cfg.atr_trailing_multiplier <= 0 and symbol in self._peak_prices:
                    # 매수 후 유예 기간 체크
                    grace_ok = True
                    if cfg.trailing_stop_grace_minutes > 0 and symbol in self._buy_timestamps:
                        elapsed = (now - self._buy_timestamps[symbol]).total_seconds() / 60
                        if elapsed < cfg.trailing_stop_grace_minutes:
                            grace_ok = False

                    peak = self._peak_prices[symbol]
                    if grace_ok and peak > 0:
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

                # 목표 수익 자동 매도 (take_profit)
                if cfg.take_profit_pct > 0 and symbol in self._entry_prices:
                    ep = self._entry_prices[symbol]
                    if ep > 0:
                        profit_pct = (signal.current_price - ep) / ep * 100
                        if profit_pct >= cfg.take_profit_pct:
                            detail = (
                                f"목표 수익 매도: 매수가 {ep:,.0f} → "
                                f"현재가 {signal.current_price:,.0f} "
                                f"(수익률 +{profit_pct:.1f}%)"
                            )
                            logger.info("[%s] %s", symbol, detail)
                            await self._execute_sell(
                                symbol, now,
                                reason="take_profit",
                                reason_detail=detail,
                            )
                            continue

                # 리스크 체크 (stop-loss / max-holding) — 전략 무관
                entry_price = self._entry_prices.get(symbol, 0.0)

                # ATR 기반 손절 (atr_stop_multiplier > 0이면 고정 % 대체)
                if (
                    cfg.atr_stop_multiplier > 0
                    and signal.atr is not None
                    and signal.atr > 0
                    and entry_price > 0
                ):
                    atr_stop_level = entry_price - signal.atr * cfg.atr_stop_multiplier
                    if signal.current_price <= atr_stop_level:
                        loss_pct = (entry_price - signal.current_price) / entry_price * 100
                        detail = (
                            f"ATR 손절: 매수가 {entry_price:,.0f} → "
                            f"현재가 {signal.current_price:,.0f} "
                            f"(ATR×{cfg.atr_stop_multiplier}={signal.atr * cfg.atr_stop_multiplier:,.0f}, "
                            f"손실 -{loss_pct:.1f}%)"
                        )
                        logger.info("[%s] %s", symbol, detail)
                        await self._execute_sell(
                            symbol, now,
                            reason="stop_loss",
                            reason_detail=detail,
                        )
                        continue

                # 고정 % 손절 (ATR 손절 미사용 시 폴백)
                if cfg.stop_loss_pct > 0 and cfg.atr_stop_multiplier <= 0 and entry_price > 0:
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

                # 매도 최소 수익률 게이트 (전략 공통)
                # 시그널 매도 시 수익률이 기준 미만이면 보류 (손실 중이면 매도 허용)
                if (
                    signal.signal == SignalType.SELL
                    and cfg.min_profit_pct > 0
                    and symbol in self._entry_prices
                ):
                    ep = self._entry_prices[symbol]
                    if ep > 0:
                        profit_pct = (signal.current_price - ep) / ep * 100
                        if 0 <= profit_pct < cfg.min_profit_pct:
                            logger.info(
                                "[%s] 수익률 부족으로 매도 보류 "
                                "(수익률 %.2f%% < 기준 %.1f%%)",
                                symbol, profit_pct, cfg.min_profit_pct,
                            )
                            self._journal.log_event(TradeEvent.engine_event(
                                EventType.SIGNAL,
                                f"{symbol}: 매도 보류 (수익률 {profit_pct:.2f}% < "
                                f"기준 {cfg.min_profit_pct:.1f}%)",
                            ))
                            continue

                # 매매 실행 (데이트레이딩 제한은 국내 종목에만 적용)
                if signal.signal == SignalType.BUY:
                    # 매도 후 쿨다운 체크
                    if cfg.sell_cooldown_minutes > 0 and symbol in self._sell_timestamps:
                        elapsed = (now - self._sell_timestamps[symbol]).total_seconds() / 60
                        if elapsed < cfg.sell_cooldown_minutes:
                            logger.info(
                                "[%s] 매도 후 쿨다운 중 (%.0f분/%.0f분)",
                                symbol, elapsed, cfg.sell_cooldown_minutes,
                            )
                            continue
                    if mkt == MarketType.DOMESTIC:
                        if self.settings.trading.no_new_buy_minute > 0 and current_hhmm >= self.settings.trading.no_new_buy_minute:
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
                    await self._execute_buy(symbol, signal.current_price, now, name=signal.name)
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
                f"종목 처리 실패: {fail_count}/{len(all_symbols)}개"
            )

    def _get_order_lock(self, symbol: str) -> asyncio.Lock:
        """종목별 주문 Lock 반환 (없으면 생성)"""
        if symbol not in self._order_locks:
            self._order_locks[symbol] = asyncio.Lock()
        return self._order_locks[symbol]

    async def _compute_volume_weights(self) -> None:
        """감시 종목의 거래량을 조회하여 가중치 기반 목표금액 계산"""
        cfg = self.settings.trading
        if cfg.allocation_mode != AllocationMode.VOLUME_WEIGHTED:
            return

        dom_symbols = [s for s in self._watch_symbols if detect_market_type(s) == MarketType.DOMESTIC]
        us_symbols = [s for s in self._watch_symbols if detect_market_type(s) == MarketType.US]

        volumes: dict[str, int] = {}

        # 국내 종목 거래량 조회
        for symbol in dom_symbols:
            try:
                price_info = await self.market.get_current_price(symbol)
                volumes[symbol] = max(price_info.volume, 1)
            except Exception:
                logger.warning("[%s] 거래량 조회 실패 — 최소값(1) 적용", symbol)
                volumes[symbol] = 1

        # 해외 종목 거래량 조회
        for symbol in us_symbols:
            try:
                exchange = self._get_exchange(symbol)
                price_info = await self.us_market.get_current_price(symbol, exchange)
                volumes[symbol] = max(price_info.volume, 1)
            except Exception:
                logger.warning("[%s] 거래량 조회 실패 — 최소값(1) 적용", symbol)
                volumes[symbol] = 1

        # 국내 가중치 계산
        dom_total = sum(volumes.get(s, 1) for s in dom_symbols) or 1
        for s in dom_symbols:
            weight = volumes.get(s, 1) / dom_total
            self._symbol_target_amounts[s] = cfg.total_order_budget * weight

        # 해외 가중치 계산
        us_total = sum(volumes.get(s, 1) for s in us_symbols) or 1
        for s in us_symbols:
            weight = volumes.get(s, 1) / us_total
            self._symbol_target_amounts[s] = cfg.us_total_order_budget * weight

        self._volume_weights_date = date.today()
        logger.info(
            "거래량 가중치 계산 완료: %d종목 | %s",
            len(self._symbol_target_amounts),
            {s: f"{amt:,.0f}" for s, amt in self._symbol_target_amounts.items()},
        )

    def _get_target_amount(
        self, symbol: str, mkt: MarketType, deposit: float
    ) -> float:
        """종목별 주문 목표금액 결정"""
        cfg = self.settings.trading

        if cfg.allocation_mode == AllocationMode.VOLUME_WEIGHTED:
            if cfg.capital_ratio > 0 and deposit > 0:
                # 예수금 비율 × 종목 가중치 비중
                market_symbols = [
                    s for s in self._watch_symbols
                    if detect_market_type(s) == mkt
                ]
                market_total = sum(
                    self._symbol_target_amounts.get(s, 0)
                    for s in market_symbols
                ) or 1.0
                sym_amount = self._symbol_target_amounts.get(symbol, 0)
                weight_ratio = sym_amount / market_total
                return deposit * cfg.capital_ratio * weight_ratio
            # 예산 기반 가중치
            return self._symbol_target_amounts.get(
                symbol,
                cfg.us_target_order_amount if mkt == MarketType.US else cfg.target_order_amount,
            )

        # EQUAL 모드
        if cfg.capital_ratio > 0 and deposit > 0:
            return deposit * cfg.capital_ratio
        return cfg.us_target_order_amount if mkt == MarketType.US else cfg.target_order_amount

    async def _execute_buy(
        self, symbol: str, current_price: float, now: datetime, *, name: str = ""
    ) -> None:
        """매수 주문 (잔고 확인 → 동적 수량 계산 → 주문을 Lock으로 원자적 실행)"""
        mkt = detect_market_type(symbol)
        cfg = self.settings.trading

        async with self._get_order_lock(symbol):
            # 시장별 잔고 조회
            if mkt == MarketType.US:
                positions, summary = await self.us_order.get_balance()
            else:
                positions, summary = await self.order.get_balance()

            # 분할 매수 체크
            split_count = cfg.split_buy_count
            tranche = self._buy_tranche_count.get(symbol, 0)

            for pos in positions:
                if pos.symbol == symbol and pos.quantity > 0:
                    # 분할 매수: 트렌치 미완료면 추가 매수 허용
                    if split_count > 1 and tranche < split_count:
                        break  # 추가 매수 진행
                    logger.info(
                        "[%s] 이미 보유 중 (%d주) — 매수 생략", symbol, pos.quantity
                    )
                    return

            if current_price <= 0:
                return

            # 동적 수량 계산 (국내/해외 분리, 배분 모드 적용)
            target = self._get_target_amount(symbol, mkt, summary.deposit)
            # 분할 매수: 주문금액을 분할 수로 나눔
            if split_count > 1:
                target = target / split_count
            if mkt == MarketType.US:
                min_qty = cfg.us_min_quantity
                max_qty = cfg.us_max_quantity
            else:
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
                name=name,
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
                # 분할 매수: 가중평균 매수가 계산
                old_price = self._entry_prices.get(symbol, 0.0)
                old_tranche = self._buy_tranche_count.get(symbol, 0)
                if old_tranche > 0 and old_price > 0:
                    new_avg = (old_price * old_tranche + float(current_price)) / (old_tranche + 1)
                    self._entry_prices[symbol] = new_avg
                else:
                    self._entry_prices[symbol] = float(current_price)
                self._buy_timestamps[symbol] = now
                self._peak_prices[symbol] = max(
                    self._peak_prices.get(symbol, 0.0), float(current_price)
                )
                self._buy_tranche_count[symbol] = old_tranche + 1

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
                        name=pos.name,
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
                    # 매도 시 매수 정보 삭제 + 쿨다운 시각 기록
                    self._entry_prices.pop(symbol, None)
                    self._buy_timestamps.pop(symbol, None)
                    self._peak_prices.pop(symbol, None)
                    self._buy_tranche_count.pop(symbol, None)
                    self._sell_timestamps[symbol] = now
                    return

            logger.info("[%s] 보유 수량 없음 — 매도 생략", symbol)

