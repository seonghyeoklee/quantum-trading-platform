package com.quantum.kis.application.service;

import com.quantum.kis.application.port.out.KisApiPort;
import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.dto.ChartDataResponse;
import com.quantum.shared.MarketDataDto;
import com.quantum.shared.MarketDataService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.List;
import java.util.stream.Collectors;

/**
 * KIS API를 사용한 시장 데이터 서비스 구현체
 */
@Service
@Transactional
public class KisMarketDataService implements MarketDataService {

    private static final Logger log = LoggerFactory.getLogger(KisMarketDataService.class);

    private final KisApiPort kisApiPort;

    public KisMarketDataService(KisApiPort kisApiPort) {
        this.kisApiPort = kisApiPort;
    }

    @Override
    public MarketDataDto.ChartResponse getDailyChartData(String stockCode, LocalDate startDate, LocalDate endDate) {
        log.info("KIS API 차트 데이터 조회: {} ({} ~ {})", stockCode, startDate, endDate);

        try {
            ChartDataResponse response = kisApiPort.getDailyChartData(
                    KisEnvironment.PROD,
                    stockCode,
                    startDate,
                    endDate
            );

            if (response == null || !response.isSuccess()) {
                String message = response != null ? response.message() : "KIS API 호출 실패";
                log.warn("KIS API 호출 실패: {}", message);
                return new MarketDataDto.ChartResponse(false, message, null, List.of());
            }

            // StockInfo 생성
            String stockName = response.output1() != null ? response.output1().htsKorIsnm() : stockCode;
            MarketDataDto.StockInfo stockInfo = new MarketDataDto.StockInfo(stockCode, stockName != null ? stockName : stockCode);

            // DailyPrice 리스트 변환
            List<MarketDataDto.DailyPrice> dailyPrices = response.output2() != null ?
                    response.output2().stream()
                            .map(output2 -> new MarketDataDto.DailyPrice(
                                    output2.stckBsopDate(),
                                    output2.stckOprc(),
                                    output2.stckHgpr(),
                                    output2.stckLwpr(),
                                    output2.stckClpr(),
                                    output2.acmlVol()
                            ))
                            .collect(Collectors.toList()) :
                    List.of();

            log.info("KIS API 차트 데이터 조회 완료: {} 건", dailyPrices.size());
            return new MarketDataDto.ChartResponse(true, "성공", stockInfo, dailyPrices);

        } catch (Exception e) {
            log.error("KIS API 차트 데이터 조회 실패: {} - {}", stockCode, e.getMessage());
            return new MarketDataDto.ChartResponse(false, "시스템 오류: " + e.getMessage(), null, List.of());
        }
    }

    @Override
    public String getStockName(String stockCode) {
        try {
            LocalDate today = LocalDate.now();
            MarketDataDto.ChartResponse response = getDailyChartData(stockCode, today.minusDays(1), today);

            if (response.success() && response.stockInfo() != null) {
                return response.stockInfo().stockName();
            }

        } catch (Exception e) {
            log.debug("종목명 조회 실패: {} - {}", stockCode, e.getMessage());
        }

        return stockCode;
    }

    @Override
    public boolean isValidStock(String stockCode) {
        if (stockCode == null || stockCode.length() != 6) {
            return false;
        }

        try {
            LocalDate today = LocalDate.now();
            MarketDataDto.ChartResponse response = getDailyChartData(stockCode, today.minusDays(1), today);
            boolean isValid = response.success() && !response.dailyPrices().isEmpty();

            log.debug("종목코드 유효성 검증: {} -> {}", stockCode, isValid);
            return isValid;

        } catch (Exception e) {
            log.debug("종목코드 유효성 검증 실패: {} - {}", stockCode, e.getMessage());
            return false;
        }
    }
}