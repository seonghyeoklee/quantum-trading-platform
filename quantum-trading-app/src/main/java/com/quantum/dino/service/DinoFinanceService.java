package com.quantum.dino.service;

import com.quantum.dino.dto.CalculationStep;
import com.quantum.dino.dto.DinoFinanceResult;
import com.quantum.dino.dto.FastApiFinanceResponse;
import com.quantum.dino.infrastructure.persistence.DinoFinanceResultEntity;
import com.quantum.dino.repository.DinoFinanceResultRepository;
import com.quantum.kis.application.port.in.GetTokenUseCase;
import com.quantum.kis.application.port.out.KisApiPort;
import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.dto.FinancialDataResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestClient;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * DINO 테스트 재무 분석 서비스
 *
 * Python finance_scorer.py 로직을 Java로 번역하여 구현
 * 재무 영역 5개 지표를 평가하여 0~5점 범위에서 점수를 산출
 */
@Service
public class DinoFinanceService {

    private static final Logger log = LoggerFactory.getLogger(DinoFinanceService.class);

    private final GetTokenUseCase getTokenUseCase;
    private final KisApiPort kisApiPort;
    private final RestClient restClient;
    private final DinoFinanceResultRepository repository;

    public DinoFinanceService(GetTokenUseCase getTokenUseCase,
                             KisApiPort kisApiPort,
                             RestClient.Builder restClientBuilder,
                             DinoFinanceResultRepository repository) {
        this.getTokenUseCase = getTokenUseCase;
        this.kisApiPort = kisApiPort;
        this.restClient = restClientBuilder.build();
        this.repository = repository;
    }

    /**
     * 종목의 재무 분석을 실행하여 0~5점 점수를 반환
     * 하루 1회만 분석하며, 기존 결과가 있으면 반환
     */
    @Transactional
    public DinoFinanceResult analyzeFinanceScore(String stockCode) {
        log.info("=== DINO 재무 분석 시작: {} ===", stockCode);

        try {
            // quantum-adapter-kis FastAPI에서 실제 재무 데이터 수집 (캐시 없이 매번 새로 조회)
            log.info("실제 FastAPI 데이터로 재무 분석 실행: {}", stockCode);
            FinanceData financeData = collectFinanceData(stockCode);
            if (financeData == null) {
                log.error("재무 데이터 수집 실패: {}", stockCode);
                return createFailedResult(stockCode);
            }

            // 계산 과정 수집용 리스트
            List<CalculationStep> calculationSteps = new ArrayList<>();

            // 2. 각 지표별 점수 계산 (계산 과정 수집)
            ScoreResult revenueScore = calculateRevenueGrowthScore(financeData, calculationSteps);
            ScoreResult operatingProfitScore = calculateOperatingProfitScore(financeData, calculationSteps);
            ScoreResult operatingMarginScore = calculateOperatingMarginScore(financeData, calculationSteps);
            ScoreResult retentionScore = calculateRetentionRateScore(financeData, calculationSteps);
            ScoreResult debtScore = calculateDebtRatioScore(financeData, calculationSteps);

            // 3. 최종 점수 계산 (엑셀 수식: MAX(0, MIN(5, 2 + SUM(개별점수들))))
            int individualSum = revenueScore.score + operatingProfitScore.score + operatingMarginScore.score
                    + retentionScore.score + debtScore.score;
            int totalScore = Math.max(0, Math.min(5, 2 + individualSum));

            // 최종 계산 공식 생성
            String finalCalculation = String.format("MAX(0, MIN(5, 2 + (%d+%d+%d+%d+%d))) = %d점",
                    revenueScore.score, operatingProfitScore.score, operatingMarginScore.score,
                    retentionScore.score, debtScore.score, totalScore);

            // 총점 계산 단계 추가
            calculationSteps.add(CalculationStep.success(
                    "총점계산",
                    "재무 분석 총점 계산",
                    String.format("기본 2점 + 개별 점수 합계(%d점)", individualSum),
                    totalScore + "점",
                    totalScore,
                    "기본 2점 + 개별 점수 합계, 최대 5점으로 제한",
                    finalCalculation
            ));

            log.info("개별 점수 합계: {}, 최종 점수: {}", individualSum, totalScore);

            // 로깅: 각 계산 단계 출력
            log.info("=== 재무 분석 계산 과정 ===");
            for (CalculationStep step : calculationSteps) {
                log.info(step.getLogDescription());
            }

            // 4. 결과 생성 (계산 과정 포함)
            DinoFinanceResult result = new DinoFinanceResult(
                    stockCode,
                    financeData.companyName != null ? financeData.companyName : stockCode,
                    revenueScore.score,
                    operatingProfitScore.score,
                    operatingMarginScore.score,
                    retentionScore.score,
                    debtScore.score,
                    totalScore,
                    revenueScore.rate,
                    operatingProfitScore.description,
                    operatingMarginScore.rate,
                    retentionScore.rate,
                    debtScore.rate,
                    financeData.currentRevenue,
                    financeData.previousRevenue,
                    financeData.currentOperatingProfit,
                    financeData.previousOperatingProfit,
                    financeData.totalDebt,
                    financeData.totalEquity,
                    financeData.retainedEarnings,
                    financeData.capitalStock,
                    financeData.currentPeriod,
                    financeData.previousPeriod,
                    LocalDateTime.now(),
                    calculationSteps, // 계산 과정 포함
                    finalCalculation // 최종 계산 공식
            );

            // 5. 데이터베이스에 저장
            DinoFinanceResultEntity savedEntity = repository.save(DinoFinanceResultEntity.from(result));
            log.info("데이터베이스 저장 완료: ID {}", savedEntity.getId());

            log.info("=== DINO 재무 분석 완료: {} - 총점: {}점 ===", stockCode, totalScore);
            return result;

        } catch (Exception e) {
            log.error("DINO 재무 분석 실패: {} - {}", stockCode, e.getMessage(), e);
            return createFailedResult(stockCode);
        }
    }

    /**
     * 매출액 증감 점수 계산 (±1점)
     * - 전년 대비 매출 증가 10% 이상: +1점
     * - 전년 대비 매출 감소: -1점
     * - 나머지: 0점
     */
    private ScoreResult calculateRevenueGrowthScore(FinanceData data, List<CalculationStep> calculationSteps) {
        if (data.currentRevenue == null || data.previousRevenue == null
                || data.previousRevenue.compareTo(BigDecimal.ZERO) == 0) {
            log.warn("매출액 데이터 부족 - 점수 0점 처리");
            calculationSteps.add(CalculationStep.failure("매출증감분석", "매출액 증감 분석", "매출액 데이터 부족"));
            return new ScoreResult(0, null, "데이터 부족");
        }

        BigDecimal growthRate = data.currentRevenue.subtract(data.previousRevenue)
                .divide(data.previousRevenue, 4, RoundingMode.HALF_UP)
                .multiply(BigDecimal.valueOf(100));

        double rate = growthRate.doubleValue();
        int score;
        String reasoning;

        if (rate >= 10.0) {
            score = 1;
            reasoning = "매출액 10% 이상 성장으로 +1점";
        } else if (rate < 0) {
            score = -1;
            reasoning = "매출액 감소로 -1점";
        } else {
            score = 0;
            reasoning = "매출액 증가율 10% 미만으로 0점";
        }

        // 계산 과정 기록
        calculationSteps.add(CalculationStep.success(
                "매출증감분석",
                "매출액 증감률 분석",
                String.format("당년: %s억원, 전년: %s억원",
                    formatNumber(data.currentRevenue), formatNumber(data.previousRevenue)),
                String.format("%.2f%%", rate),
                score,
                reasoning,
                String.format("(%.2f - %.2f) / %.2f * 100 = %.2f%%",
                    data.currentRevenue.doubleValue() / 100000000,
                    data.previousRevenue.doubleValue() / 100000000,
                    data.previousRevenue.doubleValue() / 100000000,
                    rate)
        ));

        log.info("매출액 증가율: {}%, 점수: {}", String.format("%.2f", rate), score);
        return new ScoreResult(score, rate, null);
    }

    /**
     * 영업이익 상태 점수 계산 (±2점)
     * - 영업이익 흑자 전환: +1점
     * - 영업이익 적자 전환: -1점
     * - 영업이익 적자 지속: -2점
     * - 영업이익 흑자 지속: 0점
     */
    private ScoreResult calculateOperatingProfitScore(FinanceData data, List<CalculationStep> calculationSteps) {
        if (data.currentOperatingProfit == null || data.previousOperatingProfit == null) {
            log.warn("영업이익 데이터 부족 - 점수 0점 처리");
            calculationSteps.add(CalculationStep.failure("영업이익분석", "영업이익 상태 분석", "영업이익 데이터 부족"));
            return new ScoreResult(0, null, "데이터 부족");
        }

        boolean currentProfitable = data.currentOperatingProfit.compareTo(BigDecimal.ZERO) > 0;
        boolean previousProfitable = data.previousOperatingProfit.compareTo(BigDecimal.ZERO) > 0;

        int score;
        String transition;
        String reasoning;

        if (!previousProfitable && currentProfitable) {
            score = 1;
            transition = "적자→흑자 전환";
            reasoning = "적자에서 흑자로 전환하여 +1점";
        } else if (previousProfitable && !currentProfitable) {
            score = -1;
            transition = "흑자→적자 전환";
            reasoning = "흑자에서 적자로 전환하여 -1점";
        } else if (!previousProfitable && !currentProfitable) {
            score = -2;
            transition = "적자 지속";
            reasoning = "적자가 지속되어 -2점";
        } else {
            score = 0;
            transition = "흑자 지속";
            reasoning = "흑자가 지속되어 0점";
        }

        // 계산 과정 기록
        calculationSteps.add(CalculationStep.success(
                "영업이익분석",
                "영업이익 상태 분석",
                String.format("당년: %s억원, 전년: %s억원",
                    formatNumber(data.currentOperatingProfit), formatNumber(data.previousOperatingProfit)),
                transition,
                score,
                reasoning
        ));

        log.info("영업이익 상태: {}, 점수: {}", transition, score);
        return new ScoreResult(score, null, transition);
    }

    /**
     * 영업이익률 점수 계산 (+1점)
     * - 영업이익률 10% 이상: +1점
     * - 나머지: 0점
     */
    private ScoreResult calculateOperatingMarginScore(FinanceData data, List<CalculationStep> calculationSteps) {
        if (data.currentOperatingProfit == null || data.currentRevenue == null
                || data.currentRevenue.compareTo(BigDecimal.ZERO) == 0) {
            log.warn("영업이익률 계산 데이터 부족 - 점수 0점 처리");
            calculationSteps.add(CalculationStep.failure("영업이익률분석", "영업이익률 분석", "영업이익률 계산 데이터 부족"));
            return new ScoreResult(0, null, "데이터 부족");
        }

        BigDecimal marginRate = data.currentOperatingProfit
                .divide(data.currentRevenue, 4, RoundingMode.HALF_UP)
                .multiply(BigDecimal.valueOf(100));

        double rate = marginRate.doubleValue();
        int score = rate >= 10.0 ? 1 : 0;
        String reasoning = rate >= 10.0 ? "영업이익률 10% 이상으로 +1점" : "영업이익률 10% 미만으로 0점";

        // 계산 과정 기록
        calculationSteps.add(CalculationStep.success(
                "영업이익률분석",
                "영업이익률 분석",
                String.format("영업이익: %s억원, 매출액: %s억원",
                    formatNumber(data.currentOperatingProfit), formatNumber(data.currentRevenue)),
                String.format("%.2f%%", rate),
                score,
                reasoning,
                String.format("%.2f / %.2f * 100 = %.2f%%",
                    data.currentOperatingProfit.doubleValue() / 100000000,
                    data.currentRevenue.doubleValue() / 100000000,
                    rate)
        ));

        log.info("영업이익률: {}%, 점수: {}", String.format("%.2f", rate), score);
        return new ScoreResult(score, rate, null);
    }

    /**
     * 유보율 점수 계산 (±1점)
     * - 유보율 1,000% 이상: +1점
     * - 유보율 300% 이하: -1점
     * - 나머지: 0점
     */
    private ScoreResult calculateRetentionRateScore(FinanceData data, List<CalculationStep> calculationSteps) {
        if (data.retainedEarnings == null || data.capitalStock == null
                || data.capitalStock.compareTo(BigDecimal.ZERO) == 0) {
            log.warn("유보율 계산 데이터 부족 - 점수 0점 처리");
            calculationSteps.add(CalculationStep.failure("유보율분석", "유보율 분석", "유보율 계산 데이터 부족"));
            return new ScoreResult(0, null, "데이터 부족");
        }

        BigDecimal retentionRatio = data.retainedEarnings
                .divide(data.capitalStock, 4, RoundingMode.HALF_UP)
                .multiply(BigDecimal.valueOf(100));

        double ratio = retentionRatio.doubleValue();
        int score;
        String reasoning;

        if (ratio >= 1000.0) {
            score = 1;
            reasoning = "유보율 1,000% 이상으로 +1점";
        } else if (ratio <= 300.0) {
            score = -1;
            reasoning = "유보율 300% 이하로 -1점";
        } else {
            score = 0;
            reasoning = "유보율 300%~1,000% 사이로 0점";
        }

        // 계산 과정 기록
        calculationSteps.add(CalculationStep.success(
                "유보율분석",
                "유보율 분석",
                String.format("이익잉여금: %s억원, 자본금: %s억원",
                    formatNumber(data.retainedEarnings), formatNumber(data.capitalStock)),
                String.format("%.2f%%", ratio),
                score,
                reasoning,
                String.format("%.2f / %.2f * 100 = %.2f%%",
                    data.retainedEarnings.doubleValue() / 100000000,
                    data.capitalStock.doubleValue() / 100000000,
                    ratio)
        ));

        log.info("유보율: {}%, 점수: {}", String.format("%.2f", ratio), score);
        return new ScoreResult(score, ratio, null);
    }

    /**
     * 부채비율 점수 계산 (±1점)
     * - 부채비율 50% 이하: +1점
     * - 부채비율 200% 이상: -1점
     * - 나머지: 0점
     */
    private ScoreResult calculateDebtRatioScore(FinanceData data, List<CalculationStep> calculationSteps) {
        if (data.totalDebt == null || data.totalEquity == null
                || data.totalEquity.compareTo(BigDecimal.ZERO) == 0) {
            log.warn("부채비율 계산 데이터 부족 - 점수 0점 처리");
            calculationSteps.add(CalculationStep.failure("부채비율분석", "부채비율 분석", "부채비율 계산 데이터 부족"));
            return new ScoreResult(0, null, "데이터 부족");
        }

        BigDecimal debtRatio = data.totalDebt
                .divide(data.totalEquity, 4, RoundingMode.HALF_UP)
                .multiply(BigDecimal.valueOf(100));

        double ratio = debtRatio.doubleValue();
        int score;
        String reasoning;

        if (ratio <= 50.0) {
            score = 1;
            reasoning = "부채비율 50% 이하로 +1점";
        } else if (ratio >= 200.0) {
            score = -1;
            reasoning = "부채비율 200% 이상으로 -1점";
        } else {
            score = 0;
            reasoning = "부채비율 50%~200% 사이로 0점";
        }

        // 계산 과정 기록
        calculationSteps.add(CalculationStep.success(
                "부채비율분석",
                "부채비율 분석",
                String.format("총부채: %s억원, 자기자본: %s억원",
                    formatNumber(data.totalDebt), formatNumber(data.totalEquity)),
                String.format("%.2f%%", ratio),
                score,
                reasoning,
                String.format("%.2f / %.2f * 100 = %.2f%%",
                    data.totalDebt.doubleValue() / 100000000,
                    data.totalEquity.doubleValue() / 100000000,
                    ratio)
        ));

        log.info("부채비율: {}%, 점수: {}", String.format("%.2f", ratio), score);
        return new ScoreResult(score, ratio, null);
    }

    /**
     * quantum-adapter-kis FastAPI에서 재무 데이터 수집
     * 실제 FastAPI를 호출하여 재무 정보를 조회
     */
    private FinanceData collectFinanceData(String stockCode) {
        log.info("quantum-adapter-kis FastAPI에서 재무 데이터 수집 중: {}", stockCode);

        try {
            // FastAPI 엔드포인트 호출
            String fastApiUrl = "http://localhost:8000/dino-test/finance/" + stockCode;
            log.info("FastAPI 호출: {}", fastApiUrl);

            FastApiFinanceResponse response = restClient.get()
                    .uri(fastApiUrl)
                    .retrieve()
                    .body(FastApiFinanceResponse.class);

            if (response == null) {
                log.error("FastAPI 응답이 null: {}", stockCode);
                throw new RuntimeException("FastAPI에서 재무 데이터를 가져올 수 없습니다: " + stockCode);
            }

            log.info("FastAPI 응답 수신 - 종목: {}, 총점: {}", response.stockCode(), response.totalScore());

            var rawData = response.rawData();
            if (rawData == null || !rawData.hasValidFinancialData()) {
                log.error("유효하지 않은 재무 데이터: {}", stockCode);
                throw new RuntimeException("FastAPI에서 유효하지 않은 재무 데이터를 반환했습니다: " + stockCode);
            }

            // FastAPI 응답을 FinanceData로 변환
            return new FinanceData(
                    response.stockName(),
                    rawData.getCurrentRevenueBigDecimal(),
                    rawData.getPreviousRevenueBigDecimal(),
                    rawData.getCurrentOperatingProfitBigDecimal(),
                    rawData.getPreviousOperatingProfitBigDecimal(),
                    rawData.getTotalDebtBigDecimal(),
                    rawData.getTotalEquityBigDecimal(),
                    rawData.getRetainedEarningsBigDecimal(),
                    rawData.getCapitalStockBigDecimal(),
                    rawData.basePeriod(), // 현재 기준기간
                    "전년" // 이전 기간 (FastAPI에서는 명시적으로 제공하지 않음)
            );

        } catch (Exception e) {
            log.error("FastAPI 재무 데이터 조회 실패: {} - {}", stockCode, e.getMessage());
            throw new RuntimeException("FastAPI 재무 데이터 조회 실패: " + stockCode + " - " + e.getMessage(), e);
        }
    }


    /**
     * 분석 실패 시 기본 결과 생성
     */
    private DinoFinanceResult createFailedResult(String stockCode) {
        return DinoFinanceResult.createFailedResult(stockCode);
    }

    /**
     * 숫자 포맷팅 헬퍼 메서드 (억원 단위)
     */
    private String formatNumber(BigDecimal number) {
        if (number == null) {
            return "0";
        }
        double value = number.doubleValue() / 100000000; // 억원 단위로 변환
        if (value >= 1000) {
            return String.format("%.1f조", value / 10000);
        } else {
            return String.format("%.1f", value);
        }
    }

    /**
     * JPA 엔티티를 DTO로 변환
     */
    private DinoFinanceResult convertToDto(DinoFinanceResultEntity entity) {
        // JPA 엔티티에서는 계산 과정이 저장되지 않으므로 빈 리스트와 기본 메시지를 사용
        List<CalculationStep> emptySteps = List.of();
        String basicCalculation = String.format("저장된 재무 분석 결과 (총점: %d점)", entity.getTotalScore());

        return new DinoFinanceResult(
                entity.getStockCode(),
                entity.getCompanyName(),
                entity.getRevenueGrowthScore(),
                entity.getOperatingProfitScore(),
                entity.getOperatingMarginScore(),
                entity.getRetentionRateScore(),
                entity.getDebtRatioScore(),
                entity.getTotalScore(),
                entity.getRevenueGrowthRate(),
                entity.getOperatingProfitTransition(),
                entity.getOperatingMarginRate(),
                entity.getRetentionRate(),
                entity.getDebtRatio(),
                entity.getCurrentRevenue(),
                entity.getPreviousRevenue(),
                entity.getCurrentOperatingProfit(),
                entity.getPreviousOperatingProfit(),
                entity.getTotalDebt(),
                entity.getTotalEquity(),
                entity.getRetainedEarnings(),
                entity.getCapitalStock(),
                entity.getCurrentPeriod(),
                entity.getPreviousPeriod(),
                entity.getAnalysisDate(),
                emptySteps, // 저장된 결과에는 계산 과정이 없음
                basicCalculation // 기본 계산 설명
        );
    }

    /**
     * 종목의 최근 분석 히스토리 조회
     */
    public List<DinoFinanceResult> getAnalysisHistory(String stockCode) {
        return repository.findByStockCodeOrderByAnalysisDateDesc(stockCode)
                .stream()
                .map(this::convertToDto)
                .toList();
    }

    /**
     * 오늘 분석된 모든 종목 조회
     */
    public List<DinoFinanceResult> getTodayAnalysis() {
        return repository.findByAnalysisDateOrderByTotalScoreDesc(LocalDate.now())
                .stream()
                .map(this::convertToDto)
                .toList();
    }

    /**
     * 재무 데이터 구조
     */
    private static class FinanceData {
        final String companyName;
        final BigDecimal currentRevenue;
        final BigDecimal previousRevenue;
        final BigDecimal currentOperatingProfit;
        final BigDecimal previousOperatingProfit;
        final BigDecimal totalDebt;
        final BigDecimal totalEquity;
        final BigDecimal retainedEarnings;
        final BigDecimal capitalStock;
        final String currentPeriod;
        final String previousPeriod;

        FinanceData(String companyName, BigDecimal currentRevenue, BigDecimal previousRevenue,
                   BigDecimal currentOperatingProfit, BigDecimal previousOperatingProfit,
                   BigDecimal totalDebt, BigDecimal totalEquity, BigDecimal retainedEarnings,
                   BigDecimal capitalStock, String currentPeriod, String previousPeriod) {
            this.companyName = companyName;
            this.currentRevenue = currentRevenue;
            this.previousRevenue = previousRevenue;
            this.currentOperatingProfit = currentOperatingProfit;
            this.previousOperatingProfit = previousOperatingProfit;
            this.totalDebt = totalDebt;
            this.totalEquity = totalEquity;
            this.retainedEarnings = retainedEarnings;
            this.capitalStock = capitalStock;
            this.currentPeriod = currentPeriod;
            this.previousPeriod = previousPeriod;
        }
    }

    /**
     * 점수 계산 결과 구조
     */
    private static class ScoreResult {
        final int score;
        final Double rate;
        final String description;

        ScoreResult(int score, Double rate, String description) {
            this.score = score;
            this.rate = rate;
            this.description = description;
        }
    }
}