package com.quantum.trading.platform.command.aggregate;

import com.quantum.trading.platform.shared.command.*;
import com.quantum.trading.platform.shared.event.*;
import com.quantum.trading.platform.shared.value.UserId;
import org.axonframework.test.aggregate.AggregateTestFixture;
import org.axonframework.test.aggregate.FixtureConfiguration;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/**
 * User Aggregate 테스트
 * 
 * Axon Test Fixtures를 사용한 Event Sourcing 테스트
 */
class UserTest {
    
    private FixtureConfiguration<User> fixture;
    
    @BeforeEach
    void setUp() {
        fixture = new AggregateTestFixture<>(User.class);
    }
    
    @Test
    void shouldRegisterNewUser() {
        // Given
        UserId userId = UserId.of("USER-001");
        RegisterUserCommand command = RegisterUserCommand.builder()
                .userId(userId)
                .username("testuser")
                .password("password123")
                .name("Test User")
                .email("test@example.com")
                .phone("010-1234-5678")
                .initialRoles(Set.of("ROLE_TRADER"))
                .registeredBy(UserId.of("ADMIN-001"))
                .build();
        
        // When & Then
        fixture.givenNoPriorActivity()
                .when(command)
                .expectSuccessfulHandlerExecution()
                .expectEvents(
                        UserRegisteredEvent.create(
                                userId,
                                "testuser",
                                "password123", // 패스워드 해시 (테스트에서는 평문 사용)
                                "Test User",
                                "test@example.com",
                                "010-1234-5678",
                                Set.of("ROLE_TRADER"),
                                "ADMIN-001"
                        )
                );
    }
    
    @Test
    void shouldFailRegistrationWithInvalidData() {
        // Given
        RegisterUserCommand command = RegisterUserCommand.builder()
                .userId(UserId.of("USER-001"))
                .username("") // Invalid username
                .password("123") // Too short password
                .name("Test User")
                .email("invalid-email") // Invalid email
                .initialRoles(Set.of("ROLE_TRADER"))
                .build();
        
        // When & Then
        fixture.givenNoPriorActivity()
                .when(command)
                .expectException(IllegalArgumentException.class);
    }
    
    @Test
    void shouldSucceedAuthentication() {
        // Given
        UserId userId = UserId.of("USER-001");
        
        UserRegisteredEvent registrationEvent = UserRegisteredEvent.create(
                userId,
                "testuser",
                "hashedPassword123", // 패스워드 해시
                "Test User",
                "test@example.com",
                "010-1234-5678",
                Set.of("ROLE_TRADER"),
                "ADMIN-001"
        );
        
        AuthenticateUserCommand command = AuthenticateUserCommand.builder()
                .userId(userId)
                .username("testuser")
                .password("password123")
                .sessionId("SESSION-123")
                .ipAddress("192.168.1.1")
                .userAgent("Mozilla/5.0")
                .build();
        
        // When & Then
        fixture.given(registrationEvent)
                .when(command)
                .expectSuccessfulHandlerExecution()
                .expectEvents(
                        UserLoginSucceededEvent.create(
                                userId,
                                "testuser",
                                "SESSION-123",
                                "192.168.1.1",
                                "Mozilla/5.0",
                                null
                        )
                );
    }
    
    @Test
    void shouldFailAuthenticationWithWrongPassword() {
        // Given
        UserId userId = UserId.of("USER-001");
        
        UserRegisteredEvent registrationEvent = UserRegisteredEvent.create(
                userId,
                "testuser",
                "hashedPassword123", // 패스워드 해시
                "Test User",
                "test@example.com",
                "010-1234-5678",
                Set.of("ROLE_TRADER"),
                "ADMIN-001"
        );
        
        AuthenticateUserCommand command = AuthenticateUserCommand.builder()
                .userId(userId)
                .username("testuser")
                .password("wrongpassword")
                .sessionId("SESSION-123")
                .ipAddress("192.168.1.1")
                .userAgent("Mozilla/5.0")
                .build();
        
        // When & Then
        fixture.given(registrationEvent)
                .when(command)
                .expectSuccessfulHandlerExecution()
                .expectEvents(
                        UserLoginFailedEvent.create(
                                userId,
                                "testuser",
                                "Invalid password",
                                "192.168.1.1",
                                "Mozilla/5.0",
                                1,
                                false
                        )
                );
    }
    
    @Test
    void shouldLockAccountAfter5FailedAttempts() {
        // Given
        UserId userId = UserId.of("USER-001");
        
        UserRegisteredEvent registrationEvent = UserRegisteredEvent.create(
                userId,
                "testuser",
                "hashedPassword123", // 패스워드 해시
                "Test User",
                "test@example.com",
                "010-1234-5678",
                Set.of("ROLE_TRADER"),
                "ADMIN-001"
        );
        
        // 4번의 실패한 로그인 시도
        UserLoginFailedEvent failedAttempt4 = UserLoginFailedEvent.create(
                userId,
                "testuser",
                "Invalid password",
                "192.168.1.1",
                "Mozilla/5.0",
                4,
                false
        );
        
        AuthenticateUserCommand command = AuthenticateUserCommand.builder()
                .userId(userId)
                .username("testuser")
                .password("wrongpassword")
                .sessionId("SESSION-123")
                .ipAddress("192.168.1.1")
                .userAgent("Mozilla/5.0")
                .build();
        
        // When & Then
        fixture.given(registrationEvent, failedAttempt4)
                .when(command)
                .expectSuccessfulHandlerExecution()
                .expectEvents(
                        UserLoginFailedEvent.create(
                                userId,
                                "testuser",
                                "Invalid password",
                                "192.168.1.1",
                                "Mozilla/5.0",
                                5,
                                true
                        ),
                        UserAccountLockedEvent.createAutoLock(
                                userId,
                                "testuser",
                                "TOO_MANY_FAILED_ATTEMPTS",
                                "Account locked after 5 failed login attempts"
                        )
                );
    }
    
    @Test
    void shouldGrantRoleToUser() {
        // Given
        UserId userId = UserId.of("USER-001");
        UserId adminId = UserId.of("ADMIN-001");
        
        UserRegisteredEvent registrationEvent = UserRegisteredEvent.create(
                userId,
                "testuser",
                "hashedPassword123", // 패스워드 해시
                "Test User",
                "test@example.com",
                "010-1234-5678",
                Set.of("ROLE_TRADER"),
                "ADMIN-001"
        );
        
        GrantUserRoleCommand command = GrantUserRoleCommand.builder()
                .userId(userId)
                .roleName("ROLE_MANAGER")
                .grantedBy(adminId)
                .reason("Promotion to manager")
                .build();
        
        // When & Then
        fixture.given(registrationEvent)
                .when(command)
                .expectSuccessfulHandlerExecution()
                .expectEvents(
                        UserRoleGrantedEvent.create(
                                userId,
                                "testuser",
                                "ROLE_MANAGER",
                                adminId,
                                null,
                                "Promotion to manager"
                        )
                );
    }
    
    @Test
    void shouldLogoutUser() {
        // Given
        UserId userId = UserId.of("USER-001");
        
        UserRegisteredEvent registrationEvent = UserRegisteredEvent.create(
                userId,
                "testuser",
                "hashedPassword123", // 패스워드 해시
                "Test User",
                "test@example.com",
                "010-1234-5678",
                Set.of("ROLE_TRADER"),
                "ADMIN-001"
        );
        
        UserLoginSucceededEvent loginEvent = UserLoginSucceededEvent.create(
                userId,
                "testuser",
                "SESSION-123",
                "192.168.1.1",
                "Mozilla/5.0",
                null
        );
        
        LogoutUserCommand command = LogoutUserCommand.builder()
                .userId(userId)
                .sessionId("SESSION-123")
                .reason("USER_LOGOUT")
                .ipAddress("192.168.1.1")
                .build();
        
        // When & Then
        fixture.given(registrationEvent, loginEvent)
                .when(command)
                .expectSuccessfulHandlerExecution();
    }
}