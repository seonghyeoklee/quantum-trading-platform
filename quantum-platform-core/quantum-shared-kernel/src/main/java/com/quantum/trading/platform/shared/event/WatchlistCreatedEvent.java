package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.WatchlistId;
import lombok.Value;
import lombok.Builder;

import java.time.LocalDateTime;

/**
 * 관심종목 목록 생성 Event
 */
@Value
@Builder
public class WatchlistCreatedEvent {
    WatchlistId watchlistId;
    UserId userId;
    String name;
    String description;
    boolean isDefault;
    LocalDateTime createdAt;
    
    public static WatchlistCreatedEvent of(WatchlistId watchlistId, UserId userId, String name, String description, boolean isDefault) {
        return WatchlistCreatedEvent.builder()
                .watchlistId(watchlistId)
                .userId(userId)
                .name(name)
                .description(description)
                .isDefault(isDefault)
                .createdAt(LocalDateTime.now())
                .build();
    }
}