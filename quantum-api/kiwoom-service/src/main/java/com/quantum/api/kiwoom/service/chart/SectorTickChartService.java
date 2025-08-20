package com.quantum.api.kiwoom.service.chart;

import com.quantum.api.kiwoom.client.KiwoomApiClient;
import com.quantum.api.kiwoom.dto.chart.sector.SectorTickChartRequest;
import com.quantum.api.kiwoom.dto.chart.sector.SectorTickChartResponse;
import com.quantum.api.kiwoom.service.KiwoomTokenCacheService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

/**
 * 업종틱차트 서비스
 * 키움증권 업종틱차트조회요청 (ka20004) 처리
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class SectorTickChartService {
    
    private final KiwoomApiClient kiwoomApiClient;
    private final KiwoomTokenCacheService tokenCacheService;
    
    /**
     * 업종틱차트 데이터 조회 (토큰 자동 관리)
     */
    public Mono<SectorTickChartResponse> getSectorTickChart(String sectorCode, String baseDate) {
        log.info("업종틱차트 조회 시작 - 업종: {}, 기준일: {}", sectorCode, baseDate);
        
        SectorTickChartRequest request = SectorTickChartRequest.of(sectorCode, baseDate);
        request.validate();
        
        return getTokenAndCallApi(request)
                .doOnSuccess(response -> {
                    if (response != null && response.isSuccess()) {
                        log.info("업종틱차트 조회 성공 - 업종: {} ({}), 데이터 수: {}, 총 거래대금: {}", 
                                sectorCode, response.getSectorDisplayName(), 
                                response.getDataSize(), response.getTotalTradeAmount());
                    } else {
                        log.warn("업종틱차트 조회 실패 - 업종: {}, 오류: {}", 
                                sectorCode, response != null ? response.getErrorMessage() : "null response");
                    }
                })
                .onErrorMap(error -> {
                    log.error("업종틱차트 조회 예외 - 업종: {}", sectorCode, error);
                    return new RuntimeException("업종틱차트 조회에 실패했습니다: " + error.getMessage(), error);
                });
    }
    
    /**
     * 업종틱차트 데이터 조회 (LocalDate 기준일)
     */
    public Mono<SectorTickChartResponse> getSectorTickChart(String sectorCode, LocalDate baseDate) {
        String baseDateStr = baseDate.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        return getSectorTickChart(sectorCode, baseDateStr);
    }
    
    /**
     * 오늘 기준 업종틱차트 데이터 조회
     */
    public Mono<SectorTickChartResponse> getSectorTickChartToday(String sectorCode) {
        return getSectorTickChart(sectorCode, LocalDate.now());
    }
    
    /**
     * 업종틱차트 데이터 조회 (연속조회 지원)
     */
    public Mono<SectorTickChartResponse> getSectorTickChart(String sectorCode, String baseDate, String contYn, String nextKey) {
        log.info("업종틱차트 연속조회 - 업종: {}, 기준일: {}, 연속: {}", sectorCode, baseDate, contYn);
        
        SectorTickChartRequest request = SectorTickChartRequest.of(sectorCode, baseDate);
        request.validate();
        
        return getTokenAndCallApi(request, contYn, nextKey);
    }
    
    /**
     * 특정 토큰으로 업종틱차트 조회 (테스트용)
     */
    public Mono<SectorTickChartResponse> getSectorTickChartWithToken(String accessToken, String sectorCode, String baseDate) {
        log.debug("지정 토큰으로 업종틱차트 조회 - 업종: {}, 기준일: {}", sectorCode, baseDate);
        
        SectorTickChartRequest request = SectorTickChartRequest.of(sectorCode, baseDate);
        request.validate();
        
        return kiwoomApiClient.callChartApi(accessToken, request, SectorTickChartResponse.class);
    }
    
    /**
     * 업종틱차트 조회 (수정주가구분 지정)
     */
    public Mono<SectorTickChartResponse> getSectorTickChart(String sectorCode, String baseDate, String updStkpcTp) {
        log.info("업종틱차트 조회 (수정주가구분) - 업종: {}, 기준일: {}, 수정주가: {}", 
                sectorCode, baseDate, updStkpcTp);
        
        SectorTickChartRequest request = SectorTickChartRequest.builder()
                .sectorCode(sectorCode)
                .baseDate(baseDate)
                .updStkpcTp(updStkpcTp)
                .build();
        request.validate();
        
        return getTokenAndCallApi(request);
    }
    
    // ===== 편의 메서드 - 주요 업종별 =====
    
    /**
     * 코스피 업종틱차트 조회
     */
    public Mono<SectorTickChartResponse> getKospiTickChart(String baseDate) {
        return getSectorTickChart("0001", baseDate);
    }
    
    /**
     * 코스닥 업종틱차트 조회
     */
    public Mono<SectorTickChartResponse> getKosdaqTickChart(String baseDate) {
        return getSectorTickChart("1001", baseDate);
    }
    
    /**
     * 코스피200 업종틱차트 조회
     */
    public Mono<SectorTickChartResponse> getKospi200TickChart(String baseDate) {
        return getSectorTickChart("2001", baseDate);
    }
    
    /**
     * 오늘 기준 코스피 업종틱차트 조회
     */
    public Mono<SectorTickChartResponse> getKospiTickChartToday() {
        return getKospiTickChart(LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd")));
    }
    
    /**
     * 오늘 기준 코스닥 업종틱차트 조회
     */
    public Mono<SectorTickChartResponse> getKosdaqTickChartToday() {
        return getKosdaqTickChart(LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd")));
    }
    
    /**
     * 오늘 기준 코스피200 업종틱차트 조회
     */
    public Mono<SectorTickChartResponse> getKospi200TickChartToday() {
        return getKospi200TickChart(LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd")));
    }
    
    /**
     * 정규 거래시간 업종 틱차트 조회
     */
    public Mono<SectorTickChartResponse> getRegularTradingSectorTickChart(String sectorCode, String baseDate) {
        return getSectorTickChart(sectorCode, baseDate)
                .map(response -> {
                    if (response.isSuccess() && !response.isEmpty()) {
                        // 정규 거래시간 데이터만 필터링
                        response.setChartData(response.getRegularTradingHoursData());
                    }
                    return response;
                });
    }
    
    /**
     * 고활성 업종 틱차트 조회 (거래대금 기준)
     */
    public Mono<SectorTickChartResponse> getHighActivitySectorTickChart(String sectorCode, String baseDate) {
        return getSectorTickChart(sectorCode, baseDate)
                .map(response -> {
                    if (response.isSuccess() && !response.isEmpty()) {
                        // 고활성 데이터만 필터링
                        response.setChartData(response.getHighActivitySectorTicksData());
                    }
                    return response;
                });
    }
    
    /**
     * 고변동성 업종 틱차트 조회
     */
    public Mono<SectorTickChartResponse> getHighVolatilitySectorTickChart(String sectorCode, String baseDate) {
        return getSectorTickChart(sectorCode, baseDate)
                .map(response -> {
                    if (response.isSuccess() && !response.isEmpty()) {
                        // 고변동성 데이터만 필터링
                        response.setChartData(response.getHighVolatilitySectorTicksData());
                    }
                    return response;
                });
    }
    
    /**
     * 상승 업종 틱만 조회
     */
    public Mono<SectorTickChartResponse> getRisingSectorTickChart(String sectorCode, String baseDate) {
        return getSectorTickChart(sectorCode, baseDate)
                .map(response -> {
                    if (response.isSuccess() && !response.isEmpty()) {
                        // 상승 틱만 필터링
                        response.setChartData(response.getRisingSectorTicksData());
                    }
                    return response;
                });
    }
    
    /**
     * 하락 업종 틱만 조회
     */
    public Mono<SectorTickChartResponse> getFallingSectorTickChart(String sectorCode, String baseDate) {
        return getSectorTickChart(sectorCode, baseDate)
                .map(response -> {
                    if (response.isSuccess() && !response.isEmpty()) {
                        // 하락 틱만 필터링
                        response.setChartData(response.getFallingSectorTicksData());
                    }
                    return response;
                });
    }
    
    // ===== Private Methods =====
    
    /**
     * 토큰 조회 및 API 호출
     */
    private Mono<SectorTickChartResponse> getTokenAndCallApi(SectorTickChartRequest request) {
        return getTokenAndCallApi(request, "N", "");
    }
    
    /**
     * 토큰 조회 및 API 호출 (연속조회 지원)
     */
    private Mono<SectorTickChartResponse> getTokenAndCallApi(SectorTickChartRequest request, String contYn, String nextKey) {
        // 환경변수에서 설정된 기본 키를 사용하여 캐시된 토큰 조회
        return tokenCacheService.getCachedToken("default")
                .switchIfEmpty(Mono.error(new IllegalStateException("캐시된 토큰을 찾을 수 없습니다")))
                .flatMap(cachedToken -> {
                    if (cachedToken.isExpired()) {
                        return Mono.error(new IllegalStateException("토큰이 만료되었습니다"));
                    }
                    
                    String accessToken = cachedToken.getToken();
                    return kiwoomApiClient.callChartApi(accessToken, request, SectorTickChartResponse.class, contYn, nextKey);
                });
    }
}