package com.quantum.stock.controller;

import com.quantum.stock.dto.StockSearchResult;
import com.quantum.stock.service.StockSearchService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * 종목 검색 REST API 컨트롤러
 *
 * DINO 통합 분석 화면의 자동완성 검색 기능을 위한 API 제공
 * 회사명, 영문명, 종목코드 기반 검색 지원
 */
@Slf4j
@RestController
@RequestMapping("/api/stocks")
@RequiredArgsConstructor
@CrossOrigin(origins = "*", allowedHeaders = "*")
public class StockSearchController {

    private final StockSearchService stockSearchService;

    /**
     * 종목 통합 검색 API
     *
     * @param q 검색 키워드 (필수)
     * @param limit 최대 결과 수 (선택, 기본값: 20, 최대: 50)
     * @return 검색 결과 리스트
     */
    @GetMapping("/search")
    public ResponseEntity<Map<String, Object>> searchStocks(
            @RequestParam(value = "q", required = false) String keyword,
            @RequestParam(value = "limit", required = false, defaultValue = "20") Integer limit) {

        log.debug("종목 검색 API 호출: keyword='{}', limit={}", keyword, limit);

        try {
            // 검색 실행
            List<StockSearchResult> results = stockSearchService.searchStocks(keyword, limit);

            // 응답 데이터 구성
            Map<String, Object> response = Map.of(
                "success", true,
                "data", results.stream().map(StockSearchResult::forJson).toList(),
                "total", results.size(),
                "keyword", keyword != null ? keyword.trim() : "",
                "message", results.isEmpty() ? "검색 결과가 없습니다." : "검색 완료"
            );

            log.info("종목 검색 API 성공: keyword='{}', 결과수={}", keyword, results.size());
            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("종목 검색 API 오류: keyword='{}' - {}", keyword, e.getMessage(), e);

            Map<String, Object> errorResponse = Map.of(
                "success", false,
                "data", List.of(),
                "total", 0,
                "keyword", keyword != null ? keyword.trim() : "",
                "message", "검색 중 오류가 발생했습니다.",
                "error", e.getMessage()
            );

            return ResponseEntity.status(500).body(errorResponse);
        }
    }

    /**
     * 인기 종목 조회 API
     *
     * @return 주요 대형주 목록
     */
    @GetMapping("/popular")
    public ResponseEntity<Map<String, Object>> getPopularStocks() {
        log.debug("인기 종목 조회 API 호출");

        try {
            List<StockSearchResult> results = stockSearchService.getPopularStocks();

            Map<String, Object> response = Map.of(
                "success", true,
                "data", results.stream().map(StockSearchResult::forJson).toList(),
                "total", results.size(),
                "message", "인기 종목 조회 완료"
            );

            log.info("인기 종목 조회 API 성공: 결과수={}", results.size());
            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("인기 종목 조회 API 오류: {}", e.getMessage(), e);

            Map<String, Object> errorResponse = Map.of(
                "success", false,
                "data", List.of(),
                "total", 0,
                "message", "인기 종목 조회 중 오류가 발생했습니다.",
                "error", e.getMessage()
            );

            return ResponseEntity.status(500).body(errorResponse);
        }
    }

    /**
     * 종목코드로 정확한 종목 조회 API
     *
     * @param stockCode 6자리 종목코드
     * @return 종목 정보 또는 404
     */
    @GetMapping("/{stockCode}")
    public ResponseEntity<Map<String, Object>> getStockByCode(@PathVariable String stockCode) {
        log.debug("종목코드 조회 API 호출: {}", stockCode);

        try {
            Optional<StockSearchResult> result = stockSearchService.getStockByCode(stockCode);

            if (result.isPresent()) {
                Map<String, Object> response = Map.of(
                    "success", true,
                    "data", result.get().forJson(),
                    "message", "종목 조회 완료"
                );

                log.info("종목코드 조회 API 성공: {} - {}", stockCode, result.get().getDisplayName());
                return ResponseEntity.ok(response);

            } else {
                Map<String, Object> response = Map.of(
                    "success", false,
                    "data", Map.of(),
                    "message", String.format("종목코드 '%s'를 찾을 수 없습니다.", stockCode)
                );

                log.warn("종목코드 조회 API 실패: {}", stockCode);
                return ResponseEntity.status(404).body(response);
            }

        } catch (Exception e) {
            log.error("종목코드 조회 API 오류: {} - {}", stockCode, e.getMessage(), e);

            Map<String, Object> errorResponse = Map.of(
                "success", false,
                "data", Map.of(),
                "message", "종목 조회 중 오류가 발생했습니다.",
                "error", e.getMessage()
            );

            return ResponseEntity.status(500).body(errorResponse);
        }
    }

    /**
     * 시장별 종목 조회 API
     *
     * @param marketType 시장구분 (KOSPI/KOSDAQ)
     * @return 해당 시장의 종목 목록
     */
    @GetMapping("/market/{marketType}")
    public ResponseEntity<Map<String, Object>> getStocksByMarket(@PathVariable String marketType) {
        log.debug("시장별 종목 조회 API 호출: {}", marketType);

        try {
            List<StockSearchResult> results = stockSearchService.getStocksByMarket(marketType);

            Map<String, Object> response = Map.of(
                "success", true,
                "data", results.stream().map(StockSearchResult::forJson).toList(),
                "total", results.size(),
                "marketType", marketType,
                "message", String.format("%s 시장 종목 조회 완료", marketType)
            );

            log.info("시장별 종목 조회 API 성공: 시장={}, 결과수={}", marketType, results.size());
            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("시장별 종목 조회 API 오류: 시장={} - {}", marketType, e.getMessage(), e);

            Map<String, Object> errorResponse = Map.of(
                "success", false,
                "data", List.of(),
                "total", 0,
                "marketType", marketType,
                "message", "시장별 종목 조회 중 오류가 발생했습니다.",
                "error", e.getMessage()
            );

            return ResponseEntity.status(500).body(errorResponse);
        }
    }

    /**
     * 업종별 종목 조회 API
     *
     * @param sector 업종명
     * @return 해당 업종의 종목 목록
     */
    @GetMapping("/sector/{sector}")
    public ResponseEntity<Map<String, Object>> getStocksBySector(@PathVariable String sector) {
        log.debug("업종별 종목 조회 API 호출: {}", sector);

        try {
            List<StockSearchResult> results = stockSearchService.getStocksBySector(sector);

            Map<String, Object> response = Map.of(
                "success", true,
                "data", results.stream().map(StockSearchResult::forJson).toList(),
                "total", results.size(),
                "sector", sector,
                "message", String.format("%s 업종 종목 조회 완료", sector)
            );

            log.info("업종별 종목 조회 API 성공: 업종={}, 결과수={}", sector, results.size());
            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("업종별 종목 조회 API 오류: 업종={} - {}", sector, e.getMessage(), e);

            Map<String, Object> errorResponse = Map.of(
                "success", false,
                "data", List.of(),
                "total", 0,
                "sector", sector,
                "message", "업종별 종목 조회 중 오류가 발생했습니다.",
                "error", e.getMessage()
            );

            return ResponseEntity.status(500).body(errorResponse);
        }
    }

    /**
     * 종목 존재 여부 확인 API
     *
     * @param stockCode 6자리 종목코드
     * @return 존재 여부
     */
    @GetMapping("/{stockCode}/exists")
    public ResponseEntity<Map<String, Object>> checkStockExists(@PathVariable String stockCode) {
        log.debug("종목 존재 확인 API 호출: {}", stockCode);

        try {
            boolean exists = stockSearchService.existsStock(stockCode);

            Map<String, Object> response = Map.of(
                "success", true,
                "exists", exists,
                "stockCode", stockCode,
                "message", exists ? "종목이 존재합니다." : "종목이 존재하지 않습니다."
            );

            log.info("종목 존재 확인 API 성공: {} - {}", stockCode, exists);
            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("종목 존재 확인 API 오류: {} - {}", stockCode, e.getMessage(), e);

            Map<String, Object> errorResponse = Map.of(
                "success", false,
                "exists", false,
                "stockCode", stockCode,
                "message", "종목 존재 확인 중 오류가 발생했습니다.",
                "error", e.getMessage()
            );

            return ResponseEntity.status(500).body(errorResponse);
        }
    }

    /**
     * 종목 검색 통계 API
     *
     * @return 전체 종목 수 등 통계 정보
     */
    @GetMapping("/stats")
    public ResponseEntity<Map<String, Object>> getStockStats() {
        log.debug("종목 통계 조회 API 호출");

        try {
            long totalCount = stockSearchService.getTotalActiveStockCount();

            Map<String, Object> response = Map.of(
                "success", true,
                "data", Map.of(
                    "totalActiveStocks", totalCount,
                    "popularStocksCount", stockSearchService.getPopularStocks().size(),
                    "lastUpdated", "2024-01-01T00:00:00Z" // TODO: 실제 업데이트 시간 추가
                ),
                "message", "종목 통계 조회 완료"
            );

            log.info("종목 통계 조회 API 성공: 총 종목수={}", totalCount);
            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("종목 통계 조회 API 오류: {}", e.getMessage(), e);

            Map<String, Object> errorResponse = Map.of(
                "success", false,
                "data", Map.of(),
                "message", "종목 통계 조회 중 오류가 발생했습니다.",
                "error", e.getMessage()
            );

            return ResponseEntity.status(500).body(errorResponse);
        }
    }
}