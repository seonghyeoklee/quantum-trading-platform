package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.Symbol;
import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.WatchlistId;
import com.quantum.trading.platform.shared.value.WatchlistGroupId;
import lombok.Value;
import lombok.Builder;

import java.time.LocalDateTime;

/**
 * 관심종목에 종목 추가 Event
 */
@Value
@Builder
public class StockAddedToWatchlistEvent {
    WatchlistId watchlistId;
    UserId userId;
    Symbol symbol;
    String stockName;
    WatchlistGroupId groupId; // nullable
    String note;
    LocalDateTime addedAt;
    
    public static StockAddedToWatchlistEvent of(WatchlistId watchlistId, UserId userId, Symbol symbol, String stockName, WatchlistGroupId groupId, String note) {
        return StockAddedToWatchlistEvent.builder()
                .watchlistId(watchlistId)
                .userId(userId)
                .symbol(symbol)
                .stockName(stockName)
                .groupId(groupId)
                .note(note)
                .addedAt(LocalDateTime.now())
                .build();
    }
}