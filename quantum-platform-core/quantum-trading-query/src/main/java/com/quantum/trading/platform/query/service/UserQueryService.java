package com.quantum.trading.platform.query.service;

import com.quantum.trading.platform.query.repository.UserViewRepository;
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
}