package com.quantum.dino.service;

import com.quantum.dino.dto.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * DINO 통합 분석 서비스
 *
 * 4개 영역의 분석을 병렬로 실행하여 20점 만점 종합 결과를 제공
 * - 재무 분석 (5점): DinoFinanceService
 * - 기술 분석 (5점): DinoTechnicalService
 * - 재료 분석 (5점): DinoMaterialService
 * - 가격 분석 (5점): DinoPriceService
 *
 * 병렬 처리를 통해 분석 시간을 단축하고 사용자 경험을 개선
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DinoIntegratedService {

    private final DinoFinanceService dinoFinanceService;
    private final DinoTechnicalService dinoTechnicalService;
    private final DinoMaterialService dinoMaterialService;
    private final DinoPriceService dinoPriceService;

    // 병렬 처리를 위한 스레드 풀 (최대 4개 스레드)
    private final ExecutorService executorService = Executors.newFixedThreadPool(4);

    /**
     * 종목 통합 분석 실행 (4개 영역 병렬 처리)
     *
     * @param stockCode 종목코드 (6자리)
     * @return 20점 만점 통합 분석 결과
     */
    public DinoIntegratedResult analyzeIntegrated(String stockCode) {
        log.info("=== DINO 통합 분석 시작: {} ===", stockCode);

        long startTime = System.currentTimeMillis();

        try {
            // 4개 영역 병렬 분석 실행
            CompletableFuture<DinoFinanceResult> financeTask = CompletableFuture
                    .supplyAsync(() -> executeFinanceAnalysis(stockCode), executorService);

            CompletableFuture<DinoTechnicalResult> technicalTask = CompletableFuture
                    .supplyAsync(() -> executeTechnicalAnalysis(stockCode), executorService);

            CompletableFuture<DinoMaterialResult> materialTask = CompletableFuture
                    .supplyAsync(() -> executeMaterialAnalysis(stockCode), executorService);

            CompletableFuture<DinoPriceResult> priceTask = CompletableFuture
                    .supplyAsync(() -> executePriceAnalysis(stockCode), executorService);

            // 모든 분석 완료 대기
            CompletableFuture<Void> allTasks = CompletableFuture.allOf(
                    financeTask, technicalTask, materialTask, priceTask);

            allTasks.join(); // 모든 작업 완료까지 대기

            // 각 분석 결과 수집
            DinoFinanceResult financeResult = financeTask.get();
            DinoTechnicalResult technicalResult = technicalTask.get();
            DinoMaterialResult materialResult = materialTask.get();
            DinoPriceResult priceResult = priceTask.get();

            // 회사명 결정 (가장 신뢰할 수 있는 결과에서 추출)
            String companyName = determineCompanyName(stockCode, financeResult, technicalResult, materialResult, priceResult);

            // 통합 결과 생성
            DinoIntegratedResult result = DinoIntegratedResult.create(
                    stockCode, companyName, financeResult, technicalResult, materialResult, priceResult);

            long endTime = System.currentTimeMillis();
            long executionTime = endTime - startTime;

            log.info("DINO 통합 분석 완료: {} - 총점 {}/20점 (등급: {}, 실행시간: {}ms)",
                    result.companyName(), result.totalScore(), result.overallGrade(), executionTime);

            logDetailedResults(result);

            return result;

        } catch (Exception e) {
            log.error("DINO 통합 분석 실패: {} - {}", stockCode, e.getMessage(), e);
            return DinoIntegratedResult.createFailedResult(stockCode);
        }
    }

    /**
     * 재무 분석 실행 (안전한 래퍼)
     */
    private DinoFinanceResult executeFinanceAnalysis(String stockCode) {
        try {
            log.debug("재무 분석 시작: {}", stockCode);
            DinoFinanceResult result = dinoFinanceService.analyzeFinanceScore(stockCode);
            log.debug("재무 분석 완료: {} - {}점", stockCode, result.totalScore());
            return result;
        } catch (Exception e) {
            log.warn("재무 분석 실패: {} - {}", stockCode, e.getMessage());
            return DinoFinanceResult.createFailedResult(stockCode);
        }
    }

    /**
     * 기술 분석 실행 (안전한 래퍼)
     */
    private DinoTechnicalResult executeTechnicalAnalysis(String stockCode) {
        try {
            log.debug("기술 분석 시작: {}", stockCode);
            DinoTechnicalResult result = dinoTechnicalService.analyzeTechnicalScore(stockCode);
            log.debug("기술 분석 완료: {} - {}점", stockCode, result.totalScore());
            return result;
        } catch (Exception e) {
            log.warn("기술 분석 실패: {} - {}", stockCode, e.getMessage());
            return DinoTechnicalResult.createFailedResult(stockCode, stockCode);
        }
    }

    /**
     * 재료 분석 실행 (안전한 래퍼)
     */
    private DinoMaterialResult executeMaterialAnalysis(String stockCode) {
        try {
            log.debug("재료 분석 시작: {}", stockCode);
            DinoMaterialResult result = dinoMaterialService.analyzeMaterialScore(stockCode);
            log.debug("재료 분석 완료: {} - {}점", stockCode, result.totalScore());
            return result;
        } catch (Exception e) {
            log.warn("재료 분석 실패: {} - {}", stockCode, e.getMessage());
            return DinoMaterialResult.createFailedResult(stockCode);
        }
    }

    /**
     * 가격 분석 실행 (안전한 래퍼)
     */
    private DinoPriceResult executePriceAnalysis(String stockCode) {
        try {
            log.debug("가격 분석 시작: {}", stockCode);
            DinoPriceResult result = dinoPriceService.analyzePriceScore(stockCode);
            log.debug("가격 분석 완료: {} - {}점", stockCode, result.totalScore());
            return result;
        } catch (Exception e) {
            log.warn("가격 분석 실패: {} - {}", stockCode, e.getMessage());
            return DinoPriceResult.createFailedResult(stockCode);
        }
    }

    /**
     * 가장 신뢰할 수 있는 회사명 결정
     */
    private String determineCompanyName(String stockCode, DinoFinanceResult finance,
                                      DinoTechnicalResult technical, DinoMaterialResult material, DinoPriceResult price) {

        // 우선순위: 재무 > 기술 > 재료 > 가격
        if (finance != null && finance.isSuccessful() && !finance.companyName().equals(stockCode)) {
            return finance.companyName();
        }
        if (technical != null && technical.isValidScore() && !technical.companyName().equals(stockCode)) {
            return technical.companyName();
        }
        if (material != null && material.isValidScore() && !material.companyName().equals(stockCode)) {
            return material.companyName();
        }
        if (price != null && price.isValidScore() && !price.companyName().equals(stockCode)) {
            return price.companyName();
        }

        // 모든 분석에서 회사명을 찾지 못한 경우 종목코드 사용
        return stockCode;
    }

    /**
     * 상세 분석 결과 로깅
     */
    private void logDetailedResults(DinoIntegratedResult result) {
        log.info("📊 DINO 통합 분석 상세 결과:");
        log.info("   종목: {} ({})", result.companyName(), result.stockCode());
        log.info("   총점: {}/20점 (등급: {})", result.totalScore(), result.overallGrade());
        log.info("   점수 분해: {}", result.getScoreBreakdown());
        log.info("   종합 평가: {}", result.overallSummary());
        log.info("   투자 권고: {}", result.investmentRecommendation());

        // 각 영역별 성공/실패 상태
        log.info("   📈 재무 분석: {} ({}점)",
                getAnalysisStatus(result.financeResult()),
                result.financeResult() != null ? result.financeResult().totalScore() : 0);
        log.info("   📊 기술 분석: {} ({}점)",
                getAnalysisStatus(result.technicalResult()),
                result.technicalResult() != null ? result.technicalResult().totalScore() : 0);
        log.info("   📰 재료 분석: {} ({}점)",
                getAnalysisStatus(result.materialResult()),
                result.materialResult() != null ? result.materialResult().totalScore() : 0);
        log.info("   💰 가격 분석: {} ({}점)",
                getAnalysisStatus(result.priceResult()),
                result.priceResult() != null ? result.priceResult().totalScore() : 0);
    }

    /**
     * 분석 상태 문자열 반환
     */
    private String getAnalysisStatus(Object result) {
        if (result == null) return "❌ 실패";

        if (result instanceof DinoFinanceResult finance) {
            return finance.isSuccessful() ? "✅ 성공" : "❌ 실패";
        }
        if (result instanceof DinoTechnicalResult technical) {
            return technical.isValidScore() ? "✅ 성공" : "❌ 실패";
        }
        if (result instanceof DinoMaterialResult material) {
            return material.isValidScore() ? "✅ 성공" : "❌ 실패";
        }
        if (result instanceof DinoPriceResult price) {
            return price.isValidScore() ? "✅ 성공" : "❌ 실패";
        }

        return "❓ 알 수 없음";
    }

    /**
     * 개별 영역별 분석 실행 (기존 호환성 유지)
     */
    public DinoFinanceResult analyzeFinance(String stockCode) {
        return executeFinanceAnalysis(stockCode);
    }

    public DinoTechnicalResult analyzeTechnical(String stockCode) {
        return executeTechnicalAnalysis(stockCode);
    }

    public DinoMaterialResult analyzeMaterial(String stockCode) {
        return executeMaterialAnalysis(stockCode);
    }

    public DinoPriceResult analyzePrice(String stockCode) {
        return executePriceAnalysis(stockCode);
    }

    /**
     * 애플리케이션 종료 시 스레드 풀 정리
     */
    public void shutdown() {
        if (executorService != null && !executorService.isShutdown()) {
            log.info("DINO 통합 서비스 스레드 풀 종료");
            executorService.shutdown();
        }
    }
}