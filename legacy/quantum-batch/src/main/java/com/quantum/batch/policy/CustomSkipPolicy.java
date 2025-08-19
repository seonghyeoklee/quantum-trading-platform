package com.quantum.batch.policy;

import java.net.ConnectException;
import java.net.SocketTimeoutException;
import java.util.concurrent.TimeoutException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.core.step.skip.SkipPolicy;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClientResponseException;

/** Spring Batch 커스텀 Skip 정책 특정 예외 상황에서 아이템을 스킵할지 재시도할지 결정 */
@Slf4j
@Component
public class CustomSkipPolicy implements SkipPolicy {

    // 최대 스킵 허용 횟수
    private static final int MAX_SKIP_COUNT = 5;

    // API Rate Limit 관련 최대 스킵 횟수 (더 엄격하게)
    private static final int MAX_RATE_LIMIT_SKIP_COUNT = 2;

    /**
     * 주어진 예외와 스킵 횟수를 바탕으로 스킵 여부 결정
     *
     * @param t 발생한 예외
     * @param skipCount 현재까지의 스킵 횟수
     * @return true: 스킵, false: 재시도 또는 실패
     */
    @Override
    public boolean shouldSkip(final Throwable t, final long skipCount) {
        // 전체 스킵 횟수 제한 확인
        if (skipCount >= MAX_SKIP_COUNT) {
            log.error("Maximum skip count ({}) exceeded. Failing the step.", MAX_SKIP_COUNT);
            return false;
        }

        // 예외 타입별 스킵 정책 적용
        if (isNetworkRelatedError(t)) {
            return handleNetworkError(t, skipCount);
        }

        if (isApiRateLimitError(t)) {
            return handleRateLimitError(t, skipCount);
        }

        if (isDataValidationError(t)) {
            return handleDataValidationError(t, skipCount);
        }

        // 기타 예외는 재시도하지 않고 스킵
        log.warn(
                "Unknown exception type, skipping item. Exception: {}, Skip count: {}",
                t.getClass().getSimpleName(),
                skipCount + 1);
        return true;
    }

    /** 네트워크 관련 오류 처리 일시적인 네트워크 문제는 스킵하지 않고 재시도 */
    private boolean handleNetworkError(final Throwable t, final long skipCount) {
        log.warn("Network error detected: {}. Skip count: {}", t.getMessage(), skipCount);

        // 네트워크 오류는 일시적일 가능성이 높으므로 스킵하지 않음
        // 대신 재시도 메커니즘에 의존
        return false;
    }

    /** API Rate Limit 오류 처리 Rate Limit은 스킵하지 않고 재시도 (잠시 대기 후) */
    private boolean handleRateLimitError(final Throwable t, final long skipCount) {
        log.warn("API Rate Limit error detected: {}. Skip count: {}", t.getMessage(), skipCount);

        // Rate Limit 오류가 계속 발생하면 제한된 횟수만 스킵
        if (skipCount >= MAX_RATE_LIMIT_SKIP_COUNT) {
            log.error("Maximum rate limit skip count ({}) exceeded", MAX_RATE_LIMIT_SKIP_COUNT);
            return false;
        }

        // 일반적으로는 재시도 (RetryTemplate에서 지연 처리)
        return false;
    }

    /** 데이터 검증 오류 처리 잘못된 데이터 형식 등은 스킵 처리 */
    private boolean handleDataValidationError(final Throwable t, final long skipCount) {
        log.warn(
                "Data validation error, skipping item: {}. Skip count: {}",
                t.getMessage(),
                skipCount + 1);

        // 데이터 검증 오류는 재시도해도 해결되지 않으므로 스킵
        return true;
    }

    /** 주식 처리 관련 오류 처리 특정 종목 관련 오류는 스킵 가능 */
    private boolean handleStockProcessingError(final Throwable t, final long skipCount) {
        log.warn(
                "Stock processing error, skipping item: {}. Skip count: {}",
                t.getMessage(),
                skipCount + 1);

        // 특정 종목의 처리 오류는 다른 종목에 영향을 주지 않도록 스킵
        return true;
    }

    /** 네트워크 관련 오류인지 확인 */
    private boolean isNetworkRelatedError(final Throwable t) {
        return t instanceof ConnectException
                || t instanceof SocketTimeoutException
                || t instanceof TimeoutException
                || (t instanceof WebClientResponseException
                        && isTemporaryHttpError((WebClientResponseException) t));
    }

    /** 일시적인 HTTP 오류인지 확인 */
    private boolean isTemporaryHttpError(final WebClientResponseException e) {
        int statusCode = e.getStatusCode().value();
        // 5xx 서버 오류나 408 Request Timeout, 429 Too Many Requests
        return statusCode >= 500 || statusCode == 408 || statusCode == 429;
    }

    /** API Rate Limit 오류인지 확인 */
    private boolean isApiRateLimitError(final Throwable t) {
        if (t instanceof WebClientResponseException) {
            WebClientResponseException e = (WebClientResponseException) t;
            return e.getStatusCode().value() == 429; // Too Many Requests
        }

        // 메시지에서 Rate Limit 관련 키워드 확인
        String message = t.getMessage() != null ? t.getMessage().toLowerCase() : "";
        return message.contains("rate limit")
                || message.contains("too many requests")
                || message.contains("quota exceeded");
    }

    /** 데이터 검증 오류인지 확인 */
    private boolean isDataValidationError(final Throwable t) {
        return t instanceof IllegalArgumentException
                || t instanceof NumberFormatException
                || t instanceof java.time.format.DateTimeParseException
                || (t.getMessage() != null && t.getMessage().contains("validation"));
    }
}
