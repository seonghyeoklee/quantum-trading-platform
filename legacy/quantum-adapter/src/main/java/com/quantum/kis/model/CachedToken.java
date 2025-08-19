package com.quantum.kis.model;

import java.time.LocalDateTime;

/** 캐시된 토큰 정보 KIS 정책에 맞춘 6시간 갱신 주기 관리 */
public record CachedToken(String token, LocalDateTime issueTime, LocalDateTime expiryTime) {

    /** 토큰 만료 여부 확인 5분 안전 마진을 두고 만료 체크 */
    public boolean isExpired() {
        return LocalDateTime.now().isAfter(expiryTime.minusMinutes(5));
    }

    /** KIS 정책에 따른 갱신 권장 시점 확인 발급 후 6시간이 지나면 갱신 권장 */
    public boolean shouldRefreshByPolicy() {
        return LocalDateTime.now().isAfter(issueTime.plusHours(6));
    }
}
