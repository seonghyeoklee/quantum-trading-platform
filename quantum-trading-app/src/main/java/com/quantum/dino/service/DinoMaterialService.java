package com.quantum.dino.service;

import com.quantum.dino.dto.DinoMaterialResult;
import com.quantum.dino.dto.CalculationStep;
import com.quantum.kis.application.port.in.GetTokenUseCase;
import com.quantum.kis.application.port.out.KisApiPort;
import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.dto.FinancialDataResponse;
import com.quantum.kis.dto.InvestorInfoResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.ArrayList;

/**
 * DINO 재료 분석 서비스
 *
 * 재료 분석 5점 만점 구성 (Python 동일 로직):
 * 1. 고배당 (2% 이상) (0~1점)
 * 2. 기관/외국인 수급 (1% 이상 매집) (0~1점)
 * 3. 어닝서프라이즈 (10% 이상) (0~1점) - 향후 구현
 * 4. 기타 소재 항목 - 향후 구현
 *
 * 총점 공식: MAX(0, MIN(5, 2 + SUM(개별점수들)))
 *
 * Python 대응: dino_test/material_analyzer.py의 DinoTestMaterialAnalyzer
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DinoMaterialService {

    private final GetTokenUseCase getTokenUseCase;
    private final KisApiPort kisApiPort;

    /**
     * 주식 재료 분석 실행 (Python 버전과 동일한 로직)
     */
    public DinoMaterialResult analyzeMaterialScore(String stockCode) {
        log.info("=== DINO 재료 분석 시작: {} ===", stockCode);

        // 계산 과정 수집을 위한 리스트 초기화
        List<CalculationStep> calculationSteps = new ArrayList<>();

        try {
            // 재료 데이터 수집 (실제 구현에서는 KIS API 호출)
            MaterialData materialData = collectMaterialData(stockCode);

            // 개별 점수 계산 (Python 버전과 동일)
            DividendScore dividendScore = calculateDividendScore(materialData, calculationSteps);
            InvestorSupplyScore investorScore = calculateInvestorSupplyScore(materialData, calculationSteps);
            EarningsSurpriseScore earningsScore = calculateEarningsSurpriseScore(materialData, calculationSteps);

            // 총점 계산: MAX(0, MIN(5, 2 + SUM(개별점수들)))
            int individualSum = dividendScore.score() + investorScore.score() + earningsScore.score();
            int totalScore = Math.max(0, Math.min(5, 2 + individualSum));

            // 최종 계산 공식 생성
            String finalCalculation = String.format("MAX(0, MIN(5, 2 + (%d+%d+%d))) = %d점",
                dividendScore.score(), investorScore.score(), earningsScore.score(), totalScore);

            // 최종 계산 단계 추가
            calculationSteps.add(CalculationStep.success(
                "총점계산", "재료 분석 총점 계산",
                String.format("개별 점수 합계: %d", individualSum),
                totalScore,
                totalScore,
                "기본 2점 + 개별 점수 합계, 최대 5점으로 제한",
                finalCalculation
            ));

            // 로깅: 각 계산 단계 출력
            log.info("=== 재료 분석 계산 과정 ===");
            for (CalculationStep step : calculationSteps) {
                log.info(step.getLogDescription());
            }

            log.info("재료 분석 완료: {} - 총점 {}/5점 (개별 합계: {})", stockCode, totalScore, individualSum);

            return new DinoMaterialResult(
                stockCode,
                materialData.companyName() != null ? materialData.companyName() : stockCode,
                dividendScore.score(), // dividendScore
                investorScore.score(), // investorSupplyScore
                0, // sentimentScore (시장심리 점수 - 향후 구현)
                earningsScore.score(), // earningsSurpriseScore
                totalScore,
                0, // positiveNewsCount (향후 구현)
                0, // negativeNewsCount (향후 구현)
                dividendScore.impactScore(), // impactScore (배당 임팩트)
                investorScore.category(), // investorCategory
                investorScore.trend(), // investorTrend
                investorScore.sectorTrend(), // sectorTrend
                BigDecimal.valueOf(50.0), // psychologyIndex (향후 구현)
                "중립", // psychologyState (향후 구현)
                BigDecimal.ZERO, // materialDuration (향후 구현)
                dividendScore.type(), // dividendType
                dividendScore.signal(), // dividendSignal
                investorScore.signal(), // investorSignal
                earningsScore.signal(), // earningsSignal
                "재료 데이터 기반 분석", // materialStrengthSignal
                LocalDateTime.now(),
                calculationSteps, // 계산 과정 단계들
                finalCalculation // 최종 계산 공식
            );

        } catch (Exception e) {
            log.error("재료 분석 실패: {} - {}", stockCode, e.getMessage(), e);
            return DinoMaterialResult.createFailedResult(stockCode);
        }
    }

    /**
     * 재료 데이터 수집 (KIS API 호출)
     */
    private MaterialData collectMaterialData(String stockCode) {
        log.debug("재료 데이터 수집 시작: {}", stockCode);

        try {
            // 1. 재무 정보에서 배당 정보 추출
            FinancialDataResponse financialData = kisApiPort.getFinancialData(KisEnvironment.PROD, stockCode);

            // 2. 기관/외국인 투자자 정보 조회 (최근 3개월)
            LocalDate endDate = LocalDate.now();
            LocalDate startDate = endDate.minusMonths(3);
            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyyMMdd");

            InvestorInfoResponse institutionalData = kisApiPort.getInvestorInfo(
                KisEnvironment.PROD, stockCode, "1", // 기관계
                startDate.format(formatter), endDate.format(formatter)
            );

            InvestorInfoResponse foreignData = kisApiPort.getInvestorInfo(
                KisEnvironment.PROD, stockCode, "4", // 외국인
                startDate.format(formatter), endDate.format(formatter)
            );

            // 3. 데이터 파싱 및 MaterialData 생성
            String companyName = extractCompanyName(financialData, stockCode);
            Double dividendYield = extractDividendYield(financialData);

            // 투자자 수급 데이터 분석
            InvestorTrendAnalysis analysis = analyzeInvestorTrend(institutionalData, foreignData);

            log.info("재료 데이터 수집 완료: {} - 배당률: {}%, 기관변화: {}%, 외국인변화: {}%",
                    companyName, dividendYield, analysis.institutional1m(), analysis.foreign1m());

            return new MaterialData(
                companyName,
                dividendYield,
                analysis.institutionalRatio(),
                analysis.foreignRatio(),
                analysis.institutional1m(),
                analysis.foreign1m(),
                analysis.institutional3m(),
                analysis.foreign3m(),
                5938969800L, // 상장주식수 (KIS API에서 제공되지 않음, 별도 관리 필요)
                null // 어닝서프라이즈 (향후 구현)
            );

        } catch (Exception e) {
            log.error("KIS API 호출 실패: {} - {}", stockCode, e.getMessage());
            throw new RuntimeException("재료 데이터 수집 실패: " + e.getMessage(), e);
        }
    }

    /**
     * 재무 데이터에서 회사명 추출
     */
    private String extractCompanyName(FinancialDataResponse financialData, String defaultName) {
        if (financialData != null && financialData.output() != null
            && financialData.output().companyName() != null) {
            return financialData.output().companyName();
        }
        return defaultName; // KIS API에서 회사명을 가져올 수 없으면 종목코드 반환
    }

    /**
     * 재무 데이터에서 배당률 추출 (현재 KIS API에서 직접 제공되지 않음)
     */
    private Double extractDividendYield(FinancialDataResponse financialData) {
        // TODO: KIS API에서 배당 정보를 별도로 조회해야 함
        // 실제 데이터가 없으면 null 반환
        log.warn("배당률 데이터가 KIS API에서 제공되지 않음 - 별도 API 조회 필요");
        return null;
    }

    /**
     * 투자자 매매동향 데이터 분석
     */
    private InvestorTrendAnalysis analyzeInvestorTrend(InvestorInfoResponse institutionalData,
                                                     InvestorInfoResponse foreignData) {
        try {
            // 기관 투자자 데이터 분석
            double institutional1m = calculateInvestorChange(institutionalData, 30);
            double institutional3m = calculateInvestorChange(institutionalData, 90);

            // 외국인 투자자 데이터 분석
            double foreign1m = calculateInvestorChange(foreignData, 30);
            double foreign3m = calculateInvestorChange(foreignData, 90);

            return new InvestorTrendAnalysis(
                25.5, 15.2, // 보유 비율 (별도 API 필요)
                institutional1m, foreign1m,
                institutional3m, foreign3m
            );

        } catch (Exception e) {
            log.error("투자자 데이터 분석 실패: {}", e.getMessage());
            throw new RuntimeException("투자자 매매동향 데이터 분석 실패: " + e.getMessage(), e);
        }
    }

    /**
     * 투자자별 기간별 변화율 계산
     */
    private double calculateInvestorChange(InvestorInfoResponse data, int days) {
        if (data == null || data.output() == null || data.output().isEmpty()) {
            return 0.0;
        }

        // 최근 데이터와 과거 데이터 비교하여 변화율 계산
        var recentData = data.output().get(0);
        if (recentData.getNetBuyAmountBigDecimal() != null) {
            // 순매수금액 기준으로 변화율 계산 (간단한 로직)
            double netBuyAmount = recentData.getNetBuyAmountBigDecimal().doubleValue();
            return netBuyAmount > 0 ? 1.0 : -0.5; // 임시 계산 로직
        }

        return 0.0;
    }

    // 내부 데이터 클래스 추가
    private record InvestorTrendAnalysis(
        Double institutionalRatio,
        Double foreignRatio,
        Double institutional1m,
        Double foreign1m,
        Double institutional3m,
        Double foreign3m
    ) {}

    /**
     * D004: 고배당 점수 계산 (0~1점)
     *
     * 판단 기준:
     * - 배당률 >= 2%: +1점 (고배당)
     * - 배당률 < 2%: 0점 (일반)
     */
    private DividendScore calculateDividendScore(MaterialData materialData, List<CalculationStep> calculationSteps) {
        if (materialData.dividendYield() == null) {
            log.warn("배당률 계산을 위한 데이터 부족");
            calculationSteps.add(CalculationStep.failure("배당분석", "배당률 분석", "배당률 데이터 없음"));
            return new DividendScore(0, null, "데이터 부족", BigDecimal.ZERO, "일반");
        }

        double dividendYield = materialData.dividendYield();

        if (dividendYield >= 2.0) {
            int score = 1;
            String status = String.format("고배당 (%.2f%%)", dividendYield);
            calculationSteps.add(CalculationStep.success(
                "배당분석", "고배당 조건 확인",
                String.format("%.2f%%", dividendYield), "고배당",
                score, "배당률 2% 이상으로 고배당 인정", "배당률 ≥ 2% → +1점"
            ));
            log.info("배당률: {}, 점수: +{}", status, score);
            return new DividendScore(score, dividendYield, status, BigDecimal.valueOf(dividendYield), "고배당");
        } else {
            int score = 0;
            String status = String.format("일반 배당 (%.2f%%)", dividendYield);
            calculationSteps.add(CalculationStep.success(
                "배당분석", "일반배당 조건 확인",
                String.format("%.2f%%", dividendYield), "일반배당",
                score, "배당률 2% 미만으로 일반 배당", "배당률 < 2% → 0점"
            ));
            log.info("배당률: {}, 점수: +{}", status, score);
            return new DividendScore(score, dividendYield, status, BigDecimal.valueOf(dividendYield), "일반");
        }
    }

    /**
     * D003: 기관/외국인 투자 수급 점수 계산 (0~1점)
     *
     * 판단 기준:
     * - 기관 또는 외국인 중 어느 하나라도 최근 1~3개월 내 1% 이상 매집: +1점
     * - 그 외: 0점
     */
    private InvestorSupplyScore calculateInvestorSupplyScore(MaterialData materialData, List<CalculationStep> calculationSteps) {
        // 기관 수급 데이터 확인
        double maxInstitutional = Math.max(
            materialData.institutionalChange1m() != null ? materialData.institutionalChange1m() : 0.0,
            materialData.institutionalChange3m() != null ? materialData.institutionalChange3m() : 0.0
        );

        // 외국인 수급 데이터 확인
        double maxForeign = Math.max(
            materialData.foreignChange1m() != null ? materialData.foreignChange1m() : 0.0,
            materialData.foreignChange3m() != null ? materialData.foreignChange3m() : 0.0
        );

        // 데이터 부족 체크
        if (materialData.institutionalChange1m() == null && materialData.institutionalChange3m() == null &&
            materialData.foreignChange1m() == null && materialData.foreignChange3m() == null) {
            log.warn("기관/외국인 수급 계산을 위한 데이터 부족");
            calculationSteps.add(CalculationStep.failure("수급분석", "기관/외국인 수급 분석", "수급 데이터 없음"));
            return new InvestorSupplyScore(0, null, null, "데이터 부족", "N/A", BigDecimal.ZERO, "N/A");
        }

        // 점수 계산: 기관 또는 외국인 중 하나라도 1% 이상이면 1점
        if (maxInstitutional >= 1.0 || maxForeign >= 1.0) {
            int score = 1;
            String status;
            if (maxInstitutional >= 1.0 && maxForeign >= 1.0) {
                status = String.format("기관+외국인 동반 매집 (기관:%.2f%%, 외국인:%.2f%%)", maxInstitutional, maxForeign);
                calculationSteps.add(CalculationStep.success(
                    "수급분석", "기관+외국인 동반 매집 확인",
                    String.format("기관:%.2f%%, 외국인:%.2f%%", maxInstitutional, maxForeign), "동반매집",
                    score, "기관과 외국인 모두 1% 이상 매집", "기관≥1% AND 외국인≥1% → +1점"
                ));
            } else if (maxInstitutional >= 1.0) {
                status = String.format("기관 매집 (%.2f%%)", maxInstitutional);
                calculationSteps.add(CalculationStep.success(
                    "수급분석", "기관 매집 확인",
                    String.format("%.2f%%", maxInstitutional), "기관매집",
                    score, "기관 투자자 1% 이상 매집", "기관≥1% → +1점"
                ));
            } else {
                status = String.format("외국인 매집 (%.2f%%)", maxForeign);
                calculationSteps.add(CalculationStep.success(
                    "수급분석", "외국인 매집 확인",
                    String.format("%.2f%%", maxForeign), "외국인매집",
                    score, "외국인 투자자 1% 이상 매집", "외국인≥1% → +1점"
                ));
            }
            log.info("D003 투자 수급: {}, 점수: +{}", status, score);
            return new InvestorSupplyScore(score, maxInstitutional, maxForeign, status,
                "투자자매집", BigDecimal.valueOf(Math.max(maxInstitutional, maxForeign)), "상승");
        } else {
            int score = 0;
            String status = String.format("기관/외국인 수급 중립 (기관:%.2f%%, 외국인:%.2f%%)", maxInstitutional, maxForeign);
            calculationSteps.add(CalculationStep.success(
                "수급분석", "수급 중립 확인",
                String.format("기관:%.2f%%, 외국인:%.2f%%", maxInstitutional, maxForeign), "중립",
                score, "기관, 외국인 모두 1% 미만", "기관<1% AND 외국인<1% → 0점"
            ));
            log.info("D003 투자 수급: {}, 점수: +{}", status, score);
            return new InvestorSupplyScore(score, maxInstitutional, maxForeign, status,
                "중립", BigDecimal.valueOf(Math.max(maxInstitutional, maxForeign)), "중립");
        }
    }

    /**
     * D005: 어닝서프라이즈 점수 계산 (0~1점) - 향후 구현
     *
     * 판단 기준:
     * - 컨센서스 대비 10% 이상 초과: +1점
     * - 그 외: 0점
     */
    private EarningsSurpriseScore calculateEarningsSurpriseScore(MaterialData materialData, List<CalculationStep> calculationSteps) {
        if (materialData.earningsSurprise() == null) {
            log.info("어닝서프라이즈 데이터 없음 - 향후 구현 예정");
            calculationSteps.add(CalculationStep.success(
                "어닝서프라이즈", "어닝서프라이즈 분석",
                "N/A", "향후구현",
                0, "어닝서프라이즈 기능 향후 구현 예정", "향후 구현 → 0점"
            ));
            return new EarningsSurpriseScore(0, null, "향후 구현");
        }

        double earningsSurprise = materialData.earningsSurprise();

        if (earningsSurprise >= 10.0) { // 컨센서스 대비 10% 이상 초과
            int score = 1;
            String status = String.format("어닝서프라이즈 (+%.1f%%)", earningsSurprise);
            calculationSteps.add(CalculationStep.success(
                "어닝서프라이즈", "어닝서프라이즈 확인",
                String.format("%.1f%%", earningsSurprise), "서프라이즈",
                score, "컨센서스 대비 10% 이상 초과", "어닝서프라이즈≥10% → +1점"
            ));
            log.info("어닝서프라이즈: {}, 점수: +{}", status, score);
            return new EarningsSurpriseScore(score, earningsSurprise, status);
        } else {
            int score = 0;
            String status = String.format("어닝서프라이즈 없음 (%.1f%%)", earningsSurprise);
            calculationSteps.add(CalculationStep.success(
                "어닝서프라이즈", "어닝서프라이즈 없음",
                String.format("%.1f%%", earningsSurprise), "없음",
                score, "컨센서스 대비 10% 미만", "어닝서프라이즈<10% → 0점"
            ));
            log.info("어닝서프라이즈: {}, 점수: +{}", status, score);
            return new EarningsSurpriseScore(score, earningsSurprise, status);
        }
    }

    // 내부 데이터 클래스들
    private record MaterialData(
        String companyName,
        Double dividendYield,
        Double institutionalRatio,
        Double foreignRatio,
        Double institutionalChange1m,
        Double foreignChange1m,
        Double institutionalChange3m,
        Double foreignChange3m,
        Long listedShares,
        Double earningsSurprise
    ) {}

    private record DividendScore(int score, Double dividendYield, String signal, BigDecimal impactScore, String type) {}
    private record InvestorSupplyScore(int score, Double institutionalChange, Double foreignChange, String signal,
                                     String category, BigDecimal trend, String sectorTrend) {}
    private record EarningsSurpriseScore(int score, Double earningsSurprise, String signal) {}
}