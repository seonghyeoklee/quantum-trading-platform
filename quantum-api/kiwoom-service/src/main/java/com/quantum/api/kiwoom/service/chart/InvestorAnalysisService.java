package com.quantum.api.kiwoom.service.chart;

import com.quantum.api.kiwoom.client.KiwoomApiClient;
import com.quantum.api.kiwoom.dto.chart.investor.InvestorAnalysisRequest;
import com.quantum.api.kiwoom.dto.chart.investor.InvestorAnalysisResponse;
import com.quantum.api.kiwoom.service.KiwoomTokenCacheService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.time.LocalDate;

/**
 * 투자자기관별차트 서비스 (ka10060)
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class InvestorAnalysisService {
    
    private final KiwoomApiClient kiwoomApiClient;
    private final KiwoomTokenCacheService tokenService;
    
    /**
     * 투자자기관별차트 조회 (토큰 자동 처리)
     */
    public Mono<InvestorAnalysisResponse> getInvestorAnalysis(String stockCode, String baseDate, String periodType) {
        // 토큰 캐시 서비스에서 appkey를 받기 위해 환경변수 사용
        String appkey = System.getProperty("kiwoom.appkey", "default");
        return tokenService.getCachedToken(appkey)
                .map(cachedToken -> cachedToken.getToken())
                .flatMap(token -> getInvestorAnalysisWithToken(token, stockCode, baseDate, periodType));
    }
    
    /**
     * 투자자기관별차트 조회 (토큰 직접 지정)
     */
    public Mono<InvestorAnalysisResponse> getInvestorAnalysisWithToken(String accessToken, String stockCode, String baseDate, String periodType) {
        InvestorAnalysisRequest request = InvestorAnalysisRequest.of(stockCode, baseDate, periodType);
        
        log.info("투자자기관별차트 요청: 종목={}, 날짜={}, 기간={}", stockCode, baseDate, periodType);
        
        return kiwoomApiClient.callChartApi(accessToken, request, InvestorAnalysisResponse.class)
                .doOnSuccess(response -> {
                    if (response.isSuccess()) {
                        log.info("투자자기관별차트 조회 성공: 종목={}, 데이터 개수={}", 
                                stockCode, response.getInvestorDataCount());
                    } else {
                        log.warn("투자자기관별차트 조회 실패: {}", response.getErrorMessage());
                    }
                })
                .doOnError(error -> log.error("투자자기관별차트 API 호출 오류: 종목={}", stockCode, error));
    }
    
    /**
     * 투자자기관별차트 조회 (LocalDate)
     */
    public Mono<InvestorAnalysisResponse> getInvestorAnalysis(String stockCode, LocalDate baseDate, String periodType) {
        return getInvestorAnalysis(stockCode, baseDate.format(java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd")), periodType);
    }
    
    /**
     * 일별 투자자기관별차트 조회
     */
    public Mono<InvestorAnalysisResponse> getDailyInvestorAnalysis(String stockCode, String baseDate) {
        return getInvestorAnalysis(stockCode, baseDate, "D");
    }
    
    /**
     * 주별 투자자기관별차트 조회
     */
    public Mono<InvestorAnalysisResponse> getWeeklyInvestorAnalysis(String stockCode, String baseDate) {
        return getInvestorAnalysis(stockCode, baseDate, "W");
    }
    
    /**
     * 월별 투자자기관별차트 조회
     */
    public Mono<InvestorAnalysisResponse> getMonthlyInvestorAnalysis(String stockCode, String baseDate) {
        return getInvestorAnalysis(stockCode, baseDate, "M");
    }
    
    /**
     * 오늘 일별 투자자기관별차트 조회
     */
    public Mono<InvestorAnalysisResponse> getTodayInvestorAnalysis(String stockCode) {
        return getDailyInvestorAnalysis(stockCode, LocalDate.now().format(java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd")));
    }
    
    /**
     * 투자자기관별차트 조회 (연속 조회 지원)
     */
    public Mono<InvestorAnalysisResponse> getInvestorAnalysisWithContinuation(
            String stockCode, String baseDate, String periodType, String contYn, String nextKey) {
        String appkey = System.getProperty("kiwoom.appkey", "default");
        return tokenService.getCachedToken(appkey)
                .map(cachedToken -> cachedToken.getToken())
                .flatMap(token -> {
                    InvestorAnalysisRequest request = InvestorAnalysisRequest.of(stockCode, baseDate, periodType);
                    
                    log.info("투자자기관별차트 연속 요청: 종목={}, 날짜={}, 기간={}, 연속={}, 키={}", 
                            stockCode, baseDate, periodType, contYn, nextKey);
                    
                    return kiwoomApiClient.callChartApi(token, request, 
                            InvestorAnalysisResponse.class, contYn, nextKey);
                });
    }
    
    /**
     * 주요 투자자 데이터만 조회 (개인, 기관, 외국인)
     */
    public Mono<InvestorAnalysisResponse> getMajorInvestorAnalysis(String stockCode, String baseDate, String periodType) {
        return getInvestorAnalysis(stockCode, baseDate, periodType)
                .map(response -> {
                    if (response.hasInvestorData()) {
                        var majorData = response.getMajorInvestorData();
                        return InvestorAnalysisResponse.builder()
                                .stockCode(response.getStockCode())
                                .stockName(response.getStockName())
                                .baseDate(response.getBaseDate())
                                .periodType(response.getPeriodType())
                                .returnCode(response.getReturnCode())
                                .returnMsg(response.getReturnMsg())
                                .investorData(majorData)
                                .build();
                    }
                    return response;
                });
    }
    
    /**
     * 순매수 상위 N개 투자자 데이터 조회
     */
    public Mono<InvestorAnalysisResponse> getTopNetBuyInvestors(String stockCode, String baseDate, String periodType, int topCount) {
        return getInvestorAnalysis(stockCode, baseDate, periodType)
                .map(response -> {
                    if (response.hasInvestorData()) {
                        var topData = response.getTopNetBuyInvestors(topCount);
                        return InvestorAnalysisResponse.builder()
                                .stockCode(response.getStockCode())
                                .stockName(response.getStockName())
                                .baseDate(response.getBaseDate())
                                .periodType(response.getPeriodType())
                                .returnCode(response.getReturnCode())
                                .returnMsg(response.getReturnMsg())
                                .investorData(topData)
                                .build();
                    }
                    return response;
                });
    }
}
