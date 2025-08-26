package com.quantum.trading.platform.query.repository;

import com.quantum.trading.platform.query.view.WatchlistView;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * 관심종목 목록 조회용 Repository
 * CQRS Query Side Data Access
 */
@Repository
public interface WatchlistViewRepository extends JpaRepository<WatchlistView, String> {

    /**
     * 사용자별 관심종목 목록 조회 (정렬 순서대로)
     */
    List<WatchlistView> findByUserIdOrderBySortOrderAscCreatedAtAsc(String userId);

    /**
     * 사용자별 관심종목 목록 페이징 조회
     */
    Page<WatchlistView> findByUserIdOrderBySortOrderAscCreatedAtAsc(String userId, Pageable pageable);

    /**
     * 사용자의 기본 관심종목 목록 조회
     */
    Optional<WatchlistView> findByUserIdAndIsDefaultTrue(String userId);

    /**
     * 사용자의 관심종목 목록 개수
     */
    long countByUserId(String userId);

    /**
     * 특정 사용자의 특정 관심종목 목록 존재 여부
     */
    boolean existsByIdAndUserId(String watchlistId, String userId);

    /**
     * 특정 사용자의 이름으로 관심종목 목록 검색
     */
    @Query("SELECT w FROM WatchlistView w WHERE w.userId = :userId AND w.name LIKE %:name%")
    List<WatchlistView> findByUserIdAndNameContaining(@Param("userId") String userId, @Param("name") String name);

    /**
     * 사용자별 총 관심종목 아이템 수 합계
     */
    @Query("SELECT COALESCE(SUM(w.itemCount), 0) FROM WatchlistView w WHERE w.userId = :userId")
    long getTotalItemCountByUserId(@Param("userId") String userId);

    /**
     * 아이템이 있는 관심종목 목록만 조회
     */
    List<WatchlistView> findByUserIdAndItemCountGreaterThanOrderBySortOrderAscCreatedAtAsc(String userId, Integer itemCount);

    /**
     * 최근 업데이트된 관심종목 목록 조회 (최신순)
     */
    List<WatchlistView> findByUserIdOrderByUpdatedAtDesc(String userId);

    /**
     * 특정 사용자가 소유한 관심종목 목록인지 확인
     */
    default boolean isOwnedByUser(String watchlistId, String userId) {
        return existsByIdAndUserId(watchlistId, userId);
    }

    /**
     * 사용자의 기본 관심종목 목록이 있는지 확인
     */
    default boolean hasDefaultWatchlist(String userId) {
        return findByUserIdAndIsDefaultTrue(userId).isPresent();
    }
}