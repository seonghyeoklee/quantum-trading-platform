package com.quantum.web.service;

import com.quantum.web.dto.TradingConfigDto;
import com.quantum.web.entity.TradingModeHistory;
import com.quantum.web.entity.UserTradingSettings;
import com.quantum.web.repository.TradingModeHistoryRepository;
import com.quantum.web.repository.UserTradingSettingsRepository;
import com.quantum.web.security.UserPrincipal;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientException;
import org.springframework.beans.factory.annotation.Qualifier;

import jakarta.servlet.http.HttpServletRequest;
import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 트레이딩 설정 서비스
 */
@Service
@Slf4j
public class TradingConfigService {

    private final UserTradingSettingsRepository userTradingSettingsRepository;
    private final TradingModeHistoryRepository tradingModeHistoryRepository;
    private final TwoFactorAuthService twoFactorAuthService;
    private final WebClient webClient;
    
    public TradingConfigService(UserTradingSettingsRepository userTradingSettingsRepository,
                               TradingModeHistoryRepository tradingModeHistoryRepository,
                               TwoFactorAuthService twoFactorAuthService,
                               @Qualifier("webClient") WebClient webClient) {
        this.userTradingSettingsRepository = userTradingSettingsRepository;
        this.tradingModeHistoryRepository = tradingModeHistoryRepository;
        this.twoFactorAuthService = twoFactorAuthService;
        this.webClient = webClient;
    }

    @Value("${app.python-adapter.base-url:http://quantum-kiwoom-adapter:10201}")
    private String pythonAdapterBaseUrl;

    @Value("${app.trading.require-2fa-for-production:true}")
    private boolean require2FAForProduction;

    @Value("${app.trading.mode-change-cooldown-minutes:60}")
    private int modeChangeCooldownMinutes;

    /**
     * 사용자 트레이딩 설정 조회 (없으면 기본값으로 생성)
     */
    public TradingConfigDto.UserTradingSettingsResponse getUserTradingSettings(String userId) {
        UserTradingSettings settings = userTradingSettingsRepository.findByUserId(userId)
                .orElseGet(() -> createDefaultSettings(userId));
        
        return settings.toDto();
    }

    /**
     * 사용자 트레이딩 설정 업데이트
     */
    @Transactional
    public TradingConfigDto.UserTradingSettingsResponse updateUserTradingSettings(
            String userId, 
            TradingConfigDto.UserTradingSettingsUpdateRequest request,
            UserPrincipal currentUser,
            HttpServletRequest httpRequest) {

        log.info("사용자 트레이딩 설정 업데이트 시작: userId={}, newMode={}", userId, request.getTradingMode());

        // 기존 설정 조회 또는 기본값 생성
        UserTradingSettings settings = userTradingSettingsRepository.findByUserId(userId)
                .orElseGet(() -> createDefaultSettings(userId));

        TradingConfigDto.TradingMode previousMode = settings.getTradingMode();
        TradingConfigDto.TradingMode newMode = request.getTradingMode();

        // 모드 변경 검증
        validateModeChange(userId, previousMode, newMode, request.getTotpCode(), currentUser);

        // 쿨다운 체크
        validateModeChangeCooldown(userId);

        // 설정 업데이트
        settings.updateFromRequest(request);
        settings = userTradingSettingsRepository.save(settings);

        // 모드 변경 이력 저장
        if (previousMode != newMode) {
            saveModeChangeHistory(userId, previousMode, newMode, currentUser.getUsername(), 
                               request.getChangeReason(), httpRequest);
            
            // Python 어댑터에 모드 변경 알림
            notifyPythonAdapter(userId, newMode == TradingConfigDto.TradingMode.SANDBOX, 
                              settings.getKiwoomAccountId());
        }

        log.info("사용자 트레이딩 설정 업데이트 완료: userId={}, previousMode={}, newMode={}", 
                userId, previousMode, newMode);

        return settings.toDto();
    }

    /**
     * 트레이딩 모드만 변경
     */
    @Transactional
    public TradingConfigDto.UserTradingSettingsResponse changeTradingMode(
            String userId,
            TradingConfigDto.TradingModeChangeRequest request,
            UserPrincipal currentUser,
            HttpServletRequest httpRequest) {

        TradingConfigDto.UserTradingSettingsUpdateRequest updateRequest = 
            new TradingConfigDto.UserTradingSettingsUpdateRequest();
        updateRequest.setTradingMode(request.getTradingMode());
        updateRequest.setChangeReason(request.getChangeReason());
        updateRequest.setTotpCode(request.getTotpCode());

        return updateUserTradingSettings(userId, updateRequest, currentUser, httpRequest);
    }

    /**
     * 트레이딩 모드 변경 이력 조회
     */
    public List<TradingConfigDto.TradingModeHistoryResponse> getUserModeHistory(String userId) {
        List<TradingModeHistory> historyList = tradingModeHistoryRepository
                .findByUserIdOrderByCreatedAtDesc(userId);
        
        return historyList.stream()
                .map(TradingModeHistory::toDto)
                .collect(Collectors.toList());
    }

    /**
     * 트레이딩 설정 요약 정보 조회
     */
    public TradingConfigDto.TradingConfigSummaryResponse getTradingConfigSummary(String userId) {
        UserTradingSettings settings = userTradingSettingsRepository.findByUserId(userId)
                .orElseGet(() -> createDefaultSettings(userId));

        // 최근 24시간 내 모드 변경 횟수
        LocalDateTime since24Hours = LocalDateTime.now().minusHours(24);
        long recentModeChanges = tradingModeHistoryRepository
                .countByUserIdAndCreatedAtAfter(userId, since24Hours);

        // 마지막 모드 변경 시간
        TradingModeHistory latestHistory = tradingModeHistoryRepository.findLatestByUserId(userId);
        LocalDateTime lastModeChange = latestHistory != null ? latestHistory.getCreatedAt() : null;

        // Python 어댑터 연결 상태 확인
        boolean pythonAdapterConnected = checkPythonAdapterConnection();

        return TradingConfigDto.TradingConfigSummaryResponse.builder()
                .currentMode(settings.getTradingMode())
                .modeDescription(settings.getTradingMode().getDescription())
                .isProductionAllowed(true) // 시스템 설정에서 조회 가능
                .requires2FA(require2FAForProduction)
                .maxDailyAmount(settings.getMaxDailyAmount())
                .riskLevel(settings.getRiskLevel())
                .autoTradingEnabled(settings.isAutoTradingEnabled())
                .recentModeChanges((int) recentModeChanges)
                .lastModeChange(lastModeChange)
                .pythonAdapterConnected(pythonAdapterConnected)
                .build();
    }

    /**
     * 모드 변경 검증
     */
    private void validateModeChange(String userId, TradingConfigDto.TradingMode previousMode, 
                                  TradingConfigDto.TradingMode newMode, String totpCode, 
                                  UserPrincipal currentUser) {
        
        // 실전투자 모드로 변경 시 2FA 검증
        if (newMode == TradingConfigDto.TradingMode.REAL && require2FAForProduction) {
            if (totpCode == null || totpCode.trim().isEmpty()) {
                throw new IllegalArgumentException("실전투자 모드 전환을 위해 2FA 코드가 필요합니다");
            }
            
            boolean isValidTotp = twoFactorAuthService.verifyTotp(currentUser.getUsername(), totpCode);
            if (!isValidTotp) {
                throw new IllegalArgumentException("잘못된 2FA 코드입니다");
            }
        }

        // 권한 검증 (필요시 관리자만 실전투자 허용 등)
        if (newMode == TradingConfigDto.TradingMode.REAL) {
            // 추가 권한 검증 로직
            log.info("실전투자 모드 전환 승인: userId={}, approvedBy={}", userId, currentUser.getUsername());
        }
    }

    /**
     * 모드 변경 쿨다운 검증
     */
    private void validateModeChangeCooldown(String userId) {
        LocalDateTime cooldownTime = LocalDateTime.now().minusMinutes(modeChangeCooldownMinutes);
        long recentChanges = tradingModeHistoryRepository
                .countByUserIdAndCreatedAtAfter(userId, cooldownTime);
        
        if (recentChanges > 0) {
            throw new IllegalArgumentException(
                String.format("모드 변경은 %d분 후에 다시 시도할 수 있습니다", modeChangeCooldownMinutes));
        }
    }

    /**
     * 기본 설정 생성
     */
    @Transactional
    protected UserTradingSettings createDefaultSettings(String userId) {
        UserTradingSettings defaultSettings = UserTradingSettings.builder()
                .userId(userId)
                .tradingMode(TradingConfigDto.TradingMode.SANDBOX)
                .riskLevel(TradingConfigDto.RiskLevel.MEDIUM)
                .autoTradingEnabled(false)
                .notificationsEnabled(true)
                .build();

        return userTradingSettingsRepository.save(defaultSettings);
    }

    /**
     * 모드 변경 이력 저장
     */
    private void saveModeChangeHistory(String userId, TradingConfigDto.TradingMode previousMode,
                                     TradingConfigDto.TradingMode newMode, String changedBy,
                                     String changeReason, HttpServletRequest request) {
        
        TradingModeHistory history = TradingModeHistory.builder()
                .userId(userId)
                .previousMode(previousMode)
                .newMode(newMode)
                .changedBy(changedBy)
                .changeReason(changeReason)
                .ipAddress(getClientIpAddress(request))
                .userAgent(request.getHeader("User-Agent"))
                .build();

        tradingModeHistoryRepository.save(history);
    }

    /**
     * Python 어댑터에 모드 변경 알림
     */
    private void notifyPythonAdapter(String userId, boolean sandboxMode, String kiwoomAccountId) {
        try {
            String notificationUrl = pythonAdapterBaseUrl + "/api/v1/admin/user-trading-mode";
            
            TradingConfigDto.PythonAdapterNotificationRequest request = 
                TradingConfigDto.PythonAdapterNotificationRequest.builder()
                    .userId(userId)
                    .sandboxMode(sandboxMode)
                    .kiwoomAccountId(kiwoomAccountId)
                    .timestamp(LocalDateTime.now())
                    .build();

            webClient.post()
                    .uri(notificationUrl)
                    .bodyValue(request)
                    .retrieve()
                    .bodyToMono(String.class)
                    .block();
            
            log.info("Python 어댑터 모드 변경 알림 완료: userId={}, sandboxMode={}", userId, sandboxMode);
            
        } catch (WebClientException e) {
            log.error("Python 어댑터 모드 변경 알림 실패: userId={}, error={}", userId, e.getMessage());
            // 실패해도 메인 로직에는 영향 없도록 예외를 던지지 않음
        }
    }

    /**
     * Python 어댑터 연결 상태 확인
     */
    private boolean checkPythonAdapterConnection() {
        try {
            String healthUrl = pythonAdapterBaseUrl + "/health";
            String response = webClient.get()
                    .uri(healthUrl)
                    .retrieve()
                    .bodyToMono(String.class)
                    .block();
            return response != null;
        } catch (WebClientException e) {
            log.warn("Python 어댑터 연결 확인 실패: {}", e.getMessage());
            return false;
        }
    }

    /**
     * 클라이언트 IP 주소 추출
     */
    private String getClientIpAddress(HttpServletRequest request) {
        String xForwardedFor = request.getHeader("X-Forwarded-For");
        if (xForwardedFor != null && !xForwardedFor.isEmpty()) {
            return xForwardedFor.split(",")[0].trim();
        }
        
        String xRealIp = request.getHeader("X-Real-IP");
        if (xRealIp != null && !xRealIp.isEmpty()) {
            return xRealIp;
        }
        
        return request.getRemoteAddr();
    }
}