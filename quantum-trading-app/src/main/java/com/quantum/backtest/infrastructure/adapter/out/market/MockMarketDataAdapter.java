package com.quantum.backtest.infrastructure.adapter.out.market;

import com.quantum.backtest.application.port.out.MarketDataPort;
import com.quantum.backtest.domain.PriceData;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * Mock 시장 데이터 어댑터
 * 개발 및 테스트용 임시 구현체
 * TODO: 실제 KIS API 연동으로 교체 필요
 */
@Component
public class MockMarketDataAdapter implements MarketDataPort {

    private static final Logger log = LoggerFactory.getLogger(MockMarketDataAdapter.class);

    // 주요 종목들의 기본 정보
    private static final Map<String, StockInfo> STOCK_INFO_MAP = Map.of(
            "005930", new StockInfo("삼성전자", new BigDecimal("70000")),
            "000660", new StockInfo("SK하이닉스", new BigDecimal("120000")),
            "035420", new StockInfo("NAVER", new BigDecimal("200000")),
            "051910", new StockInfo("LG화학", new BigDecimal("400000")),
            "006400", new StockInfo("삼성SDI", new BigDecimal("300000")),
            "035720", new StockInfo("카카오", new BigDecimal("50000")),
            "373220", new StockInfo("LG에너지솔루션", new BigDecimal("400000")),
            "207940", new StockInfo("삼성바이오로직스", new BigDecimal("800000"))
    );

    private final Random random = new Random();

    @Override
    public List<PriceData> getPriceHistory(String stockCode, LocalDate startDate, LocalDate endDate) {
        log.info("Mock 주가 데이터 조회: {} ({} ~ {})", stockCode, startDate, endDate);

        StockInfo stockInfo = STOCK_INFO_MAP.get(stockCode);
        if (stockInfo == null) {
            log.warn("지원하지 않는 종목코드: {}", stockCode);
            return new ArrayList<>();
        }

        List<PriceData> priceHistory = new ArrayList<>();
        BigDecimal currentPrice = stockInfo.basePrice();

        LocalDate current = startDate;
        while (!current.isAfter(endDate)) {
            // 주말 제외
            if (current.getDayOfWeek().getValue() >= 6) {
                current = current.plusDays(1);
                continue;
            }

            // 일일 변동률 -5% ~ +5% 랜덤
            double changeRate = (random.nextGaussian() * 2.0) / 100.0; // 표준편차 2%
            changeRate = Math.max(-0.05, Math.min(0.05, changeRate)); // -5% ~ +5% 제한

            BigDecimal open = currentPrice;
            BigDecimal close = open.multiply(BigDecimal.valueOf(1 + changeRate))
                    .setScale(0, RoundingMode.HALF_UP);

            // 고가/저가 계산 (변동폭의 50% 내외)
            BigDecimal dailyRange = open.multiply(BigDecimal.valueOf(Math.abs(changeRate) * 0.5 + 0.01));
            BigDecimal high = close.compareTo(open) > 0 ? close.add(dailyRange) : open.add(dailyRange);
            BigDecimal low = close.compareTo(open) < 0 ? close.subtract(dailyRange) : open.subtract(dailyRange);

            // 거래량 (10만주 ~ 100만주)
            long volume = 100_000 + random.nextInt(900_000);

            PriceData priceData = new PriceData(current, open, high, low, close, volume);
            priceHistory.add(priceData);

            currentPrice = close;
            current = current.plusDays(1);
        }

        log.info("Mock 주가 데이터 생성 완료: {} 건", priceHistory.size());
        return priceHistory;
    }

    @Override
    public PriceData getPriceData(String stockCode, LocalDate date) {
        List<PriceData> history = getPriceHistory(stockCode, date, date);
        return history.isEmpty() ? null : history.get(0);
    }

    @Override
    public boolean isValidStock(String stockCode) {
        boolean isValid = STOCK_INFO_MAP.containsKey(stockCode);
        log.debug("종목코드 유효성 검증: {} -> {}", stockCode, isValid);
        return isValid;
    }

    @Override
    public String getStockName(String stockCode) {
        StockInfo stockInfo = STOCK_INFO_MAP.get(stockCode);
        String stockName = stockInfo != null ? stockInfo.name() : stockCode;
        log.debug("종목명 조회: {} -> {}", stockCode, stockName);
        return stockName;
    }

    /**
     * 주식 기본 정보
     */
    private record StockInfo(String name, BigDecimal basePrice) {}
}