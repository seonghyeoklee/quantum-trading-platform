package com.quantum.trading.platform.query.repository;

import com.quantum.trading.platform.query.view.LoginHistoryView;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;

/**
 * 로그인 이력 View Repository
 * 
 * 보안 모니터링을 위한 로그인 이력 조회 최적화
 */
@Repository
public interface LoginHistoryViewRepository extends JpaRepository<LoginHistoryView, Long> {
    
    /**
     * 사용자별 로그인 이력 조회 (최신순)
     */
    Page<LoginHistoryView> findByUserIdOrderByAttemptTimeDesc(String userId, Pageable pageable);
    
    /**
     * 사용자명별 로그인 이력 조회 (최신순)
     */
    Page<LoginHistoryView> findByUsernameOrderByAttemptTimeDesc(String username, Pageable pageable);
    
    /**
     * 전체 로그인 이력 조회 (최신순)
     */
    Page<LoginHistoryView> findAllByOrderByAttemptTimeDesc(Pageable pageable);
    
    /**
     * 로그인 실패 이력만 조회 (최신순)
     */
    Page<LoginHistoryView> findBySuccessFalseOrderByAttemptTimeDesc(Pageable pageable);
    
    /**
     * 계정 잠금된 이력 조회
     */
    Page<LoginHistoryView> findByAccountLockedTrueOrderByAttemptTimeDesc(Pageable pageable);
    
    /**
     * 특정 IP의 로그인 시도 이력
     */
    Page<LoginHistoryView> findByIpAddressOrderByAttemptTimeDesc(String ipAddress, Pageable pageable);
    
    /**
     * 특정 기간 내 로그인 이력 조회
     */
    Page<LoginHistoryView> findByAttemptTimeBetweenOrderByAttemptTimeDesc(
        Instant startTime, Instant endTime, Pageable pageable);
    
    /**
     * 특정 기간 내 실패한 로그인 시도 조회
     */
    @Query("SELECT lh FROM LoginHistoryView lh " +
           "WHERE lh.success = false " +
           "AND lh.attemptTime BETWEEN :startTime AND :endTime " +
           "ORDER BY lh.attemptTime DESC")
    Page<LoginHistoryView> findFailuresBetween(
        @Param("startTime") Instant startTime, 
        @Param("endTime") Instant endTime, 
        Pageable pageable);
    
    /**
     * 특정 사용자의 최근 로그인 실패 횟수 조회
     */
    @Query("SELECT COUNT(lh) FROM LoginHistoryView lh " +
           "WHERE lh.userId = :userId " +
           "AND lh.success = false " +
           "AND lh.attemptTime > :since")
    Long countRecentFailuresByUserId(
        @Param("userId") String userId, 
        @Param("since") Instant since);
    
    /**
     * 특정 IP의 최근 실패 시도 횟수
     */
    @Query("SELECT COUNT(lh) FROM LoginHistoryView lh " +
           "WHERE lh.ipAddress = :ipAddress " +
           "AND lh.success = false " +
           "AND lh.attemptTime > :since")
    Long countRecentFailuresByIp(
        @Param("ipAddress") String ipAddress, 
        @Param("since") Instant since);
    
    /**
     * 의심스러운 IP 목록 (높은 실패율)
     */
    @Query("SELECT lh.ipAddress, COUNT(lh) as failureCount " +
           "FROM LoginHistoryView lh " +
           "WHERE lh.success = false " +
           "AND lh.attemptTime > :since " +
           "GROUP BY lh.ipAddress " +
           "HAVING COUNT(lh) >= :minFailures " +
           "ORDER BY failureCount DESC")
    List<Object[]> findSuspiciousIps(
        @Param("since") Instant since, 
        @Param("minFailures") int minFailures);
    
    /**
     * 오늘의 로그인 통계
     */
    @Query("SELECT " +
           "SUM(CASE WHEN lh.success = true THEN 1 ELSE 0 END) as successCount, " +
           "SUM(CASE WHEN lh.success = false THEN 1 ELSE 0 END) as failureCount, " +
           "COUNT(DISTINCT lh.ipAddress) as uniqueIps " +
           "FROM LoginHistoryView lh " +
           "WHERE lh.attemptTime >= :startOfDay")
    Object[] getTodayLoginStats(@Param("startOfDay") Instant startOfDay);
    
    /**
     * 사용자별 로그인 통계 (특정 기간)
     */
    @Query("SELECT lh.username, " +
           "SUM(CASE WHEN lh.success = true THEN 1 ELSE 0 END) as successCount, " +
           "SUM(CASE WHEN lh.success = false THEN 1 ELSE 0 END) as failureCount " +
           "FROM LoginHistoryView lh " +
           "WHERE lh.attemptTime BETWEEN :startTime AND :endTime " +
           "GROUP BY lh.username " +
           "ORDER BY failureCount DESC, lh.username")
    List<Object[]> getUserLoginStats(
        @Param("startTime") Instant startTime, 
        @Param("endTime") Instant endTime);
    
    /**
     * 최근 로그인 활동이 있는 사용자 목록
     */
    @Query("SELECT DISTINCT lh.username, lh.userId " +
           "FROM LoginHistoryView lh " +
           "WHERE lh.success = true " +
           "AND lh.attemptTime > :since " +
           "ORDER BY lh.username")
    List<Object[]> findRecentActiveUsers(@Param("since") Instant since);
}