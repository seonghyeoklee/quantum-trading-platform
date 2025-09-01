package com.quantum.trading.platform.query.repository;

import com.quantum.trading.platform.query.view.UserView;
import com.quantum.trading.platform.shared.value.UserStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

/**
 * UserView Repository
 * 
 * 사용자 조회용 최적화된 JPA 쿼리 제공
 * 비즈니스 요구사항에 맞는 조회 메서드 구현
 */
@Repository
public interface UserViewRepository extends JpaRepository<UserView, String> {
    
    /**
     * 사용자명으로 사용자 조회
     */
    Optional<UserView> findByUsername(String username);
    
    /**
     * 이메일로 사용자 조회
     */
    Optional<UserView> findByEmail(String email);
    
    /**
     * 사용자명 또는 이메일로 사용자 조회 (비밀번호 해시가 있는 사용자 우선)
     */
    @Query("SELECT u FROM UserView u WHERE (u.username = :usernameOrEmail OR u.email = :usernameOrEmail) ORDER BY CASE WHEN u.passwordHash IS NOT NULL THEN 0 ELSE 1 END, u.createdAt DESC")
    Optional<UserView> findByUsernameOrEmail(@Param("usernameOrEmail") String usernameOrEmail);
    
    /**
     * 활성 세션 ID로 사용자 조회
     */
    Optional<UserView> findByActiveSessionId(String sessionId);
    
    /**
     * 사용자 상태로 사용자 목록 조회
     */
    List<UserView> findByStatus(UserStatus status);
    
    /**
     * 사용자 상태로 사용자 목록 조회 (페이징)
     */
    Page<UserView> findByStatus(UserStatus status, Pageable pageable);
    
    /**
     * 특정 권한을 가진 사용자 목록 조회
     */
    @Query("SELECT u FROM UserView u JOIN u.roles r WHERE r = :roleName")
    List<UserView> findByRole(@Param("roleName") String roleName);
    
    /**
     * 특정 권한을 가진 사용자 목록 조회 (페이징)
     */
    @Query("SELECT u FROM UserView u JOIN u.roles r WHERE r = :roleName")
    Page<UserView> findByRole(@Param("roleName") String roleName, Pageable pageable);
    
    /**
     * 계정 잠금된 사용자 목록 조회
     */
    List<UserView> findByStatusAndFailedLoginAttemptsGreaterThanEqual(UserStatus status, Integer attempts);
    
    /**
     * 로그인 실패 횟수가 임계값 이상인 사용자 조회
     */
    @Query("SELECT u FROM UserView u WHERE u.failedLoginAttempts >= :threshold AND u.status != 'LOCKED'")
    List<UserView> findUsersNearLockThreshold(@Param("threshold") Integer threshold);
    
    /**
     * 특정 기간 내에 가입한 사용자 조회
     */
    @Query("SELECT u FROM UserView u WHERE u.createdAt BETWEEN :startDate AND :endDate")
    List<UserView> findByRegistrationDateBetween(@Param("startDate") Instant startDate, 
                                                @Param("endDate") Instant endDate);
    
    /**
     * 특정 기간 내에 마지막 로그인한 사용자 조회
     */
    @Query("SELECT u FROM UserView u WHERE u.lastLoginAt BETWEEN :startDate AND :endDate")
    List<UserView> findByLastLoginBetween(@Param("startDate") Instant startDate, 
                                         @Param("endDate") Instant endDate);
    
    /**
     * 활성 세션을 가진 사용자 조회
     */
    @Query("SELECT u FROM UserView u WHERE u.activeSessionId IS NOT NULL AND u.activeSessionId != ''")
    List<UserView> findActiveSessionUsers();
    
    /**
     * 만료된 세션을 가진 사용자 조회 (세션 시작 후 특정 시간 경과)
     */
    @Query("SELECT u FROM UserView u WHERE u.sessionStartTime IS NOT NULL AND u.sessionStartTime < :expiredBefore")
    List<UserView> findExpiredSessionUsers(@Param("expiredBefore") Instant expiredBefore);
    
    /**
     * 사용자명으로 존재 여부 확인
     */
    boolean existsByUsername(String username);
    
    /**
     * 이메일로 존재 여부 확인
     */
    boolean existsByEmail(String email);
    
    /**
     * 사용자명 검색 (부분 일치)
     */
    @Query("SELECT u FROM UserView u WHERE u.username LIKE %:searchTerm% OR u.name LIKE %:searchTerm% OR u.email LIKE %:searchTerm%")
    Page<UserView> searchUsers(@Param("searchTerm") String searchTerm, Pageable pageable);
    
    /**
     * 사용자 통계 - 상태별 사용자 수
     */
    @Query("SELECT u.status, COUNT(u) FROM UserView u GROUP BY u.status")
    List<Object[]> getUserCountByStatus();
    
    /**
     * 사용자 통계 - 권한별 사용자 수
     */
    @Query("SELECT r, COUNT(u) FROM UserView u JOIN u.roles r GROUP BY r")
    List<Object[]> getUserCountByRole();
    
    /**
     * 오늘 가입한 사용자 수
     */
    @Query("SELECT COUNT(u) FROM UserView u WHERE u.createdAt >= :startOfDay")
    Long countTodayRegistrations(@Param("startOfDay") Instant startOfDay);
    
    /**
     * 오늘 로그인한 사용자 수
     */
    @Query("SELECT COUNT(u) FROM UserView u WHERE u.lastLoginAt >= :startOfDay")
    Long countTodayLogins(@Param("startOfDay") Instant startOfDay);
    
    /**
     * 현재 활성 세션 수
     */
    @Query("SELECT COUNT(u) FROM UserView u WHERE u.activeSessionId IS NOT NULL AND u.activeSessionId != ''")
    Long countActiveSessions();
    
    /**
     * 사용자 ID 목록으로 일괄 조회
     */
    @Query("SELECT u FROM UserView u WHERE u.userId IN :userIds")
    List<UserView> findByUserIdIn(@Param("userIds") List<String> userIds);
    
    /**
     * 특정 등록자에 의해 생성된 사용자 목록
     */
    List<UserView> findByRegisteredBy(String registeredBy);
    
    // ============================================
    // 로그인 실패 카운트 관리 - 원자적 DB 연산
    // ============================================
    
    /**
     * 로그인 실패 횟수 원자적 증가 및 마지막 실패 시간 업데이트
     * @param username 사용자명
     * @return 업데이트된 행 수 (성공 시 1)
     */
    @Query("UPDATE UserView u SET u.failedLoginAttempts = u.failedLoginAttempts + 1, u.lastFailedLoginAt = CURRENT_TIMESTAMP WHERE u.username = :username")
    @Modifying
    @Transactional
    int incrementFailureCount(@Param("username") String username);
    
    /**
     * 로그인 실패 횟수 초기화 (로그인 성공 시)
     * @param username 사용자명
     * @return 업데이트된 행 수 (성공 시 1)
     */
    @Query("UPDATE UserView u SET u.failedLoginAttempts = 0, u.lastFailedLoginAt = null WHERE u.username = :username")
    @Modifying
    @Transactional
    int resetFailureCount(@Param("username") String username);
    
    /**
     * 계정 잠금 처리
     * @param username 사용자명
     * @param attempts 현재 실패 횟수
     * @return 업데이트된 행 수 (성공 시 1)
     */
    @Query("UPDATE UserView u SET u.status = 'LOCKED', u.failedLoginAttempts = :attempts WHERE u.username = :username")
    @Modifying
    @Transactional
    int lockAccount(@Param("username") String username, @Param("attempts") int attempts);
    
    /**
     * 계정 잠금 해제
     * @param username 사용자명
     * @return 업데이트된 행 수 (성공 시 1)
     */
    @Query("UPDATE UserView u SET u.status = 'ACTIVE', u.failedLoginAttempts = 0, u.lastFailedLoginAt = null WHERE u.username = :username")
    @Modifying
    @Transactional
    int unlockAccount(@Param("username") String username);
    
    /**
     * 현재 실패 횟수 조회 (원자적 연산 전 확인용)
     * @param username 사용자명
     * @return 현재 실패 횟수
     */
    @Query("SELECT u.failedLoginAttempts FROM UserView u WHERE u.username = :username")
    Optional<Integer> getCurrentFailureCount(@Param("username") String username);
}