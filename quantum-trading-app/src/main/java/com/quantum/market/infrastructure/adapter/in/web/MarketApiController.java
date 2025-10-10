package com.quantum.market.infrastructure.adapter.in.web;

import com.quantum.kis.application.port.out.KisApiPort;
import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.dto.IndexPriceResponse;
import com.quantum.kis.exception.KisApiException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * 시장 데이터 REST API 컨트롤러
 * Inbound Adapter for Web Interface (Hexagonal Architecture)
 *
 * 역할:
 * - 헤더에 표시될 실시간 시장 지수 정보 제공
 * - KOSPI, KOSDAQ, USD/KRW 데이터 조회
 */
@Slf4j
@RestController
@RequestMapping("/api/market")
@RequiredArgsConstructor
public class MarketApiController {

    private final KisApiPort kisApiPort;

    /**
     * 시장 지수 조회 (KOSPI, KOSDAQ, USD/KRW)
     * KIS API 실시간 데이터 제공
     */
    @GetMapping("/indices")
    public Map<String, Object> getMarketIndices() {
        log.debug("시장 지수 조회 요청");

        Map<String, Object> response = new HashMap<>();

        try {
            // KOSPI 조회 (지수코드: 0001)
            Map<String, Object> kospiData = getIndexData("KOSPI", "0001");

            // KOSDAQ 조회 (지수코드: 1001)
            Map<String, Object> kosdaqData = getIndexData("KOSDAQ", "1001");

            // USD/KRW는 임시로 고정값 사용 (환율 API 별도 필요)
            Map<String, Object> usdkrwData = getFixedExchangeRate();

            response.put("success", true);
            response.put("timestamp", LocalDateTime.now());
            response.put("data", Map.of(
                    "kospi", kospiData,
                    "kosdaq", kosdaqData,
                    "usdkrw", usdkrwData
            ));

        } catch (KisApiException e) {
            log.error("KIS API 조회 실패", e);
            response.put("success", false);
            response.put("error", e.getMessage());
            response.put("timestamp", LocalDateTime.now());
        } catch (Exception e) {
            log.error("시장 지수 조회 중 예외 발생", e);
            response.put("success", false);
            response.put("error", "시장 지수 조회 중 오류가 발생했습니다");
            response.put("timestamp", LocalDateTime.now());
        }

        return response;
    }

    /**
     * KIS API로 지수 데이터 조회
     */
    private Map<String, Object> getIndexData(String name, String indexCode) {
        IndexPriceResponse response = kisApiPort.getIndexPrice(KisEnvironment.PROD, indexCode);

        if (response == null || response.output() == null) {
            log.warn("{} 데이터 없음", name);
            return getDefaultIndexData(name);
        }

        IndexPriceResponse.Output output = response.output();

        // KIS API 응답 파싱
        double currentPrice = parseDouble(output.currentPrice(), 0.0);
        double priceChange = parseDouble(output.priceChange(), 0.0);
        double changeRate = parseDouble(output.changeRate(), 0.0);
        boolean isPositive = output.isPositive();

        return Map.of(
                "name", name,
                "value", BigDecimal.valueOf(currentPrice).setScale(2, RoundingMode.HALF_UP),
                "change", BigDecimal.valueOf(priceChange).setScale(2, RoundingMode.HALF_UP),
                "changePercent", BigDecimal.valueOf(changeRate).setScale(2, RoundingMode.HALF_UP),
                "isPositive", isPositive
        );
    }

    /**
     * 임시 환율 데이터 (고정값)
     */
    private Map<String, Object> getFixedExchangeRate() {
        return Map.of(
                "name", "USD/KRW",
                "value", BigDecimal.valueOf(1340.50).setScale(2, RoundingMode.HALF_UP),
                "change", BigDecimal.valueOf(5.30).setScale(2, RoundingMode.HALF_UP),
                "changePercent", BigDecimal.valueOf(0.40).setScale(2, RoundingMode.HALF_UP),
                "isPositive", true
        );
    }

    /**
     * 기본 지수 데이터 (API 실패 시 폴백)
     */
    private Map<String, Object> getDefaultIndexData(String name) {
        return Map.of(
                "name", name,
                "value", BigDecimal.valueOf(0.0),
                "change", BigDecimal.valueOf(0.0),
                "changePercent", BigDecimal.valueOf(0.0),
                "isPositive", true
        );
    }

    /**
     * 문자열을 double로 안전하게 변환
     */
    private double parseDouble(String value, double defaultValue) {
        try {
            return value != null && !value.isBlank() ? Double.parseDouble(value) : defaultValue;
        } catch (NumberFormatException e) {
            log.warn("숫자 변환 실패: {}", value);
            return defaultValue;
        }
    }
}
