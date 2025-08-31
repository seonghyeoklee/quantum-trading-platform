package com.quantum.web.repository;

import com.quantum.web.entity.AutoTradingStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * 자동매매 상태 Repository
 *
 * 자동매매 상태 엔티티에 대한 데이터 액세스를 담당
 */
@Repository
public interface AutoTradingStatusRepository extends JpaRepository<AutoTradingStatus, String> {

    /**
     * 설정 ID로 상태 조회
     *
     * @param configId 설정 ID
     * @return 해당 설정의 상태 (Optional)
     */
    Optional<AutoTradingStatus> findByConfigId(String configId);

    /**
     * 상태별 조회
     *
     * @param status 상태 ("running", "paused", "stopped", "error")
     * @return 해당 상태의 목록
     */
    List<AutoTradingStatus> findByStatus(String status);

    /**
     * 실행 중인 상태 목록 조회
     *
     * @return 실행 중인 자동매매 목록
     */
    @Query("SELECT s FROM AutoTradingStatus s WHERE s.status = 'running'")
    List<AutoTradingStatus> findRunningStatus();

    /**
     * 최근 업데이트된 상태 조회 (수정일 기준 내림차순)
     *
     * @param limit 조회 개수
     * @return 최근 업데이트된 상태 목록
     */
    @Query("SELECT s FROM AutoTradingStatus s ORDER BY s.updatedAt DESC LIMIT :limit")
    List<AutoTradingStatus> findRecentlyUpdated(@Param("limit") int limit);

    /**
     * 특정 기간 동안 시작된 자동매매 조회
     *
     * @param startDate 시작일
     * @param endDate 종료일
     * @return 기간 내 시작된 자동매매 목록
     */
    List<AutoTradingStatus> findByStartedAtBetween(LocalDateTime startDate, LocalDateTime endDate);

    /**
     * 특정 기간 동안 정지된 자동매매 조회
     *
     * @param startDate 시작일
     * @param endDate 종료일
     * @return 기간 내 정지된 자동매매 목록
     */
    List<AutoTradingStatus> findByStoppedAtBetween(LocalDateTime startDate, LocalDateTime endDate);

    /**
     * 수익률 기준 상위 성과 조회
     *
     * @param limit 조회 개수
     * @return 수익률 상위 자동매매 목록
     */
    @Query("SELECT s FROM AutoTradingStatus s WHERE s.totalReturn IS NOT NULL ORDER BY s.totalReturn DESC LIMIT :limit")
    List<AutoTradingStatus> findTopPerformers(@Param("limit") int limit);

    /**
     * 손실률 기준 하위 성과 조회
     *
     * @param limit 조회 개수
     * @return 손실률 하위 자동매매 목록
     */
    @Query("SELECT s FROM AutoTradingStatus s WHERE s.totalReturn IS NOT NULL ORDER BY s.totalReturn ASC LIMIT :limit")
    List<AutoTradingStatus> findWorstPerformers(@Param("limit") int limit);

    /**
     * 특정 수익률 이상의 자동매매 조회
     *
     * @param minReturn 최소 수익률
     * @return 최소 수익률 이상의 자동매매 목록
     */
    @Query("SELECT s FROM AutoTradingStatus s WHERE s.totalReturn >= :minReturn")
    List<AutoTradingStatus> findByMinReturn(@Param("minReturn") BigDecimal minReturn);

    /**
     * 특정 거래 횟수 이상의 자동매매 조회
     *
     * @param minTrades 최소 거래 횟수
     * @return 최소 거래 횟수 이상의 자동매매 목록
     */
    @Query("SELECT s FROM AutoTradingStatus s WHERE s.totalTrades >= :minTrades")
    List<AutoTradingStatus> findByMinTrades(@Param("minTrades") int minTrades);

    /**
     * 승률 기준 조회
     *
     * @param minWinRate 최소 승률
     * @return 최소 승률 이상의 자동매매 목록
     */
    @Query("SELECT s FROM AutoTradingStatus s WHERE (s.winningTrades * 100.0 / s.totalTrades) >= :minWinRate AND s.totalTrades > 0")
    List<AutoTradingStatus> findByMinWinRate(@Param("minWinRate") double minWinRate);

    /**
     * 최대 낙폭 기준 조회
     *
     * @param maxDrawdown 최대 허용 낙폭
     * @return 최대 낙폭 이하의 자동매매 목록
     */
    @Query("SELECT s FROM AutoTradingStatus s WHERE s.maxDrawdown <= :maxDrawdown")
    List<AutoTradingStatus> findByMaxDrawdown(@Param("maxDrawdown") BigDecimal maxDrawdown);

    /**
     * 상태별 개수 조회
     *
     * @param status 상태
     * @return 해당 상태의 개수
     */
    long countByStatus(String status);

    /**
     * 실행 중인 자동매매 개수 조회
     *
     * @return 실행 중인 개수
     */
    @Query("SELECT COUNT(s) FROM AutoTradingStatus s WHERE s.status = 'running'")
    long countRunningStatus();

    /**
     * 전체 수익률 통계 조회
     *
     * @return [평균 수익률, 최대 수익률, 최소 수익률]
     */
    @Query("SELECT AVG(s.totalReturn), MAX(s.totalReturn), MIN(s.totalReturn) FROM AutoTradingStatus s WHERE s.totalTrades > 0")
    Object[] findReturnStatistics();

    /**
     * 전체 거래 통계 조회
     *
     * @return [총 거래 횟수, 평균 거래 횟수, 총 수익 거래 횟수]
     */
    @Query("SELECT SUM(s.totalTrades), AVG(s.totalTrades), SUM(s.winningTrades) FROM AutoTradingStatus s")
    Object[] findTradeStatistics();

    /**
     * 최근 N일간의 성과 조회
     *
     * @param days 일수
     * @return 최근 N일간의 자동매매 상태 목록
     */
    @Query("SELECT s FROM AutoTradingStatus s WHERE s.updatedAt >= :sinceDate ORDER BY s.totalReturn DESC")
    List<AutoTradingStatus> findRecentPerformance(@Param("sinceDate") LocalDateTime sinceDate);

    /**
     * 활성 자동매매의 총 자본금 조회
     *
     * @return 실행 중인 자동매매의 총 자본금
     */
    @Query("SELECT SUM(c.capital) FROM AutoTradingStatus s JOIN s.config c WHERE s.status = 'running'")
    BigDecimal getTotalActiveCapital();

    /**
     * 날짜별 성과 집계 조회
     *
     * @param startDate 시작일
     * @param endDate 종료일
     * @return 날짜별 [날짜, 총 수익률, 거래 횟수] 목록
     */
    @Query("SELECT DATE(s.updatedAt), SUM(s.totalReturn), SUM(s.totalTrades) " +
           "FROM AutoTradingStatus s " +
           "WHERE s.updatedAt BETWEEN :startDate AND :endDate " +
           "GROUP BY DATE(s.updatedAt) " +
           "ORDER BY DATE(s.updatedAt)")
    List<Object[]> findDailyPerformanceAggregation(@Param("startDate") LocalDateTime startDate, 
                                                    @Param("endDate") LocalDateTime endDate);

    /**
     * 설정별 최신 상태만 조회 (중복 제거)
     *
     * @return 각 설정의 최신 상태 목록
     */
    @Query("SELECT s FROM AutoTradingStatus s WHERE s.id IN " +
           "(SELECT MAX(s2.id) FROM AutoTradingStatus s2 GROUP BY s2.configId)")
    List<AutoTradingStatus> findLatestStatusByConfig();

    /**
     * 실행 시간이 긴 자동매매 조회
     *
     * @param hoursThreshold 시간 임계값
     * @return 지정된 시간 이상 실행된 자동매매 목록
     */
    @Query("SELECT s FROM AutoTradingStatus s WHERE s.status = 'running' AND s.startedAt <= :thresholdTime")
    List<AutoTradingStatus> findLongRunningStatus(@Param("thresholdTime") LocalDateTime thresholdTime);

    /**
     * 설정 ID로 상태 삭제
     *
     * @param configId 설정 ID
     */
    void deleteByConfigId(String configId);

    /**
     * 특정 상태의 자동매매를 일괄 정지로 업데이트
     *
     * @param currentStatus 현재 상태
     */
    @Query("UPDATE AutoTradingStatus s SET s.status = 'stopped', s.stoppedAt = CURRENT_TIMESTAMP, s.updatedAt = CURRENT_TIMESTAMP " +
           "WHERE s.status = :currentStatus")
    void bulkStopByStatus(@Param("currentStatus") String currentStatus);

    /**
     * 오래된 로그 데이터 정리 (특정 날짜 이전 데이터 삭제)
     *
     * @param beforeDate 삭제 기준일
     */
    @Query("DELETE FROM AutoTradingStatus s WHERE s.createdAt < :beforeDate AND s.status IN ('stopped', 'error')")
    void cleanupOldRecords(@Param("beforeDate") LocalDateTime beforeDate);
}