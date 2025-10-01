package com.quantum.dino.controller;

import com.quantum.dino.dto.*;
import com.quantum.dino.service.*;
import com.quantum.external.application.service.NewsService;
import com.quantum.external.domain.news.News;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import java.time.LocalDate;
import java.util.List;

/**
 * DINO 테스트 웹 인터페이스 컨트롤러
 *
 * Thymeleaf 기반 MVC 패턴으로 DINO 테스트 화면을 제공
 */
@Controller
@RequestMapping("/dino")
public class DinoController {

    private static final Logger log = LoggerFactory.getLogger(DinoController.class);

    private final DinoIntegratedService dinoIntegratedService;
    private final DinoFinanceService dinoFinanceService;
    private final DinoTechnicalService dinoTechnicalService;
    private final DinoMaterialService dinoMaterialService;
    private final DinoPriceService dinoPriceService;
    private final NewsService newsService;

    public DinoController(DinoIntegratedService dinoIntegratedService,
                          DinoFinanceService dinoFinanceService,
                          DinoTechnicalService dinoTechnicalService,
                          DinoMaterialService dinoMaterialService,
                          DinoPriceService dinoPriceService,
                          NewsService newsService) {
        this.dinoIntegratedService = dinoIntegratedService;
        this.dinoFinanceService = dinoFinanceService;
        this.dinoTechnicalService = dinoTechnicalService;
        this.dinoMaterialService = dinoMaterialService;
        this.dinoPriceService = dinoPriceService;
        this.newsService = newsService;
    }

    /**
     * DINO 통합 분석 메인 페이지
     */
    @GetMapping
    public String dinoPage(Model model) {
        log.info("DINO 통합 분석 메인 페이지 요청");

        // 페이지 제목과 설명 추가
        model.addAttribute("pageTitle", "DINO 통합 분석");
        model.addAttribute("pageDescription", "4개 영역(재무+기술+재료+가격)을 종합하여 20점 만점으로 분석합니다");

        return "dino/integrated";
    }

    /**
     * DINO 통합 분석 실행 (4개 영역 동시 분석)
     */
    @PostMapping("/analyze")
    public String analyzeIntegratedStock(@RequestParam("stockCode") String stockCode,
                                        Model model,
                                        RedirectAttributes redirectAttributes) {

        log.info("DINO 통합 분석 요청: {}", stockCode);

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
            // 통합 분석 실행 (4개 영역 병렬 처리)
            DinoIntegratedResult result = dinoIntegratedService.analyzeIntegrated(cleanStockCode);

            if (result.isValidTotalScore()) {
                log.info("DINO 통합 분석 성공: {} - {}점/20점 (등급: {})",
                    result.companyName(), result.totalScore(), result.overallGrade());

                model.addAttribute("result", result);
                model.addAttribute("pageTitle", "DINO 통합 분석 결과");
                model.addAttribute("pageDescription",
                    String.format("%s (%s) 통합 분석 결과 - %s등급 (%d점/20점)",
                        result.companyName(), result.stockCode(), result.overallGrade(), result.totalScore()));

                // 분석 성공 메시지
                model.addAttribute("successMessage",
                    String.format("'%s' 통합 분석이 완료되었습니다. (4개 영역 병렬 분석)", result.companyName()));

                // 각 영역별 성공/실패 상태 정보
                model.addAttribute("analysisStatus", generateAnalysisStatusSummary(result));

                // 최근 7일 뉴스 조회
                try {
                    LocalDate endDate = LocalDate.now();
                    LocalDate startDate = endDate.minusDays(7);
                    List<News> recentNews = newsService.searchNews(result.companyName(), startDate, endDate);

                    model.addAttribute("recentNews", recentNews);
                    log.info("뉴스 조회 성공: {} - {}건", result.companyName(), recentNews.size());
                } catch (Exception e) {
                    log.warn("뉴스 조회 실패: {} - {}", result.companyName(), e.getMessage());
                    model.addAttribute("recentNews", List.of());
                }

            } else {
                log.warn("DINO 통합 분석 실패: {}", cleanStockCode);
                redirectAttributes.addFlashAttribute("errorMessage",
                    String.format("종목코드 '%s'의 분석 데이터를 처리할 수 없습니다.", cleanStockCode));
                return "redirect:/dino";
            }

        } catch (Exception e) {
            log.error("DINO 통합 분석 중 오류 발생: {} - {}", cleanStockCode, e.getMessage(), e);

            // 구체적인 오류 메시지 제공
            String errorMessage = getSpecificErrorMessage(e, "통합 분석");
            redirectAttributes.addFlashAttribute("errorMessage", errorMessage);
            return "redirect:/dino";
        }

        return "dino/integrated";
    }

    /**
     * 분석 상태 요약 정보 생성
     */
    private String generateAnalysisStatusSummary(DinoIntegratedResult result) {
        StringBuilder status = new StringBuilder();

        status.append("재무분석: ").append(getSuccessStatus(result.financeResult() != null && result.financeResult().isSuccessful())).append(" | ");
        status.append("기술분석: ").append(getSuccessStatus(result.technicalResult() != null && result.technicalResult().isValidScore())).append(" | ");
        status.append("재료분석: ").append(getSuccessStatus(result.materialResult() != null && result.materialResult().isValidScore())).append(" | ");
        status.append("가격분석: ").append(getSuccessStatus(result.priceResult() != null && result.priceResult().isValidScore()));

        return status.toString();
    }

    private String getSuccessStatus(boolean isSuccess) {
        return isSuccess ? "✅" : "❌";
    }

    /**
     * 기술 분석 페이지
     */
    @GetMapping("/technical")
    public String technicalPage(Model model) {
        log.info("DINO 기술 분석 페이지 요청");

        // 페이지 제목과 설명 추가
        model.addAttribute("pageTitle", "DINO 기술 분석");
        model.addAttribute("pageDescription", "4가지 기술지표로 주가 패턴을 5점 만점으로 분석합니다");

        return "dino/technical";
    }

    /**
     * 기술 분석 실행
     */
    @PostMapping("/technical/analyze")
    public String analyzeTechnicalStock(@RequestParam("stockCode") String stockCode,
                                        Model model,
                                        RedirectAttributes redirectAttributes) {

        log.info("DINO 기술 분석 요청: {}", stockCode);

        // 입력 검증
        if (stockCode == null || stockCode.trim().isEmpty()) {
            redirectAttributes.addFlashAttribute("errorMessage", "종목코드를 입력해주세요.");
            return "redirect:/dino/technical";
        }

        // 종목코드 정리 (공백 제거, 6자리 패딩)
        String cleanStockCode = stockCode.trim().replaceAll("[^0-9]", "");
        if (cleanStockCode.length() < 6) {
            cleanStockCode = String.format("%06d", Integer.parseInt(cleanStockCode));
        }

        try {
            // 기술 분석 실행
            DinoTechnicalResult result = dinoTechnicalService.analyzeTechnicalScore(cleanStockCode);

            if (result.isValidScore()) {
                log.info("DINO 기술 분석 성공: {} - {}점", result.companyName(), result.totalScore());

                model.addAttribute("result", result);
                model.addAttribute("pageTitle", "DINO 기술 분석 결과");
                model.addAttribute("pageDescription",
                    String.format("%s (%s) 기술 분석 결과", result.companyName(), result.stockCode()));

                // 분석 성공 메시지
                model.addAttribute("successMessage",
                    String.format("'%s' 기술 분석이 완료되었습니다.", result.companyName()));

            } else {
                log.warn("DINO 기술 분석 실패: {}", cleanStockCode);
                redirectAttributes.addFlashAttribute("errorMessage",
                    String.format("종목코드 '%s'의 기술 분석 데이터를 처리할 수 없습니다.", cleanStockCode));
                return "redirect:/dino/technical";
            }

        } catch (Exception e) {
            log.error("DINO 기술 분석 중 오류 발생: {} - {}", cleanStockCode, e.getMessage(), e);
            redirectAttributes.addFlashAttribute("errorMessage",
                "기술 분석 중 오류가 발생했습니다. 다시 시도해주세요.");
            return "redirect:/dino/technical";
        }

        return "dino/technical";
    }

    /**
     * 재료 분석 페이지
     */
    @GetMapping("/material")
    public String materialPage(Model model) {
        log.info("DINO 재료 분석 페이지 요청");

        // 페이지 제목과 설명 추가
        model.addAttribute("pageTitle", "DINO 재료 분석");
        model.addAttribute("pageDescription", "뉴스, 테마, 시장심리 등 재료 요소를 5점 만점으로 분석합니다");

        return "dino/material";
    }

    /**
     * 재료 분석 실행
     */
    @PostMapping("/material/analyze")
    public String analyzeMaterialStock(@RequestParam("stockCode") String stockCode,
                                       Model model,
                                       RedirectAttributes redirectAttributes) {

        log.info("DINO 재료 분석 요청: {}", stockCode);

        // 입력 검증
        if (stockCode == null || stockCode.trim().isEmpty()) {
            redirectAttributes.addFlashAttribute("errorMessage", "종목코드를 입력해주세요.");
            return "redirect:/dino/material";
        }

        // 종목코드 정리 (공백 제거, 6자리 패딩)
        String cleanStockCode = stockCode.trim().replaceAll("[^0-9]", "");
        if (cleanStockCode.length() < 6) {
            cleanStockCode = String.format("%06d", Integer.parseInt(cleanStockCode));
        }

        try {
            // 재료 분석 실행
            DinoMaterialResult result = dinoMaterialService.analyzeMaterialScore(cleanStockCode);

            if (result.isValidScore()) {
                log.info("DINO 재료 분석 성공: {} - {}점", result.companyName(), result.totalScore());

                model.addAttribute("result", result);
                model.addAttribute("pageTitle", "DINO 재료 분석 결과");
                model.addAttribute("pageDescription",
                    String.format("%s (%s) 재료 분석 결과", result.companyName(), result.stockCode()));

                // 분석 성공 메시지
                model.addAttribute("successMessage",
                    String.format("'%s' 재료 분석이 완료되었습니다.", result.companyName()));

            } else {
                log.warn("DINO 재료 분석 실패: {}", cleanStockCode);
                redirectAttributes.addFlashAttribute("errorMessage",
                    String.format("종목코드 '%s'의 재료 분석 데이터를 처리할 수 없습니다.", cleanStockCode));
                return "redirect:/dino/material";
            }

        } catch (Exception e) {
            log.error("DINO 재료 분석 중 오류 발생: {} - {}", cleanStockCode, e.getMessage(), e);
            redirectAttributes.addFlashAttribute("errorMessage",
                "재료 분석 중 오류가 발생했습니다. 다시 시도해주세요.");
            return "redirect:/dino/material";
        }

        return "dino/material";
    }

    /**
     * 가격 분석 페이지
     */
    @GetMapping("/price")
    public String pricePage(Model model) {
        log.info("DINO 가격 분석 페이지 요청");

        // 페이지 제목과 설명 추가
        model.addAttribute("pageTitle", "DINO 가격 분석");
        model.addAttribute("pageDescription", "가격 트렌드, 모멘텀, 변동성 등을 5점 만점으로 분석합니다");

        return "dino/price";
    }

    /**
     * 가격 분석 실행
     */
    @PostMapping("/price/analyze")
    public String analyzePriceStock(@RequestParam("stockCode") String stockCode,
                                    Model model,
                                    RedirectAttributes redirectAttributes) {

        log.info("DINO 가격 분석 요청: {}", stockCode);

        // 입력 검증
        if (stockCode == null || stockCode.trim().isEmpty()) {
            redirectAttributes.addFlashAttribute("errorMessage", "종목코드를 입력해주세요.");
            return "redirect:/dino/price";
        }

        // 종목코드 정리 (공백 제거, 6자리 패딩)
        String cleanStockCode = stockCode.trim().replaceAll("[^0-9]", "");
        if (cleanStockCode.length() < 6) {
            cleanStockCode = String.format("%06d", Integer.parseInt(cleanStockCode));
        }

        try {
            // 가격 분석 실행
            DinoPriceResult result = dinoPriceService.analyzePriceScore(cleanStockCode);

            if (result.isValidScore()) {
                log.info("DINO 가격 분석 성공: {} - {}점", result.companyName(), result.totalScore());

                model.addAttribute("result", result);
                model.addAttribute("pageTitle", "DINO 가격 분석 결과");
                model.addAttribute("pageDescription",
                    String.format("%s (%s) 가격 분석 결과", result.companyName(), result.stockCode()));

                // 분석 성공 메시지
                model.addAttribute("successMessage",
                    String.format("'%s' 가격 분석이 완료되었습니다.", result.companyName()));

            } else {
                log.warn("DINO 가격 분석 실패: {}", cleanStockCode);
                redirectAttributes.addFlashAttribute("errorMessage",
                    String.format("종목코드 '%s'의 가격 분석 데이터를 처리할 수 없습니다.", cleanStockCode));
                return "redirect:/dino/price";
            }

        } catch (Exception e) {
            log.error("DINO 가격 분석 중 오류 발생: {} - {}", cleanStockCode, e.getMessage(), e);
            redirectAttributes.addFlashAttribute("errorMessage",
                "가격 분석 중 오류가 발생했습니다. 다시 시도해주세요.");
            return "redirect:/dino/price";
        }

        return "dino/price";
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

    /**
     * 예외 타입에 따른 구체적인 오류 메시지 생성
     */
    private String getSpecificErrorMessage(Exception e, String analysisType) {
        String errorMessage = e.getMessage();

        // KIS API 관련 오류
        if (errorMessage != null) {
            if (errorMessage.contains("토큰") || errorMessage.contains("token")) {
                return String.format("%s 중 인증 오류가 발생했습니다. 잠시 후 다시 시도해주세요.", analysisType);
            }
            if (errorMessage.contains("연결") || errorMessage.contains("timeout")) {
                return String.format("%s 중 네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요.", analysisType);
            }
            if (errorMessage.contains("데이터") || errorMessage.contains("data")) {
                return String.format("%s 중 데이터 처리 오류가 발생했습니다. 종목코드를 확인해주세요.", analysisType);
            }
            if (errorMessage.contains("NumberFormat") || errorMessage.contains("형식")) {
                return "올바른 종목코드 형식을 입력해주세요. (예: 005930)";
            }
        }

        // 기본 오류 메시지
        return String.format("%s 중 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.", analysisType);
    }
}