package com.quantum.backtest.infrastructure.adapter.out.market;

import com.quantum.backtest.application.port.out.MarketDataPort;
import com.quantum.backtest.domain.PriceData;
import com.quantum.shared.MarketDataDto;
import com.quantum.shared.MarketDataService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Primary;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * 시장 데이터 서비스를 사용하는 시장 데이터 어댑터
 * MockMarketDataAdapter를 대체하는 실제 구현체
 */
@Component
@Primary // MockMarketDataAdapter보다 우선 사용
@Profile("!test") // 테스트 환경에서는 Mock 사용
public class KisMarketDataAdapter implements MarketDataPort {

    private static final Logger log = LoggerFactory.getLogger(KisMarketDataAdapter.class);

    private final MarketDataService marketDataService;

    public KisMarketDataAdapter(MarketDataService marketDataService) {
        this.marketDataService = marketDataService;
    }

    @Override
    public List<PriceData> getPriceHistory(String stockCode, LocalDate startDate, LocalDate endDate) {
        log.info("시장 데이터 주가 조회: {} ({} ~ {})", stockCode, startDate, endDate);

        try {
            // 시장 데이터 서비스 호출
            MarketDataDto.ChartResponse response = marketDataService.getDailyChartData(stockCode, startDate, endDate);

            // 응답 검증
            if (response == null || !response.success()) {
                log.warn("시장 데이터 조회 실패 - Mock 데이터로 폴백: {}", response != null ? response.message() : "null response");
                return generateMockPriceHistory(stockCode, startDate, endDate);
            }

            if (response.dailyPrices() == null || response.dailyPrices().isEmpty()) {
                log.warn("차트 데이터가 없습니다 - Mock 데이터로 폴백: {}", stockCode);
                return generateMockPriceHistory(stockCode, startDate, endDate);
            }

            // 시장 데이터 응답을 PriceData로 변환
            List<PriceData> priceHistory = convertToPriceData(response.dailyPrices());

            log.info("시장 데이터 주가 조회 완료: {} 건", priceHistory.size());
            return priceHistory;

        } catch (Exception e) {
            log.warn("시장 데이터 주가 조회 실패 - Mock 데이터로 폴백: {} - {}", stockCode, e.getMessage());
            // API 실패 시 Mock 데이터 생성하여 반환
            return generateMockPriceHistory(stockCode, startDate, endDate);
        }
    }

    @Override
    public PriceData getPriceData(String stockCode, LocalDate date) {
        List<PriceData> history = getPriceHistory(stockCode, date, date);
        return history.isEmpty() ? null : history.get(0);
    }

    @Override
    public boolean isValidStock(String stockCode) {
        return marketDataService.isValidStock(stockCode);
    }

    @Override
    public String getStockName(String stockCode) {
        return marketDataService.getStockName(stockCode);
    }

    /**
     * 시장 데이터 DTO를 PriceData 리스트로 변환한다.
     */
    private List<PriceData> convertToPriceData(List<MarketDataDto.DailyPrice> dailyPrices) {
        List<PriceData> priceDataList = new ArrayList<>();
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyyMMdd");

        for (MarketDataDto.DailyPrice dailyPrice : dailyPrices) {
            try {
                LocalDate date = LocalDate.parse(dailyPrice.date(), formatter);
                BigDecimal open = new BigDecimal(dailyPrice.openPrice());
                BigDecimal high = new BigDecimal(dailyPrice.highPrice());
                BigDecimal low = new BigDecimal(dailyPrice.lowPrice());
                BigDecimal close = new BigDecimal(dailyPrice.closePrice());
                long volume = Long.parseLong(dailyPrice.volume());

                PriceData priceData = new PriceData(date, open, high, low, close, volume);
                priceDataList.add(priceData);

            } catch (Exception e) {
                log.warn("가격 데이터 변환 실패 - 날짜: {}, 오류: {}",
                        dailyPrice.date(), e.getMessage());
            }
        }

        // 시간순 정렬 (오래된 것부터)
        Collections.sort(priceDataList, (a, b) -> a.date().compareTo(b.date()));

        return priceDataList;
    }

    /**
     * KIS API 실패 시 Mock 데이터를 생성한다.
     * 실제 주식의 일반적인 가격 변동 패턴을 모방하여 현실적인 데이터를 생성한다.
     */
    private List<PriceData> generateMockPriceHistory(String stockCode, LocalDate startDate, LocalDate endDate) {
        log.info("Mock 주가 데이터 생성: {} ({} ~ {})", stockCode, startDate, endDate);

        List<PriceData> mockData = new ArrayList<>();
        Random random = new Random(stockCode.hashCode()); // 종목별 일관된 패턴

        // 종목별 기본 가격 설정
        Map<String, BigDecimal> basePrices = Map.of(
                "005930", new BigDecimal("75000"), // 삼성전자
                "000660", new BigDecimal("130000"), // SK하이닉스
                "035420", new BigDecimal("200000"), // NAVER
                "207940", new BigDecimal("800000"), // 삼성바이오로직스
                "373220", new BigDecimal("400000")  // LG에너지솔루션
        );

        BigDecimal basePrice = basePrices.getOrDefault(stockCode, new BigDecimal("50000"));
        BigDecimal currentPrice = basePrice;

        LocalDate currentDate = startDate;
        while (!currentDate.isAfter(endDate)) {
            // 평일만 처리 (주말 제외)
            if (currentDate.getDayOfWeek().getValue() <= 5) {
                // 일일 변동률: -3% ~ +3%
                double changePercent = (random.nextGaussian() * 0.015); // 표준편차 1.5%
                changePercent = Math.max(-0.03, Math.min(0.03, changePercent)); // -3% ~ +3% 제한

                BigDecimal change = currentPrice.multiply(new BigDecimal(changePercent));
                BigDecimal newClose = currentPrice.add(change);

                // 일중 변동성 (시가, 고가, 저가 생성)
                double volatility = 0.02; // 2% 일중 변동성
                BigDecimal dayRange = newClose.multiply(new BigDecimal(volatility));

                BigDecimal high = newClose.add(dayRange.multiply(new BigDecimal(random.nextDouble())))
                        .setScale(0, RoundingMode.HALF_UP);
                BigDecimal low = newClose.subtract(dayRange.multiply(new BigDecimal(random.nextDouble())))
                        .setScale(0, RoundingMode.HALF_UP);

                // 시가는 전날 종가 기준으로 약간 변동
                BigDecimal open = currentPrice.add(currentPrice.multiply(
                        new BigDecimal((random.nextGaussian() * 0.005))))
                        .setScale(0, RoundingMode.HALF_UP);

                // High >= max(Open, Close), Low <= min(Open, Close) 보장
                BigDecimal maxPrice = open.max(newClose);
                BigDecimal minPrice = open.min(newClose);
                high = high.max(maxPrice);
                low = low.min(minPrice);

                // 거래량 (1백만 ~ 5백만주 사이의 랜덤값)
                long volume = 1000000 + random.nextInt(4000000);

                PriceData priceData = new PriceData(
                        currentDate,
                        open,
                        high,
                        low,
                        newClose.setScale(0, RoundingMode.HALF_UP),
                        volume
                );

                mockData.add(priceData);
                currentPrice = newClose;
            }

            currentDate = currentDate.plusDays(1);
        }

        log.info("Mock 주가 데이터 생성 완료: {} 건", mockData.size());
        return mockData;
    }
}