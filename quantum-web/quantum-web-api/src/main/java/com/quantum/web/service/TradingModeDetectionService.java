package com.quantum.web.service;

import com.quantum.trading.platform.query.service.KiwoomAccountQueryService;
import com.quantum.trading.platform.query.view.KiwoomAccountView;
import com.quantum.trading.platform.shared.value.ApiCredentials;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Optional;
import java.util.regex.Pattern;

/**
 * 거래 모드 자동 탐지 서비스
 * 
 * 키움증권 API 키 패턴을 분석하여 자동으로 실전투자/sandbox 모드를 판단합니다.
 * - appkey/secretkey 패턴 분석
 * - 키움증권 표준 키 형식 검증
 * - 실시간 모드 동기화 (plain text 방식)
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class TradingModeDetectionService {
    
    private final KiwoomAccountQueryService kiwoomAccountQueryService;
    
    // 키움증권 API 키 패턴 (실제 패턴은 키움증권 문서 기반으로 수정 필요)
    private static final Pattern PRODUCTION_APPKEY_PATTERN = Pattern.compile("^PS[A-Z0-9]{32}$");
    private static final Pattern SANDBOX_APPKEY_PATTERN = Pattern.compile("^PS[A-Z0-9]{32}_SB$");
    private static final Pattern PRODUCTION_SECRET_PATTERN = Pattern.compile("^[A-Za-z0-9+/]{64}={0,2}$");
    private static final Pattern SANDBOX_SECRET_PATTERN = Pattern.compile("^[A-Za-z0-9+/]{64}={0,2}_TEST$");
    
    /**
     * 사용자의 거래 모드 자동 탐지
     * 
     * @param userId 사용자 ID
     * @return 탐지된 거래 모드 정보
     */
    public TradingModeInfo detectTradingMode(String userId) {
        try {
            log.debug("사용자 {} 의 거래 모드 자동 탐지 시작", userId);
            
            // 1. 사용자의 키움증권 계정 조회
            Optional<KiwoomAccountView> accountOpt = kiwoomAccountQueryService.getUserKiwoomAccount(userId);
            if (accountOpt.isEmpty()) {
                log.debug("사용자 {} 는 키움증권 계정이 없음", userId);
                return TradingModeInfo.builder()
                    .userId(userId)
                    .tradingMode(TradingMode.UNKNOWN)
                    .detectionStatus(DetectionStatus.NO_ACCOUNT)
                    .message("키움증권 계정이 설정되지 않았습니다")
                    .build();
            }
            
            KiwoomAccountView account = accountOpt.get();
            
            // 2. API 키 패턴 분석 (실전/모의 키 확인 - 총 4개 키)
            try {
                String realAppKey = null;
                String realAppSecret = null;
                String mockAppKey = null;
                String mockAppSecret = null;
                
                // 실전투자 키 조회 (App Key + App Secret) - plain text
                realAppKey = account.getRealAppKey();
                realAppSecret = account.getRealAppSecret();
                
                // Sandbox 모드 키 조회 (App Key + App Secret) - plain text  
                mockAppKey = account.getSandboxAppKey();
                mockAppSecret = account.getSandboxAppSecret();
                
                // 3. API 키 패턴 분석 (4개 키 모두 사용)
                return analyzeApiKeyPatterns(userId, realAppKey, realAppSecret, mockAppKey, mockAppSecret);
                
            } catch (Exception e) {
                log.error("사용자 {} 의 API 인증 정보 조회 실패", userId, e);
                return TradingModeInfo.builder()
                    .userId(userId)
                    .tradingMode(TradingMode.UNKNOWN)
                    .detectionStatus(DetectionStatus.DECRYPTION_FAILED)
                    .message("API 인증 정보 조회에 실패했습니다")
                    .build();
            }
            
        } catch (Exception e) {
            log.error("사용자 {} 의 거래 모드 탐지 중 예외 발생", userId, e);
            return TradingModeInfo.builder()
                .userId(userId)
                .tradingMode(TradingMode.UNKNOWN)
                .detectionStatus(DetectionStatus.ERROR)
                .message("거래 모드 탐지 중 오류가 발생했습니다: " + e.getMessage())
                .build();
        }
    }
    
    /**
     * API 키 패턴 분석을 통한 모드 판단 (4개 키 모두 분석)
     * 
     * @param userId 사용자 ID
     * @param realAppKey 실전투자 앱키 (복호화된 값)
     * @param realAppSecret 실전투자 앱시크릿 (복호화된 값)
     * @param mockAppKey 모의투자 앱키 (복호화된 값)
     * @param mockAppSecret 모의투자 앱시크릿 (복호화된 값)
     * @return 분석된 거래 모드 정보
     */
    private TradingModeInfo analyzeApiKeyPatterns(String userId, String realAppKey, String realAppSecret, 
                                                 String mockAppKey, String mockAppSecret) {
        // 사용 가능한 키 쌍 확인 (AppKey + AppSecret 둘 다 있어야 유효)
        boolean hasRealKeys = (realAppKey != null && !realAppKey.trim().isEmpty()) && 
                             (realAppSecret != null && !realAppSecret.trim().isEmpty());
        boolean hasMockKeys = (mockAppKey != null && !mockAppKey.trim().isEmpty()) && 
                             (mockAppSecret != null && !mockAppSecret.trim().isEmpty());
        
        log.debug("사용자 {} API 키 패턴 분석 시작 (실전키쌍: {}, 모의키쌍: {})", 
                userId, hasRealKeys ? "있음" : "없음", hasMockKeys ? "있음" : "없음");
        
        // 1. 키쌍 우선순위 기반 모드 결정
        if (hasRealKeys && hasMockKeys) {
            // 둘 다 있으면 실전투자용 키 패턴 확인
            if (isProductionKeyPairPattern(realAppKey, realAppSecret)) {
                return TradingModeInfo.builder()
                    .userId(userId)
                    .tradingMode(TradingMode.REAL)
                    .detectionStatus(DetectionStatus.SUCCESS)
                    .message("실전투자용 API 키쌍(AppKey+AppSecret)이 설정되어 있습니다")
                    .appKeyPattern(extractKeyPattern(realAppKey))
                    .secretKeyPattern(extractKeyPattern(realAppSecret))
                    .confidenceScore(0.95)
                    .build();
            } else {
                return TradingModeInfo.builder()
                    .userId(userId)
                    .tradingMode(TradingMode.SANDBOX)
                    .detectionStatus(DetectionStatus.SUCCESS)
                    .message("모의투자용 API 키쌍(AppKey+AppSecret)이 설정되어 있습니다")
                    .appKeyPattern(extractKeyPattern(mockAppKey))
                    .secretKeyPattern(extractKeyPattern(mockAppSecret))
                    .confidenceScore(0.90)
                    .build();
            }
        } else if (hasRealKeys) {
            // 실전투자 키쌍만 있는 경우
            return TradingModeInfo.builder()
                .userId(userId)
                .tradingMode(TradingMode.REAL)
                .detectionStatus(DetectionStatus.SUCCESS)
                .message("실전투자용 API 키쌍만 설정되어 있습니다")
                .appKeyPattern(extractKeyPattern(realAppKey))
                .secretKeyPattern(extractKeyPattern(realAppSecret))
                .confidenceScore(0.95)
                .build();
        } else if (hasMockKeys) {
            // 모의투자 키쌍만 있는 경우
            return TradingModeInfo.builder()
                .userId(userId)
                .tradingMode(TradingMode.SANDBOX)
                .detectionStatus(DetectionStatus.SUCCESS)
                .message("모의투자용 API 키쌍만 설정되어 있습니다")
                .appKeyPattern(extractKeyPattern(mockAppKey))
                .secretKeyPattern(extractKeyPattern(mockAppSecret))
                .confidenceScore(0.90)
                .build();
        } else {
            // 키쌍이 없는 경우
            return TradingModeInfo.builder()
                .userId(userId)
                .tradingMode(TradingMode.UNKNOWN)
                .detectionStatus(DetectionStatus.NO_ACCOUNT)
                .message("API 키쌍이 설정되지 않았습니다. 키움증권 계정 설정에서 AppKey와 AppSecret을 모두 등록해주세요.")
                .appKeyPattern("[NOT_SET]")
                .secretKeyPattern("[NOT_SET]")
                .confidenceScore(0.0)
                .build();
        }
    }
    
    /**
     * 실전투자 키쌍 패턴 확인 (AppKey + AppSecret)
     */
    private boolean isProductionKeyPairPattern(String appKey, String appSecret) {
        if (appKey == null || appKey.trim().isEmpty() || 
            appSecret == null || appSecret.trim().isEmpty()) {
            return false;
        }
        
        // 키움증권 실전투자 API 키 패턴 (실제 패턴에 맞춰 조정 필요)
        boolean isProductionAppKey = appKey.length() >= 32 && 
                                   !appKey.contains("_TEST") && 
                                   !appKey.contains("_DEMO") && 
                                   !appKey.contains("_SB") &&
                                   PRODUCTION_APPKEY_PATTERN.matcher(appKey).matches();
                                   
        boolean isProductionSecret = appSecret.length() >= 32 && 
                                   !appSecret.contains("_TEST") && 
                                   !appSecret.contains("_DEMO") && 
                                   !appSecret.contains("_SB") &&
                                   PRODUCTION_SECRET_PATTERN.matcher(appSecret).matches();
        
        return isProductionAppKey && isProductionSecret;
    }
    
    /**
     * API 키 패턴 추출 (로깅 및 디버깅용)
     */
    private String extractKeyPattern(String key) {
        if (key == null || key.length() < 8) {
            return "INVALID";
        }
        
        StringBuilder pattern = new StringBuilder();
        pattern.append(key.substring(0, 4));
        pattern.append("***");
        pattern.append(key.substring(key.length() - 4));
        pattern.append(" (길이: ").append(key.length()).append(")");
        
        return pattern.toString();
    }
    
    /**
     * 모든 사용자의 거래 모드 일괄 재탐지
     * 
     * @return 재탐지 결과 통계
     */
    public BatchDetectionResult batchDetectTradingModes() {
        log.info("모든 사용자 거래 모드 일괄 재탐지 시작");
        
        var allAccounts = kiwoomAccountQueryService.getAllActiveAccounts();
        int total = allAccounts.size();
        int success = 0;
        int production = 0;
        int sandbox = 0;
        int unknown = 0;
        int errors = 0;
        
        for (KiwoomAccountView account : allAccounts) {
            try {
                TradingModeInfo result = detectTradingMode(account.getUserId());
                
                if (result.getDetectionStatus() == DetectionStatus.SUCCESS) {
                    success++;
                    switch (result.getTradingMode()) {
                        case REAL -> production++;
                        case SANDBOX -> sandbox++;
                        case UNKNOWN -> unknown++;
                    }
                } else {
                    errors++;
                }
                
            } catch (Exception e) {
                log.error("사용자 {} 거래 모드 재탐지 실패", account.getUserId(), e);
                errors++;
            }
        }
        
        BatchDetectionResult result = BatchDetectionResult.builder()
            .totalAccounts(total)
            .successfulDetections(success)
            .productionModeCount(production)
            .sandboxModeCount(sandbox)
            .unknownModeCount(unknown)
            .errorCount(errors)
            .build();
        
        log.info("거래 모드 일괄 재탐지 완료: {}", result);
        return result;
    }
    
    // Enums and DTOs
    
    public enum TradingMode {
        REAL("REAL", "REAL"),
        SANDBOX("SANDBOX", "SANDBOX"),
        UNKNOWN("UNKNOWN", "UNKNOWN");
        
        private final String code;
        private final String displayName;
        
        TradingMode(String code, String displayName) {
            this.code = code;
            this.displayName = displayName;
        }
        
        public String getCode() { return code; }
        public String getDisplayName() { return displayName; }
    }
    
    public enum DetectionStatus {
        SUCCESS("SUCCESS", "성공"),
        NO_ACCOUNT("NO_ACCOUNT", "계정 없음"),
        DECRYPTION_FAILED("DECRYPTION_FAILED", "복호화 실패"),
        PATTERN_MISMATCH("PATTERN_MISMATCH", "패턴 불일치"),
        ERROR("ERROR", "오류");
        
        private final String code;
        private final String displayName;
        
        DetectionStatus(String code, String displayName) {
            this.code = code;
            this.displayName = displayName;
        }
        
        public String getCode() { return code; }
        public String getDisplayName() { return displayName; }
    }
    
    @lombok.Builder
    @lombok.Data
    public static class TradingModeInfo {
        private String userId;
        private TradingMode tradingMode;
        private DetectionStatus detectionStatus;
        private String message;
        private String appKeyPattern;
        private String secretKeyPattern;
        private Double confidenceScore;
        private java.time.Instant detectedAt;
        
        @lombok.Builder.Default
        private java.time.Instant detectedAt_default = java.time.Instant.now();
    }
    
    @lombok.Builder
    @lombok.Data
    public static class BatchDetectionResult {
        private int totalAccounts;
        private int successfulDetections;
        private int productionModeCount;
        private int sandboxModeCount;
        private int unknownModeCount;
        private int errorCount;
        private java.time.Instant batchRunAt;
        
        @lombok.Builder.Default
        private java.time.Instant batchRunAt_default = java.time.Instant.now();
    }
}