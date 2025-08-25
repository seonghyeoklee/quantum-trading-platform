package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.Symbol;
import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.WatchlistId;
import lombok.Value;
import lombok.Builder;

import java.time.LocalDateTime;

/**
 * 관심종목에서 종목 제거 Event
 */
@Value
@Builder
public class StockRemovedFromWatchlistEvent {
    WatchlistId watchlistId;
    UserId userId;
    Symbol symbol;
    String stockName;
    LocalDateTime removedAt;
    
    public static StockRemovedFromWatchlistEvent of(WatchlistId watchlistId, UserId userId, Symbol symbol, String stockName) {
        return StockRemovedFromWatchlistEvent.builder()
                .watchlistId(watchlistId)
                .userId(userId)
                .symbol(symbol)
                .stockName(stockName)
                .removedAt(LocalDateTime.now())
                .build();
    }
}