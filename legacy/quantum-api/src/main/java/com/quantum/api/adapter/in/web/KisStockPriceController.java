package com.quantum.api.adapter.in.web;

import com.quantum.api.application.usecase.KisStockPriceQueryUsecase;
import com.quantum.kis.model.KisCurrentPriceResponse;
import com.quantum.kis.model.KisMultiStockResponse;
import com.quantum.kis.service.KisMultiStockPriceService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 주식 정보 API 컨트롤러 - Port 패턴 사용 */
@Slf4j
@RequiredArgsConstructor
@RestController
@RequestMapping("/api/v1/stocks")
@Tag(name = "Stock API", description = "주식 현재가 조회 API")
public class KisStockPriceController {

    private final KisStockPriceQueryUsecase kisStockPriceQueryUsecase;
    private final KisMultiStockPriceService kisMultiStockPriceService;

    /** 종목코드로 현재가 조회 및 저장 (Port 패턴 + 분석용 데이터 축적) */
    @GetMapping("/{symbol}/current-price")
    @Operation(summary = "주식 현재가 조회 및 저장", description = "KIS API를 통해 주식 현재가를 조회하고 분석용으로 저장합니다")
    public ResponseEntity<KisCurrentPriceResponse> getCurrentPrice(
            @Parameter(description = "종목코드 (예: 005930)", required = true) @PathVariable
                    String symbol) {

        log.info("API: Getting current price for stock: {}", symbol);

        try {
            // 현재가 조회 + 자동 저장
            KisCurrentPriceResponse response =
                    kisStockPriceQueryUsecase.getCurrentPriceAndSave(symbol);

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("API: Failed to get current price for stock: {}", symbol, e);
            return ResponseEntity.internalServerError().build();
        }
    }

    /** 여러 종목 현재가 멀티 조회 (최대 30종목) - 고성능 API */
    @GetMapping("/multi-price")
    @Operation(
            summary = "멀티 주식 현재가 조회",
            description = "KIS API 멀티 조회를 통해 최대 30종목의 현재가를 한번에 조회합니다. 단일 조회 대비 3000% 성능 향상!")
    public ResponseEntity<KisMultiStockResponse> getMultiStockPrices(
            @Parameter(description = "종목코드 리스트 (최대 30개, 예: 005930,000660,035420)", required = true)
                    @RequestParam
                    List<String> stockCodes,
            @Parameter(description = "시장구분코드 (기본값: J)", required = false)
                    @RequestParam(defaultValue = "J")
                    String marketDivCode) {

        log.info(
                "API: Getting multi stock prices for {} stocks: {}", stockCodes.size(), stockCodes);

        try {
            // 입력 검증
            if (stockCodes.isEmpty()) {
                log.warn("API: Empty stock codes provided");
                return ResponseEntity.badRequest().build();
            }

            if (stockCodes.size() > 30) {
                log.warn("API: Too many stock codes provided: {}", stockCodes.size());
                return ResponseEntity.badRequest().build();
            }

            // 멀티 조회 실행
            KisMultiStockResponse response =
                    kisMultiStockPriceService.getMultiStockPrices(stockCodes, marketDivCode);

            log.info(
                    "API: Successfully retrieved {} stock prices out of {} requested",
                    response.getStockCount(),
                    stockCodes.size());

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("API: Failed to get multi stock prices for stocks: {}", stockCodes, e);
            return ResponseEntity.internalServerError().build();
        }
    }

    /** 대용량 종목 배치 조회 (30개씩 분할 처리) */
    @GetMapping("/bulk-price")
    @Operation(summary = "대용량 주식 현재가 배치 조회", description = "30개씩 자동 분할하여 대용량 종목 리스트의 현재가를 조회합니다")
    public ResponseEntity<List<KisMultiStockResponse>> getBulkStockPrices(
            @Parameter(description = "종목코드 리스트 (개수 제한 없음, 30개씩 자동 분할)", required = true)
                    @RequestParam
                    List<String> stockCodes,
            @Parameter(description = "시장구분코드 (기본값: J)", required = false)
                    @RequestParam(defaultValue = "J")
                    String marketDivCode) {

        log.info(
                "API: Getting bulk stock prices for {} stocks (will process in batches of 30)",
                stockCodes.size());

        try {
            // 입력 검증
            if (stockCodes.isEmpty()) {
                log.warn("API: Empty stock codes provided");
                return ResponseEntity.badRequest().build();
            }

            // 대용량 배치 조회 실행
            List<KisMultiStockResponse> responses =
                    kisMultiStockPriceService.getBulkStockPrices(stockCodes, marketDivCode);

            int totalStocksProcessed =
                    responses.stream().mapToInt(KisMultiStockResponse::getStockCount).sum();

            log.info(
                    "API: Successfully processed {} stocks in {} batches",
                    totalStocksProcessed,
                    responses.size());

            return ResponseEntity.ok(responses);

        } catch (Exception e) {
            log.error("API: Failed to get bulk stock prices for {} stocks", stockCodes.size(), e);
            return ResponseEntity.internalServerError().build();
        }
    }
}
