package com.quantum.kis.service;

import com.quantum.kis.client.KisFeignClient;
import com.quantum.kis.model.KisMultiStockRequest;
import com.quantum.kis.model.KisMultiStockResponse;
import com.quantum.kis.model.enums.KisCustomerType;
import com.quantum.kis.model.enums.KisTransactionId;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

/**
 * KIS 멀티 주식 조회 서비스
 *
 * <p>intstock-multprice API를 통해 최대 30종목을 한번에 조회 Rate Limiting 적용 및 대용량 처리 지원
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class KisMultiStockPriceService {

    private final KisFeignClient kisFeignClient;
    private final KisRateLimiter kisRateLimiter;

    @Autowired(required = false)
    private KisTokenProvider kisTokenProvider;

    @Value("${kis.api.app-key}")
    private String appKey;

    @Value("${kis.api.app-secret}")
    private String appSecret;

    @Value("${kis.api.environment:sandbox}")
    private String environment;

    /**
     * 여러 종목의 시세를 한번에 조회 (최대 30종목)
     *
     * @param stockCodes 조회할 종목 코드 리스트
     * @return 멀티 주식 시세 응답
     */
    public KisMultiStockResponse getMultiStockPrices(List<String> stockCodes) {
        return getMultiStockPrices(stockCodes, "J"); // 기본 시장구분: 주식
    }

    /**
     * 여러 종목의 시세를 한번에 조회 (최대 30종목)
     *
     * @param stockCodes 조회할 종목 코드 리스트
     * @param marketDivCode 시장 구분 코드 (J: 주식, Q: 코스닥 등)
     * @return 멀티 주식 시세 응답
     */
    public KisMultiStockResponse getMultiStockPrices(
            List<String> stockCodes, String marketDivCode) {
        if (stockCodes == null || stockCodes.isEmpty()) {
            throw new IllegalArgumentException("Stock codes cannot be empty");
        }

        if (stockCodes.size() > 30) {
            throw new IllegalArgumentException(
                    "Maximum 30 stock codes allowed, got: " + stockCodes.size());
        }

        log.info("Getting multi stock prices for {} stocks", stockCodes.size());

        try {
            // 1. Rate Limiting 체크
            String apiEndpoint = "intstock-multprice";
            if (!kisRateLimiter.acquireWithWait(apiEndpoint, false)) {
                throw new RuntimeException(
                        "KIS API rate limit exceeded for multi stock price inquiry");
            }

            // 2. 액세스 토큰 조회
            String accessToken = null;
            if (kisTokenProvider != null) {
                accessToken = kisTokenProvider.getValidAccessToken();
            }
            if (accessToken == null) {
                throw new RuntimeException(
                        "Failed to get valid access token - KisTokenProvider not available");
            }

            // 3. 요청 파라미터 생성
            KisMultiStockRequest request =
                    KisMultiStockRequest.fromStockCodes(stockCodes, marketDivCode);
            Map<String, String> params = request.toQueryParams();

            // 4. TR ID 설정 (환경별)
            String trId = getTrIdForEnvironment();

            // 5. KIS API 호출
            KisMultiStockResponse response =
                    kisFeignClient.getMultiStockPrice(
                            params,
                            "Bearer " + accessToken,
                            appKey,
                            appSecret,
                            trId,
                            KisCustomerType.PERSONAL.getCode());

            log.info(
                    "Successfully retrieved multi stock prices: {} items",
                    response.getStockCount());
            return response;

        } catch (Exception e) {
            log.error("Failed to get multi stock prices for stocks: {}", stockCodes, e);
            throw new RuntimeException("멀티 주식 시세 조회 실패", e);
        }
    }

    /**
     * 대용량 종목 리스트 처리 (30개씩 분할하여 조회)
     *
     * @param stockCodes 조회할 모든 종목 코드 리스트
     * @return 모든 종목의 시세 정보 리스트
     */
    public List<KisMultiStockResponse> getBulkStockPrices(List<String> stockCodes) {
        return getBulkStockPrices(stockCodes, "J");
    }

    /**
     * 대용량 종목 리스트 처리 (30개씩 분할하여 조회)
     *
     * @param stockCodes 조회할 모든 종목 코드 리스트
     * @param marketDivCode 시장 구분 코드
     * @return 모든 종목의 시세 정보 리스트
     */
    public List<KisMultiStockResponse> getBulkStockPrices(
            List<String> stockCodes, String marketDivCode) {
        if (stockCodes == null || stockCodes.isEmpty()) {
            return List.of();
        }

        log.info(
                "Processing bulk stock prices for {} stocks (will be split into batches of 30)",
                stockCodes.size());

        List<KisMultiStockResponse> allResponses = new ArrayList<>();

        // 30개씩 분할하여 처리
        for (int i = 0; i < stockCodes.size(); i += 30) {
            int endIndex = Math.min(i + 30, stockCodes.size());
            List<String> batch = stockCodes.subList(i, endIndex);

            log.debug("Processing batch {}-{}/{}", i + 1, endIndex, stockCodes.size());

            try {
                KisMultiStockResponse response = getMultiStockPrices(batch, marketDivCode);
                allResponses.add(response);

                log.debug(
                        "Batch {}-{} completed: {} items",
                        i + 1,
                        endIndex,
                        response.getStockCount());

            } catch (Exception e) {
                log.error("Failed to process batch {}-{}", i + 1, endIndex, e);
                // 일부 배치 실패해도 계속 진행
            }
        }

        log.info(
                "Bulk processing completed: {} batches processed, {} total responses",
                (stockCodes.size() + 29) / 30,
                allResponses.size());

        return allResponses;
    }

    /** 환경별 TR ID 반환 */
    private String getTrIdForEnvironment() {
        return "sandbox".equals(environment)
                ? KisTransactionId.DOMESTIC_STOCK_MULTI_PRICE_SANDBOX.getId()
                : KisTransactionId.DOMESTIC_STOCK_MULTI_PRICE_REAL.getId();
    }

    /** Rate Limiter 상태 확인 */
    public KisRateLimiter.RateLimitStatus getRateLimitStatus() {
        return kisRateLimiter.getStatus("intstock-multprice");
    }
}
