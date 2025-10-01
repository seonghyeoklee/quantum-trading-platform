package com.quantum.dino.service;

import com.quantum.backtest.domain.PriceData;
import com.quantum.backtest.domain.strategy.util.MovingAverageCalculator;
import com.quantum.backtest.domain.strategy.util.RSICalculator;
import com.quantum.dino.dto.DinoTechnicalResult;
import com.quantum.kis.application.port.out.KisApiPort;
import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.dto.ChartDataResponse;
import com.quantum.kis.exception.KisApiException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * DINO 기술 분석 서비스
 *
 * 기술 분석 영역 5점 만점 구성 (Python 로직과 일치):
 * - OBV 분석 (±1점): 2년 변화율과 주가 추세 일치도
 * - RSI 상태 분석 (±1점): 14일 RSI 과매수/과매도 상태
 * - 투자심리 분석 (±1점): Stochastic Oscillator 기반
 * - 기타지표 분석 (±1점): MACD 기반
 *
 * 최종 점수 공식: MAX(0, MIN(5, 2 + SUM(4개 지표)))
 */
@Service
public class DinoTechnicalService {

    private static final Logger log = LoggerFactory.getLogger(DinoTechnicalService.class);

    private static final int RSI_PERIOD = 14;        // RSI 계산 기간
    private static final int STOCHASTIC_PERIOD = 14; // Stochastic 계산 기간
    private static final int MACD_FAST = 12;         // MACD 빠른 이동평균
    private static final int MACD_SLOW = 26;         // MACD 느린 이동평균
    private static final int MACD_SIGNAL = 9;        // MACD 신호선
    private static final int CHART_DATA_PERIOD = 500; // 차트 데이터 수집 기간 (2년)

    private final KisApiPort kisApiPort;

    public DinoTechnicalService(KisApiPort kisApiPort) {
        this.kisApiPort = kisApiPort;
    }

    /**
     * 종목의 기술 분석을 실행하여 0~5점 점수를 반환
     */
    @Transactional
    public DinoTechnicalResult analyzeTechnicalScore(String stockCode) {
        log.info("=== DINO 기술 분석 시작: {} ===", stockCode);

        try {
            // 1. KIS API에서 차트 데이터 수집
            List<PriceData> priceHistory = collectChartData(stockCode);
            if (priceHistory == null || priceHistory.size() < 30) {
                log.error("차트 데이터 부족: {} (필요: 30일, 실제: {}일)",
                         stockCode, priceHistory != null ? priceHistory.size() : 0);
                return DinoTechnicalResult.createFailedResult(stockCode, getCompanyName(stockCode));
            }

            // 2. OBV 분석 (±1점)
            TechnicalScore obvScore = analyzeOBVScore(priceHistory);

            // 3. RSI 분석 (±1점)
            TechnicalScore rsiScore = analyzeRSIScore(priceHistory);

            // 4. 투자심리 분석 (±1점) - Stochastic
            TechnicalScore stochasticScore = analyzeStochasticScore(priceHistory);

            // 5. 기타지표 분석 (±1점) - MACD
            TechnicalScore macdScore = analyzeMACDScore(priceHistory);

            // 6. 총점 계산 (0~5점) - Python 로직과 동일
            int individualSum = obvScore.score + rsiScore.score + stochasticScore.score + macdScore.score;
            int totalScore = Math.max(0, Math.min(5, 2 + individualSum));

            log.info("기술 분석 완료: {} - OBV: {}점, RSI: {}점, Stochastic: {}점, MACD: {}점, 총점: {}점",
                    stockCode, obvScore.score, rsiScore.score, stochasticScore.score, macdScore.score, totalScore);

            // 7. 결과 생성
            return new DinoTechnicalResult(
                    stockCode,
                    getCompanyName(stockCode),
                    obvScore.score,
                    rsiScore.score,
                    stochasticScore.score,
                    macdScore.score,
                    totalScore,
                    obvScore.obvValue,
                    rsiScore.rsiValue,
                    stochasticScore.stochasticValue,
                    macdScore.macdValue,
                    obvScore.signal,
                    rsiScore.signal,
                    stochasticScore.signal,
                    macdScore.signal,
                    LocalDateTime.now()
            );

        } catch (Exception e) {
            log.error("DINO 기술 분석 실패: {} - {}", stockCode, e.getMessage(), e);
            return DinoTechnicalResult.createFailedResult(stockCode, getCompanyName(stockCode));
        }
    }

    /**
     * OBV 분석 (±1점) - Python 로직과 동일
     * - OBV와 주가 변화율 같은 방향: +1점 (OBV 만족)
     * - OBV와 주가 변화율 반대 방향: -1점 (OBV 불만족)
     * - 나머지 경우: 0점
     */
    private TechnicalScore analyzeOBVScore(List<PriceData> priceHistory) {
        List<BigDecimal> obvValues = calculateOBV(priceHistory);

        if (obvValues.isEmpty() || priceHistory.size() < 30) {
            log.warn("OBV 계산을 위한 데이터 부족");
            return new TechnicalScore(0, "데이터 부족", null, null, null, null);
        }

        // 현재 OBV와 가격
        BigDecimal currentOBV = obvValues.get(obvValues.size() - 1);
        BigDecimal currentPrice = priceHistory.get(priceHistory.size() - 1).close();

        // 비교 기준점 설정 (실제 데이터 길이에 따라 조정)
        BigDecimal pastOBV;
        BigDecimal pastPrice;

        if (priceHistory.size() >= 500) {
            // 2년 전 데이터 (500일 전)
            pastOBV = obvValues.get(obvValues.size() - 500);
            pastPrice = priceHistory.get(priceHistory.size() - 500).close();
        } else if (priceHistory.size() >= 252) {
            // 1년 전 데이터 (252일 전)
            pastOBV = obvValues.get(obvValues.size() - 252);
            pastPrice = priceHistory.get(priceHistory.size() - 252).close();
        } else {
            // 첫 번째 데이터와 비교
            pastOBV = obvValues.get(0);
            pastPrice = priceHistory.get(0).close();
        }

        // OBV 변화율 계산
        double obvChangeRate = 0;
        if (pastOBV.compareTo(BigDecimal.ZERO) != 0) {
            obvChangeRate = currentOBV.subtract(pastOBV)
                    .divide(pastOBV.abs(), 4, RoundingMode.HALF_UP)
                    .multiply(BigDecimal.valueOf(100))
                    .doubleValue();
        }

        // 주가 변화율 계산
        double priceChangeRate = currentPrice.subtract(pastPrice)
                .divide(pastPrice, 4, RoundingMode.HALF_UP)
                .multiply(BigDecimal.valueOf(100))
                .doubleValue();

        // 방향 판단
        int obvDirection = obvChangeRate > 0 ? 1 : obvChangeRate < 0 ? -1 : 0;
        int priceDirection = priceChangeRate > 0 ? 1 : priceChangeRate < 0 ? -1 : 0;

        int score = 0;
        String signal;

        if (obvDirection == priceDirection && obvDirection != 0) {
            score = 1;
            signal = "OBV 만족 (추세 일치)";
        } else if (obvDirection != priceDirection && obvDirection != 0 && priceDirection != 0) {
            score = -1;
            signal = "OBV 불만족 (추세 불일치)";
        } else {
            score = 0;
            signal = "OBV 중립";
        }

        log.info("OBV 분석 - OBV 변화율: {}%, 가격 변화율: {}%, 점수: {}점, 신호: {}",
                obvChangeRate, priceChangeRate, score, signal);

        return new TechnicalScore(score, signal, currentOBV, null, null, null);
    }

    /**
     * RSI 상태 분석 (±1점) - Python 로직과 동일
     * - RSI ≤ 30: +1점 (과매도 매수기회)
     * - RSI ≥ 70: -1점 (과매수 위험)
     * - RSI 30~70: 0점 (중립)
     */
    private TechnicalScore analyzeRSIScore(List<PriceData> priceHistory) {
        List<BigDecimal> rsiValues = calculateRSI(priceHistory, RSI_PERIOD);

        if (rsiValues.isEmpty()) {
            log.warn("RSI 계산을 위한 데이터 부족");
            return new TechnicalScore(0, "데이터 부족", null, null, null, null);
        }

        BigDecimal currentRSI = rsiValues.get(rsiValues.size() - 1);
        int score = 0;
        String signal = "분석 실패";

        if (currentRSI != null) {
            double rsi = currentRSI.doubleValue();

            if (rsi <= 30.0) {
                score = 1;  // 과매도 → 매수 기회
                signal = "과매도 구간 - 매수 기회";
            } else if (rsi >= 70.0) {
                score = -1;  // 과매수 → 위험 신호
                signal = "과매수 구간 - 위험 신호";
            } else {
                score = 0;  // 중립
                signal = "중립 구간";
            }
        }

        log.info("RSI 분석 - 현재 RSI: {}, 점수: {}점, 신호: {}",
                currentRSI != null ? currentRSI.doubleValue() : 0, score, signal);

        return new TechnicalScore(score, signal, null, currentRSI, null, null);
    }

    /**
     * RSI 계산 (14일 기간)
     */
    private List<BigDecimal> calculateRSI(List<PriceData> priceHistory, int period) {
        List<BigDecimal> rsiValues = new ArrayList<>();

        // 첫 period개는 null로 초기화
        for (int i = 0; i < period; i++) {
            rsiValues.add(null);
        }

        if (priceHistory.size() <= period) {
            return rsiValues;
        }

        // 첫 번째 평균 게인/로스 계산
        BigDecimal firstAvgGain = BigDecimal.ZERO;
        BigDecimal firstAvgLoss = BigDecimal.ZERO;

        for (int i = 1; i <= period; i++) {
            BigDecimal change = priceHistory.get(i).close().subtract(priceHistory.get(i - 1).close());
            if (change.compareTo(BigDecimal.ZERO) > 0) {
                firstAvgGain = firstAvgGain.add(change);
            } else {
                firstAvgLoss = firstAvgLoss.add(change.abs());
            }
        }

        firstAvgGain = firstAvgGain.divide(BigDecimal.valueOf(period), 6, RoundingMode.HALF_UP);
        firstAvgLoss = firstAvgLoss.divide(BigDecimal.valueOf(period), 6, RoundingMode.HALF_UP);

        // 첫 번째 RSI 계산
        BigDecimal firstRSI = calculateRSIValue(firstAvgGain, firstAvgLoss);
        rsiValues.add(firstRSI);

        // 이후 RSI 계산 (Wilder's Smoothing)
        BigDecimal avgGain = firstAvgGain;
        BigDecimal avgLoss = firstAvgLoss;

        for (int i = period + 1; i < priceHistory.size(); i++) {
            BigDecimal change = priceHistory.get(i).close().subtract(priceHistory.get(i - 1).close());
            BigDecimal currentGain = change.compareTo(BigDecimal.ZERO) > 0 ? change : BigDecimal.ZERO;
            BigDecimal currentLoss = change.compareTo(BigDecimal.ZERO) < 0 ? change.abs() : BigDecimal.ZERO;

            // Wilder's Smoothing
            avgGain = avgGain.multiply(BigDecimal.valueOf(period - 1))
                           .add(currentGain)
                           .divide(BigDecimal.valueOf(period), 6, RoundingMode.HALF_UP);

            avgLoss = avgLoss.multiply(BigDecimal.valueOf(period - 1))
                           .add(currentLoss)
                           .divide(BigDecimal.valueOf(period), 6, RoundingMode.HALF_UP);

            BigDecimal rsi = calculateRSIValue(avgGain, avgLoss);
            rsiValues.add(rsi);
        }

        return rsiValues;
    }

    /**
     * RSI 값 계산
     */
    private BigDecimal calculateRSIValue(BigDecimal avgGain, BigDecimal avgLoss) {
        if (avgLoss.compareTo(BigDecimal.ZERO) == 0) {
            return BigDecimal.valueOf(100);
        }

        BigDecimal rs = avgGain.divide(avgLoss, 6, RoundingMode.HALF_UP);
        return BigDecimal.valueOf(100).subtract(
            BigDecimal.valueOf(100).divide(
                BigDecimal.ONE.add(rs), 2, RoundingMode.HALF_UP
            )
        );
    }

    /**
     * 투자심리 분석 (±1점) - Stochastic Oscillator 기반
     * - Stochastic ≤ 25: +1점 (침체 → 매수 시점)
     * - Stochastic ≥ 75: -1점 (과열 → 매도 시점)
     * - Stochastic 25~75: 0점 (중립)
     */
    private TechnicalScore analyzeStochasticScore(List<PriceData> priceHistory) {
        List<BigDecimal> stochasticValues = calculateStochastic(priceHistory, STOCHASTIC_PERIOD);

        if (stochasticValues.isEmpty()) {
            log.warn("Stochastic 계산을 위한 데이터 부족");
            return new TechnicalScore(0, "데이터 부족", null, null, null, null);
        }

        BigDecimal currentStochastic = stochasticValues.get(stochasticValues.size() - 1);
        int score = 0;
        String signal = "분석 실패";

        if (currentStochastic != null) {
            double stochastic = currentStochastic.doubleValue();

            if (stochastic <= 25.0) {
                score = 1;  // 침체 → 매수 기회
                signal = "침체 구간 - 매수 기회";
            } else if (stochastic >= 75.0) {
                score = -1;  // 과열 → 위험 신호
                signal = "과열 구간 - 위험 신호";
            } else {
                score = 0;  // 중립
                signal = "중립 구간";
            }
        }

        log.info("Stochastic 분석 - 현재 Stochastic: {}%, 점수: {}점, 신호: {}",
                currentStochastic != null ? currentStochastic.doubleValue() : 0, score, signal);

        return new TechnicalScore(score, signal, null, null, currentStochastic, null);
    }

    /**
     * 기타지표 분석 (±1점) - MACD 기반
     * - MACD > Signal: +1점 (상승 추세)
     * - MACD < Signal: -1점 (하락 추세)
     * - MACD ≈ Signal: 0점 (중립)
     */
    private TechnicalScore analyzeMACDScore(List<PriceData> priceHistory) {
        MACDResult macdResult = calculateMACD(priceHistory);

        if (macdResult.macdValues.isEmpty() || macdResult.signalValues.isEmpty()) {
            log.warn("MACD 계산을 위한 데이터 부족");
            return new TechnicalScore(0, "데이터 부족", null, null, null, null);
        }

        BigDecimal currentMACD = macdResult.macdValues.get(macdResult.macdValues.size() - 1);
        BigDecimal currentSignal = macdResult.signalValues.get(macdResult.signalValues.size() - 1);

        int score = 0;
        String signal = "분석 실패";

        if (currentMACD != null && currentSignal != null) {
            BigDecimal macdDiff = currentMACD.subtract(currentSignal);

            if (macdDiff.compareTo(BigDecimal.valueOf(0.01)) > 0) {
                score = 1;  // 상승 추세
                signal = "상승 추세";
            } else if (macdDiff.compareTo(BigDecimal.valueOf(-0.01)) < 0) {
                score = -1;  // 하락 추세
                signal = "하락 추세";
            } else {
                score = 0;  // 중립
                signal = "중립";
            }
        }

        log.info("MACD 분석 - MACD: {}, Signal: {}, 점수: {}점, 신호: {}",
                currentMACD != null ? currentMACD.doubleValue() : 0,
                currentSignal != null ? currentSignal.doubleValue() : 0,
                score, signal);

        return new TechnicalScore(score, signal, null, null, null, currentMACD);
    }

    /**
     * KIS API에서 차트 데이터 수집
     */
    private List<PriceData> collectChartData(String stockCode) {
        log.info("KIS API에서 차트 데이터 수집 중: {}", stockCode);

        try {
            // 2년치 데이터 수집을 위한 날짜 계산
            LocalDate endDate = LocalDate.now();
            LocalDate startDate = endDate.minusDays(CHART_DATA_PERIOD);

            // KIS API 호출
            ChartDataResponse response = kisApiPort.getDailyChartData(
                    KisEnvironment.PROD, stockCode, startDate, endDate);

            if (response == null || !response.isSuccess() || response.output2() == null) {
                log.error("KIS API에서 차트 데이터 조회 실패: {}", stockCode);
                return Collections.emptyList();
            }

            // KIS API 응답을 PriceData로 변환
            List<PriceData> priceHistory = new ArrayList<>();
            for (ChartDataResponse.Output2 dailyData : response.output2()) {
                try {
                    LocalDate date = LocalDate.parse(dailyData.stckBsopDate(),
                            java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd"));

                    BigDecimal open = new BigDecimal(dailyData.stckOprc());
                    BigDecimal high = new BigDecimal(dailyData.stckHgpr());
                    BigDecimal low = new BigDecimal(dailyData.stckLwpr());
                    BigDecimal close = new BigDecimal(dailyData.stckClpr());
                    long volume = Long.parseLong(dailyData.acmlVol());

                    priceHistory.add(new PriceData(date, open, high, low, close, volume));
                } catch (Exception e) {
                    log.warn("차트 데이터 파싱 실패: {} - {}", dailyData.stckBsopDate(), e.getMessage());
                }
            }

            // 날짜 순으로 정렬 (오래된 날짜부터)
            priceHistory.sort((a, b) -> a.date().compareTo(b.date()));

            log.info("KIS API 차트 데이터 수집 완료: {} ({}일)", stockCode, priceHistory.size());
            return priceHistory;

        } catch (KisApiException e) {
            log.error("KIS API 차트 데이터 수집 실패: {} - {}", stockCode, e.getMessage());
            return Collections.emptyList();
        } catch (Exception e) {
            log.error("차트 데이터 수집 중 예외 발생: {} - {}", stockCode, e.getMessage(), e);
            return Collections.emptyList();
        }
    }

    /**
     * 회사명 조회 (KIS API 응답에서 추출, 실패시 기본값)
     */
    private String getCompanyName(String stockCode) {
        try {
            // 최근 1일치 데이터로 회사명 조회
            LocalDate endDate = LocalDate.now();
            LocalDate startDate = endDate.minusDays(1);

            ChartDataResponse response = kisApiPort.getDailyChartData(
                    KisEnvironment.PROD, stockCode, startDate, endDate);

            if (response != null && response.isSuccess() && response.output1() != null
                    && response.output1().htsKorIsnm() != null && !response.output1().htsKorIsnm().trim().isEmpty()) {
                return response.output1().htsKorIsnm();
            }
        } catch (Exception e) {
            log.debug("KIS API에서 회사명 조회 실패: {} - {}", stockCode, e.getMessage());
        }

        // 기본값 반환
        if ("005930".equals(stockCode)) {
            return "삼성전자";
        }
        return stockCode;
    }

    /**
     * OBV (On Balance Volume) 계산
     */
    private List<BigDecimal> calculateOBV(List<PriceData> priceHistory) {
        List<BigDecimal> obvValues = new ArrayList<>();

        if (priceHistory.isEmpty()) {
            return obvValues;
        }

        BigDecimal obv = BigDecimal.ZERO;
        obvValues.add(obv);

        for (int i = 1; i < priceHistory.size(); i++) {
            BigDecimal currentClose = priceHistory.get(i).close();
            BigDecimal previousClose = priceHistory.get(i - 1).close();
            long volume = priceHistory.get(i).volume();

            if (currentClose.compareTo(previousClose) > 0) {
                // 가격 상승 시 거래량 더함
                obv = obv.add(BigDecimal.valueOf(volume));
            } else if (currentClose.compareTo(previousClose) < 0) {
                // 가격 하락 시 거래량 뺌
                obv = obv.subtract(BigDecimal.valueOf(volume));
            }
            // 가격 변화 없으면 OBV 변화 없음

            obvValues.add(obv);
        }

        return obvValues;
    }

    /**
     * Stochastic Oscillator 계산
     */
    private List<BigDecimal> calculateStochastic(List<PriceData> priceHistory, int period) {
        List<BigDecimal> stochasticValues = new ArrayList<>();

        // 첫 period개는 null로 초기화
        for (int i = 0; i < period - 1; i++) {
            stochasticValues.add(null);
        }

        for (int i = period - 1; i < priceHistory.size(); i++) {
            // period 기간 동안의 최고가와 최저가 찾기
            BigDecimal highest = BigDecimal.ZERO;
            BigDecimal lowest = new BigDecimal("999999999");

            for (int j = i - period + 1; j <= i; j++) {
                highest = highest.max(priceHistory.get(j).high());
                lowest = lowest.min(priceHistory.get(j).low());
            }

            BigDecimal currentClose = priceHistory.get(i).close();
            BigDecimal stochastic;

            if (highest.compareTo(lowest) == 0) {
                stochastic = BigDecimal.valueOf(50); // 분모가 0인 경우 중립값
            } else {
                stochastic = currentClose.subtract(lowest)
                        .divide(highest.subtract(lowest), 4, RoundingMode.HALF_UP)
                        .multiply(BigDecimal.valueOf(100));
            }

            stochasticValues.add(stochastic);
        }

        return stochasticValues;
    }

    /**
     * MACD 계산 결과를 담는 내부 클래스
     */
    private static class MACDResult {
        final List<BigDecimal> macdValues;
        final List<BigDecimal> signalValues;

        MACDResult(List<BigDecimal> macdValues, List<BigDecimal> signalValues) {
            this.macdValues = macdValues;
            this.signalValues = signalValues;
        }
    }

    /**
     * MACD 계산
     */
    private MACDResult calculateMACD(List<PriceData> priceHistory) {
        List<BigDecimal> fastMA = MovingAverageCalculator.calculateEMA(priceHistory, MACD_FAST);
        List<BigDecimal> slowMA = MovingAverageCalculator.calculateEMA(priceHistory, MACD_SLOW);

        List<BigDecimal> macdValues = new ArrayList<>();

        // MACD = 12일 EMA - 26일 EMA
        for (int i = 0; i < priceHistory.size(); i++) {
            if (fastMA.get(i) != null && slowMA.get(i) != null) {
                BigDecimal macd = fastMA.get(i).subtract(slowMA.get(i));
                macdValues.add(macd);
            } else {
                macdValues.add(null);
            }
        }

        // Signal = MACD의 9일 EMA
        List<BigDecimal> signalValues = calculateEMAFromValues(macdValues, MACD_SIGNAL);

        return new MACDResult(macdValues, signalValues);
    }

    /**
     * 값 리스트로부터 EMA 계산
     */
    private List<BigDecimal> calculateEMAFromValues(List<BigDecimal> values, int period) {
        List<BigDecimal> emaValues = new ArrayList<>();
        BigDecimal multiplier = BigDecimal.valueOf(2.0 / (period + 1));

        // 첫 period개는 null로 초기화
        for (int i = 0; i < period; i++) {
            emaValues.add(null);
        }

        if (values.size() <= period) {
            return emaValues;
        }

        // 첫 번째 EMA는 SMA로 계산
        BigDecimal sum = BigDecimal.ZERO;
        int count = 0;
        for (int i = 0; i < period && i < values.size(); i++) {
            if (values.get(i) != null) {
                sum = sum.add(values.get(i));
                count++;
            }
        }

        if (count > 0) {
            BigDecimal firstEMA = sum.divide(BigDecimal.valueOf(count), 6, RoundingMode.HALF_UP);
            emaValues.add(firstEMA);

            // 이후 EMA 계산
            BigDecimal previousEMA = firstEMA;
            for (int i = period + 1; i < values.size(); i++) {
                if (values.get(i) != null) {
                    BigDecimal currentEMA = values.get(i).subtract(previousEMA)
                            .multiply(multiplier)
                            .add(previousEMA);
                    emaValues.add(currentEMA);
                    previousEMA = currentEMA;
                } else {
                    emaValues.add(null);
                }
            }
        }

        return emaValues;
    }


    /**
     * 기술 분석 점수 결과 내부 클래스
     */
    private static class TechnicalScore {
        final int score;
        final String signal;
        final BigDecimal obvValue;
        final BigDecimal rsiValue;
        final BigDecimal stochasticValue;
        final BigDecimal macdValue;

        TechnicalScore(int score, String signal, BigDecimal obvValue, BigDecimal rsiValue,
                      BigDecimal stochasticValue, BigDecimal macdValue) {
            this.score = score;
            this.signal = signal;
            this.obvValue = obvValue;
            this.rsiValue = rsiValue;
            this.stochasticValue = stochasticValue;
            this.macdValue = macdValue;
        }
    }
}