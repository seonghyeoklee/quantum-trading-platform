package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.WatchlistGroupId;
import com.quantum.trading.platform.shared.value.WatchlistId;
import lombok.Builder;
import lombok.Value;

import java.time.LocalDateTime;

/**
 * 관심종목 그룹 삭제 Event
 */
@Value
@Builder
public class WatchlistGroupDeletedEvent {

    WatchlistGroupId groupId;
    WatchlistId watchlistId;
    String name;
    
    @Builder.Default
    LocalDateTime deletedAt = LocalDateTime.now();

    public static WatchlistGroupDeletedEvent of(WatchlistGroupId groupId, WatchlistId watchlistId, String name) {
        return WatchlistGroupDeletedEvent.builder()
                .groupId(groupId)
                .watchlistId(watchlistId)
                .name(name)
                .deletedAt(LocalDateTime.now())
                .build();
    }
}