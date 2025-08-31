package com.quantum.web.config;

import com.quantum.trading.platform.query.repository.UserViewRepository;
import com.quantum.trading.platform.shared.command.RegisterUserCommand;
import com.quantum.trading.platform.shared.value.UserId;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import java.util.Set;
import java.util.UUID;

/**
 * 애플리케이션 시작 시 초기 사용자 데이터를 생성하는 컴포넌트
 * 
 * 권한별 기본 계정을 생성하여 시스템 초기 설정을 완료합니다.
 * - ADMIN: 시스템 관리자 (모든 권한)
 * - MANAGER: 운영 관리자 (포트폴리오 및 거래 관리)
 * - TRADER: 거래자 (거래 실행만 가능)
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class DataInitializer implements CommandLineRunner {

    private final UserViewRepository userViewRepository;
    private final PasswordEncoder passwordEncoder;
    private final CommandGateway commandGateway;

    @Override
    public void run(String... args) {
        log.info("🚀 Starting initial data creation...");
        
        createInitialUsers();
        
        log.info("✅ Initial data creation completed successfully!");
    }

    /**
     * 권한별 초기 사용자 계정 생성 - Event Sourcing을 통한 올바른 방식
     */
    private void createInitialUsers() {
        // 1. ADMIN 계정 생성
        createUserWithEventSourcing(
            "admin", 
            "admin", 
            "시스템 관리자", 
            "admin@quantum-trading.com", 
            "+82-10-1234-5678",
            Set.of("ADMIN", "MANAGER", "TRADER")
        );

        // 2. MANAGER 계정 생성
        createUserWithEventSourcing(
            "manager", 
            "manager123!", 
            "운영 관리자", 
            "manager@quantum-trading.com", 
            "+82-10-2345-6789",
            Set.of("MANAGER", "TRADER")
        );

        // 3. TRADER 계정 생성
        createUserWithEventSourcing(
            "trader", 
            "trader123!", 
            "거래자", 
            "trader@quantum-trading.com", 
            "+82-10-3456-7890",
            Set.of("TRADER")
        );

        // 4. 테스트용 계정들 생성
        createUserWithEventSourcing(
            "admin.test", 
            "test123!", 
            "테스트 관리자", 
            "admin.test@quantum-trading.com", 
            "+82-10-1111-1111",
            Set.of("ADMIN", "MANAGER", "TRADER")
        );

        createUserWithEventSourcing(
            "manager.test", 
            "test123!", 
            "테스트 매니저", 
            "manager.test@quantum-trading.com", 
            "+82-10-2222-2222",
            Set.of("MANAGER", "TRADER")
        );

        createUserWithEventSourcing(
            "trader.test", 
            "test123!", 
            "테스트 트레이더", 
            "trader.test@quantum-trading.com", 
            "+82-10-3333-3333",
            Set.of("TRADER")
        );
    }

    /**
     * Event Sourcing을 통한 사용자 생성 (올바른 CQRS 패턴)
     */
    private void createUserWithEventSourcing(String username, String password, String name, 
                                            String email, String phone, Set<String> roles) {
        
        // 이미 존재하는 사용자인지 확인 (Query Side에서 확인)
        if (userViewRepository.existsByUsername(username)) {
            log.debug("⏭️  User '{}' already exists, skipping creation", username);
            return;
        }

        try {
            // 고유한 사용자 ID 생성
            UserId userId = UserId.of("USER-" + UUID.randomUUID().toString().toUpperCase());
            
            // 비밀번호 해시화 (Application Layer에서 처리)
            String hashedPassword = passwordEncoder.encode(password);

            // RegisterUserCommand 생성 및 전송 (Command Side)
            RegisterUserCommand command = new RegisterUserCommand(
                    userId,
                    username,
                    hashedPassword, // 이미 해시된 비밀번호
                    name,
                    email,
                    phone,
                    roles,
                    null // SYSTEM 사용자는 null
            );

            // Command Gateway를 통해 Event Sourcing 시스템으로 전송
            commandGateway.sendAndWait(command);

            log.info("✅ Created user via Event Sourcing: {} ({}), roles: {}", username, name, roles);
            
            // 보안상 실제 비밀번호는 로그에 출력하지 않음 (개발 시에만 임시)
            if (log.isDebugEnabled()) {
                log.debug("🔐 Initial password for {}: {}", username, password);
            }

        } catch (Exception e) {
            log.error("❌ Failed to create user '{}' via Event Sourcing: {}", username, e.getMessage(), e);
            throw new RuntimeException("Failed to initialize user: " + username, e);
        }
    }
}