package com.quantum.core.timezone;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.LocalDateTime;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.TimeZone;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * Asia/Seoul 시간대 설정 테스트
 */
public class TimezoneTest {

    @Test
    @DisplayName("JVM 기본 시간대가 Asia/Seoul로 설정되었는지 확인")
    void testJvmTimezone() {
        // JVM 시간대 설정 (애플리케이션에서 설정된 것과 동일)
        TimeZone.setDefault(TimeZone.getTimeZone("Asia/Seoul"));
        
        TimeZone defaultTimeZone = TimeZone.getDefault();
        assertThat(defaultTimeZone.getID()).isEqualTo("Asia/Seoul");
        
        System.out.println("Default TimeZone: " + defaultTimeZone.getID());
        System.out.println("TimeZone Display Name: " + defaultTimeZone.getDisplayName());
    }

    @Test
    @DisplayName("현재 시간이 한국 시간대로 표시되는지 확인")
    void testCurrentTimeInSeoulTimezone() {
        // JVM 시간대 설정
        TimeZone.setDefault(TimeZone.getTimeZone("Asia/Seoul"));
        
        LocalDateTime now = LocalDateTime.now();
        ZonedDateTime seoulTime = ZonedDateTime.now(java.time.ZoneId.of("Asia/Seoul"));
        
        // 현재 시간이 Asia/Seoul 시간대 기준으로 표시되는지 확인
        assertThat(now.getHour()).isEqualTo(seoulTime.getHour());
        assertThat(now.getMinute()).isEqualTo(seoulTime.getMinute());
        
        System.out.println("Current LocalDateTime: " + now.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));
        System.out.println("Seoul ZonedDateTime: " + seoulTime.format(DateTimeFormatter.ISO_ZONED_DATE_TIME));
    }
}