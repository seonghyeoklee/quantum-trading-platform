package com.quantum.trading.platform.command.aggregate;

import com.quantum.trading.platform.shared.command.CreateWatchlistGroupCommand;
import com.quantum.trading.platform.shared.event.WatchlistGroupCreatedEvent;
import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.WatchlistId;
import com.quantum.trading.platform.shared.value.WatchlistGroupId;

import lombok.NoArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.AggregateLifecycle;
import org.axonframework.spring.stereotype.Aggregate;

/**
 * 관심종목 그룹 Aggregate
 * CQRS Command Side 집계루트
 */
@Aggregate
@NoArgsConstructor
@Slf4j
public class WatchlistGroup {

    @AggregateIdentifier
    private WatchlistGroupId groupId;
    private WatchlistId watchlistId;
    private UserId userId;
    private String name;
    private String color;
    private boolean isDeleted = false;

    @CommandHandler
    public WatchlistGroup(CreateWatchlistGroupCommand command) {
        log.info("Creating watchlist group with command: {}", command);

        // 1. 명령 검증
        command.validate();

        // 2. 비즈니스 로직 검증
        validateCreateGroup(command);

        // 3. 이벤트 발행
        AggregateLifecycle.apply(WatchlistGroupCreatedEvent.of(
            command.groupId(),
            command.watchlistId(),
            command.userId(),
            command.name(),
            command.color()
        ));
    }

    // ===== Event Sourcing Handlers =====

    @EventSourcingHandler
    public void on(WatchlistGroupCreatedEvent event) {
        log.debug("Applying WatchlistGroupCreatedEvent: {}", event);
        this.groupId = event.groupId();
        this.watchlistId = event.watchlistId();
        this.userId = event.userId();
        this.name = event.name();
        this.color = event.color() != null ? event.color() : "blue";
        this.isDeleted = false;
    }

    // ===== 비즈니스 로직 검증 메서드 =====

    private void validateCreateGroup(CreateWatchlistGroupCommand command) {
        // 비즈니스 규칙 검증
        if (command.name().trim().isEmpty()) {
            throw new IllegalArgumentException("Group name cannot be empty");
        }

        // 색상 유효성 검증 (선택적)
        if (command.color() != null && !isValidColor(command.color())) {
            throw new IllegalArgumentException("Invalid color format: " + command.color());
        }
    }

    private boolean isValidColor(String color) {
        // 기본적인 색상 값들 또는 hex 색상 코드 검증
        String[] validColors = {"red", "blue", "green", "yellow", "purple", "orange", "pink", "gray", "black"};

        for (String validColor : validColors) {
            if (validColor.equals(color.toLowerCase())) {
                return true;
            }
        }

        // hex 색상 코드 검증 (#RRGGBB 또는 #RGB)
        if (color.matches("^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")) {
            return true;
        }

        return false;
    }

    // ===== Getter 메서드 (테스트용) =====

    public WatchlistGroupId getGroupId() {
        return groupId;
    }

    public WatchlistId getWatchlistId() {
        return watchlistId;
    }

    public UserId getUserId() {
        return userId;
    }

    public String getName() {
        return name;
    }

    public String getColor() {
        return color;
    }

    public boolean isDeleted() {
        return isDeleted;
    }
}
