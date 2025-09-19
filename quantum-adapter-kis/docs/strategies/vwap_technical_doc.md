# VWAP Strategy Technical Documentation

## Overview

The VWAP (Volume Weighted Average Price) strategy implementation provides institutional-grade algorithmic trading capabilities for overseas stock markets. This document details the technical architecture, algorithms, and implementation specifics.

## Architecture

### Class Hierarchy
```
BaseOverseasStrategy (Abstract)
    ├── analyze_signal() [Abstract]
    ├── Common crash protection methods
    └── Risk management utilities

VWAPStrategy (Concrete Implementation)
    ├── analyze_signal() [Implemented]
    ├── VWAP calculation engine
    ├── Statistical band analysis
    └── Session-aware trading logic
```

## Core Algorithms

### 1. VWAP Calculation Engine

#### Cumulative VWAP Formula
```python
def _update_vwap(self, market_data: OverseasMarketData):
    price = market_data.current_price
    volume = market_data.volume

    # Cumulative calculation
    self.cumulative_volume_price += (price * volume)
    self.cumulative_volume += volume

    # VWAP computation
    if self.cumulative_volume > 0:
        self.current_vwap = self.cumulative_volume_price / self.cumulative_volume

    # Store deviation for standard deviation calculation
    price_deviation = price - self.current_vwap
    self.vwap_data_points.append(price_deviation)
```

#### Session Reset Logic
```python
def _is_new_session(self, market_data: OverseasMarketData) -> bool:
    current_time = datetime.now().time()
    session_start = time(9, 30)  # 9:30 AM EST

    # First execution or day transition
    if self.session_start_time is None:
        if current_time >= session_start:
            self.session_start_time = datetime.now()
            return True
    else:
        # Day rollover detection
        today = datetime.now().date()
        if self.session_start_time.date() < today and current_time >= session_start:
            self.session_start_time = datetime.now()
            return True

    return False
```

### 2. Statistical Band Calculation

#### Standard Deviation Bands
```python
def _calculate_bands(self):
    if len(self.vwap_data_points) < 2:
        return

    # Calculate standard deviation of price deviations
    deviations = list(self.vwap_data_points)
    self.std_deviation = statistics.stdev(deviations)

    # Band calculation
    multiplier = self.config['std_multiplier']  # Default: 2.0
    self.upper_band = self.current_vwap + (multiplier * self.std_deviation)
    self.lower_band = self.current_vwap - (multiplier * self.std_deviation)
```

#### Mathematical Properties
- **Upper Band**: VWAP + (k × σ), where k = std_multiplier, σ = standard deviation
- **Lower Band**: VWAP - (k × σ)
- **Band Width**: 2 × k × σ (adaptive to market volatility)

### 3. Signal Generation Algorithm

#### 7-Stage Signal Analysis Pipeline

```python
def _generate_vwap_signal(self, market_data: OverseasMarketData) -> tuple[SignalType, float, str]:
    current_price = market_data.current_price
    reasons = []
    buy_score = 0.0
    sell_score = 0.0

    # Stage 1: Band Position Analysis
    vwap_distance_pct = ((current_price - self.current_vwap) / self.current_vwap) * 100

    if current_price <= self.lower_band:
        band_distance = abs(current_price - self.lower_band) / self.current_vwap * 100
        buy_score += 0.4
        reasons.append(f"Lower Band Touch (VWAP: {vwap_distance_pct:.1f}%)")

        # Precision bonus
        if band_distance < 0.2:
            buy_score += 0.2
            reasons.append("Exact Band Touch")

    elif current_price >= self.upper_band:
        band_distance = abs(current_price - self.upper_band) / self.current_vwap * 100
        sell_score += 0.4
        reasons.append(f"Upper Band Touch (VWAP: {vwap_distance_pct:.1f}%)")

        if band_distance < 0.2:
            sell_score += 0.2
            reasons.append("Exact Band Touch")

    # Stage 2: Mean Reversion Analysis
    if len(self.price_history) >= 3:
        recent_prices = list(self.price_history)[-3:]

        if current_price < self.current_vwap:
            # Below VWAP, check for upward movement toward VWAP
            if recent_prices[-1] > recent_prices[-2] > recent_prices[-3]:
                buy_score += 0.15
                reasons.append("VWAP Reversion Movement")
        else:
            # Above VWAP, check for downward movement toward VWAP
            if recent_prices[-1] < recent_prices[-2] < recent_prices[-3]:
                sell_score += 0.15
                reasons.append("VWAP Reversion Movement")

    # Stage 3: Volume Spike Analysis
    avg_volume = self.get_average_volume(20)
    if market_data.volume > avg_volume * self.config['volume_threshold']:
        volume_multiplier = min(market_data.volume / avg_volume, 3.0) / 3.0
        buy_score += 0.1 * volume_multiplier
        sell_score += 0.1 * volume_multiplier
        reasons.append(f"Volume Spike ({market_data.volume/avg_volume:.1f}x)")

    # Stage 4: RSI Confirmation
    rsi = self.calculate_rsi()
    if rsi < 35 and current_price < self.current_vwap:
        buy_score += 0.1
        reasons.append(f"RSI Oversold ({rsi:.0f})")
    elif rsi > 65 and current_price > self.current_vwap:
        sell_score += 0.1
        reasons.append(f"RSI Overbought ({rsi:.0f})")

    # Stage 5: Session Weight Application
    session_weight = self._get_session_weight(market_data.trading_session)
    buy_score *= session_weight
    sell_score *= session_weight

    if session_weight < 1.0:
        reasons.append(f"Session Weight ({session_weight:.1f}x)")

    # Stage 6: Risk Filter Application (Inherited from BaseOverseasStrategy)
    buy_score, sell_score, reasons = self._apply_risk_filter(buy_score, sell_score, reasons, market_data)

    # Stage 7: Final Signal Decision
    if buy_score > sell_score and buy_score > 0.5:
        confidence = min(buy_score, 1.0)
        return SignalType.BUY, confidence, " | ".join(reasons)
    elif sell_score > buy_score and sell_score > 0.5:
        confidence = min(sell_score, 1.0)
        return SignalType.SELL, confidence, " | ".join(reasons)
    else:
        return SignalType.NONE, 0.0, "Insufficient Signal Strength"
```

### 4. Session-Aware Trading Logic

#### Trading Session Weights
```python
def _get_session_weight(self, session: TradingSession) -> float:
    weights = {
        TradingSession.PRE_MARKET: 0.6,    # 60% confidence (low liquidity)
        TradingSession.REGULAR: 1.0,       # 100% confidence (optimal conditions)
        TradingSession.AFTER_HOURS: 0.4,   # 40% confidence (minimal liquidity)
        TradingSession.CLOSED: 0.1         # 10% confidence (emergency only)
    }
    return weights.get(session, 1.0)
```

#### Rationale
- **Pre-market**: Reduced institutional activity, higher spreads
- **Regular hours**: Peak liquidity and institutional participation
- **After-hours**: Limited participation, higher volatility

### 5. Position Sizing Algorithm

#### Multi-Factor Position Calculation
```python
def _calculate_position_size(self, confidence: float, market_data: OverseasMarketData) -> int:
    base_quantity = 1

    # Confidence multiplier (0.0 - 1.0)
    confidence_multiplier = confidence

    # Volatility adjustment
    volatility = self.get_volatility()
    if volatility > 0:
        volatility_ratio = min(volatility / market_data.current_price * 100, 10.0)
        volatility_multiplier = max(0.5, 1 - (volatility_ratio / 20.0))
    else:
        volatility_multiplier = 1.0

    # Volume adjustment
    avg_volume = self.get_average_volume()
    if avg_volume > 0:
        volume_ratio = market_data.volume / avg_volume
        volume_multiplier = min(1.5, max(0.5, volume_ratio / 2.0))
    else:
        volume_multiplier = 1.0

    # Initial calculation
    final_quantity = int(base_quantity * confidence_multiplier * volatility_multiplier * volume_multiplier)

    # Risk-based adjustment (inherited from BaseOverseasStrategy)
    risk_score = self._calculate_risk_score(market_data)
    final_quantity = self._adjust_position_size_for_risk(final_quantity, risk_score)

    return max(1, final_quantity)
```

## Data Structures

### Market Data Input
```python
@dataclass
class OverseasMarketData:
    symbol: str
    exchange: ExchangeType
    current_price: float
    volume: int
    change: float
    change_percent: float
    high: float
    low: float
    open_price: float
    previous_close: float
    trading_session: TradingSession
    timestamp: datetime
```

### Signal Output
```python
@dataclass
class OverseasTradingSignal:
    symbol: str
    exchange: ExchangeType
    signal_type: SignalType
    confidence: float
    price: float
    quantity: int
    reason: str
    session: TradingSession
    timestamp: datetime = field(default_factory=datetime.now)
```

## Configuration Parameters

### Default Configuration
```python
default_config = {
    'std_multiplier': 2.0,           # Band width multiplier
    'volume_threshold': 1.5,         # Volume spike threshold
    'min_confidence': 0.7,           # Minimum signal confidence
    'vwap_period': 'intraday',       # VWAP calculation period
    'session_start_hour': 9,         # EST session start
    'session_start_minute': 30,      # EST session start
    'price_deviation_threshold': 0.5, # Price deviation threshold (%)
    'min_data_points': 20,           # Minimum data points required

    # Crash protection (inherited from BaseOverseasStrategy)
    'enable_crash_protection': True,
    'crash_5min_threshold': -0.02,   # 5-minute crash threshold
    'crash_10min_threshold': -0.03,  # 10-minute crash threshold
    'risk_threshold_critical': 70,   # Critical risk score threshold
    'consecutive_drops_limit': 3     # Consecutive price drop limit
}
```

### Parameter Tuning Guidelines

#### Conservative Settings
```python
conservative_config = {
    'std_multiplier': 2.5,           # Wider bands
    'min_confidence': 0.8,           # Higher confidence threshold
    'volume_threshold': 2.0,         # Higher volume requirement
    'crash_5min_threshold': -0.015,  # More sensitive crash detection
}
```

#### Aggressive Settings
```python
aggressive_config = {
    'std_multiplier': 1.5,           # Narrower bands
    'min_confidence': 0.6,           # Lower confidence threshold
    'volume_threshold': 1.2,         # Lower volume requirement
    'min_data_points': 15,           # Faster signal generation
}
```

## Performance Optimization

### Memory Management
- **Deque Usage**: Fixed-size circular buffers for price/volume history
- **Data Point Limit**: Maximum 500 VWAP deviations stored
- **Session Reset**: Automatic memory cleanup on new sessions

### Computational Efficiency
- **Incremental VWAP**: O(1) calculation per update
- **Standard Deviation**: Efficient calculation using stored deviations
- **Signal Caching**: Avoid redundant calculations within same time window

## Error Handling

### Data Validation
```python
def _update_vwap(self, market_data: OverseasMarketData):
    price = market_data.current_price
    volume = market_data.volume

    # Handle invalid volume
    if volume <= 0:
        volume = 1000  # Default volume fallback

    # Prevent division by zero
    if self.cumulative_volume > 0:
        self.current_vwap = self.cumulative_volume_price / self.cumulative_volume
```

### Graceful Degradation
- **Insufficient Data**: Return None signal when data points < minimum
- **Invalid Session**: Default to regular hours weighting
- **Calculation Errors**: Use fallback values and log warnings

## Integration Points

### Risk Management Integration
The VWAP strategy inherits comprehensive risk management from `BaseOverseasStrategy`:

```python
# Crash protection methods
def _detect_crash_momentum(self) -> tuple[bool, float]
def _calculate_risk_score(self, market_data: OverseasMarketData) -> int
def _apply_risk_filter(self, buy_score: float, sell_score: float, reasons: list, market_data: OverseasMarketData) -> tuple[float, float, list]
def _adjust_position_size_for_risk(self, quantity: int, risk_score: int) -> int
```

### Logging Integration
```python
def get_current_analysis(self) -> Dict[str, Any]:
    return {
        'vwap': self.current_vwap,
        'upper_band': self.upper_band,
        'lower_band': self.lower_band,
        'std_deviation': self.std_deviation,
        'position': position,  # 'UPPER', 'MID', 'LOWER'
        'data_points': len(self.vwap_data_points)
    }
```

## Testing

### Unit Tests
```python
# Test VWAP calculation accuracy
def test_vwap_calculation():
    strategy = VWAPStrategy()

    # Input test data
    test_data = [
        (100.0, 1000),  # price, volume
        (101.0, 2000),
        (99.0, 1500)
    ]

    # Expected VWAP = (100*1000 + 101*2000 + 99*1500) / (1000+2000+1500)
    expected_vwap = 450500 / 4500  # 100.11

    for price, volume in test_data:
        market_data = create_test_market_data(price, volume)
        strategy.add_market_data(market_data)
        strategy._update_vwap(market_data)

    assert abs(strategy.current_vwap - expected_vwap) < 0.01
```

### Integration Tests
```python
# Test complete signal generation pipeline
def test_signal_generation():
    strategy = VWAPStrategy()

    # Setup with sufficient data
    for i in range(25):  # min_data_points = 20
        market_data = create_test_market_data(100 + i*0.1, 1000)
        strategy.add_market_data(market_data)
        strategy._update_vwap(market_data)

    # Test lower band touch
    lower_band_price = strategy.lower_band - 0.01
    test_data = create_test_market_data(lower_band_price, 2000)
    signal = strategy.analyze_signal(test_data)

    assert signal is not None
    assert signal.signal_type == SignalType.BUY
    assert signal.confidence > 0.5
```

### Performance Tests
```python
# Test execution time for real-time requirements
def test_signal_latency():
    strategy = VWAPStrategy()

    # Warm up with data
    setup_test_data(strategy, 100)

    # Measure signal generation time
    start_time = time.perf_counter()
    market_data = create_test_market_data(100.0, 1000)
    signal = strategy.analyze_signal(market_data)
    end_time = time.perf_counter()

    # Assert sub-millisecond execution
    assert (end_time - start_time) < 0.001
```

## Deployment Configuration

### Production Environment
```python
production_config = {
    'std_multiplier': 2.0,
    'volume_threshold': 1.5,
    'min_confidence': 0.75,          # Slightly higher for production
    'enable_crash_protection': True,
    'risk_threshold_critical': 65,   # More conservative
    'min_data_points': 25,           # More data for stability
}
```

### Sandbox Environment
```python
sandbox_config = {
    'std_multiplier': 1.8,           # More signals for testing
    'min_confidence': 0.6,           # Lower threshold for testing
    'enable_crash_protection': True,
    'min_data_points': 15,           # Faster signal generation
}
```

## Monitoring and Alerting

### Key Metrics
- **Signal Generation Rate**: Signals per hour
- **Signal Accuracy**: Percentage of profitable signals
- **VWAP Calculation Stability**: Standard deviation of VWAP updates
- **Risk Filter Activation Rate**: Crash protection trigger frequency

### Health Checks
```python
def health_check(self) -> Dict[str, Any]:
    return {
        'vwap_initialized': self.current_vwap > 0,
        'data_sufficiency': len(self.vwap_data_points) >= self.config['min_data_points'],
        'session_active': self.session_start_time is not None,
        'crash_protection_enabled': self.config.get('enable_crash_protection', False),
        'last_update': self.last_signal.timestamp if self.last_signal else None
    }
```

## Future Enhancements

### Planned Features
1. **Multi-timeframe VWAP**: Support for 1min, 5min, 15min VWAPs
2. **Anchored VWAP**: VWAP calculation from specific events
3. **Volume Profile Integration**: Enhanced support/resistance levels
4. **Machine Learning Enhancement**: Adaptive parameter tuning

### Performance Improvements
1. **Vectorized Calculations**: NumPy-based batch processing
2. **Caching Layer**: Redis integration for cross-session data
3. **Parallel Processing**: Multi-symbol strategy execution
4. **GPU Acceleration**: CUDA-based technical indicator calculations

---

*This technical documentation is maintained alongside the codebase and should be updated with any architectural changes or algorithm modifications.*