package com.quantum.kis.service;

import com.quantum.kis.model.enums.KisTimeframe;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

/**
 * KIS 어댑터 모델과 도메인 모델 간 매핑 서비스
 *
 * <p>어댑터 계층의 독립성을 위해 외부 API 모델과 내부 도메인 모델을 분리
 */
@Slf4j
@Component
public class KisModelMapper {

    /**
     * 도메인 TimeframeCode를 KIS TimeFrame으로 변환
     *
     * @param domainTimeframe 도메인 시간프레임 문자열
     * @return KIS API 시간프레임
     */
    public KisTimeframe toKisTimeframe(String domainTimeframe) {
        if (domainTimeframe == null) {
            return KisTimeframe.DAILY;
        }

        return switch (domainTimeframe.toUpperCase()) {
            case "1M", "ONE_MINUTE" -> KisTimeframe.MINUTE_1;
            case "5M", "FIVE_MINUTE" -> KisTimeframe.MINUTE_5;
            case "15M", "FIFTEEN_MINUTE" -> KisTimeframe.MINUTE_15;
            case "30M", "THIRTY_MINUTE" -> KisTimeframe.MINUTE_30;
            case "1H", "ONE_HOUR" -> KisTimeframe.MINUTE_60;
            case "1D", "ONE_DAY" -> KisTimeframe.DAILY;
            case "1W", "ONE_WEEK" -> KisTimeframe.WEEKLY;
            case "1MO", "ONE_MONTH" -> KisTimeframe.MONTHLY;
            default -> {
                log.warn("Unknown timeframe: {}, defaulting to DAILY", domainTimeframe);
                yield KisTimeframe.DAILY;
            }
        };
    }

    /**
     * KIS TimeFrame을 도메인 모델로 역변환
     *
     * @param kisTimeframe KIS 시간프레임
     * @return 도메인 시간프레임 문자열
     */
    public String toDomainTimeframe(KisTimeframe kisTimeframe) {
        return switch (kisTimeframe) {
            case MINUTE_1 -> "ONE_MINUTE";
            case MINUTE_5 -> "FIVE_MINUTE";
            case MINUTE_15 -> "FIFTEEN_MINUTE";
            case MINUTE_30 -> "THIRTY_MINUTE";
            case MINUTE_60 -> "ONE_HOUR";
            case DAILY -> "ONE_DAY";
            case WEEKLY -> "ONE_WEEK";
            case MONTHLY -> "ONE_MONTH";
        };
    }

    /** 환경별 설정 확인 */
    public boolean isProductionEnvironment(String environment) {
        return "production".equalsIgnoreCase(environment) || "prod".equalsIgnoreCase(environment);
    }
}
