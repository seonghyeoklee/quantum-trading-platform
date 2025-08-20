package com.quantum.api.kiwoom.service.chart;

import com.quantum.api.kiwoom.client.KiwoomApiClient;
import com.quantum.api.kiwoom.dto.chart.realtime.TickChartRequest;
import com.quantum.api.kiwoom.dto.chart.realtime.TickChartResponse;
import com.quantum.api.kiwoom.service.KiwoomTokenCacheService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

/**
 * 틱차트 서비스
 * 키움증권 주식틱차트조회요청 (ka10079) 처리
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class TickChartService {
    
    private final KiwoomApiClient kiwoomApiClient;
    private final KiwoomTokenCacheService tokenCacheService;
    
    /**
     * 틱차트 데이터 조회 (토큰 자동 관리)
     */
    public Mono<TickChartResponse> getTickChart(String stockCode, String baseDate) {
        log.info("틱차트 조회 시작 - 종목: {}, 기준일: {}", stockCode, baseDate);
        
        TickChartRequest request = TickChartRequest.of(stockCode, baseDate);
        request.validate();
        
        return getTokenAndCallApi(request)
                .doOnSuccess(response -> {
                    if (response != null && response.isSuccess()) {
                        log.info("틱차트 조회 성공 - 종목: {}, 데이터 수: {}, 총 거래량: {}", 
                                stockCode, response.getDataSize(), response.getTotalTradeQuantity());
                    } else {
                        log.warn("틱차트 조회 실패 - 종목: {}, 오류: {}", 
                                stockCode, response != null ? response.getErrorMessage() : "null response");
                    }
                })
                .onErrorMap(error -> {
                    log.error("틱차트 조회 예외 - 종목: {}", stockCode, error);
                    return new RuntimeException("틱차트 조회에 실패했습니다: " + error.getMessage(), error);
                });
    }
    
    /**
     * 틱차트 데이터 조회 (LocalDate 기준일)
     */
    public Mono<TickChartResponse> getTickChart(String stockCode, LocalDate baseDate) {
        String baseDateStr = baseDate.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        return getTickChart(stockCode, baseDateStr);
    }
    
    /**
     * 오늘 기준 틱차트 데이터 조회
     */
    public Mono<TickChartResponse> getTickChartToday(String stockCode) {
        return getTickChart(stockCode, LocalDate.now());
    }
    
    /**
     * 틱차트 데이터 조회 (연속조회 지원)
     */
    public Mono<TickChartResponse> getTickChart(String stockCode, String baseDate, String contYn, String nextKey) {
        log.info("틱차트 연속조회 - 종목: {}, 기준일: {}, 연속: {}", stockCode, baseDate, contYn);
        
        TickChartRequest request = TickChartRequest.of(stockCode, baseDate);
        request.validate();
        
        return getTokenAndCallApi(request, contYn, nextKey);
    }
    
    /**
     * 특정 토큰으로 틱차트 조회 (테스트용)
     */
    public Mono<TickChartResponse> getTickChartWithToken(String accessToken, String stockCode, String baseDate) {
        log.debug("지정 토큰으로 틱차트 조회 - 종목: {}, 기준일: {}", stockCode, baseDate);
        
        TickChartRequest request = TickChartRequest.of(stockCode, baseDate);
        request.validate();
        
        return kiwoomApiClient.callChartApi(accessToken, request, TickChartResponse.class);
    }
    
    /**
     * 틱차트 조회 (수정주가구분 지정)
     */
    public Mono<TickChartResponse> getTickChart(String stockCode, String baseDate, String updStkpcTp) {
        log.info("틱차트 조회 (수정주가구분) - 종목: {}, 기준일: {}, 수정주가: {}", 
                stockCode, baseDate, updStkpcTp);
        
        TickChartRequest request = TickChartRequest.builder()
                .stockCode(stockCode)
                .baseDate(baseDate)
                .updStkpcTp(updStkpcTp)
                .build();
        request.validate();
        
        return getTokenAndCallApi(request);
    }
    
    /**
     * 실시간 틱 데이터 조회 (정규 거래시간만)
     */
    public Mono<TickChartResponse> getRegularTradingTickChart(String stockCode, String baseDate) {
        return getTickChart(stockCode, baseDate)
                .map(response -> {
                    if (response.isSuccess() && !response.isEmpty()) {
                        // 정규 거래시간 데이터만 필터링
                        response.setChartData(response.getRegularTradingHoursData());
                    }
                    return response;
                });
    }
    
    /**
     * 대량 거래 틱 데이터 조회 (10,000주 이상)
     */
    public Mono<TickChartResponse> getLargeVolumeTickChart(String stockCode, String baseDate) {
        return getTickChart(stockCode, baseDate)
                .map(response -> {
                    if (response.isSuccess() && !response.isEmpty()) {
                        // 대량 거래 데이터만 필터링
                        response.setChartData(response.getLargeVolumeTicksData());
                    }
                    return response;
                });
    }
    
    /**
     * 상승 틱만 조회
     */
    public Mono<TickChartResponse> getRisingTickChart(String stockCode, String baseDate) {
        return getTickChart(stockCode, baseDate)
                .map(response -> {
                    if (response.isSuccess() && !response.isEmpty()) {
                        // 상승 틱만 필터링
                        response.setChartData(response.getRisingTicksData());
                    }
                    return response;
                });
    }
    
    /**
     * 하락 틱만 조회
     */
    public Mono<TickChartResponse> getFallingTickChart(String stockCode, String baseDate) {
        return getTickChart(stockCode, baseDate)
                .map(response -> {
                    if (response.isSuccess() && !response.isEmpty()) {
                        // 하락 틱만 필터링
                        response.setChartData(response.getFallingTicksData());
                    }
                    return response;
                });
    }
    
    // ===== Private Methods =====
    
    /**
     * 토큰 조회 및 API 호출
     */
    private Mono<TickChartResponse> getTokenAndCallApi(TickChartRequest request) {
        return getTokenAndCallApi(request, "N", "");
    }
    
    /**
     * 토큰 조회 및 API 호출 (연속조회 지원)
     */
    private Mono<TickChartResponse> getTokenAndCallApi(TickChartRequest request, String contYn, String nextKey) {
        // 환경변수에서 설정된 기본 키를 사용하여 캐시된 토큰 조회
        return tokenCacheService.getCachedToken("default")
                .switchIfEmpty(Mono.error(new IllegalStateException("캐시된 토큰을 찾을 수 없습니다")))
                .flatMap(cachedToken -> {
                    if (cachedToken.isExpired()) {
                        return Mono.error(new IllegalStateException("토큰이 만료되었습니다"));
                    }
                    
                    String accessToken = cachedToken.getToken();
                    return kiwoomApiClient.callChartApi(accessToken, request, TickChartResponse.class, contYn, nextKey);
                });
    }
}