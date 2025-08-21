package com.quantum.api.kiwoom.service.sector;

import com.quantum.api.kiwoom.client.KiwoomApiClient;
import com.quantum.api.kiwoom.dto.sector.info.SectorStockPricesRequest;
import com.quantum.api.kiwoom.dto.sector.info.SectorStockPricesResponse;
import com.quantum.api.kiwoom.service.KiwoomTokenCacheService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

/**
 * 업종별주가요청 서비스 (ka20002)
 * 특정 업종에 속한 종목들의 주가 정보 조회
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class SectorStockPricesService {

    private final KiwoomApiClient kiwoomApiClient;
    private final KiwoomTokenCacheService tokenCacheService;

    /**
     * 업종별 종목 주가 조회
     * 
     * @param sectorCode 업종코드 (3자리)
     * @param marketType 시장구분 (0:코스피, 1:코스닥, 2:코스피200)
     * @param sortType 정렬기준 (1:시가총액순, 2:거래대금순, 3:등락률순, 4:종목명순)
     * @param sortOrder 정렬방향 (1:내림차순, 2:오름차순)
     * @param stockCount 조회개수 (1-100)
     * @param startIndex 조회시작번호 (페이징용, 1부터 시작)
     * @return 업종별 종목 주가 정보
     */
    public Mono<SectorStockPricesResponse> getSectorStockPrices(
            String sectorCode, 
            String marketType, 
            String sortType, 
            String sortOrder, 
            String stockCount, 
            String startIndex) {
        
        log.info("업종별주가요청 시작 - 업종코드: {}, 시장구분: {}, 정렬: {}({}), 개수: {}, 시작: {}", 
                sectorCode, marketType, sortType, sortOrder, stockCount, startIndex);
        
        // 요청 객체 생성
        SectorStockPricesRequest request = SectorStockPricesRequest.builder()
                .sectorCode(sectorCode)
                .marketType(marketType)
                .sortType(sortType)
                .sortOrder(sortOrder)
                .stockCount(stockCount)
                .startIndex(startIndex)
                .build();
        
        // 요청 데이터 유효성 검증
        request.validate();
        
        return getTokenAndCallApi(request)
                .doOnSuccess(response -> {
                    if (response != null && response.isSuccess()) {
                        int dataSize = response.getStockPrices() != null ? response.getStockPrices().size() : 0;
                        log.info("업종별주가요청 성공 - 업종코드: {}, 업종명: {}, 데이터 수: {}", 
                                sectorCode, 
                                response.getSectorSummary() != null ? response.getSectorSummary().getSectorName() : "N/A",
                                dataSize);
                    } else {
                        log.warn("업종별주가요청 응답 오류 - 업종코드: {}, 오류: {}", 
                                sectorCode, response != null ? response.getErrorMessage() : "null response");
                    }
                })
                .doOnError(error -> log.error("업종별주가요청 실패 - 업종코드: {}", sectorCode, error));
    }

    /**
     * 시가총액 순 상위 종목 조회 (기본값)
     * 
     * @param sectorCode 업종코드
     * @param marketType 시장구분
     * @param stockCount 조회개수 (기본: 50)
     * @return 시가총액 순 상위 종목 목록
     */
    public Mono<SectorStockPricesResponse> getTopStocksByMarketCap(
            String sectorCode, 
            String marketType, 
            int stockCount) {
        return getSectorStockPrices(sectorCode, marketType, "1", "1", String.valueOf(stockCount), "1");
    }

    /**
     * 거래대금 순 상위 종목 조회
     * 
     * @param sectorCode 업종코드
     * @param marketType 시장구분
     * @param stockCount 조회개수
     * @return 거래대금 순 상위 종목 목록
     */
    public Mono<SectorStockPricesResponse> getTopStocksByTradingValue(
            String sectorCode, 
            String marketType, 
            int stockCount) {
        return getSectorStockPrices(sectorCode, marketType, "2", "1", String.valueOf(stockCount), "1");
    }

    /**
     * 등락률 순 종목 조회
     * 
     * @param sectorCode 업종코드
     * @param marketType 시장구분
     * @param stockCount 조회개수
     * @param isDescending true: 상승률 순(내림차순), false: 하락률 순(오름차순)
     * @return 등락률 순 종목 목록
     */
    public Mono<SectorStockPricesResponse> getStocksByChangeRate(
            String sectorCode, 
            String marketType, 
            int stockCount, 
            boolean isDescending) {
        String sortOrder = isDescending ? "1" : "2"; // 1:내림차순(상승률), 2:오름차순(하락률)
        return getSectorStockPrices(sectorCode, marketType, "3", sortOrder, String.valueOf(stockCount), "1");
    }

    /**
     * 종목명 순 종목 조회
     * 
     * @param sectorCode 업종코드
     * @param marketType 시장구분
     * @param stockCount 조회개수
     * @param isAscending true: 가나다 순(오름차순), false: 역순(내림차순)
     * @return 종목명 순 종목 목록
     */
    public Mono<SectorStockPricesResponse> getStocksByName(
            String sectorCode, 
            String marketType, 
            int stockCount, 
            boolean isAscending) {
        String sortOrder = isAscending ? "2" : "1"; // 2:오름차순(가나다), 1:내림차순(역순)
        return getSectorStockPrices(sectorCode, marketType, "4", sortOrder, String.valueOf(stockCount), "1");
    }

    /**
     * 페이징된 종목 조회
     * 
     * @param sectorCode 업종코드
     * @param marketType 시장구분
     * @param sortType 정렬기준
     * @param sortOrder 정렬방향
     * @param pageSize 페이지 크기
     * @param pageNumber 페이지 번호 (1부터 시작)
     * @return 페이징된 종목 목록
     */
    public Mono<SectorStockPricesResponse> getStocksPaged(
            String sectorCode, 
            String marketType, 
            String sortType, 
            String sortOrder, 
            int pageSize, 
            int pageNumber) {
        
        if (pageSize < 1 || pageSize > 100) {
            return Mono.error(new IllegalArgumentException("페이지 크기는 1-100 사이여야 합니다: " + pageSize));
        }
        
        if (pageNumber < 1) {
            return Mono.error(new IllegalArgumentException("페이지 번호는 1 이상이어야 합니다: " + pageNumber));
        }
        
        int startIndex = (pageNumber - 1) * pageSize + 1;
        
        return getSectorStockPrices(
                sectorCode, 
                marketType, 
                sortType, 
                sortOrder, 
                String.valueOf(pageSize), 
                String.valueOf(startIndex));
    }

    /**
     * 주요 업종별 종목 조회 (KOSPI 종합, KOSDAQ 종합, KOSPI200)
     * 
     * @param sectorCode 주요 업종코드 (001, 101, 201)
     * @param stockCount 조회개수
     * @return 주요 업종 종목 목록
     */
    public Mono<SectorStockPricesResponse> getMajorSectorStocks(String sectorCode, int stockCount) {
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
        
        return getTopStocksByMarketCap(sectorCode, marketType, stockCount);
    }
    
    // ===== Private Methods =====
    
    /**
     * 토큰 조회 및 API 호출
     */
    private Mono<SectorStockPricesResponse> getTokenAndCallApi(SectorStockPricesRequest request) {
        return getTokenAndCallApi(request, "N", "");
    }
    
    /**
     * 토큰 조회 및 API 호출 (연속조회 지원)
     */
    private Mono<SectorStockPricesResponse> getTokenAndCallApi(
            SectorStockPricesRequest request, 
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
                            SectorStockPricesResponse.class, 
                            contYn, 
                            nextKey);
                });
    }
}