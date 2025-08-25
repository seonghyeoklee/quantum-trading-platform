package com.quantum.trading.platform.query.projection;

import com.quantum.trading.platform.shared.event.*;
import com.quantum.trading.platform.shared.event.WatchlistDeletedEvent;
import com.quantum.trading.platform.query.view.WatchlistView;
import com.quantum.trading.platform.query.view.WatchlistGroupView;
import com.quantum.trading.platform.query.view.WatchlistItemView;
import com.quantum.trading.platform.query.repository.WatchlistViewRepository;
import com.quantum.trading.platform.query.repository.WatchlistGroupViewRepository;
import com.quantum.trading.platform.query.repository.WatchlistItemViewRepository;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.axonframework.eventhandling.EventHandler;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * 관심종목 관련 이벤트를 처리하여 Query Side View를 업데이트하는 Projection Handler
 * CQRS Event Sourcing → View 동기화
 */
@Component
@RequiredArgsConstructor
@Slf4j
@Transactional
public class WatchlistProjectionHandler {

    private final WatchlistViewRepository watchlistViewRepository;
    private final WatchlistGroupViewRepository watchlistGroupViewRepository;
    private final WatchlistItemViewRepository watchlistItemViewRepository;

    // ===== 관심종목 목록 이벤트 처리 =====

    @EventHandler
    public void on(WatchlistCreatedEvent event) {
        log.info("Processing WatchlistCreatedEvent: {}", event);

        WatchlistView watchlistView = WatchlistView.builder()
                .id(event.getWatchlistId().getValue())
                .userId(event.getUserId().getValue())
                .name(event.getName())
                .description(event.getDescription())
                .isDefault(event.isDefault())
                .sortOrder(0)
                .itemCount(0)
                .createdAt(event.getCreatedAt())
                .updatedAt(event.getCreatedAt())
                .version(0L)
                .build();

        watchlistViewRepository.save(watchlistView);
        log.debug("WatchlistView saved: {}", watchlistView);
    }

    @EventHandler
    public void on(WatchlistDeletedEvent event) {
        log.info("Processing WatchlistDeletedEvent: {}", event);

        try {
            // 1. 관심종목 목록 삭제 (CASCADE로 자동으로 아이템들도 삭제됨)
            watchlistViewRepository.findById(event.getWatchlistId().getValue()).ifPresentOrElse(
                    watchlist -> {
                        watchlistViewRepository.delete(watchlist);
                        log.debug("WatchlistView deleted: {}", watchlist.getId());
                    },
                    () -> {
                        log.warn("WatchlistView not found for deletion: watchlistId={}",
                                event.getWatchlistId().getValue());
                    }
            );

        } catch (Exception e) {
            log.error("Error processing WatchlistDeletedEvent: {}", event, e);
            throw new RuntimeException("Failed to delete watchlist view", e);
        }
    }

    // ===== 관심종목 그룹 이벤트 처리 =====

    @EventHandler
    public void on(WatchlistGroupCreatedEvent event) {
        log.info("Processing WatchlistGroupCreatedEvent: {}", event);

        WatchlistGroupView groupView = WatchlistGroupView.builder()
                .id(event.getGroupId().getValue())
                .watchlistId(event.getWatchlistId().getValue())
                .name(event.getName())
                .color(event.getColor() != null ? event.getColor() : "blue")
                .sortOrder(0)
                .itemCount(0)
                .createdAt(event.getCreatedAt())
                .updatedAt(event.getCreatedAt())
                .version(0L)
                .build();

        watchlistGroupViewRepository.save(groupView);
        log.debug("WatchlistGroupView saved: {}", groupView);
    }

    // ===== 관심종목 아이템 이벤트 처리 =====

    @EventHandler
    public void on(StockAddedToWatchlistEvent event) {
        log.info("Processing StockAddedToWatchlistEvent: {}", event);

        try {
            // 1. 새 아이템 생성
            WatchlistItemView itemView = WatchlistItemView.builder()
                    .id(UUID.randomUUID().toString())
                    .watchlistId(event.getWatchlistId().getValue())
                    .groupId(event.getGroupId() != null ? event.getGroupId().getValue() : null)
                    .symbol(event.getSymbol().getValue())
                    .stockName(event.getStockName())
                    .sortOrder(getNextSortOrder(event.getWatchlistId().getValue()))
                    .note(event.getNote())
                    .addedAt(event.getAddedAt())
                    .updatedAt(event.getAddedAt())
                    .version(0L)
                    .build();

            watchlistItemViewRepository.save(itemView);
            log.debug("WatchlistItemView saved: {}", itemView);

            // 2. 관심종목 목록의 아이템 카운트 증가 (트리거가 처리하지만 명시적으로 업데이트)
            updateWatchlistItemCount(event.getWatchlistId().getValue());

            // 3. 그룹의 아이템 카운트 증가 (그룹이 있는 경우)
            if (event.getGroupId() != null) {
                updateGroupItemCount(event.getGroupId().getValue());
            }

        } catch (Exception e) {
            log.error("Error processing StockAddedToWatchlistEvent: {}", event, e);
            throw new RuntimeException("Failed to add stock to watchlist view", e);
        }
    }

    @EventHandler
    public void on(StockRemovedFromWatchlistEvent event) {
        log.info("Processing StockRemovedFromWatchlistEvent: {}", event);

        try {
            // 1. 기존 아이템 조회 및 삭제
            watchlistItemViewRepository.findByWatchlistIdAndSymbol(
                    event.getWatchlistId().getValue(),
                    event.getSymbol().getValue()
            ).ifPresentOrElse(
                    itemView -> {
                        String groupId = itemView.getGroupId();
                        
                        // 아이템 삭제
                        watchlistItemViewRepository.delete(itemView);
                        log.debug("WatchlistItemView deleted: {}", itemView);

                        // 관심종목 목록의 아이템 카운트 감소
                        updateWatchlistItemCount(event.getWatchlistId().getValue());

                        // 그룹의 아이템 카운트 감소 (그룹이 있었던 경우)
                        if (groupId != null) {
                            updateGroupItemCount(groupId);
                        }
                    },
                    () -> {
                        log.warn("WatchlistItemView not found for removal: watchlistId={}, symbol={}",
                                event.getWatchlistId().getValue(), event.getSymbol().getValue());
                    }
            );

        } catch (Exception e) {
            log.error("Error processing StockRemovedFromWatchlistEvent: {}", event, e);
            throw new RuntimeException("Failed to remove stock from watchlist view", e);
        }
    }

    // ===== Helper 메서드 =====

    private int getNextSortOrder(String watchlistId) {
        return (int) watchlistItemViewRepository.countByWatchlistId(watchlistId);
    }

    private void updateWatchlistItemCount(String watchlistId) {
        watchlistViewRepository.findById(watchlistId).ifPresent(watchlist -> {
            long itemCount = watchlistItemViewRepository.countByWatchlistId(watchlistId);
            watchlist.setItemCount((int) itemCount);
            watchlist.updateTimestamp();
            watchlistViewRepository.save(watchlist);
            log.debug("Updated watchlist item count: watchlistId={}, count={}", watchlistId, itemCount);
        });
    }

    private void updateGroupItemCount(String groupId) {
        watchlistGroupViewRepository.findById(groupId).ifPresent(group -> {
            long itemCount = watchlistItemViewRepository.countByGroupId(groupId);
            group.setItemCount((int) itemCount);
            group.updateTimestamp();
            watchlistGroupViewRepository.save(group);
            log.debug("Updated group item count: groupId={}, count={}", groupId, itemCount);
        });
    }
}