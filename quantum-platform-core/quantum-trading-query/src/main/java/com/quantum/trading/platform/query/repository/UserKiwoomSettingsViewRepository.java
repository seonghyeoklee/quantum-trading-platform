package com.quantum.trading.platform.query.repository;

import com.quantum.trading.platform.query.view.UserKiwoomSettingsView;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

/**
 * 사용자별 키움증권 설정 Repository
 */
@Repository
public interface UserKiwoomSettingsViewRepository extends JpaRepository<UserKiwoomSettingsView, String> {

    /**
     * 사용자 ID로 설정 조회
     */
    Optional<UserKiwoomSettingsView> findByUserId(String userId);

    /**
     * 기본 모드별 사용자 수 조회
     */
    @Query("SELECT COUNT(u) FROM UserKiwoomSettingsView u WHERE u.defaultRealMode = :realMode")
    long countByDefaultRealMode(@Param("realMode") boolean realMode);

    /**
     * 자동 토큰 갱신 활성화된 사용자 수 조회
     */
    @Query("SELECT COUNT(u) FROM UserKiwoomSettingsView u WHERE u.autoRefreshEnabled = true")
    long countAutoRefreshEnabledUsers();

    /**
     * 토큰 만료 알림 활성화된 사용자들 조회
     */
    @Query("SELECT u FROM UserKiwoomSettingsView u WHERE u.tokenExpiryNotification = true")
    List<UserKiwoomSettingsView> findUsersWithTokenExpiryNotification();

    /**
     * 특정 알림 임계시간을 사용하는 사용자들 조회
     */
    @Query("SELECT u FROM UserKiwoomSettingsView u WHERE u.notificationThresholdMinutes = :threshold")
    List<UserKiwoomSettingsView> findByNotificationThreshold(@Param("threshold") int threshold);

    /**
     * 최근에 모드를 변경한 사용자들 조회 (지정된 시간 이후)
     */
    @Query("SELECT u FROM UserKiwoomSettingsView u WHERE u.lastModeChangeAt > :since ORDER BY u.lastModeChangeAt DESC")
    List<UserKiwoomSettingsView> findRecentModeChanges(@Param("since") Instant since);

    /**
     * 실전투자 모드 사용자들 조회
     */
    @Query("SELECT u FROM UserKiwoomSettingsView u WHERE u.defaultRealMode = true ORDER BY u.updatedAt DESC")
    List<UserKiwoomSettingsView> findRealTradingUsers();

    /**
     * 모의투자 모드 사용자들 조회
     */
    @Query("SELECT u FROM UserKiwoomSettingsView u WHERE u.defaultRealMode = false ORDER BY u.updatedAt DESC")
    List<UserKiwoomSettingsView> findSandboxTradingUsers();

    /**
     * 자동 재발급 설정이 활성화된 사용자들 조회
     */
    @Query("SELECT u FROM UserKiwoomSettingsView u WHERE u.autoReissueOnModeSwitch = true")
    List<UserKiwoomSettingsView> findAutoReissueEnabledUsers();

    /**
     * 특정 시간 이후 업데이트된 설정들 조회
     */
    @Query("SELECT u FROM UserKiwoomSettingsView u WHERE u.updatedAt > :since ORDER BY u.updatedAt DESC")
    List<UserKiwoomSettingsView> findUpdatedSince(@Param("since") Instant since);

    /**
     * 설정 통계 조회를 위한 집계 쿼리
     */
    @Query("""
        SELECT 
            COUNT(*) as totalUsers,
            SUM(CASE WHEN u.defaultRealMode = true THEN 1 ELSE 0 END) as realModeUsers,
            SUM(CASE WHEN u.defaultRealMode = false THEN 1 ELSE 0 END) as sandboxModeUsers,
            SUM(CASE WHEN u.autoRefreshEnabled = true THEN 1 ELSE 0 END) as autoRefreshUsers,
            SUM(CASE WHEN u.tokenExpiryNotification = true THEN 1 ELSE 0 END) as notificationUsers
        FROM UserKiwoomSettingsView u
    """)
    Object[] getSettingsStatistics();

    /**
     * 설정이 존재하는지 확인
     */
    boolean existsByUserId(String userId);

    /**
     * 사용자 설정 삭제
     */
    void deleteByUserId(String userId);
}