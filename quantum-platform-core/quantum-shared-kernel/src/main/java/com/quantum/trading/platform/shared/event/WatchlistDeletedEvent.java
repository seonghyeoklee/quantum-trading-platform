package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.WatchlistId;
import lombok.Builder;

import java.time.LocalDateTime;

/**
 * 관심종목 목록 삭제 Event
 */
@Builder
public record WatchlistDeletedEvent(WatchlistId watchlistId, UserId userId, String name, LocalDateTime deletedAt) {

    public static WatchlistDeletedEvent of(WatchlistId watchlistId, UserId userId, String name) {
        return WatchlistDeletedEvent.builder()
                .watchlistId(watchlistId)
                .userId(userId)
                .name(name)
                .deletedAt(LocalDateTime.now())
                .build();
    }
}
