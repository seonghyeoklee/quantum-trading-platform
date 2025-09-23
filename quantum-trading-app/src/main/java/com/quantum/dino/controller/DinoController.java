package com.quantum.dino.controller;

import com.quantum.dino.dto.DinoFinanceResult;
import com.quantum.dino.service.DinoFinanceService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

/**
 * DINO 테스트 웹 인터페이스 컨트롤러
 *
 * Thymeleaf 기반 MVC 패턴으로 DINO 테스트 화면을 제공
 */
@Controller
@RequestMapping("/dino")
public class DinoController {

    private static final Logger log = LoggerFactory.getLogger(DinoController.class);

    private final DinoFinanceService dinoFinanceService;

    public DinoController(DinoFinanceService dinoFinanceService) {
        this.dinoFinanceService = dinoFinanceService;
    }

    /**
     * DINO 테스트 메인 페이지
     */
    @GetMapping
    public String dinoPage(Model model) {
        log.info("DINO 테스트 메인 페이지 요청");

        // 페이지 제목과 설명 추가
        model.addAttribute("pageTitle", "DINO 테스트");
        model.addAttribute("pageDescription", "종목의 재무 상태를 15점 만점으로 분석합니다");

        return "dino/dino";
    }

    /**
     * 재무 분석 실행
     */
    @PostMapping("/analyze")
    public String analyzeStock(@RequestParam("stockCode") String stockCode,
                               Model model,
                               RedirectAttributes redirectAttributes) {

        log.info("DINO 재무 분석 요청: {}", stockCode);

        // 입력 검증
        if (stockCode == null || stockCode.trim().isEmpty()) {
            redirectAttributes.addFlashAttribute("errorMessage", "종목코드를 입력해주세요.");
            return "redirect:/dino";
        }

        // 종목코드 정리 (공백 제거, 6자리 패딩)
        String cleanStockCode = stockCode.trim().replaceAll("[^0-9]", "");
        if (cleanStockCode.length() < 6) {
            cleanStockCode = String.format("%06d", Integer.parseInt(cleanStockCode));
        }

        try {
            // 재무 분석 실행
            DinoFinanceResult result = dinoFinanceService.analyzeFinanceScore(cleanStockCode);

            if (result.isSuccessful()) {
                log.info("DINO 분석 성공: {} - {}점", result.companyName(), result.totalScore());

                model.addAttribute("result", result);
                model.addAttribute("pageTitle", "DINO 분석 결과");
                model.addAttribute("pageDescription",
                    String.format("%s (%s) 재무 분석 결과", result.companyName(), result.stockCode()));

                // 분석 성공 메시지
                model.addAttribute("successMessage",
                    String.format("'%s' 재무 분석이 완료되었습니다.", result.companyName()));

            } else {
                log.warn("DINO 분석 실패: {}", cleanStockCode);
                redirectAttributes.addFlashAttribute("errorMessage",
                    String.format("종목코드 '%s'의 재무 데이터를 찾을 수 없습니다.", cleanStockCode));
                return "redirect:/dino";
            }

        } catch (Exception e) {
            log.error("DINO 분석 중 오류 발생: {} - {}", cleanStockCode, e.getMessage(), e);
            redirectAttributes.addFlashAttribute("errorMessage",
                "분석 중 오류가 발생했습니다. 다시 시도해주세요.");
            return "redirect:/dino";
        }

        return "dino/dino";
    }

    /**
     * 분석 히스토리 페이지 (향후 확장용)
     */
    @GetMapping("/history")
    public String historyPage(Model model) {
        log.info("DINO 분석 히스토리 페이지 요청");

        model.addAttribute("pageTitle", "분석 히스토리");
        model.addAttribute("pageDescription", "과거 DINO 분석 결과를 확인합니다");

        // TODO: 히스토리 데이터 조회 및 모델 추가

        return "dino/history";
    }
}