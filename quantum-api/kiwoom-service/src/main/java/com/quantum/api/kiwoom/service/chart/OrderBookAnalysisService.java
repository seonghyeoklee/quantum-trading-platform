package com.quantum.api.kiwoom.service.chart;

import com.quantum.api.kiwoom.client.KiwoomApiClient;
import com.quantum.api.kiwoom.dto.chart.analysis.OrderBookAnalysisRequest;
import com.quantum.api.kiwoom.dto.chart.analysis.OrderBookAnalysisResponse;
import com.quantum.api.kiwoom.service.KiwoomTokenCacheService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.time.LocalDate;

/**
 * 거래원매물대분석 서비스 (ka10043)
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class OrderBookAnalysisService {
    
    private final KiwoomApiClient kiwoomApiClient;
    private final KiwoomTokenCacheService tokenService;
    
    /**
     * 거래원매물대분석 조회 (토큰 자동 처리)
     */
    public Mono<OrderBookAnalysisResponse> getOrderBookAnalysis(String stockCode, String baseDate) {
        String appkey = System.getProperty("kiwoom.appkey", "default");
        return tokenService.getCachedToken(appkey)
                .map(cachedToken -> cachedToken.getToken())
                .flatMap(token -> getOrderBookAnalysisWithToken(token, stockCode, baseDate));
    }
    
    /**
     * 거래원매물대분석 조회 (토큰 직접 지정)
     */
    public Mono<OrderBookAnalysisResponse> getOrderBookAnalysisWithToken(String accessToken, String stockCode, String baseDate) {
        OrderBookAnalysisRequest request = OrderBookAnalysisRequest.of(stockCode, baseDate);
        
        log.info("거래원매물대분석 요청: 종목={}, 날짜={}", stockCode, baseDate);
        
        return kiwoomApiClient.callStockInfoApi(accessToken, request, OrderBookAnalysisResponse.class)
                .doOnSuccess(response -> {
                    if (response.isSuccess()) {
                        log.info("거래원매물대분석 조회 성공: 종목={}, 데이터 개수={}", 
                                stockCode, response.getOrderBookDataCount());
                    } else {
                        log.warn("거래원매물대분석 조회 실패: {}", response.getErrorMessage());
                    }
                })
                .doOnError(error -> log.error("거래원매물대분석 API 호출 오류: 종목={}", stockCode, error));
    }
    
    /**
     * 거래원매물대분석 조회 (LocalDate)
     */
    public Mono<OrderBookAnalysisResponse> getOrderBookAnalysis(String stockCode, LocalDate baseDate) {
        return getOrderBookAnalysis(stockCode, baseDate.format(java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd")));
    }
    
    /**
     * 오늘 거래원매물대분석 조회
     */
    public Mono<OrderBookAnalysisResponse> getTodayOrderBookAnalysis(String stockCode) {
        return getOrderBookAnalysis(stockCode, LocalDate.now());
    }
    
    /**
     * 거래원매물대분석 조회 (연속 조회 지원)
     */
    public Mono<OrderBookAnalysisResponse> getOrderBookAnalysisWithContinuation(
            String stockCode, String baseDate, String contYn, String nextKey) {
        String appkey = System.getProperty("kiwoom.appkey", "default");
        return tokenService.getCachedToken(appkey)
                .map(cachedToken -> cachedToken.getToken())
                .flatMap(token -> {
                    OrderBookAnalysisRequest request = OrderBookAnalysisRequest.of(stockCode, baseDate);
                    
                    log.info("거래원매물대분석 연속 요청: 종목={}, 날짜={}, 연속={}, 키={}", 
                            stockCode, baseDate, contYn, nextKey);
                    
                    return kiwoomApiClient.callStockInfoApi(token, request, 
                            OrderBookAnalysisResponse.class, contYn, nextKey);
                });
    }
    
    /**
     * 상위 N개 거래원 매물대 데이터 조회
     */
    public Mono<OrderBookAnalysisResponse> getTopOrderBookAnalysis(String stockCode, String baseDate, int topCount) {
        return getOrderBookAnalysis(stockCode, baseDate)
                .map(response -> {
                    if (response.hasOrderBookData()) {
                        var topData = response.getTopOrderBookData(topCount);
                        return OrderBookAnalysisResponse.builder()
                                .stockCode(response.getStockCode())
                                .stockName(response.getStockName())
                                .baseDate(response.getBaseDate())
                                .returnCode(response.getReturnCode())
                                .returnMsg(response.getReturnMsg())
                                .orderBookData(topData)
                                .build();
                    }
                    return response;
                });
    }
}
