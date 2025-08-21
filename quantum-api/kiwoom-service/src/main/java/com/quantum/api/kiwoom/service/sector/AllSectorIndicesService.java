package com.quantum.api.kiwoom.service.sector;

import com.quantum.api.kiwoom.client.KiwoomApiClient;
import com.quantum.api.kiwoom.dto.sector.info.AllSectorIndicesRequest;
import com.quantum.api.kiwoom.dto.sector.info.AllSectorIndicesResponse;
import com.quantum.api.kiwoom.service.KiwoomTokenCacheService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

/**
 * 전업종지수요청 서비스 (ka20003)
 * 전체 업종 지수의 현재가 정보 조회
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class AllSectorIndicesService {

    private final KiwoomApiClient kiwoomApiClient;
    private final KiwoomTokenCacheService tokenCacheService;

    /**
     * 전업종 지수 조회
     * 
     * @param marketType 시장구분 (0:코스피, 1:코스닥, 2:코스피200, 9:전체)
     * @param sortType 정렬기준 (1:지수순, 2:등락률순, 3:거래량순)
     * @param sortOrder 정렬방향 (1:내림차순, 2:오름차순)
     * @param categoryType 업종분류 (1:전체, 2:대분류만, 3:중분류만, 4:소분류만)
     * @return 전업종 지수 정보
     */
    public Mono<AllSectorIndicesResponse> getAllSectorIndices(
            String marketType, 
            String sortType, 
            String sortOrder, 
            String categoryType) {
        
        log.info("전업종지수요청 시작 - 시장구분: {}, 정렬: {}({}), 분류: {}", 
                marketType, sortType, sortOrder, categoryType);
        
        // 요청 객체 생성
        AllSectorIndicesRequest request = AllSectorIndicesRequest.builder()
                .marketType(marketType)
                .sortType(sortType)
                .sortOrder(sortOrder)
                .categoryType(categoryType)
                .build();
        
        // 요청 데이터 유효성 검증
        request.validate();
        
        return getTokenAndCallApi(request)
                .doOnSuccess(response -> {
                    if (response != null && response.isSuccess()) {
                        int dataSize = response.getSectorIndices() != null ? response.getSectorIndices().size() : 0;
                        log.info("전업종지수요청 성공 - 시장구분: {}, 업종 수: {}", 
                                marketType, dataSize);
                    } else {
                        log.warn("전업종지수요청 응답 오류 - 시장구분: {}, 오류: {}", 
                                marketType, response != null ? response.getErrorMessage() : "null response");
                    }
                })
                .doOnError(error -> log.error("전업종지수요청 실패 - 시장구분: {}", marketType, error));
    }

    /**
     * 전체 시장 업종 지수 조회 (등락률 순)
     * 
     * @return 전체 시장 업종 지수 (등락률 내림차순)
     */
    public Mono<AllSectorIndicesResponse> getAllMarketSectorsByChangeRate() {
        return getAllSectorIndices("9", "2", "1", "1");
    }

    /**
     * 코스피 업종 지수 조회 (등락률 순)
     * 
     * @return 코스피 업종 지수 (등락률 내림차순)
     */
    public Mono<AllSectorIndicesResponse> getKospiSectorsByChangeRate() {
        return getAllSectorIndices("0", "2", "1", "1");
    }

    /**
     * 코스닥 업종 지수 조회 (등락률 순)
     * 
     * @return 코스닥 업종 지수 (등락률 내림차순)
     */
    public Mono<AllSectorIndicesResponse> getKosdaqSectorsByChangeRate() {
        return getAllSectorIndices("1", "2", "1", "1");
    }

    /**
     * 코스피200 업종 지수 조회 (등락률 순)
     * 
     * @return 코스피200 업종 지수 (등락률 내림차순)
     */
    public Mono<AllSectorIndicesResponse> getKospi200SectorsByChangeRate() {
        return getAllSectorIndices("2", "2", "1", "1");
    }

    /**
     * 거래량 순 업종 지수 조회
     * 
     * @param marketType 시장구분
     * @return 거래량 순 업종 지수 (내림차순)
     */
    public Mono<AllSectorIndicesResponse> getSectorsByVolume(String marketType) {
        return getAllSectorIndices(marketType, "3", "1", "1");
    }

    /**
     * 지수 순 업종 지수 조회
     * 
     * @param marketType 시장구분
     * @param isDescending true: 내림차순(지수 높은 순), false: 오름차순(지수 낮은 순)
     * @return 지수 순 업종 지수
     */
    public Mono<AllSectorIndicesResponse> getSectorsByIndex(String marketType, boolean isDescending) {
        String sortOrder = isDescending ? "1" : "2"; // 1:내림차순, 2:오름차순
        return getAllSectorIndices(marketType, "1", sortOrder, "1");
    }

    /**
     * 대분류 업종만 조회
     * 
     * @param marketType 시장구분
     * @param sortType 정렬기준
     * @return 대분류 업종 지수 목록
     */
    public Mono<AllSectorIndicesResponse> getMajorCategorySectors(String marketType, String sortType) {
        return getAllSectorIndices(marketType, sortType, "1", "2"); // 대분류만
    }

    /**
     * 중분류 업종만 조회
     * 
     * @param marketType 시장구분
     * @param sortType 정렬기준
     * @return 중분류 업종 지수 목록
     */
    public Mono<AllSectorIndicesResponse> getMidCategorySectors(String marketType, String sortType) {
        return getAllSectorIndices(marketType, sortType, "1", "3"); // 중분류만
    }

    /**
     * 소분류 업종만 조회
     * 
     * @param marketType 시장구분
     * @param sortType 정렬기준
     * @return 소분류 업종 지수 목록
     */
    public Mono<AllSectorIndicesResponse> getMinorCategorySectors(String marketType, String sortType) {
        return getAllSectorIndices(marketType, sortType, "1", "4"); // 소분류만
    }

    /**
     * 상승률 상위 업종 조회
     * 
     * @param marketType 시장구분
     * @return 상승률 상위 업종 (등락률 내림차순)
     */
    public Mono<AllSectorIndicesResponse> getTopGainerSectors(String marketType) {
        return getAllSectorIndices(marketType, "2", "1", "1"); // 등락률 내림차순
    }

    /**
     * 하락률 상위 업종 조회
     * 
     * @param marketType 시장구분
     * @return 하락률 상위 업종 (등락률 오름차순)
     */
    public Mono<AllSectorIndicesResponse> getTopLoserSectors(String marketType) {
        return getAllSectorIndices(marketType, "2", "2", "1"); // 등락률 오름차순
    }

    /**
     * 시장 전체 현황 조회 (모든 정보 포함)
     * 
     * @return 시장 전체 업종 현황
     */
    public Mono<AllSectorIndicesResponse> getMarketOverview() {
        return getAllMarketSectorsByChangeRate()
                .doOnSuccess(response -> {
                    if (response != null && response.isSuccess()) {
                        log.info("시장 전체 현황 조회 완료 - 업종 수: {}, 상승 업종: {}", 
                                response.getSectorIndices() != null ? response.getSectorIndices().size() : 0,
                                response.getMarketSummary() != null ? response.getMarketSummary().getRisingSectorCount() : 0);
                    }
                });
    }
    
    // ===== Private Methods =====
    
    /**
     * 토큰 조회 및 API 호출
     */
    private Mono<AllSectorIndicesResponse> getTokenAndCallApi(AllSectorIndicesRequest request) {
        return getTokenAndCallApi(request, "N", "");
    }
    
    /**
     * 토큰 조회 및 API 호출 (연속조회 지원)
     */
    private Mono<AllSectorIndicesResponse> getTokenAndCallApi(
            AllSectorIndicesRequest request, 
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
                            AllSectorIndicesResponse.class, 
                            contYn, 
                            nextKey);
                });
    }
}