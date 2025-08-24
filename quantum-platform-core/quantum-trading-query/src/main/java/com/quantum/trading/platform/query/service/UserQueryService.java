package com.quantum.trading.platform.query.service;

import com.quantum.trading.platform.query.repository.LoginHistoryViewRepository;
import com.quantum.trading.platform.query.repository.UserViewRepository;
import com.quantum.trading.platform.query.view.LoginHistoryView;
import com.quantum.trading.platform.query.view.UserView;
import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.UserStatus;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

/**
 * User Query Service
 * 
 * 비즈니스 중심의 사용자 조회 서비스
 * Repository의 기본 기능을 조합하여 복잡한 비즈니스 쿼리 제공
 */
@Service
@RequiredArgsConstructor
@Slf4j
@Transactional(readOnly = true)
public class UserQueryService {
    
    private final UserViewRepository userViewRepository;
    private final LoginHistoryViewRepository loginHistoryRepository;
    
    /**
     * 사용자 ID로 조회
     */
    public Optional<UserView> findById(String userId) {
        return userViewRepository.findById(userId);
    }
    
    /**
     * 도메인 UserId로 조회
     */
    public Optional<UserView> findById(UserId userId) {
        return userViewRepository.findById(userId.getValue());
    }
    
    /**
     * 사용자명으로 조회
     */
    public Optional<UserView> findByUsername(String username) {
        return userViewRepository.findByUsername(username);
    }
    
    /**
     * 이메일로 조회
     */
    public Optional<UserView> findByEmail(String email) {
        return userViewRepository.findByEmail(email);
    }
    
    /**
     * 로그인용 사용자 조회 (사용자명 또는 이메일)
     */
    public Optional<UserView> findForLogin(String usernameOrEmail) {
        return userViewRepository.findByUsernameOrEmail(usernameOrEmail);
    }
    
    /**
     * 활성 세션 ID로 사용자 조회
     */
    public Optional<UserView> findByActiveSession(String sessionId) {
        return userViewRepository.findByActiveSessionId(sessionId);
    }
    
    /**
     * 사용자 검색 (사용자명, 이름, 이메일 검색)
     */
    public Page<UserView> searchUsers(String searchTerm, Pageable pageable) {
        return userViewRepository.searchUsers(searchTerm, pageable);
    }
    
    /**
     * 상태별 사용자 조회
     */
    public List<UserView> findByStatus(UserStatus status) {
        return userViewRepository.findByStatus(status);
    }
    
    /**
     * 상태별 사용자 조회 (페이징)
     */
    public Page<UserView> findByStatus(UserStatus status, Pageable pageable) {
        return userViewRepository.findByStatus(status, pageable);
    }
    
    /**
     * 권한별 사용자 조회
     */
    public List<UserView> findByRole(String roleName) {
        return userViewRepository.findByRole(roleName);
    }
    
    /**
     * 권한별 사용자 조회 (페이징)
     */
    public Page<UserView> findByRole(String roleName, Pageable pageable) {
        return userViewRepository.findByRole(roleName, pageable);
    }
    
    /**
     * 현재 활성 사용자 목록 조회
     */
    public List<UserView> findActiveUsers() {
        return userViewRepository.findByStatus(UserStatus.ACTIVE);
    }
    
    /**
     * 잠금된 사용자 목록 조회
     */
    public List<UserView> findLockedUsers() {
        return userViewRepository.findByStatus(UserStatus.LOCKED);
    }
    
    /**
     * 로그인 실패 위험 사용자 조회 (임계값에 근접한 사용자)
     */
    public List<UserView> findUsersAtRisk() {
        return userViewRepository.findUsersNearLockThreshold(3); // 3회 이상 실패
    }
    
    /**
     * 현재 로그인된 사용자 목록
     */
    public List<UserView> findCurrentlyLoggedInUsers() {
        return userViewRepository.findActiveSessionUsers();
    }
    
    /**
     * 만료된 세션을 가진 사용자 조회
     */
    public List<UserView> findExpiredSessionUsers(int sessionTimeoutHours) {
        Instant expiredBefore = Instant.now().minusSeconds(sessionTimeoutHours * 3600);
        return userViewRepository.findExpiredSessionUsers(expiredBefore);
    }
    
    /**
     * 사용자명 중복 확인
     */
    public boolean isUsernameExists(String username) {
        return userViewRepository.existsByUsername(username);
    }
    
    /**
     * 이메일 중복 확인
     */
    public boolean isEmailExists(String email) {
        return userViewRepository.existsByEmail(email);
    }
    
    /**
     * 특정 기간 신규 가입자 조회
     */
    public List<UserView> findNewRegistrations(LocalDate startDate, LocalDate endDate) {
        Instant startInstant = startDate.atStartOfDay().toInstant(ZoneOffset.UTC);
        Instant endInstant = endDate.plusDays(1).atStartOfDay().toInstant(ZoneOffset.UTC);
        return userViewRepository.findByRegistrationDateBetween(startInstant, endInstant);
    }
    
    /**
     * 특정 기간 활성 사용자 조회 (로그인한 사용자)
     */
    public List<UserView> findActiveUsers(LocalDate startDate, LocalDate endDate) {
        Instant startInstant = startDate.atStartOfDay().toInstant(ZoneOffset.UTC);
        Instant endInstant = endDate.plusDays(1).atStartOfDay().toInstant(ZoneOffset.UTC);
        return userViewRepository.findByLastLoginBetween(startInstant, endInstant);
    }
    
    /**
     * 사용자 통계 - 상태별 사용자 수
     */
    public Map<UserStatus, Long> getUserCountByStatus() {
        List<Object[]> results = userViewRepository.getUserCountByStatus();
        return results.stream()
                .collect(Collectors.toMap(
                        result -> (UserStatus) result[0],
                        result -> (Long) result[1]
                ));
    }
    
    /**
     * 사용자 통계 - 권한별 사용자 수
     */
    public Map<String, Long> getUserCountByRole() {
        List<Object[]> results = userViewRepository.getUserCountByRole();
        return results.stream()
                .collect(Collectors.toMap(
                        result -> (String) result[0],
                        result -> (Long) result[1]
                ));
    }
    
    /**
     * 오늘의 통계 정보
     */
    public DailyUserStats getTodayStats() {
        Instant startOfDay = LocalDate.now().atStartOfDay().toInstant(ZoneOffset.UTC);
        
        Long todayRegistrations = userViewRepository.countTodayRegistrations(startOfDay);
        Long todayLogins = userViewRepository.countTodayLogins(startOfDay);
        Long activeSessions = userViewRepository.countActiveSessions();
        
        return new DailyUserStats(todayRegistrations, todayLogins, activeSessions);
    }
    
    /**
     * 관리자 대시보드용 통계
     */
    public AdminDashboardStats getAdminDashboardStats() {
        Map<UserStatus, Long> statusCounts = getUserCountByStatus();
        Map<String, Long> roleCounts = getUserCountByRole();
        DailyUserStats todayStats = getTodayStats();
        
        Long totalUsers = userViewRepository.count();
        Long riskUsers = (long) findUsersAtRisk().size();
        
        return new AdminDashboardStats(
                totalUsers,
                statusCounts,
                roleCounts,
                todayStats,
                riskUsers
        );
    }
    
    /**
     * 특정 등록자에 의해 생성된 사용자 목록
     */
    public List<UserView> findByRegisteredBy(String registeredBy) {
        return userViewRepository.findByRegisteredBy(registeredBy);
    }
    
    /**
     * 복수 사용자 ID로 일괄 조회
     */
    public List<UserView> findByUserIds(List<String> userIds) {
        return userViewRepository.findByUserIdIn(userIds);
    }
    
    /**
     * 사용자 인증 정보 조회 (로그인용)
     */
    public Optional<UserLoginInfo> findLoginInfo(String usernameOrEmail) {
        return findForLogin(usernameOrEmail)
                .filter(user -> user.getStatus() != UserStatus.DELETED)
                .filter(user -> user.getPasswordHash() != null) // 패스워드 해시가 있는 사용자만
                .map(user -> new UserLoginInfo(
                        user.getUserId(),
                        user.getUsername(),
                        user.getPasswordHash(),
                        user.getStatus(),
                        user.getFailedLoginAttempts(),
                        user.canLogin()
                ));
    }
    
    /**
     * 세션 검증용 사용자 정보 조회
     */
    public Optional<UserSessionInfo> findSessionInfo(String sessionId) {
        return findByActiveSession(sessionId)
                .map(user -> new UserSessionInfo(
                        user.getUserId(),
                        user.getUsername(),
                        user.getRoles(),
                        user.getSessionStartTime()
                ));
    }
    
    // DTO 클래스들
    public record DailyUserStats(
            Long todayRegistrations,
            Long todayLogins,
            Long activeSessions
    ) {}
    
    public record AdminDashboardStats(
            Long totalUsers,
            Map<UserStatus, Long> statusCounts,
            Map<String, Long> roleCounts,
            DailyUserStats todayStats,
            Long usersAtRisk
    ) {}
    
    public record UserLoginInfo(
            String userId,
            String username,
            String passwordHash,
            UserStatus status,
            Integer failedLoginAttempts,
            boolean canLogin
    ) {}
    
    public record UserSessionInfo(
            String userId,
            String username,
            java.util.Set<String> roles,
            Instant sessionStartTime
    ) {}
    
    // ============== 로그인 이력 관련 메서드들 ==============
    
    /**
     * 전체 로그인 이력 조회 (최신순)
     */
    public Page<LoginHistoryView> findAllLoginHistory(Pageable pageable) {
        return loginHistoryRepository.findAllByOrderByAttemptTimeDesc(pageable);
    }
    
    /**
     * 로그인 실패 이력만 조회 (최신순)
     */
    public Page<LoginHistoryView> findLoginFailureHistory(Pageable pageable) {
        return loginHistoryRepository.findBySuccessFalseOrderByAttemptTimeDesc(pageable);
    }
    
    /**
     * 계정 잠금된 이력 조회
     */
    public Page<LoginHistoryView> findAccountLockedHistory(Pageable pageable) {
        return loginHistoryRepository.findByAccountLockedTrueOrderByAttemptTimeDesc(pageable);
    }
    
    /**
     * 특정 사용자의 로그인 이력 조회
     */
    public Page<LoginHistoryView> findUserLoginHistory(String userId, Pageable pageable) {
        return loginHistoryRepository.findByUserIdOrderByAttemptTimeDesc(userId, pageable);
    }
    
    /**
     * 특정 IP의 로그인 시도 이력
     */
    public Page<LoginHistoryView> findLoginHistoryByIp(String ipAddress, Pageable pageable) {
        return loginHistoryRepository.findByIpAddressOrderByAttemptTimeDesc(ipAddress, pageable);
    }
    
    /**
     * 특정 기간 내 로그인 실패 조회
     */
    public Page<LoginHistoryView> findLoginFailuresBetween(LocalDate startDate, LocalDate endDate, Pageable pageable) {
        Instant startInstant = startDate.atStartOfDay().toInstant(ZoneOffset.UTC);
        Instant endInstant = endDate.plusDays(1).atStartOfDay().toInstant(ZoneOffset.UTC);
        return loginHistoryRepository.findFailuresBetween(startInstant, endInstant, pageable);
    }
    
    /**
     * 의심스러운 IP 목록 조회 (최근 24시간)
     */
    public List<SuspiciousIpInfo> findSuspiciousIps(int minFailures) {
        Instant since = Instant.now().minusSeconds(24 * 3600); // 24시간 전
        List<Object[]> results = loginHistoryRepository.findSuspiciousIps(since, minFailures);
        
        return results.stream()
                .map(result -> new SuspiciousIpInfo(
                        (String) result[0],  // IP address
                        (Long) result[1]     // failure count
                ))
                .collect(Collectors.toList());
    }
    
    /**
     * 오늘의 로그인 통계
     */
    public LoginStats getTodayLoginStats() {
        Instant startOfDay = LocalDate.now().atStartOfDay().toInstant(ZoneOffset.UTC);
        Object[] result = loginHistoryRepository.getTodayLoginStats(startOfDay);
        
        if (result != null && result.length >= 3) {
            // 안전한 타입 변환 - Number 타입을 Long으로 변환
            Long successCount = convertToLong(result[0]);
            Long failureCount = convertToLong(result[1]);
            Long uniqueIps = convertToLong(result[2]);
            
            return new LoginStats(successCount, failureCount, uniqueIps);
        }
        
        return new LoginStats(0L, 0L, 0L);
    }
    
    /**
     * Object를 Long으로 안전하게 변환
     */
    private Long convertToLong(Object value) {
        if (value == null) return 0L;
        if (value instanceof Long) return (Long) value;
        if (value instanceof Number) return ((Number) value).longValue();
        if (value instanceof String) {
            try {
                return Long.parseLong((String) value);
            } catch (NumberFormatException e) {
                return 0L;
            }
        }
        return 0L;
    }
    
    /**
     * 사용자별 로그인 통계 (특정 기간)
     */
    public List<UserLoginStats> getUserLoginStats(LocalDate startDate, LocalDate endDate) {
        Instant startInstant = startDate.atStartOfDay().toInstant(ZoneOffset.UTC);
        Instant endInstant = endDate.plusDays(1).atStartOfDay().toInstant(ZoneOffset.UTC);
        
        List<Object[]> results = loginHistoryRepository.getUserLoginStats(startInstant, endInstant);
        
        return results.stream()
                .map(result -> new UserLoginStats(
                        (String) result[0],  // username
                        (Long) result[1],    // success count
                        (Long) result[2]     // failure count
                ))
                .collect(Collectors.toList());
    }
    
    /**
     * 최근 활성 사용자 목록 (최근 7일간 로그인한 사용자)
     */
    public List<RecentActiveUser> findRecentActiveUsers() {
        Instant since = Instant.now().minusSeconds(7 * 24 * 3600); // 7일 전
        List<Object[]> results = loginHistoryRepository.findRecentActiveUsers(since);
        
        return results.stream()
                .map(result -> new RecentActiveUser(
                        (String) result[0],  // username
                        (String) result[1]   // userId
                ))
                .collect(Collectors.toList());
    }
    
    // 로그인 이력 관련 DTO 클래스들
    public record LoginStats(
            Long successCount,
            Long failureCount,
            Long uniqueIps
    ) {
        public Long getTotalAttempts() {
            return successCount + failureCount;
        }
        
        public double getSuccessRate() {
            Long total = getTotalAttempts();
            return total > 0 ? (double) successCount / total * 100.0 : 0.0;
        }
    }
    
    public record UserLoginStats(
            String username,
            Long successCount,
            Long failureCount
    ) {
        public Long getTotalAttempts() {
            return successCount + failureCount;
        }
        
        public double getSuccessRate() {
            Long total = getTotalAttempts();
            return total > 0 ? (double) successCount / total * 100.0 : 0.0;
        }
    }
    
    public record SuspiciousIpInfo(
            String ipAddress,
            Long failureCount
    ) {}
    
    public record RecentActiveUser(
            String username,
            String userId
    ) {}
}