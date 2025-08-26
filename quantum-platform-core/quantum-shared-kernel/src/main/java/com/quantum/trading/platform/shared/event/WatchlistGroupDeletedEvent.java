package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.WatchlistGroupId;
import com.quantum.trading.platform.shared.value.WatchlistId;
import lombok.Builder;

import java.time.LocalDateTime;

/**
 * 관심종목 그룹 삭제 Event
 */
@Builder
public record WatchlistGroupDeletedEvent(WatchlistGroupId groupId, WatchlistId watchlistId, String name,
                                         LocalDateTime deletedAt) {

    public static WatchlistGroupDeletedEvent of(WatchlistGroupId groupId, WatchlistId watchlistId, String name) {
        return WatchlistGroupDeletedEvent.builder()
                .groupId(groupId)
                .watchlistId(watchlistId)
                .name(name)
                .deletedAt(LocalDateTime.now())
                .build();
    }
}
