package com.quantum.trading.platform.query.repository;

import com.quantum.trading.platform.query.view.WatchlistGroupView;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * 관심종목 그룹 조회용 Repository
 * CQRS Query Side Data Access
 */
@Repository
public interface WatchlistGroupViewRepository extends JpaRepository<WatchlistGroupView, String> {

    /**
     * 특정 관심종목 목록의 그룹들 조회 (정렬 순서대로)
     */
    List<WatchlistGroupView> findByWatchlistIdOrderBySortOrderAscCreatedAtAsc(String watchlistId);

    /**
     * 특정 관심종목 목록의 그룹 개수
     */
    long countByWatchlistId(String watchlistId);

    /**
     * 특정 관심종목 목록에 그룹이 있는지 확인
     */
    boolean existsByWatchlistId(String watchlistId);

    /**
     * 특정 관심종목 목록의 특정 이름을 가진 그룹 존재 여부
     */
    boolean existsByWatchlistIdAndName(String watchlistId, String name);

    /**
     * 특정 관심종목 목록에서 이름으로 그룹 검색
     */
    @Query("SELECT g FROM WatchlistGroupView g WHERE g.watchlistId = :watchlistId AND g.name LIKE %:name%")
    List<WatchlistGroupView> findByWatchlistIdAndNameContaining(@Param("watchlistId") String watchlistId, @Param("name") String name);

    /**
     * 아이템이 있는 그룹만 조회
     */
    List<WatchlistGroupView> findByWatchlistIdAndItemCountGreaterThanOrderBySortOrderAscCreatedAtAsc(String watchlistId, Integer itemCount);

    /**
     * 특정 관심종목 목록의 총 그룹별 아이템 수 합계
     */
    @Query("SELECT COALESCE(SUM(g.itemCount), 0) FROM WatchlistGroupView g WHERE g.watchlistId = :watchlistId")
    long getTotalItemCountByWatchlistId(@Param("watchlistId") String watchlistId);

    /**
     * 색상별 그룹 조회
     */
    List<WatchlistGroupView> findByWatchlistIdAndColorOrderBySortOrderAscCreatedAtAsc(String watchlistId, String color);

    /**
     * 최근 업데이트된 그룹 조회 (최신순)
     */
    List<WatchlistGroupView> findByWatchlistIdOrderByUpdatedAtDesc(String watchlistId);

    /**
     * 특정 관심종목 목록에 그룹이 속하는지 확인
     */
    default boolean belongsToWatchlist(String groupId, String watchlistId) {
        return findById(groupId)
                .map(group -> group.getWatchlistId().equals(watchlistId))
                .orElse(false);
    }
}