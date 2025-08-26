package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.WatchlistGroupId;
import lombok.Builder;
import lombok.Value;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import java.time.LocalDateTime;

/**
 * 관심종목 그룹 삭제 Command
 */
@Value
@Builder
public class DeleteWatchlistGroupCommand {

    @TargetAggregateIdentifier
    WatchlistGroupId groupId;
    
    @Builder.Default
    LocalDateTime deletedAt = LocalDateTime.now();

    public void validate() {
        if (groupId == null) {
            throw new IllegalArgumentException("GroupId cannot be null");
        }
        if (deletedAt == null) {
            throw new IllegalArgumentException("DeletedAt cannot be null");
        }
    }
}