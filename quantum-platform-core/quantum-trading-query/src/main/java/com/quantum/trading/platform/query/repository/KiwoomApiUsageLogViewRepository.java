package com.quantum.trading.platform.query.repository;

import com.quantum.trading.platform.query.view.KiwoomApiUsageLogView;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;

/**
 * 키움증권 API 사용 로그 조회용 Repository
 * 
 * Spring Data JPA 기반으로 API 사용 통계 및 모니터링 쿼리 최적화
 */
@Repository
public interface KiwoomApiUsageLogViewRepository extends JpaRepository<KiwoomApiUsageLogView, Long> {

    /**
     * 사용자별 API 사용 로그 조회 (페이징)
     */
    Page<KiwoomApiUsageLogView> findByUserIdOrderByUsageTimestampDesc(String userId, Pageable pageable);

    /**
     * 키움증권 계좌별 API 사용 로그 조회
     */
    Page<KiwoomApiUsageLogView> findByKiwoomAccountIdOrderByUsageTimestampDesc(String kiwoomAccountId, Pageable pageable);

    /**
     * 특정 기간의 API 사용 로그 조회
     */
    @Query("SELECT log FROM KiwoomApiUsageLogView log WHERE log.usageTimestamp BETWEEN :startTime AND :endTime ORDER BY log.usageTimestamp DESC")
    Page<KiwoomApiUsageLogView> findByUsageTimestampBetween(
            @Param("startTime") Instant startTime, 
            @Param("endTime") Instant endTime, 
            Pageable pageable
    );

    /**
     * 사용자별 특정 기간 API 사용 로그 조회
     */
    @Query("SELECT log FROM KiwoomApiUsageLogView log WHERE log.userId = :userId AND log.usageTimestamp BETWEEN :startTime AND :endTime ORDER BY log.usageTimestamp DESC")
    List<KiwoomApiUsageLogView> findByUserIdAndUsageTimestampBetween(
            @Param("userId") String userId,
            @Param("startTime") Instant startTime,
            @Param("endTime") Instant endTime
    );

    /**
     * 성공/실패별 API 사용 로그 조회
     */
    Page<KiwoomApiUsageLogView> findBySuccessOrderByUsageTimestampDesc(Boolean success, Pageable pageable);

    /**
     * 특정 API 엔드포인트 사용 로그 조회
     */
    Page<KiwoomApiUsageLogView> findByApiEndpointOrderByUsageTimestampDesc(String apiEndpoint, Pageable pageable);

    /**
     * 사용자별 API 사용 통계 (성공 횟수)
     */
    @Query("SELECT COUNT(log) FROM KiwoomApiUsageLogView log WHERE log.userId = :userId AND log.success = true AND log.usageTimestamp >= :fromDate")
    long countSuccessfulApiCallsByUserSince(@Param("userId") String userId, @Param("fromDate") Instant fromDate);

    /**
     * 사용자별 API 사용 통계 (실패 횟수)
     */
    @Query("SELECT COUNT(log) FROM KiwoomApiUsageLogView log WHERE log.userId = :userId AND log.success = false AND log.usageTimestamp >= :fromDate")
    long countFailedApiCallsByUserSince(@Param("userId") String userId, @Param("fromDate") Instant fromDate);

    /**
     * 전체 API 사용량 통계 (일별)
     */
    @Query("SELECT DATE(log.usageTimestamp) as date, COUNT(log) as count FROM KiwoomApiUsageLogView log WHERE log.usageTimestamp >= :fromDate GROUP BY DATE(log.usageTimestamp) ORDER BY date DESC")
    List<Object[]> getDailyApiUsageStats(@Param("fromDate") Instant fromDate);

    /**
     * API 엔드포인트별 사용 통계
     */
    @Query("SELECT log.apiEndpoint, COUNT(log) as count FROM KiwoomApiUsageLogView log WHERE log.usageTimestamp >= :fromDate GROUP BY log.apiEndpoint ORDER BY count DESC")
    List<Object[]> getApiEndpointUsageStats(@Param("fromDate") Instant fromDate);

    /**
     * 최근 실패한 API 호출 조회
     */
    @Query("SELECT log FROM KiwoomApiUsageLogView log WHERE log.success = false AND log.usageTimestamp >= :fromDate ORDER BY log.usageTimestamp DESC")
    List<KiwoomApiUsageLogView> findRecentFailedApiCalls(@Param("fromDate") Instant fromDate);

    /**
     * 사용자별 평균 요청 크기 조회
     */
    @Query("SELECT AVG(log.requestSize) FROM KiwoomApiUsageLogView log WHERE log.userId = :userId AND log.usageTimestamp >= :fromDate")
    Double getAverageRequestSizeByUser(@Param("userId") String userId, @Param("fromDate") Instant fromDate);

    /**
     * 키움증권 계좌별 최근 API 사용 시점 조회
     */
    @Query("SELECT MAX(log.usageTimestamp) FROM KiwoomApiUsageLogView log WHERE log.kiwoomAccountId = :kiwoomAccountId")
    Instant findLastUsageByKiwoomAccount(@Param("kiwoomAccountId") String kiwoomAccountId);

    /**
     * 활성 사용자 조회 (최근 API 사용한 사용자)
     */
    @Query("SELECT DISTINCT log.userId FROM KiwoomApiUsageLogView log WHERE log.usageTimestamp >= :fromDate")
    List<String> findActiveUsersSince(@Param("fromDate") Instant fromDate);

    /**
     * 특정 사용자의 최근 API 사용 내역 (제한된 개수)
     */
    @Query("SELECT log FROM KiwoomApiUsageLogView log WHERE log.userId = :userId ORDER BY log.usageTimestamp DESC LIMIT :limit")
    List<KiwoomApiUsageLogView> findRecentApiUsageByUser(@Param("userId") String userId, @Param("limit") int limit);
}