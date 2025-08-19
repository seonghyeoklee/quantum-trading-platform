package com.quantum.kis.architecture;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.*;

import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * Quantum Adapter 독립성 및 아키텍처 검증 테스트
 * 
 * quantum-adapter 모듈의 독립성과 외부 시스템 격리 원칙들을 ArchUnit으로 강제한다:
 * 1. Core 도메인 모델에 직접 의존하지 않음 (우리가 최근 수정한 부분)
 * 2. 외부 API 클라이언트의 적절한 격리
 * 3. Rate Limiting 패턴의 일관성
 * 4. 모델 매핑의 명확한 분리
 * 5. KIS API 특화 규칙들
 */
@DisplayName("🔌 Quantum Adapter Independence Rules")
class AdapterIndependenceTest {

    private static final String BASE_PACKAGE = "com.quantum.kis";
    private static final JavaClasses classes = new ClassFileImporter()
            .importPackages(BASE_PACKAGE);

    @Test
    @DisplayName("어댑터는 quantum-core 도메인 모델에 직접 의존하지 않아야 한다")
    void adapter_should_not_depend_on_core_domain_models() {
        noClasses()
                .that().resideInAPackage("com.quantum.kis..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "com.quantum.core.domain.model..",
                        "com.quantum.core.domain.service.."
                )
                .because("어댑터는 도메인 모델에 직접 의존하지 않고 매핑을 통해 분리되어야 함")
                .check(classes);
    }

    @Test
    @DisplayName("KIS 어댑터 전용 모델은 독립적이어야 한다")
    void kis_adapter_models_should_be_independent() {
        classes()
                .that().resideInAPackage("..model..")
                .should().onlyDependOnClassesThat()
                .resideInAnyPackage(
                        "com.quantum.kis..",
                        "java..",
                        "com.fasterxml.jackson..",
                        "lombok..",
                        "jakarta.validation.."
                )
                .because("KIS 어댑터 모델은 외부 의존성을 최소화해야 함")
                .check(classes);
    }

    @Test
    @DisplayName("KisTimeframe은 어댑터 전용이어야 한다")
    void kis_timeframe_should_be_adapter_specific() {
        classes()
                .that().haveSimpleName("KisTimeframe")
                .should().resideInAPackage("..model.enums..")
                .andShould().beEnums()
                .because("KisTimeframe은 KIS API 전용 열거형이어야 함")
                .check(classes);
    }

    @Test
    @DisplayName("KisModelMapper는 도메인과 어댑터 모델 간 변환만 담당해야 한다")
    void kis_model_mapper_should_only_handle_model_conversion() {
        classes()
                .that().haveSimpleName("KisModelMapper")
                .should().resideInAPackage("..service..")
                .andShould().onlyDependOnClassesThat()
                .resideInAnyPackage(
                        "com.quantum.kis..",
                        "java..",
                        "org.springframework.stereotype..",
                        "lombok.."
                )
                .because("KisModelMapper는 모델 변환만 담당하고 외부 의존성을 최소화해야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Rate Limiter는 일관된 패턴을 사용해야 한다")
    void rate_limiter_should_use_consistent_pattern() {
        classes()
                .that().haveSimpleNameContaining("RateLimit")
                .should().resideInAPackage("..service..")
                .or().resideInAPackage("..config..")
                .because("Rate Limiting 관련 클래스는 서비스나 설정 패키지에 있어야 함")
                .check(classes);
    }

    @Test
    @DisplayName("외부 API 클라이언트는 Feign 인터페이스여야 한다")
    void external_api_clients_should_be_feign_interfaces() {
        classes()
                .that().haveSimpleNameEndingWith("FeignClient")
                .or().haveSimpleNameEndingWith("Client")
                .should().beInterfaces()
                .andShould().resideInAPackage("..client..")
                .because("외부 API 클라이언트는 Feign 인터페이스로 정의되어야 함")
                .check(classes);
    }

    @Test
    @DisplayName("KIS 서비스는 토큰 프로바이더에 의존해야 한다")
    void kis_services_should_depend_on_token_provider() {
        classes()
                .that().resideInAPackage("..service..")
                .and().haveSimpleNameStartingWith("Kis")
                .and().haveSimpleNameEndingWith("Service")
                .should().onlyAccessFieldsThat(field -> 
                    field.getName().contains("kisTokenProvider") ||
                    field.getName().contains("kisRateLimiter") ||
                    field.getName().contains("kisModelMapper") ||
                    field.getRawType().getSimpleName().contains("Feign") ||
                    field.getRawType().getPackageName().startsWith("java") ||
                    field.getRawType().getPackageName().startsWith("org.springframework")
                )
                .because("KIS 서비스는 토큰 프로바이더와 Rate Limiter에 의존해야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Configuration은 어댑터 설정에만 집중해야 한다")
    void configurations_should_focus_on_adapter_settings() {
        classes()
                .that().haveSimpleNameEndingWith("Config")
                .or().haveSimpleNameEndingWith("Configuration")
                .should().resideInAPackage("..config..")
                .andShould().onlyDependOnClassesThat()
                .resideInAnyPackage(
                        "com.quantum.kis..",
                        "java..",
                        "org.springframework..",
                        "feign.."
                )
                .because("Configuration은 어댑터 설정만 담당해야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Token Provider는 인터페이스와 구현체로 분리되어야 한다")
    void token_provider_should_be_separated_interface_and_implementation() {
        classes()
                .that().haveSimpleName("KisTokenProvider")
                .should().beInterfaces()
                .because("KisTokenProvider는 인터페이스여야 함");

        classes()
                .that().haveSimpleNameEndingWith("TokenProvider")
                .and().areNotInterfaces()
                .should().resideInAPackage("..service..")
                .because("Token Provider 구현체는 서비스 패키지에 있어야 함")
                .check(classes);
    }

    @Test
    @DisplayName("응답 모델은 불변이어야 한다")
    void response_models_should_be_immutable() {
        classes()
                .that().haveSimpleNameEndingWith("Response")
                .should().beRecords()
                .orShould().haveOnlyFinalFields()
                .because("응답 모델은 불변성을 보장해야 함")
                .check(classes);
    }

    @Test
    @DisplayName("요청 모델은 Builder 패턴을 사용해야 한다")
    void request_models_should_use_builder_pattern() {
        classes()
                .that().haveSimpleNameEndingWith("Request")
                .should().haveMethodThat(method -> method.getName().equals("builder"))
                .orShould().haveInnerClassThat(innerClass -> innerClass.getSimpleName().equals("Builder"))
                .because("요청 모델은 Builder 패턴을 사용해야 함")
                .check(classes);
    }

    @Test
    @DisplayName("KIS API 관련 상수는 열거형으로 정의되어야 한다")
    void kis_api_constants_should_be_defined_as_enums() {
        classes()
                .that().resideInAPackage("..model.enums..")
                .should().beEnums()
                .andShould().haveMethodThat(method -> !method.getName().equals("values") && !method.getName().equals("valueOf"))
                .because("KIS API 상수는 비즈니스 로직을 포함한 열거형이어야 함")
                .check(classes);
    }

    @Test
    @DisplayName("WebSocket 설정은 별도 패키지에 분리되어야 한다")
    void websocket_config_should_be_in_separate_package() {
        classes()
                .that().haveSimpleNameContaining("WebSocket")
                .should().resideInAPackage("..config..")
                .because("WebSocket 설정은 설정 패키지에 있어야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Rate Limit 정책은 환경별로 구성되어야 한다")
    void rate_limit_policy_should_be_configurable_by_environment() {
        classes()
                .that().haveSimpleNameContaining("RateLimit")
                .and().haveSimpleNameEndingWith("Config")
                .should().haveFieldThat(field -> field.getName().contains("environment"))
                .orShould().dependOnClassesThat().resideInAnyPackage("org.springframework.boot.context.properties..")
                .because("Rate Limit 정책은 환경별로 구성 가능해야 함")
                .check(classes);
    }

    @Test
    @DisplayName("API 클라이언트는 Circuit Breaker 패턴을 고려해야 한다")
    void api_clients_should_consider_circuit_breaker_pattern() {
        classes()
                .that().haveSimpleNameEndingWith("Service")
                .and().resideInAPackage("..service..")
                .should().haveMethodThat(method -> 
                    method.getName().contains("isAvailable") ||
                    method.getName().contains("getStatus") ||
                    method.getParameterTypes().stream().anyMatch(type -> 
                        type.getSimpleName().contains("Timeout") ||
                        type.getSimpleName().contains("Retry")
                    )
                )
                .orShould().dependOnClassesThat().resideInAnyPackage("org.springframework.retry..")
                .because("API 클라이언트는 장애 대응을 위한 패턴을 구현해야 함")
                .check(classes);
    }

    @Test
    @DisplayName("보안 정보는 하드코딩하지 않아야 한다")
    void security_information_should_not_be_hardcoded() {
        noClasses()
                .that().resideInAPackage("com.quantum.kis..")
                .should().haveFieldThat(field -> 
                    field.getName().toLowerCase().contains("password") ||
                    field.getName().toLowerCase().contains("secret") ||
                    field.getName().toLowerCase().contains("key")
                )
                .because("보안 정보는 하드코딩하지 않고 환경변수나 설정을 통해 주입받아야 함")
                .check(classes);
    }
}