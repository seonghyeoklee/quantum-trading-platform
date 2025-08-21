package com.quantum.api.kiwoom.service.sector;

import com.quantum.api.kiwoom.client.KiwoomApiClient;
import com.quantum.api.kiwoom.dto.sector.info.SectorCurrentPriceRequest;
import com.quantum.api.kiwoom.dto.sector.info.SectorCurrentPriceResponse;
import com.quantum.api.kiwoom.service.KiwoomTokenCacheService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

/**
 * 업종현재가요청 서비스 (ka20001)
 * 특정 업종의 현재가 정보 및 상위/하위 종목 조회
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class SectorCurrentPriceService {

    private final KiwoomApiClient kiwoomApiClient;
    private final KiwoomTokenCacheService tokenCacheService;

    /**
     * 업종 현재가 조회
     * 
     * @param sectorCode 업종코드 (3자리)
     * @param marketType 시장구분 (0:코스피, 1:코스닥, 2:코스피200)
     * @param searchScope 조회범위 (1:업종지수만, 2:업종지수+상위종목, 3:업종지수+하위종목)
     * @param stockCount 종목개수 (1-30)
     * @return 업종 현재가 정보
     */
    public Mono<SectorCurrentPriceResponse> getSectorCurrentPrice(
            String sectorCode, 
            String marketType, 
            String searchScope, 
            String stockCount) {
        
        log.info("업종현재가요청 시작 - 업종코드: {}, 시장구분: {}, 조회범위: {}, 종목개수: {}", 
                sectorCode, marketType, searchScope, stockCount);
        
        // 요청 객체 생성
        SectorCurrentPriceRequest request = SectorCurrentPriceRequest.builder()
                .sectorCode(sectorCode)
                .marketType(marketType)
                .searchScope(searchScope)
                .stockCount(stockCount)
                .build();
        
        // 요청 데이터 유효성 검증
        request.validate();
        
        return getTokenAndCallApi(request)
                .doOnSuccess(response -> {
                    if (response != null && response.isSuccess()) {
                        log.info("업종현재가요청 성공 - 업종코드: {}, 업종명: {}", 
                                sectorCode, 
                                response.getSectorInfo() != null ? response.getSectorInfo().getSectorName() : "N/A");
                    } else {
                        log.warn("업종현재가요청 응답 오류 - 업종코드: {}, 오류: {}", 
                                sectorCode, response != null ? response.getErrorMessage() : "null response");
                    }
                })
                .doOnError(error -> log.error("업종현재가요청 실패 - 업종코드: {}", sectorCode, error));
    }

    /**
     * 업종 지수만 조회 (관련 종목 없이)
     * 
     * @param sectorCode 업종코드
     * @param marketType 시장구분
     * @return 업종 지수 정보만
     */
    public Mono<SectorCurrentPriceResponse> getSectorIndexOnly(String sectorCode, String marketType) {
        return getSectorCurrentPrice(sectorCode, marketType, "1", "1");
    }

    /**
     * 업종 지수 + 상위 종목 조회
     * 
     * @param sectorCode 업종코드
     * @param marketType 시장구분
     * @param stockCount 상위 종목 개수 (1-30)
     * @return 업종 정보 + 상위 종목 목록
     */
    public Mono<SectorCurrentPriceResponse> getSectorWithTopStocks(
            String sectorCode, 
            String marketType, 
            int stockCount) {
        return getSectorCurrentPrice(sectorCode, marketType, "2", String.valueOf(stockCount));
    }

    /**
     * 업종 지수 + 하위 종목 조회
     * 
     * @param sectorCode 업종코드
     * @param marketType 시장구분
     * @param stockCount 하위 종목 개수 (1-30)
     * @return 업종 정보 + 하위 종목 목록
     */
    public Mono<SectorCurrentPriceResponse> getSectorWithBottomStocks(
            String sectorCode, 
            String marketType, 
            int stockCount) {
        return getSectorCurrentPrice(sectorCode, marketType, "3", String.valueOf(stockCount));
    }

    /**
     * 주요 업종 현재가 조회 (KOSPI 종합, KOSDAQ 종합, KOSPI200)
     * 
     * @param stockCount 관련 종목 개수
     * @return 주요 업종 현재가 정보 목록
     */
    public Mono<SectorCurrentPriceResponse> getMajorSectorCurrentPrice(String sectorCode, int stockCount) {
        String marketType;
        
        switch (sectorCode) {
            case "001": // KOSPI 종합
                marketType = "0";
                break;
            case "101": // KOSDAQ 종합  
                marketType = "1";
                break;
            case "201": // KOSPI200
                marketType = "2";
                break;
            default:
                return Mono.error(new IllegalArgumentException("지원하지 않는 주요 업종코드입니다: " + sectorCode));
        }
        
        return getSectorWithTopStocks(sectorCode, marketType, stockCount);
    }
    
    // ===== Private Methods =====
    
    /**
     * 토큰 조회 및 API 호출
     */
    private Mono<SectorCurrentPriceResponse> getTokenAndCallApi(SectorCurrentPriceRequest request) {
        return getTokenAndCallApi(request, "N", "");
    }
    
    /**
     * 토큰 조회 및 API 호출 (연속조회 지원)
     */
    private Mono<SectorCurrentPriceResponse> getTokenAndCallApi(
            SectorCurrentPriceRequest request, 
            String contYn, 
            String nextKey) {
        // 환경변수에서 설정된 기본 키를 사용하여 캐시된 토큰 조회
        return tokenCacheService.getCachedToken("default")
                .switchIfEmpty(Mono.error(new IllegalStateException("캐시된 토큰을 찾을 수 없습니다")))
                .flatMap(cachedToken -> {
                    if (cachedToken.isExpired()) {
                        return Mono.error(new IllegalStateException("토큰이 만료되었습니다"));
                    }
                    
                    String accessToken = cachedToken.getToken();
                    return kiwoomApiClient.callSectorApi(
                            accessToken, 
                            request, 
                            SectorCurrentPriceResponse.class, 
                            contYn, 
                            nextKey);
                });
    }
}