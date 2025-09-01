package com.quantum.web.repository;

import com.quantum.web.entity.TradingModeHistory;
import com.quantum.web.dto.TradingConfigDto;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 트레이딩 모드 변경 이력 리포지토리
 */
@Repository
public interface TradingModeHistoryRepository extends JpaRepository<TradingModeHistory, Long> {

    /**
     * 사용자별 모드 변경 이력 조회 (최신순)
     */
    List<TradingModeHistory> findByUserIdOrderByCreatedAtDesc(String userId);

    /**
     * 특정 기간 내 사용자 모드 변경 횟수 조회
     */
    @Query("SELECT COUNT(h) FROM TradingModeHistory h WHERE h.userId = :userId AND h.createdAt >= :since")
    long countByUserIdAndCreatedAtAfter(@Param("userId") String userId, @Param("since") LocalDateTime since);

    /**
     * 전체 모드 변경 이력 조회 (최신순, 페이징)
     */
    List<TradingModeHistory> findAllByOrderByCreatedAtDesc();

    /**
     * 특정 모드로 변경된 이력 조회
     */
    List<TradingModeHistory> findByNewModeOrderByCreatedAtDesc(TradingConfigDto.TradingMode newMode);

    /**
     * 특정 기간 내 전체 모드 변경 이력 조회
     */
    @Query("SELECT h FROM TradingModeHistory h WHERE h.createdAt >= :since ORDER BY h.createdAt DESC")
    List<TradingModeHistory> findRecentHistory(@Param("since") LocalDateTime since);

    /**
     * 사용자의 최근 모드 변경 이력 조회 (1건)
     */
    @Query("SELECT h FROM TradingModeHistory h WHERE h.userId = :userId ORDER BY h.createdAt DESC LIMIT 1")
    TradingModeHistory findLatestByUserId(@Param("userId") String userId);

    /**
     * IP 주소별 모드 변경 횟수 조회 (보안 모니터링용)
     */
    @Query("SELECT h.ipAddress, COUNT(h) FROM TradingModeHistory h WHERE h.createdAt >= :since GROUP BY h.ipAddress ORDER BY COUNT(h) DESC")
    List<Object[]> findModeChangesByIpAddress(@Param("since") LocalDateTime since);
}