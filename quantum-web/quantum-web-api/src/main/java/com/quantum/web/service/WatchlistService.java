package com.quantum.web.service;

import com.quantum.trading.platform.query.service.WatchlistQueryService;
import com.quantum.trading.platform.shared.command.*;
import com.quantum.trading.platform.shared.value.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

/**
 * Watchlist Service
 * 
 * 관심종목 관련 비즈니스 로직을 처리하는 서비스
 * - CQRS Command/Query 모델과 연동
 * - Event Sourcing을 통한 관심종목 상태 관리
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class WatchlistService {

    private final CommandGateway commandGateway;
    private final WatchlistQueryService watchlistQueryService;

    /**
     * 관심종목 목록 생성
     */
    public String createWatchlist(String userId, String name, String description, boolean isDefault) {
        log.info("Creating watchlist - userId: {}, name: {}, isDefault: {}", userId, name, isDefault);
        
        try {
            WatchlistId watchlistId = WatchlistId.generate();
            
            CreateWatchlistCommand command = CreateWatchlistCommand.of(
                    watchlistId,
                    UserId.of(userId),
                    name,
                    description,
                    isDefault
            );

            commandGateway.sendAndWait(command);
            
            log.info("Watchlist created successfully - watchlistId: {}, userId: {}", 
                    watchlistId.getValue(), userId);
            
            return watchlistId.getValue();
            
        } catch (Exception e) {
            log.error("Failed to create watchlist for user: {}", userId, e);
            throw new RuntimeException("관심종목 목록 생성에 실패했습니다", e);
        }
    }

    /**
     * 관심종목 목록 삭제
     */
    public void deleteWatchlist(String watchlistId, String userId) {
        log.info("Deleting watchlist - watchlistId: {}, userId: {}", watchlistId, userId);
        
        try {
            // 권한 확인
            if (!watchlistQueryService.isWatchlistOwner(watchlistId, userId)) {
                throw new IllegalArgumentException("관심종목 목록을 삭제할 권한이 없습니다");
            }
            
            DeleteWatchlistCommand command = DeleteWatchlistCommand.builder()
                    .watchlistId(WatchlistId.of(watchlistId))
                    .userId(UserId.of(userId))
                    .build();

            commandGateway.sendAndWait(command);
            
            log.info("Watchlist deleted successfully - watchlistId: {}, userId: {}", watchlistId, userId);
            
        } catch (Exception e) {
            log.error("Failed to delete watchlist: {}", watchlistId, e);
            throw new RuntimeException("관심종목 목록 삭제에 실패했습니다", e);
        }
    }

    /**
     * 관심종목에 종목 추가
     */
    public void addStockToWatchlist(String watchlistId, String userId, String groupId, 
                                   String symbol, String stockName, String note) {
        log.info("Adding stock to watchlist - watchlistId: {}, symbol: {}, userId: {}", 
                watchlistId, symbol, userId);
        
        try {
            // 권한 확인
            if (!watchlistQueryService.isWatchlistOwner(watchlistId, userId)) {
                throw new IllegalArgumentException("관심종목 목록에 접근할 권한이 없습니다");
            }

            // 중복 확인
            if (watchlistQueryService.isStockInWatchlist(watchlistId, symbol)) {
                throw new IllegalArgumentException("이미 관심종목에 등록된 종목입니다");
            }

            AddStockToWatchlistCommand command = AddStockToWatchlistCommand.of(
                    WatchlistId.of(watchlistId),
                    UserId.of(userId),
                    Symbol.of(symbol),
                    stockName,
                    groupId != null ? WatchlistGroupId.of(groupId) : null,
                    note
            );

            commandGateway.sendAndWait(command);
            
            log.info("Stock added to watchlist successfully - watchlistId: {}, symbol: {}, userId: {}", 
                    watchlistId, symbol, userId);
            
        } catch (Exception e) {
            log.error("Failed to add stock to watchlist - watchlistId: {}, symbol: {}", 
                    watchlistId, symbol, e);
            throw new RuntimeException("관심종목 추가에 실패했습니다", e);
        }
    }

    /**
     * 관심종목에서 종목 제거
     */
    public void removeStockFromWatchlist(String watchlistId, String userId, String symbol) {
        log.info("Removing stock from watchlist - watchlistId: {}, symbol: {}, userId: {}", 
                watchlistId, symbol, userId);
        
        try {
            // 권한 확인
            if (!watchlistQueryService.isWatchlistOwner(watchlistId, userId)) {
                throw new IllegalArgumentException("관심종목 목록에 접근할 권한이 없습니다");
            }

            // 존재 확인
            if (!watchlistQueryService.isStockInWatchlist(watchlistId, symbol)) {
                throw new IllegalArgumentException("관심종목에서 해당 종목을 찾을 수 없습니다");
            }

            RemoveStockFromWatchlistCommand command = RemoveStockFromWatchlistCommand.of(
                    WatchlistId.of(watchlistId),
                    UserId.of(userId),
                    Symbol.of(symbol)
            );

            commandGateway.sendAndWait(command);
            
            log.info("Stock removed from watchlist successfully - watchlistId: {}, symbol: {}, userId: {}", 
                    watchlistId, symbol, userId);
            
        } catch (Exception e) {
            log.error("Failed to remove stock from watchlist - watchlistId: {}, symbol: {}", 
                    watchlistId, symbol, e);
            throw new RuntimeException("관심종목 제거에 실패했습니다", e);
        }
    }

    /**
     * 관심종목 그룹 생성
     */
    public String createWatchlistGroup(String watchlistId, String userId, String name, String color) {
        log.info("Creating watchlist group - watchlistId: {}, name: {}, userId: {}", 
                watchlistId, name, userId);
        
        try {
            // 권한 확인
            if (!watchlistQueryService.isWatchlistOwner(watchlistId, userId)) {
                throw new IllegalArgumentException("관심종목 목록에 접근할 권한이 없습니다");
            }

            WatchlistGroupId groupId = WatchlistGroupId.generate();
            
            CreateWatchlistGroupCommand command = CreateWatchlistGroupCommand.of(
                    groupId,
                    WatchlistId.of(watchlistId),
                    UserId.of(userId),
                    name,
                    color
            );

            commandGateway.sendAndWait(command);
            
            log.info("Watchlist group created successfully - groupId: {}, watchlistId: {}, userId: {}", 
                    groupId.getValue(), watchlistId, userId);
            
            return groupId.getValue();
            
        } catch (Exception e) {
            log.error("Failed to create watchlist group - watchlistId: {}, name: {}", 
                    watchlistId, name, e);
            throw new RuntimeException("관심종목 그룹 생성에 실패했습니다", e);
        }
    }

    /**
     * 관심종목 그룹 삭제
     */
    public void deleteWatchlistGroup(String groupId, String userId) {
        log.info("Deleting watchlist group - groupId: {}, userId: {}", groupId, userId);
        
        try {
            // 권한 확인
            if (!watchlistQueryService.isGroupOwner(groupId, userId)) {
                throw new IllegalArgumentException("관심종목 그룹을 삭제할 권한이 없습니다");
            }

            DeleteWatchlistGroupCommand command = DeleteWatchlistGroupCommand.builder()
                    .groupId(WatchlistGroupId.of(groupId))
                    .build();

            commandGateway.sendAndWait(command);
            
            log.info("Watchlist group deleted successfully - groupId: {}, userId: {}", groupId, userId);
            
        } catch (Exception e) {
            log.error("Failed to delete watchlist group: {}", groupId, e);
            throw new RuntimeException("관심종목 그룹 삭제에 실패했습니다", e);
        }
    }

    // ===== Query 메서드들 (QueryService에 위임) =====

    public Page<com.quantum.trading.platform.query.view.WatchlistView> getUserWatchlists(String userId, Pageable pageable) {
        return watchlistQueryService.getUserWatchlists(userId, pageable);
    }

    public com.quantum.trading.platform.query.view.WatchlistView getWatchlist(String watchlistId, String userId) {
        return watchlistQueryService.getWatchlistById(watchlistId, userId).orElse(null);
    }

    public boolean isWatchlistOwner(String watchlistId, String userId) {
        return watchlistQueryService.isWatchlistOwner(watchlistId, userId);
    }

    public boolean isStockInWatchlist(String watchlistId, String symbol) {
        return watchlistQueryService.isStockInWatchlist(watchlistId, symbol);
    }

    public WatchlistQueryService.UserWatchlistStats getUserWatchlistStats(String userId) {
        return watchlistQueryService.getUserWatchlistStats(userId);
    }
}