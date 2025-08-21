package com.quantum.api.kiwoom.service.chart;

import com.quantum.api.kiwoom.client.KiwoomApiClient;
import com.quantum.api.kiwoom.dto.chart.timeseries.DailyChartRequest;
import com.quantum.api.kiwoom.dto.chart.timeseries.DailyChartResponse;
import com.quantum.api.kiwoom.service.KiwoomTokenCacheService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

/**
 * 일봉 차트 서비스
 * 키움증권 주식일봉차트조회요청 (ka10081) 처리
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class DailyChartService {
    
    private final KiwoomApiClient kiwoomApiClient;
    private final KiwoomTokenCacheService tokenCacheService;
    
    /**
     * 일봉 차트 데이터 조회 (토큰 자동 관리)
     */
    public Mono<DailyChartResponse> getDailyChart(String stockCode, String baseDate) {
        log.info("일봉 차트 조회 시작 - 종목: {}, 기준일: {}", stockCode, baseDate);
        
        DailyChartRequest request = DailyChartRequest.of(stockCode, baseDate);
        request.validate();
        
        return getTokenAndCallApi(request)
                .doOnSuccess(response -> {
                    if (response != null && response.isSuccess()) {
                        log.info("일봉 차트 조회 성공 - 종목: {}, 데이터 수: {}", 
                                stockCode, response.getDataSize());
                    } else {
                        log.warn("일봉 차트 조회 실패 - 종목: {}, 오류: {}", 
                                stockCode, response != null ? response.getErrorMessage() : "null response");
                    }
                })
                .onErrorMap(error -> {
                    log.error("일봉 차트 조회 예외 - 종목: {}", stockCode, error);
                    return new RuntimeException("일봉 차트 조회에 실패했습니다: " + error.getMessage(), error);
                });
    }
    
    /**
     * 일봉 차트 데이터 조회 (LocalDate 기준일)
     */
    public Mono<DailyChartResponse> getDailyChart(String stockCode, LocalDate baseDate) {
        String baseDateStr = baseDate.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        return getDailyChart(stockCode, baseDateStr);
    }
    
    /**
     * 오늘 기준 일봉 차트 데이터 조회
     */
    public Mono<DailyChartResponse> getDailyChartToday(String stockCode) {
        return getDailyChart(stockCode, LocalDate.now());
    }
    
    /**
     * 일봉 차트 데이터 조회 (연속조회 지원)
     */
    public Mono<DailyChartResponse> getDailyChart(String stockCode, String baseDate, String contYn, String nextKey) {
        log.info("일봉 차트 연속조회 - 종목: {}, 기준일: {}, 연속: {}", stockCode, baseDate, contYn);
        
        DailyChartRequest request = DailyChartRequest.of(stockCode, baseDate);
        request.validate();
        
        return getTokenAndCallApi(request, contYn, nextKey);
    }
    
    /**
     * 특정 토큰으로 일봉 차트 조회 (테스트용)
     */
    public Mono<DailyChartResponse> getDailyChartWithToken(String accessToken, String stockCode, String baseDate) {
        log.debug("지정 토큰으로 일봉 차트 조회 - 종목: {}, 기준일: {}", stockCode, baseDate);
        
        DailyChartRequest request = DailyChartRequest.of(stockCode, baseDate);
        request.validate();
        
        return kiwoomApiClient.callChartApi(accessToken, request, DailyChartResponse.class);
    }
    
    /**
     * 일봉 차트 조회 (수정주가구분 지정)
     */
    public Mono<DailyChartResponse> getDailyChart(String stockCode, String baseDate, String updStkpcTp) {
        log.info("일봉 차트 조회 (수정주가구분) - 종목: {}, 기준일: {}, 수정주가: {}", 
                stockCode, baseDate, updStkpcTp);
        
        DailyChartRequest request = DailyChartRequest.builder()
                .stockCode(stockCode)
                .baseDate(baseDate)
                .updStkpcTp(updStkpcTp)
                .build();
        request.validate();
        
        return getTokenAndCallApi(request);
    }
    
    // ===== Private Methods =====
    
    /**
     * 토큰 조회 및 API 호출
     */
    private Mono<DailyChartResponse> getTokenAndCallApi(DailyChartRequest request) {
        return getTokenAndCallApi(request, "N", "");
    }
    
    /**
     * 토큰 조회 및 API 호출 (연속조회 지원)
     */
    private Mono<DailyChartResponse> getTokenAndCallApi(DailyChartRequest request, String contYn, String nextKey) {
        // 환경변수에서 설정된 기본 키를 사용하여 캐시된 토큰 조회
        return tokenCacheService.getCachedToken("default")
                .switchIfEmpty(Mono.error(new IllegalStateException("캐시된 토큰을 찾을 수 없습니다")))
                .flatMap(cachedToken -> {
                    if (cachedToken.isExpired()) {
                        return Mono.error(new IllegalStateException("토큰이 만료되었습니다"));
                    }
                    
                    String accessToken = cachedToken.getToken();
                    return kiwoomApiClient.callChartApi(accessToken, request, DailyChartResponse.class, contYn, nextKey);
                });
    }
    
    /**
     * 요청 검증
     */
    private void validateRequest(String stockCode, String baseDate) {
        if (stockCode == null || stockCode.trim().isEmpty()) {
            throw new IllegalArgumentException("종목코드는 필수입니다");
        }
        
        if (baseDate == null || baseDate.length() != 8) {
            throw new IllegalArgumentException("기준일자는 YYYYMMDD 형식이어야 합니다");
        }
        
        try {
            LocalDate.parse(baseDate, DateTimeFormatter.ofPattern("yyyyMMdd"));
        } catch (Exception e) {
            throw new IllegalArgumentException("기준일자 형식이 올바르지 않습니다: " + baseDate);
        }
    }
}