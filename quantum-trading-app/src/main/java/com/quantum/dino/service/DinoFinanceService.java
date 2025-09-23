package com.quantum.dino.service;

import com.quantum.dino.dto.DinoFinanceResult;
import com.quantum.dino.domain.DinoFinanceResultEntity;
import com.quantum.dino.repository.DinoFinanceResultRepository;
import com.quantum.kis.service.KisTokenService;
import com.quantum.kis.domain.KisEnvironment;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestClient;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
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

    private final KisTokenService kisTokenService;
    private final RestClient restClient;
    private final DinoFinanceResultRepository repository;

    public DinoFinanceService(KisTokenService kisTokenService,
                             RestClient.Builder restClientBuilder,
                             DinoFinanceResultRepository repository) {
        this.kisTokenService = kisTokenService;
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
            // 1. 당일 분석 결과가 이미 있는지 확인
            LocalDate today = LocalDate.now();
            Optional<DinoFinanceResultEntity> existingResult =
                repository.findByStockCodeAndAnalysisDate(stockCode, today);

            if (existingResult.isPresent()) {
                log.info("당일 분석 결과가 이미 존재: {}", stockCode);
                return convertToDto(existingResult.get());
            }

            // 2. KIS API에서 재무 데이터 수집
            FinanceData financeData = collectFinanceData(stockCode);
            if (financeData == null) {
                log.error("재무 데이터 수집 실패: {}", stockCode);
                return createFailedResult(stockCode);
            }

            // 2. 각 지표별 점수 계산
            ScoreResult revenueScore = calculateRevenueGrowthScore(financeData);
            ScoreResult operatingProfitScore = calculateOperatingProfitScore(financeData);
            ScoreResult operatingMarginScore = calculateOperatingMarginScore(financeData);
            ScoreResult retentionScore = calculateRetentionRateScore(financeData);
            ScoreResult debtScore = calculateDebtRatioScore(financeData);

            // 3. 최종 점수 계산 (엑셀 수식: MAX(0, MIN(5, 2 + SUM(개별점수들))))
            int individualSum = revenueScore.score + operatingProfitScore.score + operatingMarginScore.score
                    + retentionScore.score + debtScore.score;
            int totalScore = Math.max(0, Math.min(5, 2 + individualSum));

            log.info("개별 점수 합계: {}, 최종 점수: {}", individualSum, totalScore);

            // 4. 결과 생성
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
                    LocalDateTime.now()
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
    private ScoreResult calculateRevenueGrowthScore(FinanceData data) {
        if (data.currentRevenue == null || data.previousRevenue == null
                || data.previousRevenue.compareTo(BigDecimal.ZERO) == 0) {
            log.warn("매출액 데이터 부족 - 점수 0점 처리");
            return new ScoreResult(0, null, "데이터 부족");
        }

        BigDecimal growthRate = data.currentRevenue.subtract(data.previousRevenue)
                .divide(data.previousRevenue, 4, RoundingMode.HALF_UP)
                .multiply(BigDecimal.valueOf(100));

        double rate = growthRate.doubleValue();
        int score;

        if (rate >= 10.0) {
            score = 1;
        } else if (rate < 0) {
            score = -1;
        } else {
            score = 0;
        }

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
    private ScoreResult calculateOperatingProfitScore(FinanceData data) {
        if (data.currentOperatingProfit == null || data.previousOperatingProfit == null) {
            log.warn("영업이익 데이터 부족 - 점수 0점 처리");
            return new ScoreResult(0, null, "데이터 부족");
        }

        boolean currentProfitable = data.currentOperatingProfit.compareTo(BigDecimal.ZERO) > 0;
        boolean previousProfitable = data.previousOperatingProfit.compareTo(BigDecimal.ZERO) > 0;

        int score;
        String transition;

        if (!previousProfitable && currentProfitable) {
            score = 1;
            transition = "적자→흑자 전환";
        } else if (previousProfitable && !currentProfitable) {
            score = -1;
            transition = "흑자→적자 전환";
        } else if (!previousProfitable && !currentProfitable) {
            score = -2;
            transition = "적자 지속";
        } else {
            score = 0;
            transition = "흑자 지속";
        }

        log.info("영업이익 상태: {}, 점수: {}", transition, score);
        return new ScoreResult(score, null, transition);
    }

    /**
     * 영업이익률 점수 계산 (+1점)
     * - 영업이익률 10% 이상: +1점
     * - 나머지: 0점
     */
    private ScoreResult calculateOperatingMarginScore(FinanceData data) {
        if (data.currentOperatingProfit == null || data.currentRevenue == null
                || data.currentRevenue.compareTo(BigDecimal.ZERO) == 0) {
            log.warn("영업이익률 계산 데이터 부족 - 점수 0점 처리");
            return new ScoreResult(0, null, "데이터 부족");
        }

        BigDecimal marginRate = data.currentOperatingProfit
                .divide(data.currentRevenue, 4, RoundingMode.HALF_UP)
                .multiply(BigDecimal.valueOf(100));

        double rate = marginRate.doubleValue();
        int score = rate >= 10.0 ? 1 : 0;

        log.info("영업이익률: {}%, 점수: {}", String.format("%.2f", rate), score);
        return new ScoreResult(score, rate, null);
    }

    /**
     * 유보율 점수 계산 (±1점)
     * - 유보율 1,000% 이상: +1점
     * - 유보율 300% 이하: -1점
     * - 나머지: 0점
     */
    private ScoreResult calculateRetentionRateScore(FinanceData data) {
        if (data.retainedEarnings == null || data.capitalStock == null
                || data.capitalStock.compareTo(BigDecimal.ZERO) == 0) {
            log.warn("유보율 계산 데이터 부족 - 점수 0점 처리");
            return new ScoreResult(0, null, "데이터 부족");
        }

        BigDecimal retentionRatio = data.retainedEarnings
                .divide(data.capitalStock, 4, RoundingMode.HALF_UP)
                .multiply(BigDecimal.valueOf(100));

        double ratio = retentionRatio.doubleValue();
        int score;

        if (ratio >= 1000.0) {
            score = 1;
        } else if (ratio <= 300.0) {
            score = -1;
        } else {
            score = 0;
        }

        log.info("유보율: {}%, 점수: {}", String.format("%.2f", ratio), score);
        return new ScoreResult(score, ratio, null);
    }

    /**
     * 부채비율 점수 계산 (±1점)
     * - 부채비율 50% 이하: +1점
     * - 부채비율 200% 이상: -1점
     * - 나머지: 0점
     */
    private ScoreResult calculateDebtRatioScore(FinanceData data) {
        if (data.totalDebt == null || data.totalEquity == null
                || data.totalEquity.compareTo(BigDecimal.ZERO) == 0) {
            log.warn("부채비율 계산 데이터 부족 - 점수 0점 처리");
            return new ScoreResult(0, null, "데이터 부족");
        }

        BigDecimal debtRatio = data.totalDebt
                .divide(data.totalEquity, 4, RoundingMode.HALF_UP)
                .multiply(BigDecimal.valueOf(100));

        double ratio = debtRatio.doubleValue();
        int score;

        if (ratio <= 50.0) {
            score = 1;
        } else if (ratio >= 200.0) {
            score = -1;
        } else {
            score = 0;
        }

        log.info("부채비율: {}%, 점수: {}", String.format("%.2f", ratio), score);
        return new ScoreResult(score, ratio, null);
    }

    /**
     * KIS API에서 재무 데이터 수집 (실제 구현 시 KIS API 호출)
     * TODO: 실제 KIS API 호출로 교체 필요
     */
    private FinanceData collectFinanceData(String stockCode) {
        // TODO: 실제 KIS API 호출 구현
        log.info("KIS API에서 재무 데이터 수집 중: {}", stockCode);

        // 현재는 샘플 데이터로 테스트 (삼성전자 예시)
        if ("005930".equals(stockCode)) {
            return new FinanceData(
                    "삼성전자",
                    new BigDecimal("302231000000000"), // 당년 매출액 (302조)
                    new BigDecimal("279621000000000"), // 전년 매출액 (279조)
                    new BigDecimal("54336000000000"),  // 당년 영업이익 (54조)
                    new BigDecimal("42186000000000"),  // 전년 영업이익 (42조)
                    new BigDecimal("90896000000000"),  // 총부채 (90조)
                    new BigDecimal("368014000000000"), // 자기자본 (368조)
                    new BigDecimal("272101000000000"), // 이익잉여금 (272조)
                    new BigDecimal("11775000000000"),  // 자본금 (11조)
                    "202312",
                    "202212"
            );
        }

        return null; // 데이터 없음
    }

    /**
     * 분석 실패 시 기본 결과 생성
     */
    private DinoFinanceResult createFailedResult(String stockCode) {
        return new DinoFinanceResult(
                stockCode, stockCode, 0, 0, 0, 0, 0, 0,
                null, "분석 실패", null, null, null,
                null, null, null, null, null, null, null, null,
                null, null, LocalDateTime.now()
        );
    }

    /**
     * JPA 엔티티를 DTO로 변환
     */
    private DinoFinanceResult convertToDto(DinoFinanceResultEntity entity) {
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
                entity.getAnalysisDate()
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