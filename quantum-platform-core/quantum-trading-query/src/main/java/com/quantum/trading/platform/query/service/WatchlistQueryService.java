package com.quantum.trading.platform.query.service;

import com.quantum.trading.platform.query.view.WatchlistView;
import com.quantum.trading.platform.query.view.WatchlistGroupView;
import com.quantum.trading.platform.query.view.WatchlistItemView;
import com.quantum.trading.platform.query.repository.WatchlistViewRepository;
import com.quantum.trading.platform.query.repository.WatchlistGroupViewRepository;
import com.quantum.trading.platform.query.repository.WatchlistItemViewRepository;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

/**
 * 관심종목 조회 전용 서비스
 * CQRS Query Side Business Logic
 */
@Service
@RequiredArgsConstructor
@Slf4j
@Transactional(readOnly = true)
public class WatchlistQueryService {

    private final WatchlistViewRepository watchlistViewRepository;
    private final WatchlistGroupViewRepository watchlistGroupViewRepository;
    private final WatchlistItemViewRepository watchlistItemViewRepository;

    // ===== 관심종목 목록 조회 =====

    /**
     * 사용자의 모든 관심종목 목록 조회
     */
    public List<WatchlistView> getUserWatchlists(String userId) {
        log.debug("Getting user watchlists: userId={}", userId);
        return watchlistViewRepository.findByUserIdOrderBySortOrderAscCreatedAtAsc(userId);
    }

    /**
     * 사용자의 관심종목 목록 페이징 조회
     */
    public Page<WatchlistView> getUserWatchlists(String userId, Pageable pageable) {
        log.debug("Getting user watchlists with paging: userId={}, pageable={}", userId, pageable);
        return watchlistViewRepository.findByUserIdOrderBySortOrderAscCreatedAtAsc(userId, pageable);
    }

    /**
     * 특정 관심종목 목록 조회 (사용자 권한 확인 포함)
     */
    public Optional<WatchlistView> getWatchlistById(String watchlistId, String userId) {
        log.debug("Getting watchlist by id: watchlistId={}, userId={}", watchlistId, userId);
        
        return watchlistViewRepository.findById(watchlistId)
                .filter(watchlist -> watchlist.getUserId().equals(userId));
    }

    /**
     * 사용자의 기본 관심종목 목록 조회
     */
    public Optional<WatchlistView> getDefaultWatchlist(String userId) {
        log.debug("Getting default watchlist: userId={}", userId);
        return watchlistViewRepository.findByUserIdAndIsDefaultTrue(userId);
    }

    /**
     * 사용자의 관심종목 목록 개수
     */
    public long getUserWatchlistCount(String userId) {
        log.debug("Getting user watchlist count: userId={}", userId);
        return watchlistViewRepository.countByUserId(userId);
    }

    /**
     * 사용자의 총 관심종목 아이템 수
     */
    public long getUserTotalItemCount(String userId) {
        log.debug("Getting user total item count: userId={}", userId);
        return watchlistViewRepository.getTotalItemCountByUserId(userId);
    }

    /**
     * 관심종목 목록 검색
     */
    public List<WatchlistView> searchWatchlists(String userId, String query) {
        log.debug("Searching watchlists: userId={}, query={}", userId, query);
        return watchlistViewRepository.findByUserIdAndNameContaining(userId, query);
    }

    // ===== 관심종목 그룹 조회 =====

    /**
     * 특정 관심종목 목록의 그룹들 조회
     */
    public List<WatchlistGroupView> getWatchlistGroups(String watchlistId) {
        log.debug("Getting watchlist groups: watchlistId={}", watchlistId);
        return watchlistGroupViewRepository.findByWatchlistIdOrderBySortOrderAscCreatedAtAsc(watchlistId);
    }

    /**
     * 특정 그룹 조회
     */
    public Optional<WatchlistGroupView> getGroupById(String groupId) {
        log.debug("Getting group by id: groupId={}", groupId);
        return watchlistGroupViewRepository.findById(groupId);
    }

    /**
     * 아이템이 있는 그룹만 조회
     */
    public List<WatchlistGroupView> getGroupsWithItems(String watchlistId) {
        log.debug("Getting groups with items: watchlistId={}", watchlistId);
        return watchlistGroupViewRepository.findByWatchlistIdAndItemCountGreaterThanOrderBySortOrderAscCreatedAtAsc(watchlistId, 0);
    }

    // ===== 관심종목 아이템 조회 =====

    /**
     * 특정 관심종목 목록의 모든 아이템 조회
     */
    public List<WatchlistItemView> getWatchlistItems(String watchlistId) {
        log.debug("Getting watchlist items: watchlistId={}", watchlistId);
        return watchlistItemViewRepository.findByWatchlistIdOrderBySortOrderAscAddedAtAsc(watchlistId);
    }

    /**
     * 특정 관심종목 목록의 아이템 페이징 조회
     */
    public Page<WatchlistItemView> getWatchlistItems(String watchlistId, Pageable pageable) {
        log.debug("Getting watchlist items with paging: watchlistId={}, pageable={}", watchlistId, pageable);
        return watchlistItemViewRepository.findByWatchlistIdOrderBySortOrderAscAddedAtAsc(watchlistId, pageable);
    }

    /**
     * 특정 그룹의 아이템들 조회
     */
    public List<WatchlistItemView> getGroupItems(String groupId) {
        log.debug("Getting group items: groupId={}", groupId);
        return watchlistItemViewRepository.findByGroupIdOrderBySortOrderAscAddedAtAsc(groupId);
    }

    /**
     * 그룹이 없는 아이템들 조회
     */
    public List<WatchlistItemView> getUngroupedItems(String watchlistId) {
        log.debug("Getting ungrouped items: watchlistId={}", watchlistId);
        return watchlistItemViewRepository.findByWatchlistIdAndGroupIdIsNullOrderBySortOrderAscAddedAtAsc(watchlistId);
    }

    /**
     * 특정 종목 조회
     */
    public Optional<WatchlistItemView> getWatchlistItem(String watchlistId, String symbol) {
        log.debug("Getting watchlist item: watchlistId={}, symbol={}", watchlistId, symbol);
        return watchlistItemViewRepository.findByWatchlistIdAndSymbol(watchlistId, symbol);
    }

    /**
     * 특정 종목이 관심종목에 있는지 확인
     */
    public boolean isStockInWatchlist(String watchlistId, String symbol) {
        log.debug("Checking if stock in watchlist: watchlistId={}, symbol={}", watchlistId, symbol);
        return watchlistItemViewRepository.existsByWatchlistIdAndSymbol(watchlistId, symbol);
    }

    /**
     * 사용자의 모든 관심종목에서 특정 종목 검색
     */
    public List<WatchlistItemView> findUserStock(String userId, String symbol) {
        log.debug("Finding user stock: userId={}, symbol={}", userId, symbol);
        return watchlistItemViewRepository.findByUserIdAndSymbol(userId, symbol);
    }

    /**
     * 관심종목 아이템 검색
     */
    public List<WatchlistItemView> searchWatchlistItems(String watchlistId, String query) {
        log.debug("Searching watchlist items: watchlistId={}, query={}", watchlistId, query);
        return watchlistItemViewRepository.searchByWatchlistIdAndQuery(watchlistId, query);
    }

    /**
     * 사용자의 모든 관심종목에서 종목 검색
     */
    public List<WatchlistItemView> searchUserStocks(String userId, String query) {
        log.debug("Searching user stocks: userId={}, query={}", userId, query);
        return watchlistItemViewRepository.searchByUserIdAndQuery(userId, query);
    }

    /**
     * 최근 추가된 아이템들 조회
     */
    public List<WatchlistItemView> getRecentItems(String watchlistId, int limit) {
        log.debug("Getting recent items: watchlistId={}, limit={}", watchlistId, limit);
        if (limit <= 10) {
            return watchlistItemViewRepository.findTop10ByWatchlistIdOrderByAddedAtDesc(watchlistId);
        } else {
            return watchlistItemViewRepository.findByWatchlistIdOrderByAddedAtDesc(watchlistId);
        }
    }

    // ===== 권한 검증 메서드 =====

    /**
     * 사용자가 관심종목 목록의 소유자인지 확인
     */
    public boolean isWatchlistOwner(String watchlistId, String userId) {
        log.debug("Checking watchlist ownership: watchlistId={}, userId={}", watchlistId, userId);
        return watchlistViewRepository.isOwnedByUser(watchlistId, userId);
    }

    /**
     * 사용자가 그룹의 소유자인지 확인
     */
    public boolean isGroupOwner(String groupId, String userId) {
        log.debug("Checking group ownership: groupId={}, userId={}", groupId, userId);
        return watchlistGroupViewRepository.findById(groupId)
                .map(group -> isWatchlistOwner(group.getWatchlistId(), userId))
                .orElse(false);
    }

    // ===== 통계 조회 =====

    /**
     * 사용자 관심종목 통계 조회
     */
    public UserWatchlistStats getUserWatchlistStats(String userId) {
        log.debug("Getting user watchlist stats: userId={}", userId);
        
        long watchlistCount = getUserWatchlistCount(userId);
        long totalItemCount = getUserTotalItemCount(userId);
        boolean hasDefault = watchlistViewRepository.hasDefaultWatchlist(userId);
        
        return UserWatchlistStats.builder()
                .userId(userId)
                .watchlistCount(watchlistCount)
                .totalItemCount(totalItemCount)
                .hasDefaultWatchlist(hasDefault)
                .build();
    }

    // ===== 내부 DTO 클래스 =====

    @lombok.Value
    @lombok.Builder
    public static class UserWatchlistStats {
        String userId;
        long watchlistCount;
        long totalItemCount;
        boolean hasDefaultWatchlist;
    }
}