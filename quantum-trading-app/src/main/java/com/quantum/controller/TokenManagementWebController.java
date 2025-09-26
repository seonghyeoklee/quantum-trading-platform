package com.quantum.controller;

import com.quantum.kis.application.port.in.GetTokenStatusUseCase;
import com.quantum.kis.application.port.in.RefreshTokenUseCase;
import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.dto.TokenInfo;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import java.util.Map;

/**
 * KIS 토큰 관리 웹 컨트롤러
 * 토큰 상태 조회 및 재발급을 위한 웹 인터페이스 제공
 */
@Controller
@RequestMapping("/tokens")
public class TokenManagementWebController {

    private static final Logger log = LoggerFactory.getLogger(TokenManagementWebController.class);

    private final GetTokenStatusUseCase getTokenStatusUseCase;
    private final RefreshTokenUseCase refreshTokenUseCase;

    public TokenManagementWebController(GetTokenStatusUseCase getTokenStatusUseCase,
                                      RefreshTokenUseCase refreshTokenUseCase) {
        this.getTokenStatusUseCase = getTokenStatusUseCase;
        this.refreshTokenUseCase = refreshTokenUseCase;
    }

    /**
     * 토큰 관리 메인 페이지
     */
    @GetMapping
    public String tokenManagement(Model model) {
        log.info("토큰 관리 페이지 접근");

        try {
            Map<String, TokenInfo> tokenStatus = getTokenStatusUseCase.getAllTokenStatus();
            model.addAttribute("tokenStatus", tokenStatus);
            model.addAttribute("title", "토큰 관리");

            // 환경별 토큰 상태 추가
            model.addAttribute("prodTokens", filterTokensByEnvironment(tokenStatus, KisEnvironment.PROD));
            model.addAttribute("vpsTokens", filterTokensByEnvironment(tokenStatus, KisEnvironment.VPS));

            return "tokens/management";

        } catch (Exception e) {
            log.error("토큰 상태 조회 실패: {}", e.getMessage());
            model.addAttribute("errorMessage", "토큰 상태 조회 중 오류가 발생했습니다: " + e.getMessage());
            model.addAttribute("title", "토큰 관리");
            return "tokens/management";
        }
    }

    /**
     * 특정 환경의 액세스 토큰 재발급
     */
    @PostMapping("/refresh/access-token")
    public String refreshAccessToken(@RequestParam KisEnvironment environment,
                                   RedirectAttributes redirectAttributes) {
        log.info("액세스 토큰 재발급 요청 - 환경: {}", environment);

        try {
            String newToken = refreshTokenUseCase.refreshAccessToken(environment);
            redirectAttributes.addFlashAttribute("successMessage",
                environment.getDescription() + " 환경의 액세스 토큰이 재발급되었습니다.");

            log.info("액세스 토큰 재발급 성공 - 환경: {}", environment);

        } catch (Exception e) {
            log.error("액세스 토큰 재발급 실패 - 환경: {}, 오류: {}", environment, e.getMessage());
            redirectAttributes.addFlashAttribute("errorMessage",
                environment.getDescription() + " 환경의 액세스 토큰 재발급 실패: " + e.getMessage());
        }

        return "redirect:/tokens";
    }

    /**
     * 특정 환경의 웹소켓 키 재발급
     */
    @PostMapping("/refresh/websocket-key")
    public String refreshWebSocketKey(@RequestParam KisEnvironment environment,
                                    RedirectAttributes redirectAttributes) {
        log.info("웹소켓 키 재발급 요청 - 환경: {}", environment);

        try {
            String newKey = refreshTokenUseCase.refreshWebSocketKey(environment);
            redirectAttributes.addFlashAttribute("successMessage",
                environment.getDescription() + " 환경의 웹소켓 키가 재발급되었습니다.");

            log.info("웹소켓 키 재발급 성공 - 환경: {}", environment);

        } catch (Exception e) {
            log.error("웹소켓 키 재발급 실패 - 환경: {}, 오류: {}", environment, e.getMessage());
            redirectAttributes.addFlashAttribute("errorMessage",
                environment.getDescription() + " 환경의 웹소켓 키 재발급 실패: " + e.getMessage());
        }

        return "redirect:/tokens";
    }

    /**
     * 모든 토큰 재발급
     */
    @PostMapping("/refresh/all")
    public String refreshAllTokens(RedirectAttributes redirectAttributes) {
        log.info("모든 토큰 재발급 요청");

        try {
            refreshTokenUseCase.refreshAllTokens();
            redirectAttributes.addFlashAttribute("successMessage", "모든 토큰이 재발급되었습니다.");

            log.info("모든 토큰 재발급 성공");

        } catch (Exception e) {
            log.error("모든 토큰 재발급 실패 - 오류: {}", e.getMessage());
            redirectAttributes.addFlashAttribute("errorMessage",
                "모든 토큰 재발급 실패: " + e.getMessage());
        }

        return "redirect:/tokens";
    }

    /**
     * 토큰 상태를 환경별로 필터링
     */
    private Map<String, TokenInfo> filterTokensByEnvironment(Map<String, TokenInfo> tokenStatus,
                                                            KisEnvironment environment) {
        return tokenStatus.entrySet().stream()
                .filter(entry -> entry.getValue().environment() == environment)
                .collect(java.util.stream.Collectors.toMap(
                    Map.Entry::getKey,
                    Map.Entry::getValue
                ));
    }
}