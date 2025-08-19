package com.quantum.kis.service;

import com.quantum.kis.model.KisStockCandleResponse;
import com.quantum.kis.model.enums.KisTimeframe;
import java.time.LocalDate;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

/**
 * KIS API 캔들 데이터 조회 서비스
 *
 * <p>국내주식 차트 분석을 위한 캔들(봉) 데이터를 KIS API를 통해 조회
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class KisCandleDataService {

    private final KisTokenProvider kisTokenProvider;
    private final KisRateLimiter kisRateLimiter;
    private final KisModelMapper kisModelMapper;

    @Value("${kis.api.environment:sandbox}")
    private String environment;

    // TODO: KisFeignClient 주입 필요 (캔들 데이터 조회용 메서드 추가 후)

    /**
     * 국내주식 일봉 데이터 조회
     *
     * @param stockCode 종목코드 (6자리)
     * @param startDate 조회 시작일
     * @param endDate 조회 종료일
     * @param adjustedPrice 수정주가 적용 여부
     * @return 캔들 데이터 응답
     */
    public KisStockCandleResponse getDailyCandleData(
            String stockCode, LocalDate startDate, LocalDate endDate, boolean adjustedPrice) {

        KisTimeframe kisTimeframe = kisModelMapper.toKisTimeframe("ONE_DAY");
        return getCandleData(stockCode, kisTimeframe, startDate, endDate, adjustedPrice);
    }

    /**
     * 국내주식 주봉 데이터 조회
     *
     * @param stockCode 종목코드
     * @param startDate 조회 시작일
     * @param endDate 조회 종료일
     * @param adjustedPrice 수정주가 적용 여부
     * @return 캔들 데이터 응답
     */
    public KisStockCandleResponse getWeeklyCandleData(
            String stockCode, LocalDate startDate, LocalDate endDate, boolean adjustedPrice) {

        KisTimeframe kisTimeframe = kisModelMapper.toKisTimeframe("ONE_WEEK");
        return getCandleData(stockCode, kisTimeframe, startDate, endDate, adjustedPrice);
    }

    /**
     * 국내주식 월봉 데이터 조회
     *
     * @param stockCode 종목코드
     * @param startDate 조회 시작일
     * @param endDate 조회 종료일
     * @param adjustedPrice 수정주가 적용 여부
     * @return 캔들 데이터 응답
     */
    public KisStockCandleResponse getMonthlyCandleData(
            String stockCode, LocalDate startDate, LocalDate endDate, boolean adjustedPrice) {

        KisTimeframe kisTimeframe = kisModelMapper.toKisTimeframe("ONE_MONTH");
        return getCandleData(stockCode, kisTimeframe, startDate, endDate, adjustedPrice);
    }

    /**
     * 분봉 데이터 조회 (1분, 5분, 15분, 30분, 60분)
     *
     * @param stockCode 종목코드
     * @param domainTimeframe 도메인 시간프레임
     * @param startDate 조회 시작일
     * @param endDate 조회 종료일
     * @return 캔들 데이터 응답
     */
    public KisStockCandleResponse getIntradayCandleData(
            String stockCode, String domainTimeframe, LocalDate startDate, LocalDate endDate) {

        KisTimeframe kisTimeframe = kisModelMapper.toKisTimeframe(domainTimeframe);
        if (!kisTimeframe.isIntraday()) {
            throw new IllegalArgumentException("분봉 시간프레임이 아닙니다: " + domainTimeframe);
        }

        return getCandleData(stockCode, kisTimeframe, startDate, endDate, false);
    }

    /**
     * 캔들 데이터 조회 (공통 메서드)
     *
     * @param stockCode 종목코드
     * @param timeframe 시간프레임
     * @param startDate 조회 시작일
     * @param endDate 조회 종료일
     * @param adjustedPrice 수정주가 적용 여부
     * @return 캔들 데이터 응답
     */
    private KisStockCandleResponse getCandleData(
            String stockCode,
            KisTimeframe timeframe,
            LocalDate startDate,
            LocalDate endDate,
            boolean adjustedPrice) {

        validateParameters(stockCode, timeframe.getDescription(), startDate, endDate);

        try {
            // 1. Rate Limiting 체크
            String apiEndpoint = getApiEndpoint(timeframe);
            if (!kisRateLimiter.acquireWithWait(apiEndpoint, false)) {
                throw new RuntimeException("KIS API rate limit exceeded for candle data inquiry");
            }

            // 2. 액세스 토큰 조회
            String accessToken = null;
            if (kisTokenProvider != null) {
                accessToken = kisTokenProvider.getValidAccessToken();
            }
            if (accessToken == null) {
                throw new RuntimeException("Failed to get valid access token for candle data");
            }

            log.info(
                    "Requesting {} candle data for {} from {} to {}",
                    timeframe.getDescription(),
                    stockCode,
                    startDate,
                    endDate);

            // 3. KIS API 호출
            // TODO: KisFeignClient에 캔들 데이터 조회 메서드 구현 필요
            // return kisFeignClient.getCandleData(...)

            // 임시 응답 (실제 구현 시 제거)
            log.warn("KIS Candle Data Service: API 호출 구현 필요");
            return new KisStockCandleResponse("0", "SUCCESS", "임시 응답 - API 구현 필요", List.of(), null);

        } catch (Exception e) {
            log.error(
                    "Failed to get {} candle data for {}: {}",
                    timeframe.getDescription(),
                    stockCode,
                    e.getMessage(),
                    e);
            throw new RuntimeException("캔들 데이터 조회 실패: " + e.getMessage(), e);
        }
    }

    /**
     * 최근 N개 캔들 데이터 조회
     *
     * @param stockCode 종목코드
     * @param domainTimeframe 도메인 시간프레임
     * @param count 조회할 캔들 개수
     * @return 캔들 데이터 응답
     */
    public KisStockCandleResponse getRecentCandleData(
            String stockCode, String domainTimeframe, int count) {

        if (count <= 0 || count > 100) {
            throw new IllegalArgumentException("캔들 개수는 1~100 사이여야 합니다: " + count);
        }

        KisTimeframe kisTimeframe = kisModelMapper.toKisTimeframe(domainTimeframe);
        LocalDate endDate = LocalDate.now();
        LocalDate startDate = calculateStartDate(kisTimeframe, count);

        return getCandleData(stockCode, kisTimeframe, startDate, endDate, false);
    }

    /** 파라미터 검증 */
    private void validateParameters(
            String stockCode, String timeframe, LocalDate startDate, LocalDate endDate) {
        if (stockCode == null || stockCode.trim().length() != 6) {
            throw new IllegalArgumentException("종목코드는 6자리여야 합니다: " + stockCode);
        }
        if (timeframe == null || timeframe.trim().isEmpty()) {
            throw new IllegalArgumentException("시간프레임은 필수입니다");
        }
        if (startDate == null || endDate == null) {
            throw new IllegalArgumentException("시작일과 종료일은 필수입니다");
        }
        if (startDate.isAfter(endDate)) {
            throw new IllegalArgumentException("시작일이 종료일보다 늦을 수 없습니다");
        }
    }

    /** 시간프레임별 API 엔드포인트 반환 */
    private String getApiEndpoint(KisTimeframe timeframe) {
        return switch (timeframe) {
            case MINUTE_1, MINUTE_5, MINUTE_15, MINUTE_30, MINUTE_60 ->
                    "domestic-stock-minute-candle";
            case DAILY -> "domestic-stock-daily-candle";
            case WEEKLY -> "domestic-stock-weekly-candle";
            case MONTHLY -> "domestic-stock-monthly-candle";
        };
    }

    /** 캔들 개수 기반 시작일 계산 */
    private LocalDate calculateStartDate(KisTimeframe timeframe, int count) {
        LocalDate now = LocalDate.now();
        return switch (timeframe) {
            case MINUTE_1, MINUTE_5, MINUTE_15, MINUTE_30, MINUTE_60 ->
                    now.minusDays(Math.max(count / 300, 1)); // 분봉은 하루 기준
            case DAILY -> now.minusDays(count);
            case WEEKLY -> now.minusWeeks(count);
            case MONTHLY -> now.minusMonths(count);
        };
    }

    /** Rate Limiter 상태 확인 */
    public KisRateLimiter.RateLimitStatus getRateLimitStatus(String domainTimeframe) {
        KisTimeframe kisTimeframe = kisModelMapper.toKisTimeframe(domainTimeframe);
        String apiEndpoint = getApiEndpoint(kisTimeframe);
        return kisRateLimiter.getStatus(apiEndpoint);
    }
}
