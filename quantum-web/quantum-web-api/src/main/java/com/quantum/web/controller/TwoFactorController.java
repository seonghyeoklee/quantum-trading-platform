package com.quantum.web.controller;

import com.quantum.trading.platform.query.service.UserQueryService;
import com.quantum.trading.platform.query.view.UserView;
import com.quantum.trading.platform.shared.command.EnableTwoFactorCommand;
import com.quantum.trading.platform.shared.command.DisableTwoFactorCommand;
import com.quantum.trading.platform.shared.command.UseBackupCodeCommand;
import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.web.service.AuthService;
import com.quantum.web.service.TwoFactorAuthService;
import com.quantum.web.service.TwoFactorAuthService.TwoFactorSetupData;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.*;
import java.util.stream.Collectors;

/**
 * 2FA (Two-Factor Authentication) 관련 API 컨트롤러
 */
@RestController
@RequestMapping("/api/v1/auth/2fa")
@CrossOrigin(origins = {"http://localhost:10301"})
public class TwoFactorController {
    
    private static final Logger logger = LoggerFactory.getLogger(TwoFactorController.class);
    
    private final TwoFactorAuthService twoFactorAuthService;
    private final UserQueryService userQueryService;
    private final AuthService authService;
    private final CommandGateway commandGateway;
    
    @Autowired
    public TwoFactorController(TwoFactorAuthService twoFactorAuthService, 
                               UserQueryService userQueryService,
                               AuthService authService,
                               CommandGateway commandGateway) {
        this.twoFactorAuthService = twoFactorAuthService;
        this.userQueryService = userQueryService;
        this.authService = authService;
        this.commandGateway = commandGateway;
    }
    
    /**
     * 2FA 설정 초기화 - QR 코드와 시크릿 키 생성
     */
    @PostMapping("/setup")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER', 'TRADER')")
    public ResponseEntity<Map<String, Object>> setupTwoFactor() {
        try {
            Authentication auth = SecurityContextHolder.getContext().getAuthentication();
            String username = auth.getName();
            
            logger.info("Starting 2FA setup for user: {}", username);
            
            // 설정 데이터 생성
            TwoFactorSetupData setupData = twoFactorAuthService.generateSetupData(username);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("data", Map.of(
                "secretKey", setupData.getSecretKey(),
                "qrCodeUrl", setupData.getQrCodeUrl(),
                "qrCodeImage", setupData.getQrCodeImage()
            ));
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("Failed to setup 2FA", e);
            return ResponseEntity.badRequest().body(Map.of(
                "success", false,
                "error", "2FA 설정 초기화에 실패했습니다."
            ));
        }
    }
    
    /**
     * 2FA 인증 코드 검증 및 활성화
     */
    @PostMapping("/verify")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER', 'TRADER')")
    public ResponseEntity<Map<String, Object>> verifyAndEnable(@RequestBody Map<String, String> request) {
        try {
            Authentication auth = SecurityContextHolder.getContext().getAuthentication();
            String username = auth.getName();
            
            String secretKey = request.get("secretKey");
            String verificationCode = request.get("verificationCode");
            
            if (secretKey == null || verificationCode == null) {
                return ResponseEntity.badRequest().body(Map.of(
                    "success", false,
                    "error", "시크릿 키와 인증 코드가 필요합니다."
                ));
            }
            
            logger.info("Verifying 2FA code for user: {}", username);
            
            // TOTP 코드 검증
            if (!twoFactorAuthService.verifyTotp(secretKey, verificationCode)) {
                return ResponseEntity.badRequest().body(Map.of(
                    "success", false,
                    "error", "인증 코드가 올바르지 않습니다."
                ));
            }
            
            // 백업 코드 생성
            List<String> backupCodes = twoFactorAuthService.generateBackupCodes();
            Set<String> hashedBackupCodes = backupCodes.stream()
                .map(twoFactorAuthService::hashBackupCode)
                .collect(Collectors.toSet());
            
            // 사용자 조회하여 UserId 가져오기
            Optional<UserView> userOpt = userQueryService.findByUsername(username);
            if (userOpt.isEmpty()) {
                return ResponseEntity.badRequest().body(Map.of(
                    "success", false,
                    "error", "사용자를 찾을 수 없습니다."
                ));
            }
            
            UserView user = userOpt.get();
            
            // Command를 통한 2FA 활성화
            EnableTwoFactorCommand command = EnableTwoFactorCommand.of(
                UserId.of(user.getUserId()),
                secretKey,
                hashedBackupCodes
            );
            
            try {
                commandGateway.sendAndWait(command);
                logger.info("2FA enabled successfully for user: {}", username);
            } catch (Exception commandException) {
                logger.error("Failed to enable 2FA via command for user: {}", username, commandException);
                return ResponseEntity.badRequest().body(Map.of(
                    "success", false,
                    "error", "2FA 활성화 처리에 실패했습니다."
                ));
            }
            
            return ResponseEntity.ok(Map.of(
                "success", true,
                "data", Map.of(
                    "backupCodes", backupCodes,
                    "message", "2FA가 성공적으로 활성화되었습니다."
                )
            ));
            
        } catch (Exception e) {
            logger.error("Failed to verify and enable 2FA", e);
            return ResponseEntity.badRequest().body(Map.of(
                "success", false,
                "error", "2FA 활성화에 실패했습니다."
            ));
        }
    }
    
    /**
     * 2FA 비활성화
     */
    @PostMapping("/disable")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER', 'TRADER')")
    public ResponseEntity<Map<String, Object>> disableTwoFactor() {
        try {
            Authentication auth = SecurityContextHolder.getContext().getAuthentication();
            String username = auth.getName();
            
            logger.info("Disabling 2FA for user: {}", username);
            
            // 사용자 조회하여 UserId 가져오기
            Optional<UserView> userOpt = userQueryService.findByUsername(username);
            if (userOpt.isEmpty()) {
                return ResponseEntity.badRequest().body(Map.of(
                    "success", false,
                    "error", "사용자를 찾을 수 없습니다."
                ));
            }
            
            UserView user = userOpt.get();
            
            // Command를 통한 2FA 비활성화
            DisableTwoFactorCommand command = DisableTwoFactorCommand.of(
                UserId.of(user.getUserId()),
                "사용자 요청으로 비활성화"
            );
            
            try {
                commandGateway.sendAndWait(command);
                logger.info("2FA disabled successfully for user: {}", username);
            } catch (Exception commandException) {
                logger.error("Failed to disable 2FA via command for user: {}", username, commandException);
                return ResponseEntity.badRequest().body(Map.of(
                    "success", false,
                    "error", "2FA 비활성화 처리에 실패했습니다."
                ));
            }
            
            return ResponseEntity.ok(Map.of(
                "success", true,
                "message", "2FA가 비활성화되었습니다."
            ));
            
        } catch (Exception e) {
            logger.error("Failed to disable 2FA", e);
            return ResponseEntity.badRequest().body(Map.of(
                "success", false,
                "error", "2FA 비활성화에 실패했습니다."
            ));
        }
    }
    
    /**
     * 2FA 상태 조회
     */
    @GetMapping("/status")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER', 'TRADER')")
    public ResponseEntity<Map<String, Object>> getTwoFactorStatus() {
        try {
            logger.info("Starting 2FA status check");
            
            Authentication auth = SecurityContextHolder.getContext().getAuthentication();
            if (auth == null) {
                logger.error("Authentication is null");
                throw new IllegalStateException("No authentication found");
            }
            
            String username = auth.getName();
            logger.info("Checking 2FA status for username: {}", username);
            
            Optional<UserView> userOpt = userQueryService.findByUsername(username);
            logger.info("User query result: {}", userOpt.isPresent() ? "found" : "not found");
            
            if (userOpt.isPresent()) {
                UserView user = userOpt.get();
                logger.info("User found: {}, processing 2FA fields", user.getUsername());
                
                // Safe access to 2FA fields with null checks
                Boolean twoFactorEnabled = null;
                String setupAt = null;
                Integer remainingBackupCodes = null;
                
                try {
                    logger.info("Getting twoFactorEnabled...");
                    twoFactorEnabled = user.isTwoFactorEnabled();
                    logger.info("twoFactorEnabled: {}", twoFactorEnabled);
                } catch (Exception e) {
                    logger.error("Error getting twoFactorEnabled: {}", e.getMessage(), e);
                    throw e;
                }
                
                try {
                    logger.info("Getting twoFactorSetupAt...");
                    setupAt = user.getTwoFactorSetupAt() != null ? 
                        user.getTwoFactorSetupAt().toString() : null;
                    logger.info("setupAt: {}", setupAt);
                } catch (Exception e) {
                    logger.error("Error getting twoFactorSetupAt: {}", e.getMessage(), e);
                    throw e;
                }
                
                try {
                    logger.info("Getting remainingBackupCodesCount...");
                    remainingBackupCodes = user.getRemainingBackupCodesCount();
                    logger.info("remainingBackupCodes: {}", remainingBackupCodes);
                } catch (Exception e) {
                    logger.error("Error getting remainingBackupCodesCount: {}", e.getMessage(), e);
                    throw e;
                }
                
                logger.info("2FA status for user {}: enabled={}, setupAt={}, backupCodes={}", 
                    username, twoFactorEnabled, setupAt, remainingBackupCodes);
                
                return ResponseEntity.ok(Map.of(
                    "success", true,
                    "data", Map.of(
                        "enabled", twoFactorEnabled,
                        "setupAt", setupAt,
                        "remainingBackupCodes", remainingBackupCodes
                    )
                ));
            } else {
                logger.warn("User not found: {}", username);
                return ResponseEntity.badRequest().body(Map.of(
                    "success", false,
                    "error", "사용자를 찾을 수 없습니다."
                ));
            }
            
        } catch (Exception e) {
            logger.error("Failed to get 2FA status - Exception: {} - Message: {}", 
                e.getClass().getSimpleName(), e.getMessage(), e);
            return ResponseEntity.badRequest().body(Map.of(
                "success", false,
                "error", "2FA 상태 조회에 실패했습니다."
            ));
        }
    }
    
    /**
     * 로그인 시 2FA 코드 검증 (공개 엔드포인트)
     */
    @PostMapping("/verify-login")
    public ResponseEntity<Map<String, Object>> verifyTwoFactorLogin(@RequestBody Map<String, String> request) {
        try {
            String username = request.get("username");
            String code = request.get("code");
            String sessionToken = request.get("sessionToken"); // 임시 세션 토큰
            Boolean isBackupCode = Boolean.valueOf(request.get("isBackupCode"));
            
            if (username == null || code == null || sessionToken == null) {
                return ResponseEntity.badRequest().body(Map.of(
                    "success", false,
                    "error", "필수 파라미터가 누락되었습니다."
                ));
            }
            
            logger.info("Verifying 2FA login code for user: {} (backup: {})", username, isBackupCode);
            
            // 임시 세션 토큰 검증 (실제로는 Redis 등에서 검증해야 함)
            // 여기서는 단순 구현
            
            Optional<UserView> userOpt = userQueryService.findByUsername(username);
            if (userOpt.isEmpty()) {
                return ResponseEntity.badRequest().body(Map.of(
                    "success", false,
                    "error", "사용자를 찾을 수 없습니다."
                ));
            }
            
            UserView user = userOpt.get();
            
            if (!user.isTwoFactorEnabled()) {
                return ResponseEntity.badRequest().body(Map.of(
                    "success", false,
                    "error", "2FA가 활성화되지 않은 사용자입니다."
                ));
            }
            
            boolean verified = false;
            
            if (isBackupCode) {
                // 백업 코드 검증
                String hashedCode = twoFactorAuthService.hashBackupCode(code.toUpperCase().trim());
                verified = user.getRemainingBackupCodesCount() > 0 && 
                          user.getBackupCodeHashes().contains(hashedCode);
                
                // Command를 통한 백업 코드 사용 처리
                if (verified) {
                    try {
                        UseBackupCodeCommand command = UseBackupCodeCommand.of(
                            UserId.of(user.getUserId()),
                            hashedCode,
                            request.get("ipAddress"), // IP 주소가 있으면 사용
                            request.get("userAgent")  // User-Agent가 있으면 사용
                        );
                        commandGateway.sendAndWait(command);
                        logger.info("Backup code used successfully for user: {}", username);
                    } catch (Exception commandException) {
                        logger.error("Failed to process backup code usage via command for user: {}", username, commandException);
                        // 명령 실패해도 로그인은 계속 진행 (이미 검증됨)
                    }
                }
            } else {
                // TOTP 코드 검증
                verified = twoFactorAuthService.verifyTotp(user.getTotpSecretKey(), code);
            }
            
            if (verified) {
                // 로그인 성공 - 실제 JWT 토큰 생성
                String jwtToken = authService.generateTokenForUser(user);
                
                logger.info("2FA verification successful for user: {}", username);
                
                return ResponseEntity.ok(Map.of(
                    "success", true,
                    "data", Map.of(
                        "accessToken", jwtToken,
                        "tokenType", "Bearer",
                        "expiresIn", 3600,
                        "user", Map.of(
                            "id", user.getUserId(),
                            "username", user.getUsername(),
                            "email", user.getEmail(),
                            "roles", user.getRoles()
                        )
                    )
                ));
            } else {
                return ResponseEntity.badRequest().body(Map.of(
                    "success", false,
                    "error", isBackupCode ? "백업 코드가 올바르지 않습니다." : "인증 코드가 올바르지 않습니다."
                ));
            }
            
        } catch (Exception e) {
            logger.error("Failed to verify 2FA login", e);
            return ResponseEntity.badRequest().body(Map.of(
                "success", false,
                "error", "2FA 로그인 검증에 실패했습니다."
            ));
        }
    }
}