package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.WatchlistId;
import com.quantum.trading.platform.shared.value.WatchlistGroupId;
import lombok.Builder;

import java.time.LocalDateTime;

/**
 * 관심종목 그룹 생성 Event
 */
@Builder
public record WatchlistGroupCreatedEvent(WatchlistGroupId groupId, WatchlistId watchlistId, UserId userId, String name,
                                         String color, LocalDateTime createdAt) {

    public static WatchlistGroupCreatedEvent of(WatchlistGroupId groupId, WatchlistId watchlistId, UserId userId,
            String name, String color) {
        return WatchlistGroupCreatedEvent.builder()
                .groupId(groupId)
                .watchlistId(watchlistId)
                .userId(userId)
                .name(name)
                .color(color)
                .createdAt(LocalDateTime.now())
                .build();
    }
}
