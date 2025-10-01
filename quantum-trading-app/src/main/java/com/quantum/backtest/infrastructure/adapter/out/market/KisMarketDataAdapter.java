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
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

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
                log.error("시장 데이터 조회 실패: {}", response != null ? response.message() : "null response");
                return Collections.emptyList();
            }

            if (response.dailyPrices() == null || response.dailyPrices().isEmpty()) {
                log.error("차트 데이터가 없습니다: {}", stockCode);
                return Collections.emptyList();
            }

            // 시장 데이터 응답을 PriceData로 변환
            List<PriceData> priceHistory = convertToPriceData(response.dailyPrices());

            log.info("시장 데이터 주가 조회 완료: {} 건", priceHistory.size());
            return priceHistory;

        } catch (Exception e) {
            log.error("시장 데이터 주가 조회 실패: {} - {}", stockCode, e.getMessage(), e);
            return Collections.emptyList();
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

}