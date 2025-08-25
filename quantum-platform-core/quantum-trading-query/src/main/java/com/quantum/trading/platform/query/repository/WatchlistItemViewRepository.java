package com.quantum.trading.platform.query.repository;

import com.quantum.trading.platform.query.view.WatchlistItemView;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * 관심종목 아이템 조회용 Repository
 * CQRS Query Side Data Access
 */
@Repository
public interface WatchlistItemViewRepository extends JpaRepository<WatchlistItemView, String> {

    /**
     * 특정 관심종목 목록의 아이템들 조회 (정렬 순서대로)
     */
    List<WatchlistItemView> findByWatchlistIdOrderBySortOrderAscAddedAtAsc(String watchlistId);

    /**
     * 특정 관심종목 목록의 아이템들 페이징 조회
     */
    Page<WatchlistItemView> findByWatchlistIdOrderBySortOrderAscAddedAtAsc(String watchlistId, Pageable pageable);

    /**
     * 특정 그룹의 아이템들 조회 (정렬 순서대로)
     */
    List<WatchlistItemView> findByGroupIdOrderBySortOrderAscAddedAtAsc(String groupId);

    /**
     * 그룹이 없는 아이템들 조회 (정렬 순서대로)
     */
    List<WatchlistItemView> findByWatchlistIdAndGroupIdIsNullOrderBySortOrderAscAddedAtAsc(String watchlistId);

    /**
     * 특정 관심종목 목록에서 심볼로 아이템 조회
     */
    Optional<WatchlistItemView> findByWatchlistIdAndSymbol(String watchlistId, String symbol);

    /**
     * 특정 관심종목 목록의 아이템 개수
     */
    long countByWatchlistId(String watchlistId);

    /**
     * 특정 그룹의 아이템 개수
     */
    long countByGroupId(String groupId);

    /**
     * 그룹이 없는 아이템 개수
     */
    long countByWatchlistIdAndGroupIdIsNull(String watchlistId);

    /**
     * 특정 관심종목 목록에 특정 심볼이 존재하는지 확인
     */
    boolean existsByWatchlistIdAndSymbol(String watchlistId, String symbol);

    /**
     * 특정 관심종목 목록에서 종목명으로 검색
     */
    @Query("SELECT i FROM WatchlistItemView i WHERE i.watchlistId = :watchlistId AND (i.stockName LIKE %:query% OR i.symbol LIKE %:query%)")
    List<WatchlistItemView> searchByWatchlistIdAndQuery(@Param("watchlistId") String watchlistId, @Param("query") String query);

    /**
     * 최근 추가된 아이템들 조회 (최신순)
     */
    List<WatchlistItemView> findByWatchlistIdOrderByAddedAtDesc(String watchlistId);

    /**
     * 최근 추가된 아이템들 조회 (최신순, 제한)
     */
    List<WatchlistItemView> findTop10ByWatchlistIdOrderByAddedAtDesc(String watchlistId);

    /**
     * 메모가 있는 아이템들 조회
     */
    List<WatchlistItemView> findByWatchlistIdAndNoteIsNotNullOrderBySortOrderAscAddedAtAsc(String watchlistId);

    /**
     * 특정 심볼을 포함한 모든 관심종목 목록에서 아이템 조회
     */
    List<WatchlistItemView> findBySymbolOrderByAddedAtDesc(String symbol);

    /**
     * 특정 사용자의 모든 관심종목에서 특정 심볼 검색
     */
    @Query("SELECT i FROM WatchlistItemView i JOIN WatchlistView w ON i.watchlistId = w.id WHERE w.userId = :userId AND i.symbol = :symbol")
    List<WatchlistItemView> findByUserIdAndSymbol(@Param("userId") String userId, @Param("symbol") String symbol);

    /**
     * 특정 사용자의 모든 관심종목에서 종목 검색
     */
    @Query("SELECT i FROM WatchlistItemView i JOIN WatchlistView w ON i.watchlistId = w.id WHERE w.userId = :userId AND (i.stockName LIKE %:query% OR i.symbol LIKE %:query%)")
    List<WatchlistItemView> searchByUserIdAndQuery(@Param("userId") String userId, @Param("query") String query);

    /**
     * 특정 관심종목 목록에 아이템이 속하는지 확인
     */
    default boolean belongsToWatchlist(String itemId, String watchlistId) {
        return findById(itemId)
                .map(item -> item.getWatchlistId().equals(watchlistId))
                .orElse(false);
    }

    /**
     * 중복 종목 추가 방지를 위한 확인
     */
    default boolean isDuplicateStock(String watchlistId, String symbol) {
        return existsByWatchlistIdAndSymbol(watchlistId, symbol);
    }
}