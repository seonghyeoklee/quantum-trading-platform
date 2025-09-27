package com.quantum.stock.service;

import com.quantum.stock.domain.StockMaster;
import com.quantum.stock.dto.StockSearchResult;
import com.quantum.stock.infrastructure.StockMasterRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

/**
 * 종목 검색 서비스
 *
 * 종목 마스터 데이터를 활용한 검색 기능 제공
 * 회사명, 영문명, 종목코드 기반 통합 검색 지원
 */
@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class StockSearchService {

    private final StockMasterRepository stockMasterRepository;

    /**
     * 통합 종목 검색 (키워드 기반)
     *
     * @param keyword 검색 키워드 (회사명, 영문명, 종목코드)
     * @param maxResults 최대 결과 수 (기본값: 20)
     * @return 검색 결과 리스트 (관련도 순)
     */
    public List<StockSearchResult> searchStocks(String keyword, Integer maxResults) {
        if (keyword == null || keyword.trim().isEmpty()) {
            return getPopularStocks();
        }

        String cleanKeyword = keyword.trim();
        int limit = (maxResults != null && maxResults > 0) ? Math.min(maxResults, 50) : 20;

        log.debug("종목 검색 요청: 키워드='{}', 최대결과={}", cleanKeyword, limit);

        // 통합 검색 실행 (관련도 순으로 정렬됨)
        List<StockMaster> stocks = stockMasterRepository.findByKeywordWithRelevanceRanking(cleanKeyword);

        // 결과를 DTO로 변환 및 제한
        List<StockSearchResult> results = stocks.stream()
                .limit(limit)
                .map(this::convertToSearchResult)
                .collect(Collectors.toList());

        log.info("종목 검색 완료: 키워드='{}', 결과수={}", cleanKeyword, results.size());
        return results;
    }

    /**
     * 인기 종목 조회 (기본 추천 목록)
     *
     * @return 주요 대형주 목록
     */
    public List<StockSearchResult> getPopularStocks() {
        log.debug("인기 종목 조회 요청");

        List<StockMaster> popularStocks = stockMasterRepository.findPopularStocks();
        List<StockSearchResult> results = popularStocks.stream()
                .map(this::convertToSearchResult)
                .collect(Collectors.toList());

        log.info("인기 종목 조회 완료: 결과수={}", results.size());
        return results;
    }

    /**
     * 시장구분별 종목 조회
     *
     * @param marketType 시장구분 (KOSPI/KOSDAQ)
     * @return 해당 시장의 종목 목록
     */
    public List<StockSearchResult> getStocksByMarket(String marketType) {
        if (marketType == null || marketType.trim().isEmpty()) {
            return List.of();
        }

        log.debug("시장별 종목 조회: 시장={}", marketType);

        List<StockMaster> stocks = stockMasterRepository.findByMarketTypeAndIsActiveTrue(marketType.trim());
        List<StockSearchResult> results = stocks.stream()
                .limit(100) // 시장별 조회는 최대 100개로 제한
                .map(this::convertToSearchResult)
                .collect(Collectors.toList());

        log.info("시장별 종목 조회 완료: 시장={}, 결과수={}", marketType, results.size());
        return results;
    }

    /**
     * 업종별 종목 조회
     *
     * @param sector 업종명
     * @return 해당 업종의 종목 목록
     */
    public List<StockSearchResult> getStocksBySector(String sector) {
        if (sector == null || sector.trim().isEmpty()) {
            return List.of();
        }

        log.debug("업종별 종목 조회: 업종={}", sector);

        List<StockMaster> stocks = stockMasterRepository.findBySectorAndIsActiveTrue(sector.trim());
        List<StockSearchResult> results = stocks.stream()
                .limit(50) // 업종별 조회는 최대 50개로 제한
                .map(this::convertToSearchResult)
                .collect(Collectors.toList());

        log.info("업종별 종목 조회 완료: 업종={}, 결과수={}", sector, results.size());
        return results;
    }

    /**
     * 종목코드로 정확한 종목 조회
     *
     * @param stockCode 6자리 종목코드
     * @return 종목 정보 (Optional)
     */
    public Optional<StockSearchResult> getStockByCode(String stockCode) {
        if (stockCode == null || stockCode.trim().isEmpty()) {
            return Optional.empty();
        }

        String cleanStockCode = stockCode.trim();
        log.debug("종목코드 조회: {}", cleanStockCode);

        Optional<StockMaster> stock = stockMasterRepository.findById(cleanStockCode);

        if (stock.isPresent() && stock.get().isActiveStock()) {
            StockSearchResult result = convertToSearchResult(stock.get());
            log.info("종목코드 조회 성공: {} - {}", cleanStockCode, result.getDisplayName());
            return Optional.of(result);
        } else {
            log.warn("종목코드 조회 실패: {}", cleanStockCode);
            return Optional.empty();
        }
    }

    /**
     * 종목 존재 여부 확인
     *
     * @param stockCode 6자리 종목코드
     * @return 존재 여부
     */
    public boolean existsStock(String stockCode) {
        if (stockCode == null || stockCode.trim().isEmpty()) {
            return false;
        }

        boolean exists = stockMasterRepository.existsByStockCodeAndIsActiveTrue(stockCode.trim());
        log.debug("종목 존재 확인: {} - {}", stockCode, exists);
        return exists;
    }

    /**
     * 전체 활성 종목 수 조회
     *
     * @return 활성 종목 총 개수
     */
    public long getTotalActiveStockCount() {
        long count = stockMasterRepository.findAllActiveStocks().size();
        log.debug("전체 활성 종목 수: {}", count);
        return count;
    }

    /**
     * StockMaster 엔티티를 StockSearchResult DTO로 변환
     *
     * @param stock StockMaster 엔티티
     * @return StockSearchResult DTO
     */
    private StockSearchResult convertToSearchResult(StockMaster stock) {
        return StockSearchResult.builder()
                .stockCode(stock.getStockCode())
                .companyName(stock.getCompanyName())
                .companyNameEn(stock.getCompanyNameEn())
                .marketType(stock.getMarketType())
                .sector(stock.getSector())
                .displayName(stock.getDisplayName())
                .fullDisplayName(stock.getFullDisplayName())
                .isActive(stock.isActiveStock())
                .build();
    }

    /**
     * 검색 키워드 정리 (특수문자 제거, 공백 정리)
     *
     * @param keyword 원본 키워드
     * @return 정리된 키워드
     */
    private String sanitizeKeyword(String keyword) {
        if (keyword == null) {
            return "";
        }

        // 특수문자 제거 및 공백 정리
        return keyword.trim()
                .replaceAll("[^가-힣a-zA-Z0-9\\s]", "")
                .replaceAll("\\s+", " ");
    }
}