package com.quantum.trading.platform.shared.event;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.quantum.trading.platform.shared.value.UserId;
import lombok.Builder;

import java.time.Instant;
import java.util.Set;

/**
 * 사용자 등록 이벤트
 * <p>
 * 새로운 사용자가 시스템에 등록되었을 때 발행되는 도메인 이벤트
 */
@Builder
public record UserRegisteredEvent(@JsonProperty("userId") UserId userId, @JsonProperty("username") String username,
                                  @JsonProperty("passwordHash") String passwordHash, @JsonProperty("name") String name,
                                  @JsonProperty("email") String email, @JsonProperty("phone") String phone,
                                  @JsonProperty("initialRoles") Set<String> initialRoles,
                                  @JsonProperty("registeredAt") Instant registeredAt,
                                  @JsonProperty("registeredBy") String registeredBy) {

    @JsonCreator
    public UserRegisteredEvent {
    }

    public static UserRegisteredEvent create(
            UserId userId,
            String username,
            String passwordHash,
            String name,
            String email,
            String phone,
            Set<String> initialRoles,
            String registeredBy) {
        return UserRegisteredEvent.builder()
                .userId(userId)
                .username(username)
                .passwordHash(passwordHash)
                .name(name)
                .email(email)
                .phone(phone)
                .initialRoles(initialRoles)
                .registeredAt(Instant.now())
                .registeredBy(registeredBy)
                .build();
    }
}
